"""
Perplexity API integration for real-time news and competitive intelligence
Production-ready with error handling and rate limiting
"""
from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta
from loguru import logger
from src.core.config import settings
import time
import json


class PerplexityService:
    """Perplexity API service for news aggregation and research"""
    
    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.rate_limit_delay = 1.0  # seconds
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def search_competitor_news(
        self,
        competitor_name: str,
        days_back: int = 7,
        max_results: int = 10
    ) -> Dict:
        """
        Search for recent news about a competitor
        
        Args:
            competitor_name: Name of the competitor company
            days_back: Number of days to search back
            max_results: Maximum number of results
            
        Returns:
            Dict containing news articles and analysis
        """
        logger.info(f"Searching news for {competitor_name} (last {days_back} days)")
        
        query = f"{competitor_name} company news product launch funding partnership acquisition"
        
        news_data = {
            'competitor': competitor_name,
            'search_date': datetime.utcnow().isoformat(),
            'articles': [],
            'summary': {
                'total_results': 0,
                'categories': {},
                'key_topics': []
            }
        }
        
        try:
            self._rate_limit()
            
            payload = {
                "model": "sonar-pro",  # Perplexity's production model
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a competitive intelligence analyst. Provide factual, sourced information about companies."
                    },
                    {
                        "role": "user",
                        "content": f"Find and summarize the most important news about {competitor_name} from the last {days_back} days. Include: product launches, funding rounds, partnerships, acquisitions, executive changes, and major announcements. For each item, provide: title, date, summary, and source URL."
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.2,
                "return_citations": True,
                "return_images": False
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Parse response
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            citations = result.get('citations', [])
            
            # Extract structured news items
            news_items = self._parse_news_response(content, citations)
            news_data['articles'] = news_items
            news_data['summary']['total_results'] = len(news_items)
            
            # Categorize news
            news_data['summary']['categories'] = self._categorize_news(news_items)
            news_data['summary']['key_topics'] = self._extract_key_topics(content)
            
            logger.info(f"Found {len(news_items)} news items for {competitor_name}")
            
        except requests.RequestException as e:
            logger.error(f"Error fetching news from Perplexity: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing Perplexity response: {str(e)}")
        
        return news_data
    
    def search_industry_trends(self, industry: str, topics: List[str]) -> Dict:
        """Search for industry trends and insights"""
        logger.info(f"Searching industry trends for {industry}")
        
        topics_str = ', '.join(topics)
        query = f"Latest trends and insights in {industry} industry related to {topics_str}"
        
        trends_data = {
            'industry': industry,
            'search_date': datetime.utcnow().isoformat(),
            'trends': [],
            'insights': ''
        }
        
        try:
            self._rate_limit()
            
            payload = {
                "model": "sonar-pro",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an industry analyst providing strategic insights."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze the latest trends in the {industry} industry, focusing on: {topics_str}. Provide key trends, emerging technologies, market shifts, and strategic implications."
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.3
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            trends_data['insights'] = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            logger.info(f"Retrieved industry trends for {industry}")
            
        except requests.RequestException as e:
            logger.error(f"Error fetching industry trends: {str(e)}")
        
        return trends_data
    
    def search_funding_rounds(self, competitor_name: str) -> Dict:
        """Search for funding and financial news"""
        logger.info(f"Searching funding information for {competitor_name}")
        
        funding_data = {
            'competitor': competitor_name,
            'search_date': datetime.utcnow().isoformat(),
            'funding_rounds': [],
            'valuation': None,
            'investors': []
        }
        
        try:
            self._rate_limit()
            
            payload = {
                "model": "sonar-pro",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Find information about {competitor_name}'s funding rounds, investors, and current valuation. Include dates, amounts, lead investors, and any recent financial news."
                    }
                ],
                "max_tokens": 1000,
                "return_citations": True
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            funding_data['raw_analysis'] = content
            
            logger.info(f"Retrieved funding information for {competitor_name}")
            
        except requests.RequestException as e:
            logger.error(f"Error fetching funding information: {str(e)}")
        
        return funding_data
    
    def analyze_competitor_strategy(self, competitor_name: str, context: str = '') -> Dict:
        """Analyze competitor's overall strategy using Perplexity"""
        logger.info(f"Analyzing strategy for {competitor_name}")
        
        analysis_data = {
            'competitor': competitor_name,
            'analysis_date': datetime.utcnow().isoformat(),
            'strategic_analysis': '',
            'key_insights': [],
            'recommendations': []
        }
        
        try:
            self._rate_limit()
            
            context_str = f"Context: {context}" if context else ""
            
            payload = {
                "model": "sonar-pro",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a strategic business analyst specializing in competitive intelligence."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze {competitor_name}'s business strategy, market positioning, and competitive advantages. {context_str} Provide: 1) Strategic direction 2) Key differentiators 3) Potential vulnerabilities 4) Recommendations for competing against them."
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.3
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            analysis_data['strategic_analysis'] = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            logger.info(f"Completed strategic analysis for {competitor_name}")
            
        except requests.RequestException as e:
            logger.error(f"Error performing strategic analysis: {str(e)}")
        
        return analysis_data
    
    def _parse_news_response(self, content: str, citations: List[str]) -> List[Dict]:
        """Parse Perplexity response into structured news items"""
        news_items = []
        
        # Split by common delimiters
        sections = content.split('\n\n')
        
        for i, section in enumerate(sections):
            if len(section.strip()) < 20:
                continue
            
            item = {
                'title': self._extract_title(section),
                'summary': section.strip()[:500],
                'source': citations[i] if i < len(citations) else None,
                'category': self._classify_news_category(section)
            }
            
            if item['title']:
                news_items.append(item)
        
        return news_items
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Extract title from news text"""
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.endswith(':') or line.startswith('##') or line.startswith('-')):
                return line.rstrip(':').replace('##', '').replace('-', '').strip()[:200]
        
        # Fallback: use first sentence
        sentences = text.split('.')
        return sentences[0].strip()[:200] if sentences else None
    
    def _classify_news_category(self, text: str) -> str:
        """Classify news into categories"""
        text_lower = text.lower()
        
        categories = {
            'funding': ['funding', 'raised', 'investment', 'series', 'valuation'],
            'product_launch': ['launch', 'release', 'unveil', 'announce', 'new product'],
            'partnership': ['partner', 'collaboration', 'alliance', 'joint'],
            'acquisition': ['acquire', 'acquisition', 'merge', 'buy', 'purchase'],
            'executive': ['ceo', 'cto', 'cfo', 'appoint', 'hire', 'executive'],
            'expansion': ['expand', 'grow', 'open', 'market', 'international']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _categorize_news(self, news_items: List[Dict]) -> Dict[str, int]:
        """Count news by category"""
        categories = {}
        for item in news_items:
            category = item.get('category', 'general')
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _extract_key_topics(self, content: str) -> List[str]:
        """Extract key topics from content"""
        # Simple keyword extraction
        important_terms = [
            'AI', 'machine learning', 'cloud', 'SaaS', 'enterprise',
            'mobile', 'security', 'analytics', 'automation', 'API'
        ]
        
        content_lower = content.lower()
        found_topics = [term for term in important_terms if term.lower() in content_lower]
        
        return found_topics[:5]


class NewsAggregator:
    """Aggregate news from multiple sources"""
    
    def __init__(self):
        self.perplexity = PerplexityService()
    
    def aggregate_competitor_intel(
        self,
        competitor_name: str,
        competitor_domain: str
    ) -> Dict:
        """Aggregate all intelligence for a competitor"""
        logger.info(f"Aggregating intelligence for {competitor_name}")
        
        intel_data = {
            'competitor': competitor_name,
            'domain': competitor_domain,
            'aggregation_date': datetime.utcnow().isoformat(),
            'news': {},
            'funding': {},
            'strategy': {},
            'impact_score': 0.0
        }
        
        # Fetch news
        intel_data['news'] = self.perplexity.search_competitor_news(competitor_name)
        
        # Fetch funding info
        intel_data['funding'] = self.perplexity.search_funding_rounds(competitor_name)
        
        # Strategic analysis
        intel_data['strategy'] = self.perplexity.analyze_competitor_strategy(competitor_name)
        
        # Calculate impact score
        intel_data['impact_score'] = self._calculate_impact_score(intel_data)
        
        return intel_data
    
    def _calculate_impact_score(self, intel_data: Dict) -> float:
        """Calculate overall impact score from aggregated intelligence"""
        score = 0.0
        
        # News impact
        news_count = intel_data.get('news', {}).get('summary', {}).get('total_results', 0)
        if news_count > 0:
            score += min(news_count * 0.5, 3.0)
        
        # Funding impact
        if 'raised' in str(intel_data.get('funding', {})).lower():
            score += 3.0
        
        # High-impact categories
        categories = intel_data.get('news', {}).get('summary', {}).get('categories', {})
        if categories.get('acquisition', 0) > 0:
            score += 4.0
        if categories.get('product_launch', 0) > 0:
            score += 2.0
        
        return min(score, 10.0)  # Cap at 10
