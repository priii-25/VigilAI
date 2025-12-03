"""
AI service for processing and analyzing competitor data
"""
from typing import Dict, List, Optional
import google.generativeai as genai
from loguru import logger
from src.core.config import settings


class AIProcessor:
    """AI-powered data processing and analysis"""
    
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def analyze_pricing_change(self, old_data: Dict, new_data: Dict) -> Dict:
        """Analyze pricing changes and determine impact"""
        
        prompt = f"""
Analyze the following pricing change for a competitor:

OLD PRICING:
{self._format_pricing(old_data)}

NEW PRICING:
{self._format_pricing(new_data)}

Provide:
1. Summary of key changes (2-3 sentences)
2. Impact score (0-10, where 10 is highest impact)
3. Recommended action for sales team
4. Talking points for objection handling

Format as JSON with keys: summary, impact_score, recommended_action, talking_points
"""
        
        try:
            response = await self._call_gemini(prompt)
            result = self._parse_json_response(response)
            logger.info("Pricing change analysis completed")
            return result
        except Exception as e:
            logger.error(f"Error analyzing pricing change: {str(e)}")
            return self._default_analysis()
    
    async def analyze_hiring_trends(self, careers_data: Dict) -> Dict:
        """Analyze hiring data to detect strategic pivots"""
        
        job_postings = careers_data.get('job_postings', [])
        trends = careers_data.get('hiring_trends', {})
        
        prompt = f"""
Analyze the following hiring data from a competitor:

TOTAL OPENINGS: {trends.get('total_openings', 0)}

JOB POSTINGS:
{self._format_jobs(job_postings[:10])}

DEPARTMENT BREAKDOWN:
{trends.get('departments', {})}

Determine:
1. What strategic direction is this company taking?
2. Are they building new capabilities? (mobile, AI, enterprise, etc.)
3. Impact score (0-10) - how relevant is this to our competitive position?
4. Recommended intelligence gathering or response

Format as JSON with keys: strategic_direction, new_capabilities, impact_score, recommendations
"""
        
        try:
            response = await self._call_gemini(prompt)
            result = self._parse_json_response(response)
            logger.info("Hiring trends analysis completed")
            return result
        except Exception as e:
            logger.error(f"Error analyzing hiring trends: {str(e)}")
            return self._default_analysis()
    
    async def generate_battlecard_section(self, competitor_name: str, section_type: str, data: Dict) -> str:
        """Generate specific battlecard section content"""
        
        prompts = {
            'overview': f"Create a concise overview (3-4 sentences) of {competitor_name} based on: {data}",
            'strengths': f"List 5 key strengths of {competitor_name} based on: {data}",
            'weaknesses': f"List 5 key weaknesses of {competitor_name} based on: {data}",
            'objections': f"Create 3 objection handling scripts for competing against {competitor_name}. Data: {data}",
            'kill_points': f"Identify 3-5 'kill points' - reasons why we win against {competitor_name}. Data: {data}"
        }
        
        prompt = prompts.get(section_type, "")
        if not prompt:
            return ""
        
        try:
            response = await self._call_gemini(prompt)
            logger.info(f"Generated {section_type} section for {competitor_name}")
            return response
        except Exception as e:
            logger.error(f"Error generating battlecard section: {str(e)}")
            return ""
    
    async def summarize_content_change(self, article_data: Dict) -> Dict:
        """Summarize competitor content/blog post"""
        
        prompt = f"""
Analyze this competitor article/announcement:

TITLE: {article_data.get('title', 'Unknown')}
SUMMARY: {article_data.get('summary', 'No summary available')}
DATE: {article_data.get('date', 'Unknown')}

Provide:
1. Key takeaway (1 sentence)
2. Business implication for us
3. Impact score (0-10)
4. Category (product_launch, partnership, thought_leadership, hiring, funding)

Format as JSON with keys: takeaway, implication, impact_score, category
"""
        
        try:
            response = await self._call_gemini(prompt)
            result = self._parse_json_response(response)
            logger.info("Content change summarized")
            return result
        except Exception as e:
            logger.error(f"Error summarizing content: {str(e)}")
            return self._default_analysis()
    
    async def detect_noise(self, html_diff: str) -> bool:
        """Determine if HTML change is substantive or just noise"""
        
        # Quick heuristics first
        noise_indicators = [
            'timestamp', 'date', 'cookie', 'session', 'analytics',
            'gtm', 'facebook', 'twitter', 'linkedin', 'pixel'
        ]
        
        if any(indicator in html_diff.lower() for indicator in noise_indicators):
            if len(html_diff) < 500:  # Small changes with tracking = noise
                return True
        
        # For larger changes, use AI
        if len(html_diff) > 1000:
            prompt = f"""
Is this HTML change substantive content or just noise (tracking codes, timestamps, etc.)?

CHANGE:
{html_diff[:1000]}

Answer with just: SUBSTANTIVE or NOISE
"""
            try:
                response = await self._call_gemini(prompt)
                return 'NOISE' in response.upper()
            except:
                return False
        
        return False
    
    async def _call_gemini(self, prompt: str, max_tokens: int = 2000) -> str:
        """Call Google Gemini API"""
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise
    
    def _format_pricing(self, data: Dict) -> str:
        """Format pricing data for prompt"""
        plans = data.get('plans', [])
        if not plans:
            return "No pricing data available"
        
        formatted = []
        for plan in plans[:5]:
            formatted.append(f"- {plan.get('name', 'Unknown')}: {plan.get('price', 'N/A')}")
        return '\n'.join(formatted)
    
    def _format_jobs(self, jobs: List[Dict]) -> str:
        """Format job postings for prompt"""
        if not jobs:
            return "No job postings available"
        
        formatted = []
        for job in jobs:
            formatted.append(f"- {job.get('title', 'Unknown')} | {job.get('department', 'N/A')} | {job.get('location', 'N/A')}")
        return '\n'.join(formatted)
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from AI response"""
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        return self._default_analysis()
    
    def _default_analysis(self) -> Dict:
        """Default analysis response"""
        return {
            'summary': 'Analysis pending',
            'impact_score': 5.0,
            'recommended_action': 'Review manually',
            'category': 'unknown'
        }
