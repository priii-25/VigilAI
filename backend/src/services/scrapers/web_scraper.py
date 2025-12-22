"""
Web scraping service for competitor monitoring
"""
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from loguru import logger
import re
from src.core.config import settings


class WebScraper:
    """Base web scraper with proxy support"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """Get proxy from pool if enabled"""
        if settings.PROXY_POOL_ENABLED:
            # Production: Use configured proxy service
            # Supports simple rotation via environment variable configuration
            import random
            if hasattr(settings, 'PROXY_LIST') and settings.PROXY_LIST:
                proxy = random.choice(settings.PROXY_LIST)
                return {"http": proxy, "https": proxy}
            
            # Fallback to single proxy if defined
            if hasattr(settings, 'HTTP_PROXY') and settings.HTTP_PROXY:
                 return {"http": settings.HTTP_PROXY, "https": settings.HTTP_PROXY}
        return None
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch webpage content"""
        try:
            proxies = self.get_proxy()
            response = self.session.get(
                url,
                headers=self.headers,
                proxies=proxies,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Successfully fetched: {url}")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def check_page_modified(self, url: str, last_modified: Optional[datetime] = None) -> bool:
        """Check if page was modified using HEAD request"""
        try:
            response = self.session.head(url, headers=self.headers, timeout=10)
            if 'Last-Modified' in response.headers:
                page_modified = datetime.strptime(
                    response.headers['Last-Modified'],
                    '%a, %d %b %Y %H:%M:%S %Z'
                )
                if last_modified and page_modified <= last_modified:
                    return False
            return True
        except Exception as e:
            logger.warning(f"Could not check modification time for {url}: {str(e)}")
            return True  # Assume modified if check fails


class PricingScraper(WebScraper):
    """Scraper for competitor pricing pages"""
    
    def scrape_pricing(self, url: str) -> Dict:
        """Extract pricing information from competitor page"""
        html = self.fetch_page(url)
        if not html:
            return {}
        
        soup = BeautifulSoup(html, 'lxml')
        
        pricing_data = {
            'url': url,
            'scraped_at': datetime.utcnow().isoformat(),
            'plans': [],
            'raw_html': html[:5000]  # Store sample for analysis
        }
        
        # Extract pricing plans (customize selectors per competitor)
        pricing_sections = soup.find_all(['div', 'section'], class_=lambda x: x and 'pric' in x.lower())
        
        for section in pricing_sections[:5]:  # Limit to 5 plans
            plan = {
                'name': self._extract_plan_name(section),
                'price': self._extract_price(section),
                'features': self._extract_features(section)
            }
            if plan['name'] or plan['price']:
                pricing_data['plans'].append(plan)
        
        logger.info(f"Extracted {len(pricing_data['plans'])} pricing plans from {url}")
        return pricing_data
    
    def _extract_plan_name(self, section) -> Optional[str]:
        """Extract plan name from section"""
        for tag in ['h2', 'h3', 'h4', 'strong']:
            element = section.find(tag)
            if element:
                return element.get_text(strip=True)
        return None
    
    def _extract_price(self, section) -> Optional[str]:
        """Extract price from section using regex"""
        text = section.get_text()
        
        # Regex for currency patterns (e.g., $10, 10 USD, €20/mo)
        # Matches: Symbol+Number or Number+Currency Code, optional per-month/year
        price_pattern = r'([$€£¥]\s?\d+(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?\s?(?:USD|EUR|GBP))(?:\s?\/\s?(?:mo|month|yr|year|user))?'
        
        match = re.search(price_pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
            
        return None
    
    def _extract_features(self, section) -> List[str]:
        """Extract feature list from section"""
        features = []
        for ul in section.find_all('ul', limit=3):
            for li in ul.find_all('li', limit=10):
                feature = li.get_text(strip=True)
                if feature and len(feature) > 5:
                    features.append(feature[:200])
        return features


class CareersScraper(WebScraper):
    """Scraper for competitor job postings"""
    
    def scrape_careers(self, url: str) -> Dict:
        """Extract job posting information"""
        html = self.fetch_page(url)
        if not html:
            return {}
        
        soup = BeautifulSoup(html, 'lxml')
        
        careers_data = {
            'url': url,
            'scraped_at': datetime.utcnow().isoformat(),
            'job_postings': [],
            'hiring_trends': {}
        }
        
        # Extract job listings
        job_elements = soup.find_all(['div', 'li', 'article'], class_=lambda x: x and ('job' in str(x).lower() or 'position' in str(x).lower()))
        
        for job in job_elements[:20]:  # Limit to 20 jobs
            job_data = {
                'title': self._extract_text(job, ['h2', 'h3', 'h4', 'a']),
                'department': self._extract_department(job),
                'location': self._extract_location(job)
            }
            if job_data['title']:
                careers_data['job_postings'].append(job_data)
        
        # Analyze hiring trends
        careers_data['hiring_trends'] = self._analyze_hiring_trends(careers_data['job_postings'])
        
        logger.info(f"Extracted {len(careers_data['job_postings'])} job postings from {url}")
        return careers_data
    
    def _extract_text(self, element, tags: List[str]) -> Optional[str]:
        """Extract text from first matching tag"""
        for tag in tags:
            found = element.find(tag)
            if found:
                return found.get_text(strip=True)[:200]
        return None
    
    def _extract_department(self, element) -> Optional[str]:
        """Extract department/team information"""
        dept_keywords = ['engineering', 'sales', 'marketing', 'product', 'design', 'data', 'customer']
        text = element.get_text().lower()
        
        for keyword in dept_keywords:
            if keyword in text:
                return keyword.capitalize()
        return None
    
    def _extract_location(self, element) -> Optional[str]:
        """Extract location information"""
        text = element.get_text()
        location_indicators = ['remote', 'hybrid', 'office', 'location:']
        
        for indicator in location_indicators:
            if indicator in text.lower():
                lines = [line.strip() for line in text.split('\n') if indicator in line.lower()]
                if lines:
                    return lines[0][:100]
        return None
    
    def _analyze_hiring_trends(self, job_postings: List[Dict]) -> Dict:
        """Analyze hiring patterns"""
        trends = {
            'total_openings': len(job_postings),
            'departments': {},
            'locations': {}
        }
        
        for job in job_postings:
            if job.get('department'):
                dept = job['department']
                trends['departments'][dept] = trends['departments'].get(dept, 0) + 1
            
            if job.get('location'):
                loc = job['location']
                trends['locations'][loc] = trends['locations'].get(loc, 0) + 1
        
        return trends


class ContentScraper(WebScraper):
    """Scraper for competitor blog and content pages"""
    
    def scrape_blog(self, url: str) -> Dict:
        """Extract blog posts and content updates"""
        html = self.fetch_page(url)
        if not html:
            return {}
        
        soup = BeautifulSoup(html, 'lxml')
        
        content_data = {
            'url': url,
            'scraped_at': datetime.utcnow().isoformat(),
            'articles': []
        }
        
        # Extract articles
        article_elements = soup.find_all(['article', 'div'], class_=lambda x: x and ('post' in str(x).lower() or 'article' in str(x).lower()), limit=10)
        
        for article in article_elements:
            article_data = {
                'title': self._extract_title(article),
                'summary': self._extract_summary(article),
                'date': self._extract_date(article),
                'link': self._extract_link(article, url)
            }
            if article_data['title']:
                content_data['articles'].append(article_data)
        
        logger.info(f"Extracted {len(content_data['articles'])} articles from {url}")
        return content_data
    
    def _extract_title(self, element) -> Optional[str]:
        """Extract article title"""
        for tag in ['h1', 'h2', 'h3']:
            title = element.find(tag)
            if title:
                return title.get_text(strip=True)[:300]
        return None
    
    def _extract_summary(self, element) -> Optional[str]:
        """Extract article summary"""
        for tag in ['p', 'div']:
            summary = element.find(tag, class_=lambda x: x and 'summar' in str(x).lower())
            if summary:
                return summary.get_text(strip=True)[:500]
        
        # Fallback: get first paragraph
        p = element.find('p')
        if p:
            return p.get_text(strip=True)[:500]
        return None
    
    def _extract_date(self, element) -> Optional[str]:
        """Extract publication date"""
        time_tag = element.find('time')
        if time_tag and time_tag.get('datetime'):
            return time_tag['datetime']
        
        # Look for date in text
        date_indicators = ['published', 'posted', 'date']
        for indicator in date_indicators:
            date_elem = element.find(text=lambda x: x and indicator in x.lower())
            if date_elem:
                return str(date_elem).strip()[:50]
        return None
    
    def _extract_link(self, element, base_url: str) -> Optional[str]:
        """Extract article link"""
        a_tag = element.find('a', href=True)
        if a_tag:
            href = a_tag['href']
            if href.startswith('http'):
                return href
            else:
                # Relative URL
                from urllib.parse import urljoin
                return urljoin(base_url, href)
        return None
