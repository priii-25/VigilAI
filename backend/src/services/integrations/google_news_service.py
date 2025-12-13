"""
Google News API Integration Service
Free alternative using Google News RSS feed and web scraping.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Represents a news article."""
    title: str
    url: str
    source: str
    published_date: Optional[datetime]
    snippet: str
    category: str = "general"
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['published_date'] = self.published_date.isoformat() if self.published_date else None
        return data


class GoogleNewsService:
    """
    Google News integration using RSS feed (free, no API key required).
    Provides competitor news monitoring without paid API access.
    """
    
    RSS_BASE_URL = "https://news.google.com/rss/search"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml'
        })
    
    def search_news(
        self,
        query: str,
        language: str = "en",
        country: str = "US",
        max_results: int = 20
    ) -> Dict[str, Any]:
        """
        Search Google News for a query.
        
        Args:
            query: Search query (e.g., "Stripe pricing changes")
            language: Language code
            country: Country code
            max_results: Maximum articles to return
            
        Returns:
            Dict containing articles and metadata
        """
        try:
            # Build RSS URL
            encoded_query = urllib.parse.quote(query)
            url = f"{self.RSS_BASE_URL}?q={encoded_query}&hl={language}&gl={country}&ceid={country}:{language}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse RSS XML
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:max_results]
            
            articles = []
            for item in items:
                article = self._parse_rss_item(item)
                if article:
                    articles.append(article)
            
            return {
                'success': True,
                'query': query,
                'total_results': len(articles),
                'articles': [a.to_dict() for a in articles],
                'fetched_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching Google News for '{query}': {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    def _parse_rss_item(self, item) -> Optional[NewsArticle]:
        """Parse RSS item into NewsArticle."""
        try:
            title = item.find('title')
            title_text = title.get_text() if title else "Untitled"
            
            link = item.find('link')
            url = link.get_text() if link else ""
            
            # Extract source from title (format: "Article Title - Source Name")
            source = "Unknown"
            if " - " in title_text:
                parts = title_text.rsplit(" - ", 1)
                title_text = parts[0]
                source = parts[1] if len(parts) > 1 else "Unknown"
            
            # Parse publication date
            pub_date = item.find('pubDate')
            published = None
            if pub_date:
                try:
                    date_str = pub_date.get_text()
                    published = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
                except:
                    pass
            
            # Get description/snippet
            description = item.find('description')
            snippet = ""
            if description:
                # Remove HTML tags from snippet
                snippet_soup = BeautifulSoup(description.get_text(), 'html.parser')
                snippet = snippet_soup.get_text()[:300]
            
            return NewsArticle(
                title=title_text,
                url=url,
                source=source,
                published_date=published,
                snippet=snippet
            )
            
        except Exception as e:
            logger.debug(f"Error parsing RSS item: {str(e)}")
            return None
    
    def get_competitor_news(
        self,
        competitor_name: str,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Get recent news about a competitor.
        
        Args:
            competitor_name: Name of competitor company
            days_back: Look back period in days
            
        Returns:
            News articles about the competitor
        """
        # Build comprehensive query
        queries = [
            f'"{competitor_name}"',  # Exact match
            f'{competitor_name} announcement',
            f'{competitor_name} product launch',
            f'{competitor_name} funding'
        ]
        
        all_articles = []
        seen_urls = set()
        
        for query in queries:
            result = self.search_news(query, max_results=10)
            if result.get('success'):
                for article in result.get('articles', []):
                    if article['url'] not in seen_urls:
                        seen_urls.add(article['url'])
                        all_articles.append(article)
        
        # Categorize articles
        categorized = self._categorize_articles(all_articles)
        
        return {
            'competitor': competitor_name,
            'total_articles': len(all_articles),
            'articles': all_articles,
            'by_category': categorized,
            'fetched_at': datetime.utcnow().isoformat()
        }
    
    def _categorize_articles(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize articles by topic."""
        categories = {
            'product': [],
            'funding': [],
            'partnership': [],
            'leadership': [],
            'general': []
        }
        
        category_keywords = {
            'product': ['launch', 'release', 'product', 'feature', 'update', 'version'],
            'funding': ['funding', 'investment', 'raised', 'valuation', 'series'],
            'partnership': ['partner', 'collaboration', 'integration', 'alliance'],
            'leadership': ['ceo', 'cto', 'hire', 'executive', 'appoint', 'board']
        }
        
        for article in articles:
            title_lower = article.get('title', '').lower()
            snippet_lower = article.get('snippet', '').lower()
            text = f"{title_lower} {snippet_lower}"
            
            categorized = False
            for category, keywords in category_keywords.items():
                if any(kw in text for kw in keywords):
                    categories[category].append(article)
                    categorized = True
                    break
            
            if not categorized:
                categories['general'].append(article)
        
        return categories
    
    def get_industry_news(
        self,
        industry: str,
        topics: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get industry-wide news and trends.
        
        Args:
            industry: Industry name (e.g., "fintech", "saas")
            topics: Optional specific topics to search
            
        Returns:
            Industry news aggregation
        """
        base_topics = topics or ['trends', 'market', 'growth', 'innovation']
        
        all_articles = []
        seen_urls = set()
        
        for topic in base_topics:
            query = f'{industry} {topic}'
            result = self.search_news(query, max_results=10)
            if result.get('success'):
                for article in result.get('articles', []):
                    if article['url'] not in seen_urls:
                        seen_urls.add(article['url'])
                        article['topic'] = topic
                        all_articles.append(article)
        
        return {
            'industry': industry,
            'topics': base_topics,
            'total_articles': len(all_articles),
            'articles': all_articles,
            'fetched_at': datetime.utcnow().isoformat()
        }


class UnifiedNewsAggregator:
    """
    Unified news aggregator combining Google News RSS and Perplexity.
    Provides comprehensive news coverage using free APIs.
    """
    
    def __init__(self):
        self.google_news = GoogleNewsService()
        self._perplexity = None
    
    @property
    def perplexity(self):
        """Lazy load Perplexity service."""
        if self._perplexity is None:
            try:
                from src.services.integrations.perplexity_service import PerplexityService
                self._perplexity = PerplexityService()
            except:
                pass
        return self._perplexity
    
    def get_comprehensive_news(
        self,
        competitor_name: str,
        include_perplexity: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive news from all sources.
        
        Args:
            competitor_name: Name of competitor
            include_perplexity: Whether to include Perplexity results
            
        Returns:
            Aggregated news from all sources
        """
        results = {
            'competitor': competitor_name,
            'sources': [],
            'articles': [],
            'summary': None,
            'fetched_at': datetime.utcnow().isoformat()
        }
        
        # Get Google News
        google_result = self.google_news.get_competitor_news(competitor_name)
        if google_result.get('total_articles', 0) > 0:
            results['sources'].append('google_news')
            results['articles'].extend(google_result.get('articles', []))
            results['google_news'] = google_result
        
        # Get Perplexity analysis if available
        if include_perplexity and self.perplexity:
            try:
                perplexity_result = self.perplexity.search_competitor_news(competitor_name)
                if perplexity_result.get('success'):
                    results['sources'].append('perplexity')
                    results['perplexity_analysis'] = perplexity_result
            except Exception as e:
                logger.warning(f"Perplexity unavailable: {str(e)}")
        
        results['total_articles'] = len(results['articles'])
        
        return results


# Convenience function
def get_news_service() -> UnifiedNewsAggregator:
    """Get unified news aggregator instance."""
    return UnifiedNewsAggregator()
