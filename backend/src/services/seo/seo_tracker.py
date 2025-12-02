"""
SEO & Keyword Tracking Service
Monitors competitor keyword rankings, SERP positions, and SEO metrics.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import time
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class KeywordRanking:
    """Represents a keyword ranking result."""
    keyword: str
    domain: str
    position: Optional[int]
    url: str
    title: str
    snippet: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class SitemapEntry:
    """Represents a sitemap URL entry."""
    url: str
    lastmod: Optional[str]
    changefreq: Optional[str]
    priority: Optional[float]
    detected_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['detected_at'] = self.detected_at.isoformat()
        return data


class SEOTracker:
    """
    Production-grade SEO tracking service.
    Monitors keyword rankings and SERP positions for competitors.
    """
    
    def __init__(self, user_agent: Optional[str] = None):
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        
    def search_google(
        self,
        query: str,
        num_results: int = 10,
        country: str = 'us'
    ) -> List[Dict[str, Any]]:
        """
        Search Google and extract SERP results.
        
        Args:
            query: Search query
            num_results: Number of results to fetch
            country: Country code for localized results
            
        Returns:
            List of search results with position, URL, title, snippet
        """
        try:
            # Use Google Custom Search API (production) or scraping (demo)
            # For production, use: https://developers.google.com/custom-search/v1/overview
            
            # Demo implementation using scraping
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num={num_results}&gl={country}"
            
            time.sleep(2)  # Rate limiting
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract organic search results
            for idx, result in enumerate(soup.select('div.g'), start=1):
                try:
                    title_elem = result.select_one('h3')
                    link_elem = result.select_one('a')
                    snippet_elem = result.select_one('div.VwiC3b')
                    
                    if title_elem and link_elem:
                        url = link_elem.get('href', '')
                        if url.startswith('/url?q='):
                            url = url.split('/url?q=')[1].split('&')[0]
                        
                        results.append({
                            'position': idx,
                            'url': url,
                            'title': title_elem.get_text(strip=True),
                            'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                            'timestamp': datetime.utcnow().isoformat()
                        })
                        
                        if len(results) >= num_results:
                            break
                except Exception as e:
                    logger.warning(f"Error parsing search result: {e}")
                    continue
            
            logger.info(f"Extracted {len(results)} search results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching Google for '{query}': {e}")
            return []
    
    def track_keyword_rankings(
        self,
        keywords: List[str],
        target_domains: List[str],
        country: str = 'us'
    ) -> List[KeywordRanking]:
        """
        Track rankings for multiple keywords across target domains.
        
        Args:
            keywords: List of keywords to track
            target_domains: List of competitor domains
            country: Country code for localized results
            
        Returns:
            List of KeywordRanking objects
        """
        rankings = []
        
        for keyword in keywords:
            try:
                logger.info(f"Tracking keyword: {keyword}")
                results = self.search_google(keyword, num_results=20, country=country)
                
                for target_domain in target_domains:
                    domain_found = False
                    
                    for result in results:
                        result_domain = urlparse(result['url']).netloc
                        if target_domain in result_domain:
                            ranking = KeywordRanking(
                                keyword=keyword,
                                domain=target_domain,
                                position=result['position'],
                                url=result['url'],
                                title=result['title'],
                                snippet=result['snippet'],
                                timestamp=datetime.utcnow()
                            )
                            rankings.append(ranking)
                            domain_found = True
                            logger.info(f"{target_domain} ranks #{result['position']} for '{keyword}'")
                            break
                    
                    if not domain_found:
                        # Domain not in top results
                        ranking = KeywordRanking(
                            keyword=keyword,
                            domain=target_domain,
                            position=None,  # Not in top 20
                            url='',
                            title='',
                            snippet='',
                            timestamp=datetime.utcnow()
                        )
                        rankings.append(ranking)
                        logger.info(f"{target_domain} not in top 20 for '{keyword}'")
                
                time.sleep(3)  # Rate limiting between searches
                
            except Exception as e:
                logger.error(f"Error tracking keyword '{keyword}': {e}")
                continue
        
        return rankings
    
    def analyze_serp_changes(
        self,
        previous_rankings: List[KeywordRanking],
        current_rankings: List[KeywordRanking]
    ) -> List[Dict[str, Any]]:
        """
        Analyze changes in SERP positions between two time periods.
        
        Args:
            previous_rankings: Rankings from previous period
            current_rankings: Rankings from current period
            
        Returns:
            List of changes with movement analysis
        """
        changes = []
        
        # Create lookup dict for previous rankings
        prev_dict = {}
        for ranking in previous_rankings:
            key = f"{ranking.keyword}|{ranking.domain}"
            prev_dict[key] = ranking
        
        for current in current_rankings:
            key = f"{current.keyword}|{current.domain}"
            prev = prev_dict.get(key)
            
            if not prev:
                # New keyword tracking
                changes.append({
                    'keyword': current.keyword,
                    'domain': current.domain,
                    'change_type': 'new',
                    'current_position': current.position,
                    'previous_position': None,
                    'movement': None,
                    'timestamp': current.timestamp.isoformat()
                })
            else:
                # Calculate position change
                if current.position and prev.position:
                    movement = prev.position - current.position  # Positive = moved up
                    
                    if movement != 0:
                        changes.append({
                            'keyword': current.keyword,
                            'domain': current.domain,
                            'change_type': 'moved_up' if movement > 0 else 'moved_down',
                            'current_position': current.position,
                            'previous_position': prev.position,
                            'movement': movement,
                            'timestamp': current.timestamp.isoformat()
                        })
                elif current.position and not prev.position:
                    # Entered top rankings
                    changes.append({
                        'keyword': current.keyword,
                        'domain': current.domain,
                        'change_type': 'entered_rankings',
                        'current_position': current.position,
                        'previous_position': None,
                        'movement': None,
                        'timestamp': current.timestamp.isoformat()
                    })
                elif not current.position and prev.position:
                    # Dropped out of rankings
                    changes.append({
                        'keyword': current.keyword,
                        'domain': current.domain,
                        'change_type': 'dropped_out',
                        'current_position': None,
                        'previous_position': prev.position,
                        'movement': None,
                        'timestamp': current.timestamp.isoformat()
                    })
        
        return changes
    
    def calculate_seo_score(self, rankings: List[KeywordRanking]) -> Dict[str, Any]:
        """
        Calculate overall SEO performance score for a domain.
        
        Args:
            rankings: List of keyword rankings for a domain
            
        Returns:
            Dictionary with SEO metrics
        """
        if not rankings:
            return {
                'total_keywords': 0,
                'avg_position': None,
                'top_3_count': 0,
                'top_10_count': 0,
                'seo_score': 0
            }
        
        positions = [r.position for r in rankings if r.position]
        
        if not positions:
            return {
                'total_keywords': len(rankings),
                'avg_position': None,
                'top_3_count': 0,
                'top_10_count': 0,
                'seo_score': 0
            }
        
        avg_position = sum(positions) / len(positions)
        top_3_count = sum(1 for p in positions if p <= 3)
        top_10_count = sum(1 for p in positions if p <= 10)
        
        # Calculate SEO score (0-100)
        # Higher weight for top positions
        score = 0
        for position in positions:
            if position == 1:
                score += 20
            elif position <= 3:
                score += 15
            elif position <= 5:
                score += 10
            elif position <= 10:
                score += 5
            else:
                score += 2
        
        max_score = len(rankings) * 20
        seo_score = min(100, (score / max_score) * 100) if max_score > 0 else 0
        
        return {
            'total_keywords': len(rankings),
            'ranked_keywords': len(positions),
            'avg_position': round(avg_position, 2),
            'top_3_count': top_3_count,
            'top_10_count': top_10_count,
            'seo_score': round(seo_score, 2)
        }


class SitemapMonitor:
    """
    Monitor competitor sitemaps for new pages and content updates.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; SEOBot/1.0; +http://example.com/bot)'
        })
    
    def fetch_sitemap(self, domain: str) -> Optional[str]:
        """
        Fetch sitemap.xml from a domain.
        
        Args:
            domain: Domain to fetch sitemap from
            
        Returns:
            Sitemap XML content or None
        """
        sitemap_urls = [
            f"https://{domain}/sitemap.xml",
            f"https://{domain}/sitemap_index.xml",
            f"https://www.{domain}/sitemap.xml",
            f"https://www.{domain}/sitemap_index.xml"
        ]
        
        for url in sitemap_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Successfully fetched sitemap from {url}")
                    return response.text
            except Exception as e:
                logger.debug(f"Failed to fetch {url}: {e}")
                continue
        
        logger.warning(f"No sitemap found for {domain}")
        return None
    
    def parse_sitemap(self, sitemap_xml: str) -> List[SitemapEntry]:
        """
        Parse sitemap XML and extract URLs.
        
        Args:
            sitemap_xml: XML content of sitemap
            
        Returns:
            List of SitemapEntry objects
        """
        entries = []
        
        try:
            root = ET.fromstring(sitemap_xml)
            
            # Handle namespace
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Check if this is a sitemap index
            sitemaps = root.findall('ns:sitemap', namespace)
            if sitemaps:
                logger.info("Found sitemap index with multiple sitemaps")
                # This is a sitemap index, not individual URLs
                for sitemap in sitemaps:
                    loc = sitemap.find('ns:loc', namespace)
                    lastmod = sitemap.find('ns:lastmod', namespace)
                    
                    if loc is not None:
                        entries.append(SitemapEntry(
                            url=loc.text,
                            lastmod=lastmod.text if lastmod is not None else None,
                            changefreq=None,
                            priority=None,
                            detected_at=datetime.utcnow()
                        ))
            else:
                # Parse individual URLs
                urls = root.findall('ns:url', namespace)
                for url_elem in urls:
                    loc = url_elem.find('ns:loc', namespace)
                    lastmod = url_elem.find('ns:lastmod', namespace)
                    changefreq = url_elem.find('ns:changefreq', namespace)
                    priority = url_elem.find('ns:priority', namespace)
                    
                    if loc is not None:
                        entries.append(SitemapEntry(
                            url=loc.text,
                            lastmod=lastmod.text if lastmod is not None else None,
                            changefreq=changefreq.text if changefreq is not None else None,
                            priority=float(priority.text) if priority is not None else None,
                            detected_at=datetime.utcnow()
                        ))
            
            logger.info(f"Parsed {len(entries)} entries from sitemap")
            
        except Exception as e:
            logger.error(f"Error parsing sitemap: {e}")
        
        return entries
    
    def detect_new_pages(
        self,
        current_entries: List[SitemapEntry],
        previous_entries: List[SitemapEntry]
    ) -> List[SitemapEntry]:
        """
        Detect new pages by comparing current and previous sitemap entries.
        
        Args:
            current_entries: Current sitemap entries
            previous_entries: Previous sitemap entries
            
        Returns:
            List of new pages
        """
        previous_urls = {entry.url for entry in previous_entries}
        new_pages = [entry for entry in current_entries if entry.url not in previous_urls]
        
        logger.info(f"Detected {len(new_pages)} new pages")
        return new_pages
    
    def categorize_page(self, url: str) -> str:
        """
        Categorize a page based on URL patterns.
        
        Args:
            url: URL to categorize
            
        Returns:
            Category string
        """
        url_lower = url.lower()
        
        if any(keyword in url_lower for keyword in ['/product/', '/products/', '/p/']):
            return 'product'
        elif any(keyword in url_lower for keyword in ['/blog/', '/news/', '/article/']):
            return 'content'
        elif any(keyword in url_lower for keyword in ['/pricing', '/plans']):
            return 'pricing'
        elif any(keyword in url_lower for keyword in ['/about', '/company']):
            return 'about'
        elif any(keyword in url_lower for keyword in ['/careers', '/jobs']):
            return 'careers'
        elif any(keyword in url_lower for keyword in ['/case-study', '/customer', '/success']):
            return 'case_study'
        elif any(keyword in url_lower for keyword in ['/feature', '/solution']):
            return 'feature'
        else:
            return 'other'
    
    def monitor_competitor_sitemap(
        self,
        domain: str,
        previous_entries: Optional[List[SitemapEntry]] = None
    ) -> Dict[str, Any]:
        """
        Monitor a competitor's sitemap and detect changes.
        
        Args:
            domain: Competitor domain
            previous_entries: Previous sitemap entries for comparison
            
        Returns:
            Dictionary with monitoring results
        """
        sitemap_xml = self.fetch_sitemap(domain)
        
        if not sitemap_xml:
            return {
                'domain': domain,
                'success': False,
                'error': 'Sitemap not found',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        current_entries = self.parse_sitemap(sitemap_xml)
        
        result = {
            'domain': domain,
            'success': True,
            'total_pages': len(current_entries),
            'timestamp': datetime.utcnow().isoformat(),
            'entries': [entry.to_dict() for entry in current_entries]
        }
        
        if previous_entries:
            new_pages = self.detect_new_pages(current_entries, previous_entries)
            
            # Categorize new pages
            categorized = {}
            for page in new_pages:
                category = self.categorize_page(page.url)
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(page.to_dict())
            
            result['new_pages'] = len(new_pages)
            result['new_pages_by_category'] = categorized
        
        return result
