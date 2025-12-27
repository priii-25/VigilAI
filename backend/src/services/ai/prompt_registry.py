"""
Prompt Registry - Version-controlled prompt templates.
Treats prompts as code with versioning and audit trail.

Benefits:
- Version control for prompts
- A/B testing capability
- Consistent formatting
- Audit trail
"""
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger


@dataclass
class PromptTemplate:
    """Versioned prompt template"""
    name: str
    version: str
    template: str
    description: str
    parameters: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # AI settings for deterministic outputs
    temperature: float = 0.3  # Low for consistency
    max_tokens: int = 2000
    response_format: Optional[str] = "json"  # Structured output


class PromptRegistry:
    """
    Central registry for all AI prompts.
    
    Features:
    - Version control
    - Parameter validation
    - Consistent rendering
    - Audit trail
    
    Example usage:
        registry = PromptRegistry()
        
        # Get rendered prompt
        prompt = registry.render(
            "analyze_pricing",
            old_pricing="$99/mo",
            new_pricing="$149/mo"
        )
        
        # Use in AI call with settings
        template = registry.get("analyze_pricing")
        response = await llm.generate(
            prompt,
            temperature=template.temperature
        )
    """
    
    def __init__(self):
        self._prompts: Dict[str, Dict[str, PromptTemplate]] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompt templates"""
        
        # ===== PRICING ANALYSIS =====
        self.register(PromptTemplate(
            name="analyze_pricing",
            version="1.0.0",
            template="""Analyze the following competitor pricing change:

## Previous Pricing
{old_pricing}

## New Pricing
{new_pricing}

Provide your analysis in the following JSON format:
{{
    "impact_score": <number 1-10>,
    "summary": "<brief summary of the change>",
    "direction": "<increase|decrease|restructure>",
    "percentage_change": <estimated percentage or null>,
    "implications": [
        "<implication 1>",
        "<implication 2>",
        "<implication 3>"
    ],
    "recommended_response": "<specific action to take>",
    "urgency": "<low|medium|high|critical>"
}}

Be specific and actionable in your analysis.""",
            description="Analyzes competitor pricing changes and provides strategic recommendations",
            parameters=["old_pricing", "new_pricing"],
            temperature=0.3
        ))
        
        # ===== BATTLECARD GENERATION =====
        self.register(PromptTemplate(
            name="generate_battlecard_section",
            version="1.0.0",
            template="""Generate a sales battlecard section for the competitor: {competitor_name}

## Section Type
{section_type}

## Available Context Data
{context_data}

Generate content for the {section_type} section that sales reps can use in competitive situations.

Respond with JSON:
{{
    "content": "<markdown formatted content for this section>",
    "key_points": ["<point1>", "<point2>", "<point3>"],
    "talk_tracks": ["<sample phrase 1>", "<sample phrase 2>"],
    "confidence": <0.0-1.0 confidence in the analysis>
}}

Make the content specific, actionable, and directly usable in sales conversations.""",
            description="Generates specific battlecard sections (strengths, weaknesses, kill points, etc.)",
            parameters=["competitor_name", "section_type", "context_data"],
            temperature=0.4,
            max_tokens=3000
        ))
        
        # ===== NOISE DETECTION =====
        self.register(PromptTemplate(
            name="detect_noise",
            version="1.0.0",
            template="""Analyze this HTML/content diff and determine if it represents a substantive business change or just noise:

## Content Diff
{html_diff}

Respond with JSON:
{{
    "is_noise": <true if cosmetic/meaningless, false if substantive>,
    "confidence": <0.0-1.0>,
    "reason": "<brief explanation>",
    "change_type": "<pricing|feature|content|hiring|cosmetic|technical>",
    "should_alert": <true if this warrants an alert to users>
}}

Noise includes: CSS changes, timestamp updates, session IDs, tracking parameters, minor typos.
Substantive includes: Pricing changes, feature updates, new products, team changes.""",
            description="Determines if content change is noise or substantive",
            parameters=["html_diff"],
            temperature=0.2
        ))
        
        # ===== HIRING ANALYSIS =====
        self.register(PromptTemplate(
            name="analyze_hiring",
            version="1.0.0",
            template="""Analyze the following job postings from {competitor_name} to identify strategic signals:

## Job Postings
{job_postings}

Provide analysis in JSON format:
{{
    "total_roles": <number>,
    "strategic_signals": [
        {{
            "signal": "<description of signal>",
            "evidence": "<supporting job titles/requirements>",
            "implication": "<what this means for competition>"
        }}
    ],
    "investment_areas": ["<area1>", "<area2>"],
    "technology_focus": ["<tech1>", "<tech2>"],
    "growth_indicator": "<aggressive|moderate|stable|contracting>",
    "summary": "<2-3 sentence summary of hiring strategy>"
}}""",
            description="Analyzes job postings to detect strategic pivots and investment areas",
            parameters=["competitor_name", "job_postings"],
            temperature=0.3
        ))
        
        # ===== CONTENT SUMMARIZATION =====
        self.register(PromptTemplate(
            name="summarize_content",
            version="1.0.0",
            template="""Summarize the following competitor content for competitive intelligence:

## Source
{source_url}

## Content
{content}

Provide a JSON response:
{{
    "title": "<article/content title>",
    "summary": "<2-3 sentence summary>",
    "key_announcements": ["<announcement1>", "<announcement2>"],
    "competitive_implications": "<how this affects our competitive position>",
    "category": "<product|marketing|leadership|partnership|other>",
    "sentiment": "<positive|neutral|negative>",
    "importance": <1-10>
}}""",
            description="Summarizes competitor blog posts, announcements, and content",
            parameters=["source_url", "content"],
            temperature=0.3
        ))
        
        # ===== OBJECTION HANDLING =====
        self.register(PromptTemplate(
            name="generate_objection_handling",
            version="1.0.0",
            template="""Generate objection handling responses for common objections when competing against {competitor_name}.

## Competitor Information
{competitor_info}

## Our Product Strengths
{our_strengths}

Generate 5 common objections and responses in JSON:
{{
    "objections": [
        {{
            "objection": "<common objection sales hears>",
            "response": "<recommended response>",
            "proof_points": ["<evidence1>", "<evidence2>"],
            "follow_up_question": "<question to ask the prospect>"
        }}
    ]
}}

Make responses natural and conversational, not scripted.""",
            description="Generates objection handling content for battlecards",
            parameters=["competitor_name", "competitor_info", "our_strengths"],
            temperature=0.5,
            max_tokens=3000
        ))
        
        # ===== COMPETITIVE POSITIONING =====
        self.register(PromptTemplate(
            name="generate_positioning",
            version="1.0.0",
            template="""Create competitive positioning messaging against {competitor_name}.

## Our Product
{our_product}

## Competitor Profile
{competitor_profile}

## Target Audience
{target_audience}

Generate positioning in JSON:
{{
    "primary_differentiator": "<single most important difference>",
    "value_proposition": "<why choose us over them>",
    "messaging_pillars": [
        {{
            "pillar": "<theme>",
            "our_strength": "<what we do well>",
            "their_weakness": "<where they fall short>",
            "proof": "<evidence>"
        }}
    ],
    "elevator_pitch": "<30 second pitch against this competitor>",
    "when_we_win": "<scenarios where we typically win>",
    "when_they_win": "<scenarios where they typically win>"
}}""",
            description="Creates competitive positioning and messaging",
            parameters=["competitor_name", "our_product", "competitor_profile", "target_audience"],
            temperature=0.4,
            max_tokens=3000
        ))
    
    def register(self, prompt: PromptTemplate):
        """Register a prompt template"""
        if prompt.name not in self._prompts:
            self._prompts[prompt.name] = {}
        self._prompts[prompt.name][prompt.version] = prompt
        logger.debug(f"Registered prompt: {prompt.name} v{prompt.version}")
    
    def get(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[PromptTemplate]:
        """
        Get prompt template by name and optional version.
        
        Args:
            name: Prompt name
            version: Specific version or None for latest
            
        Returns:
            PromptTemplate or None if not found
        """
        if name not in self._prompts:
            logger.warning(f"Prompt not found: {name}")
            return None
        
        versions = self._prompts[name]
        if version:
            return versions.get(version)
        
        # Return latest version
        latest = max(versions.keys())
        return versions[latest]
    
    def render(
        self,
        name: str,
        version: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Render prompt with parameters.
        
        Args:
            name: Prompt name
            version: Optional specific version
            **kwargs: Template parameters
            
        Returns:
            Rendered prompt string
            
        Raises:
            ValueError: If prompt not found or parameters missing
        """
        prompt = self.get(name, version)
        if not prompt:
            raise ValueError(f"Prompt not found: {name}")
        
        # Validate parameters
        missing = [p for p in prompt.parameters if p not in kwargs]
        if missing:
            raise ValueError(f"Missing parameters for {name}: {missing}")
        
        # Extra parameters are allowed but logged
        extra = [k for k in kwargs if k not in prompt.parameters]
        if extra:
            logger.debug(f"Extra parameters ignored for {name}: {extra}")
        
        return prompt.template.format(**kwargs)
    
    def list_prompts(self) -> List[Dict]:
        """List all registered prompts with versions"""
        result = []
        for name, versions in self._prompts.items():
            for version, template in versions.items():
                result.append({
                    "name": name,
                    "version": version,
                    "description": template.description,
                    "parameters": template.parameters
                })
        return result
    
    def get_settings(self, name: str, version: Optional[str] = None) -> Dict:
        """
        Get AI settings for a prompt.
        
        Returns temperature, max_tokens, etc. for consistent AI calls.
        """
        prompt = self.get(name, version)
        if not prompt:
            return {
                "temperature": 0.3,
                "max_tokens": 2000,
                "response_format": "json"
            }
        
        return {
            "temperature": prompt.temperature,
            "max_tokens": prompt.max_tokens,
            "response_format": prompt.response_format
        }


# Global registry instance
prompt_registry = PromptRegistry()


def get_prompt(name: str, version: Optional[str] = None, **kwargs) -> str:
    """Convenience function to render a prompt"""
    return prompt_registry.render(name, version, **kwargs)


def get_prompt_settings(name: str) -> Dict:
    """Convenience function to get prompt AI settings"""
    return prompt_registry.get_settings(name)
