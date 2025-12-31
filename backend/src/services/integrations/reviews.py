"""
Review Monitoring Service
Monitors G2, Gartner, and Capterra for competitor reviews and sentiment.

Data Sources (in order of preference):
1. SerpAPI - Reliable SERP data extraction (requires API key)
2. Google News RSS - Free fallback for review mentions
3. Capterra Scraping - Less strict than G2/Gartner
"""
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


@dataclass
class ReviewSummary:
    """Summary of a review or aggregate rating update."""
    source: str  # 'G2', 'Gartner', 'Capterra', 'TrustRadius'
    competitor_name: str
    title: str
    rating: Optional[float]
    summary: str
    url: str
    review_count: Optional[int] = None
    detected_at: datetime = None
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['detected_at'] = self.detected_at.isoformat()
        return data


class SerpAPIClient:
    """
    SerpAPI integration for extracting review data from search results.
    Get API key at: https://serpapi.com (100 free searches/month)
    """
    
    BASE_URL = "https://serpapi.com/search"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
    
    def search_reviews(
        self,
        competitor_name: str,
        platform: str = "G2",
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for review data using SerpAPI.
        
        Args:
            competitor_name: Name of the competitor
            platform: Review platform (G2, Gartner, Capterra)
            num_results: Number of results to fetch
            
        Returns:
            List of search results with review snippets
        """
        if not self.api_key:
            logger.debug("SerpAPI key not configured, skipping")
            return []
        
        try:
            query = f"{competitor_name} {platform} reviews ratings"
            
            params = {
                'api_key': self.api_key,
                'engine': 'google',
                'q': query,
                'num': num_results,
                'hl': 'en',
                'gl': 'us'
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract organic results
            for result in data.get('organic_results', []):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'platform': platform,
                    'source': 'serpapi'
                })
            
            # Extract knowledge graph rating if available
            if 'knowledge_graph' in data:
                kg = data['knowledge_graph']
                if 'rating' in kg:
                    results.insert(0, {
                        'title': f"{competitor_name} on {platform}",
                        'url': kg.get('website', ''),
                        'snippet': f"Rating: {kg.get('rating')}/5 ({kg.get('reviews', 'N/A')} reviews)",
                        'rating': kg.get('rating'),
                        'review_count': kg.get('reviews'),
                        'platform': platform,
                        'source': 'serpapi_kg'
                    })
            
            logger.info(f"SerpAPI found {len(results)} results for {competitor_name} {platform}")
            return results
            
        except Exception as e:
            logger.error(f"SerpAPI error for {competitor_name}: {e}")
            return []


class CapterraScraper:
    """
    Capterra scraper - less aggressive anti-bot than G2.
    Extracts ratings and review counts from public Capterra pages.
    """
    
    SEARCH_URL = "https://www.capterra.com/search/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def search_capterra(self, competitor_name: str) -> List[ReviewSummary]:
        """
        Search Capterra for competitor product reviews.
        
        Args:
            competitor_name: Name of the competitor product
            
        Returns:
            List of ReviewSummary objects
        """
        reviews = []
        
        try:
            # Use Google to find Capterra page (safer than direct access)
            google_url = f"https://www.google.com/search?q=site:capterra.com+{quote_plus(competitor_name)}+reviews"
            
            response = self.session.get(google_url, timeout=15)
            if response.status_code != 200:
                logger.warning(f"Google search failed for Capterra {competitor_name}")
                return reviews
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract Capterra links from Google results
            for result in soup.select('div.g')[:5]:
                try:
                    link_elem = result.select_one('a')
                    title_elem = result.select_one('h3')
                    snippet_elem = result.select_one('div.VwiC3b')
                    
                    if not link_elem or not title_elem:
                        continue
                    
                    url = link_elem.get('href', '')
                    if 'capterra.com' not in url:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    # Extract rating from snippet if present
                    rating = self._extract_rating(snippet)
                    review_count = self._extract_review_count(snippet)
                    
                    reviews.append(ReviewSummary(
                        source='Capterra',
                        competitor_name=competitor_name,
                        title=title,
                        rating=rating,
                        summary=snippet[:300],
                        url=url,
                        review_count=review_count
                    ))
                    
                except Exception as e:
                    logger.debug(f"Error parsing Capterra result: {e}")
                    continue
            
            logger.info(f"Capterra scraper found {len(reviews)} results for {competitor_name}")
            
        except Exception as e:
            logger.error(f"Capterra search error for {competitor_name}: {e}")
        
        return reviews
    
    def _extract_rating(self, text: str) -> Optional[float]:
        """Extract rating from text like '4.5/5' or '4.5 out of 5'."""
        patterns = [
            r'(\d+\.?\d*)\s*/\s*5',  # 4.5/5
            r'(\d+\.?\d*)\s+out\s+of\s+5',  # 4.5 out of 5
            r'rating[:\s]+(\d+\.?\d*)',  # Rating: 4.5
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_review_count(self, text: str) -> Optional[int]:
        """Extract review count from text like '(500 reviews)' or '500+ reviews'."""
        patterns = [
            r'\((\d+[,\d]*)\+?\s*reviews?\)',  # (500 reviews)
            r'(\d+[,\d]*)\+?\s*reviews?',  # 500 reviews
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        return None


class GoogleNewsReviewSearch:
    """
    Fallback: Search Google News for review-related mentions.
    Free alternative when SerpAPI is not available.
    """
    
    RSS_URL = "https://news.google.com/rss/search"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_review_mentions(
        self,
        competitor_name: str,
        platform: str = "G2"
    ) -> List[ReviewSummary]:
        """
        Search Google News for review mentions.
        
        Args:
            competitor_name: Name of the competitor
            platform: Review platform to search for
            
        Returns:
            List of ReviewSummary objects from news mentions
        """
        reviews = []
        
        try:
            query = f"{competitor_name} {platform} review"
            url = f"{self.RSS_URL}?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return reviews
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:5]
            
            for item in items:
                try:
                    title = item.find('title').get_text() if item.find('title') else ''
                    link = item.find('link').get_text() if item.find('link') else ''
                    
                    # Only include if it's actually about reviews
                    if 'review' not in title.lower():
                        continue
                    
                    # Extract source from title
                    source_name = platform
                    if ' - ' in title:
                        parts = title.rsplit(' - ', 1)
                        title = parts[0]
                        source_name = parts[1] if len(parts) > 1 else platform
                    
                    reviews.append(ReviewSummary(
                        source=platform,
                        competitor_name=competitor_name,
                        title=title,
                        rating=None,
                        summary=f"News mention from {source_name}",
                        url=link
                    ))
                    
                except Exception as e:
                    logger.debug(f"Error parsing news item: {e}")
                    continue
            
            logger.info(f"Google News found {len(reviews)} review mentions for {competitor_name}")
            
        except Exception as e:
            logger.error(f"Google News search error: {e}")
        
        return reviews


class ReviewMonitor:
    """
    Unified review monitoring service.
    Aggregates data from SerpAPI, Capterra, and Google News.
    """
    
    PLATFORMS = ['G2', 'Gartner', 'Capterra', 'TrustRadius']
    
    def __init__(self, serpapi_key: Optional[str] = None):
        """
        Initialize review monitor with optional SerpAPI key.
        
        Args:
            serpapi_key: SerpAPI key for enhanced search (optional)
        """
        self.serpapi = SerpAPIClient(serpapi_key)
        self.capterra = CapterraScraper()
        self.news_search = GoogleNewsReviewSearch()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_reviews_via_serpapi(
        self,
        competitor_name: str,
        platforms: List[str] = None
    ) -> List[ReviewSummary]:
        """
        Search for reviews using SerpAPI (primary method if key available).
        
        Args:
            competitor_name: Name of the competitor
            platforms: List of platforms to search
            
        Returns:
            List of ReviewSummary objects
        """
        if not self.serpapi.api_key:
            return []
        
        platforms = platforms or self.PLATFORMS
        reviews = []
        
        for platform in platforms:
            results = self.serpapi.search_reviews(competitor_name, platform)
            
            for result in results:
                reviews.append(ReviewSummary(
                    source=platform,
                    competitor_name=competitor_name,
                    title=result.get('title', ''),
                    rating=result.get('rating'),
                    summary=result.get('snippet', ''),
                    url=result.get('url', ''),
                    review_count=result.get('review_count')
                ))
        
        return reviews
    
    def monitor_competitor(self, competitor_name: str) -> Dict[str, Any]:
        """
        Aggregates review data for a competitor from all sources.
        
        Tries sources in order:
        1. SerpAPI (if key configured)
        2. Capterra scraping
        3. Google News fallback
        
        Args:
            competitor_name: Name of the competitor
            
        Returns:
            Dictionary with review data and metadata
        """
        all_reviews = []
        sources_used = []
        
        # 1. Try SerpAPI first (most reliable if key available)
        serpapi_reviews = self.search_reviews_via_serpapi(competitor_name)
        if serpapi_reviews:
            all_reviews.extend(serpapi_reviews)
            sources_used.append('serpapi')
            logger.info(f"SerpAPI returned {len(serpapi_reviews)} reviews for {competitor_name}")
        
        # 2. Try Capterra scraping (less strict anti-bot)
        capterra_reviews = self.capterra.search_capterra(competitor_name)
        if capterra_reviews:
            all_reviews.extend(capterra_reviews)
            sources_used.append('capterra')
            logger.info(f"Capterra returned {len(capterra_reviews)} reviews for {competitor_name}")
        
        # 3. Fallback to Google News for review mentions
        if not all_reviews:
            for platform in ['G2', 'Gartner']:
                news_reviews = self.news_search.search_review_mentions(
                    competitor_name, platform
                )
                if news_reviews:
                    all_reviews.extend(news_reviews)
                    sources_used.append('google_news')
        
        # Calculate aggregate stats
        ratings = [r.rating for r in all_reviews if r.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        result = {
            'competitor': competitor_name,
            'total_reviews_detected': len(all_reviews),
            'reviews': [r.to_dict() for r in all_reviews],
            'sources_used': list(set(sources_used)),
            'data_available': len(all_reviews) > 0,
            'aggregate': {
                'average_rating': round(avg_rating, 2) if avg_rating else None,
                'platforms_found': list(set(r.source for r in all_reviews)),
                'total_review_count': sum(r.review_count for r in all_reviews if r.review_count)
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if not all_reviews:
            result['note'] = (
                'No review data found. For best results, configure SERPAPI_KEY in .env '
                'or check that the competitor name matches their product listing.'
            )
            logger.info(f"No review data available for {competitor_name}")
        
        return result


def get_review_monitor() -> ReviewMonitor:
    """
    Factory function to create ReviewMonitor with config settings.
    
    Returns:
        Configured ReviewMonitor instance
    """
    try:
        from src.core.config import settings
        return ReviewMonitor(serpapi_key=settings.SERPAPI_KEY or None)
    except ImportError:
        logger.warning("Could not import settings, creating ReviewMonitor without SerpAPI")
        return ReviewMonitor()
