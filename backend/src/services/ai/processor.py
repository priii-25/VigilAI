"""
AI service for processing and analyzing competitor data

Enhanced with:
- Circuit breaker for fault tolerance
- Prompt registry for versioned prompts
- Change detection to skip unchanged content
- Fallback cache for graceful degradation
"""
from typing import Dict, List, Optional, Any
import asyncio
import json
import re
import google.generativeai as genai
from loguru import logger
from src.core.config import settings
from src.core.circuit_breaker import with_circuit_breaker, CircuitBreakerOpenError
from src.services.ai.prompt_registry import prompt_registry, get_prompt_settings
from src.utils.ai_utils import gemini_limiter


class AIProcessor:
    """
    AI-powered data processing and analysis.
    
    Features:
    - Circuit breaker protection for LLM API
    - Versioned prompts via prompt registry
    - Exponential backoff retry logic
    - Graceful degradation with cached results
    """
    
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self._fallback_cache: Dict[str, Any] = {}  # In-memory fallback
    
    @with_circuit_breaker("llm_api")
    async def analyze_pricing_change(self, old_data: Dict, new_data: Dict) -> Dict:
        """
        Analyze pricing changes and determine impact.
        
        Uses circuit breaker to prevent cascading failures.
        Falls back to cached/default analysis if LLM unavailable.
        """
        cache_key = f"pricing:{hash(str(old_data))}-{hash(str(new_data))}"
        
        try:
            # Use versioned prompt from registry
            prompt = prompt_registry.render(
                "analyze_pricing",
                old_pricing=self._format_pricing(old_data),
                new_pricing=self._format_pricing(new_data)
            )
            settings_config = get_prompt_settings("analyze_pricing")
            
            response = await self._call_gemini(
                prompt,
                temperature=settings_config.get("temperature", 0.3)
            )
            result = self._parse_json_response(response)
            
            # Cache successful result for fallback
            self._fallback_cache[cache_key] = result
            
            logger.info("Pricing change analysis completed", impact_score=result.get("impact_score"))
            return result
            
        except CircuitBreakerOpenError:
            logger.warning("Circuit breaker open, using fallback for pricing analysis")
            return self._fallback_cache.get(cache_key, self._default_analysis())
        except Exception as e:
            logger.error(f"Error analyzing pricing change: {str(e)}")
            return self._fallback_cache.get(cache_key, self._default_analysis())
    
    @with_circuit_breaker("llm_api")
    async def analyze_hiring_trends(self, careers_data: Dict) -> Dict:
        """
        Analyze hiring data to detect strategic pivots.
        
        Protected by circuit breaker with graceful degradation.
        """
        job_postings = careers_data.get('job_postings', [])
        trends = careers_data.get('hiring_trends', {})
        
        try:
            prompt = prompt_registry.render(
                "analyze_hiring",
                competitor_name=careers_data.get('competitor_name', 'Unknown'),
                job_postings=self._format_jobs(job_postings[:15])
            )
            settings_config = get_prompt_settings("analyze_hiring")
            
            response = await self._call_gemini(
                prompt,
                temperature=settings_config.get("temperature", 0.3)
            )
            result = self._parse_json_response(response)
            
            logger.info("Hiring trends analysis completed", total_jobs=len(job_postings))
            return result
            
        except CircuitBreakerOpenError:
            logger.warning("Circuit breaker open for hiring analysis")
            return self._default_hiring_analysis(trends)
        except Exception as e:
            logger.error(f"Error analyzing hiring trends: {str(e)}")
            return self._default_hiring_analysis(trends)
    
    @with_circuit_breaker("llm_api")
    async def generate_battlecard_section(
        self,
        competitor_name: str,
        section_type: str,
        data: Dict
    ) -> Dict:
        """
        Generate specific battlecard section content.
        
        Uses prompt registry for consistent, versioned prompts.
        """
        try:
            prompt = prompt_registry.render(
                "generate_battlecard_section",
                competitor_name=competitor_name,
                section_type=section_type,
                context_data=json.dumps(data, indent=2, default=str)[:3000]
            )
            settings_config = get_prompt_settings("generate_battlecard_section")
            
            response = await self._call_gemini(
                prompt,
                temperature=settings_config.get("temperature", 0.4),
                max_tokens=settings_config.get("max_tokens", 3000)
            )
            
            result = self._parse_json_response(response)
            logger.info(f"Generated {section_type} section for {competitor_name}")
            return result
            
        except CircuitBreakerOpenError:
            logger.warning(f"Circuit breaker open, returning cached {section_type}")
            return {"content": f"[{section_type.upper()} - Analysis pending]", "key_points": []}
        except Exception as e:
            logger.error(f"Error generating battlecard section: {str(e)}")
            return {"content": "", "key_points": []}
    
    @with_circuit_breaker("llm_api")
    async def summarize_content_change(self, article_data: Dict) -> Dict:
        """Summarize competitor content/blog post"""
        try:
            prompt = prompt_registry.render(
                "summarize_content",
                source_url=article_data.get('url', 'Unknown'),
                content=f"""
Title: {article_data.get('title', 'Unknown')}
Summary: {article_data.get('summary', 'No summary available')}
Date: {article_data.get('date', 'Unknown')}
"""
            )
            
            response = await self._call_gemini(prompt)
            result = self._parse_json_response(response)
            
            logger.info("Content change summarized", title=article_data.get('title', '')[:50])
            return result
            
        except CircuitBreakerOpenError:
            return self._default_analysis()
        except Exception as e:
            logger.error(f"Error summarizing content: {str(e)}")
            return self._default_analysis()
    
    @with_circuit_breaker("llm_api")
    async def detect_noise(self, html_diff: str) -> Dict:
        """
        Determine if HTML change is substantive or just noise.
        
        Uses prompt registry for consistent noise detection.
        Returns structured response with confidence.
        """
        # Quick heuristics first (no LLM needed)
        noise_indicators = [
            'timestamp', 'date', 'cookie', 'session', 'analytics',
            'gtm', 'facebook', 'twitter', 'linkedin', 'pixel',
            'csrf', 'nonce', 'cache-bust', 'version='
        ]
        
        if any(indicator in html_diff.lower() for indicator in noise_indicators):
            if len(html_diff) < 500:  # Small changes with tracking = noise
                return {
                    "is_noise": True,
                    "confidence": 0.9,
                    "reason": "Contains tracking/session data with minimal size",
                    "change_type": "technical",
                    "should_alert": False
                }
        
        # For larger changes, use AI
        if len(html_diff) > 1000:
            try:
                prompt = prompt_registry.render(
                    "detect_noise",
                    html_diff=html_diff[:2000]  # Limit size
                )
                
                response = await self._call_gemini(prompt)
                result = self._parse_json_response(response)
                
                return {
                    "is_noise": result.get("is_noise", False),
                    "confidence": result.get("confidence", 0.5),
                    "reason": result.get("reason", "AI analysis"),
                    "change_type": result.get("change_type", "unknown"),
                    "should_alert": result.get("should_alert", True)
                }
                
            except Exception as e:
                logger.warning(f"Noise detection failed, assuming substantive: {e}")
                return {
                    "is_noise": False,
                    "confidence": 0.5,
                    "reason": "Analysis unavailable, defaulting to substantive",
                    "change_type": "unknown",
                    "should_alert": True
                }
        
        # Medium-sized changes without noise indicators = likely substantive
        return {
            "is_noise": False,
            "confidence": 0.7,
            "reason": "No obvious noise indicators detected",
            "change_type": "content",
            "should_alert": True
        }
    
    @with_circuit_breaker("llm_api")
    async def generate_objection_handling(
        self,
        competitor_name: str,
        competitor_info: Dict,
        our_strengths: List[str]
    ) -> Dict:
        """Generate objection handling responses for battlecards"""
        try:
            prompt = prompt_registry.render(
                "generate_objection_handling",
                competitor_name=competitor_name,
                competitor_info=json.dumps(competitor_info, default=str)[:2000],
                our_strengths="\n".join(f"- {s}" for s in our_strengths)
            )
            
            response = await self._call_gemini(prompt)
            return self._parse_json_response(response)
            
        except Exception as e:
            logger.error(f"Error generating objection handling: {e}")
            return {"objections": []}
    
    async def _call_gemini(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> str:
        """
        Call Google Gemini API with rate limiting, retry logic and exponential backoff.
        
        Implements proper exponential backoff:
        - Retry after 30s → 60s → 90s (Aggressive backoff for free tier)
        - Maximum 3 retries
        """
        # Ensure we respect global rate limit before even trying
        await gemini_limiter.acquire()
        
        max_retries = 3
        # Aggressive backoff for 429s since free tier quota reset takes time (usually 1 minute)
        base_delay = 30  
        
        for attempt in range(max_retries):
            try:
                # Configure generation settings
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
                
                response = await self.model.generate_content_async(
                    prompt,
                    generation_config=generation_config
                )
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                
                # Check for rate limiting
                if "429" in error_msg or "Quota exceeded" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt == max_retries - 1:
                        logger.error(f"Gemini API rate limit exceeded after {max_retries} retries")
                        raise
                    
                    # Exponential backoff
                    delay = base_delay * (attempt + 1) # 30s, 60s, 90s
                    logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    
                    # Re-acquire rate limit token before retry
                    await gemini_limiter.acquire()
                    
                else:
                    logger.error(f"Gemini API error: {error_msg}")
                    raise
        
        raise Exception("Max retries exceeded for Gemini API call")
    
    def _format_pricing(self, data: Dict) -> str:
        """Format pricing data for prompt"""
        plans = data.get('plans', [])
        if not plans:
            return "No pricing data available"
        
        formatted = []
        for plan in plans[:5]:
            features = plan.get('features', [])[:3]
            features_str = ", ".join(features) if features else "No features listed"
            formatted.append(
                f"- {plan.get('name', 'Unknown')}: {plan.get('price', 'N/A')} "
                f"({features_str})"
            )
        return '\n'.join(formatted)
    
    def _format_jobs(self, jobs: List[Dict]) -> str:
        """Format job postings for prompt"""
        if not jobs:
            return "No job postings available"
        
        formatted = []
        for job in jobs:
            formatted.append(
                f"- {job.get('title', 'Unknown')} | "
                f"{job.get('department', 'N/A')} | "
                f"{job.get('location', 'N/A')}"
            )
        return '\n'.join(formatted)
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from AI response with robust handling"""
        # Try to extract JSON from response
        # Handle cases where JSON is wrapped in markdown code blocks
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        # Try direct parse first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON object in response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        logger.warning("Failed to parse JSON from AI response")
        return self._default_analysis()
    
    def _default_analysis(self) -> Dict:
        """Default analysis response when AI is unavailable"""
        return {
            'summary': 'Analysis pending - AI temporarily unavailable',
            'impact_score': 5.0,
            'recommended_action': 'Review manually when AI service recovers',
            'category': 'unknown',
            'confidence': 0.0
        }
    
    def _default_hiring_analysis(self, trends: Dict) -> Dict:
        """Default hiring analysis based on available data"""
        total = trends.get('total_openings', 0)
        
        return {
            'strategic_direction': 'Unable to analyze - AI temporarily unavailable',
            'new_capabilities': [],
            'impact_score': 5.0,
            'recommendations': ['Monitor hiring pages manually'],
            'summary': f'{total} open positions detected, analysis pending'
        }


# Singleton instance for convenience
_processor_instance: Optional[AIProcessor] = None


def get_ai_processor() -> AIProcessor:
    """Get or create AI processor instance"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = AIProcessor()
    return _processor_instance
