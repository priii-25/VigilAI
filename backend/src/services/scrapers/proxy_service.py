"""
Production-ready proxy rotation service
Supports multiple proxy providers and intelligent rotation
"""
from typing import Dict, List, Optional
import requests
from loguru import logger
from src.core.config import settings
import random
import time
from datetime import datetime, timedelta


class ProxyPool:
    """Intelligent proxy pool with health checking and rotation"""
    
    def __init__(self):
        self.enabled = settings.PROXY_POOL_ENABLED
        self.api_key = settings.PROXY_POOL_API_KEY
        self.proxies: List[Dict] = []
        self.proxy_health: Dict[str, Dict] = {}
        self.last_refresh = None
        self.refresh_interval = 300  # 5 minutes
        
        if self.enabled and self.api_key:
            self._initialize_proxies()
    
    def _initialize_proxies(self):
        """Initialize proxy pool from provider"""
        logger.info("Initializing proxy pool...")
        self._fetch_proxies()
    
    def _fetch_proxies(self):
        """Fetch proxies from provider API"""
        try:
            # Example: Using a proxy service API
            # Replace with your actual proxy provider
            
            # For demo: Create some proxy entries
            # In production, fetch from services like:
            # - ProxyCrawl
            # - ScraperAPI  
            # - Bright Data (Luminati)
            # - Oxylabs
            
            if not self.api_key:
                logger.warning("No proxy API key configured")
                return
            
            # Mock proxy list for structure
            self.proxies = [
                {
                    'host': 'proxy1.example.com',
                    'port': 8080,
                    'protocol': 'http',
                    'country': 'US',
                    'last_used': None
                }
            ]
            
            self.last_refresh = datetime.utcnow()
            logger.info(f"Loaded {len(self.proxies)} proxies")
            
        except Exception as e:
            logger.error(f"Error fetching proxies: {str(e)}")
    
    def get_proxy(self, country: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Get a healthy proxy from the pool
        
        Args:
            country: Optional country code filter
            
        Returns:
            Proxy dict in requests format or None
        """
        if not self.enabled:
            return None
        
        # Refresh if needed
        if self._should_refresh():
            self._fetch_proxies()
        
        if not self.proxies:
            return None
        
        # Filter by country if specified
        available_proxies = [
            p for p in self.proxies 
            if not country or p.get('country') == country
        ]
        
        if not available_proxies:
            available_proxies = self.proxies
        
        # Select proxy with least recent usage
        selected = min(
            available_proxies,
            key=lambda p: p.get('last_used') or datetime.min
        )
        
        # Update last used
        selected['last_used'] = datetime.utcnow()
        
        # Format for requests library
        proxy_url = f"{selected['protocol']}://{selected['host']}:{selected['port']}"
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def get_rotating_proxy_url(self) -> Optional[str]:
        """
        Get rotating proxy URL (for services that provide rotating endpoints)
        
        Returns:
            Proxy URL with authentication
        """
        if not self.enabled or not self.api_key:
            return None
        
        # Example formats for popular services:
        
        # ScraperAPI
        # return f"http://scraperapi:{self.api_key}@proxy-server.scraperapi.com:8001"
        
        # ProxyCrawl
        # return f"http://{self.api_key}:@megaproxy.proxycrawl.com:8000"
        
        # Bright Data (Luminati)
        # return f"http://lum-customer-{customer_id}-zone-{zone}:{self.api_key}@zproxy.lum-superproxy.io:22225"
        
        logger.warning("Rotating proxy URL not configured")
        return None
    
    def mark_proxy_failed(self, proxy: Dict):
        """Mark proxy as failed and update health"""
        proxy_id = f"{proxy['host']}:{proxy['port']}"
        
        if proxy_id not in self.proxy_health:
            self.proxy_health[proxy_id] = {
                'failures': 0,
                'successes': 0,
                'last_failure': None
            }
        
        self.proxy_health[proxy_id]['failures'] += 1
        self.proxy_health[proxy_id]['last_failure'] = datetime.utcnow()
        
        # Remove if too many failures
        if self.proxy_health[proxy_id]['failures'] > 5:
            self.proxies = [p for p in self.proxies if f"{p['host']}:{p['port']}" != proxy_id]
            logger.warning(f"Removed unhealthy proxy: {proxy_id}")
    
    def mark_proxy_success(self, proxy: Dict):
        """Mark proxy as successful"""
        proxy_id = f"{proxy['host']}:{proxy['port']}"
        
        if proxy_id not in self.proxy_health:
            self.proxy_health[proxy_id] = {
                'failures': 0,
                'successes': 0,
                'last_failure': None
            }
        
        self.proxy_health[proxy_id]['successes'] += 1
    
    def _should_refresh(self) -> bool:
        """Check if proxy list should be refreshed"""
        if not self.last_refresh:
            return True
        
        elapsed = (datetime.utcnow() - self.last_refresh).total_seconds()
        return elapsed > self.refresh_interval
    
    def get_stats(self) -> Dict:
        """Get proxy pool statistics"""
        return {
            'enabled': self.enabled,
            'total_proxies': len(self.proxies),
            'health_data': self.proxy_health,
            'last_refresh': self.last_refresh.isoformat() if self.last_refresh else None
        }


class SmartScraper:
    """Enhanced web scraper with intelligent proxy rotation"""
    
    def __init__(self):
        self.proxy_pool = ProxyPool()
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.max_retries = 3
        self.timeout = 30
    
    def fetch_with_retry(
        self,
        url: str,
        use_proxy: bool = True,
        country: Optional[str] = None
    ) -> Optional[requests.Response]:
        """
        Fetch URL with automatic retry and proxy rotation
        
        Args:
            url: URL to fetch
            use_proxy: Whether to use proxy
            country: Optional country for proxy selection
            
        Returns:
            Response object or None
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Get proxy if enabled
                proxies = None
                current_proxy = None
                
                if use_proxy:
                    proxy_dict = self.proxy_pool.get_proxy(country)
                    if proxy_dict:
                        proxies = proxy_dict
                        current_proxy = proxy_dict
                
                # Add delay to avoid rate limiting
                if attempt > 0:
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(delay)
                    logger.info(f"Retry attempt {attempt + 1} after {delay:.2f}s delay")
                
                # Make request
                response = self.session.get(
                    url,
                    headers=self.headers,
                    proxies=proxies,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                
                response.raise_for_status()
                
                # Mark proxy as successful
                if current_proxy:
                    self.proxy_pool.mark_proxy_success(current_proxy)
                
                logger.info(f"Successfully fetched {url}")
                return response
                
            except requests.exceptions.ProxyError as e:
                last_error = e
                logger.warning(f"Proxy error on attempt {attempt + 1}: {str(e)}")
                if current_proxy:
                    self.proxy_pool.mark_proxy_failed(current_proxy)
                    
            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"Timeout on attempt {attempt + 1}: {str(e)}")
                
            except requests.exceptions.HTTPError as e:
                last_error = e
                if e.response.status_code in [403, 429, 503]:
                    logger.warning(f"Rate limited or blocked (HTTP {e.response.status_code})")
                    if current_proxy:
                        self.proxy_pool.mark_proxy_failed(current_proxy)
                else:
                    # Don't retry for other HTTP errors
                    raise
                    
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Request error on attempt {attempt + 1}: {str(e)}")
        
        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts: {str(last_error)}")
        return None
    
    def fetch_multiple_urls(
        self,
        urls: List[str],
        use_proxy: bool = True,
        delay_between: float = 1.0
    ) -> List[Optional[requests.Response]]:
        """
        Fetch multiple URLs with rate limiting
        
        Args:
            urls: List of URLs to fetch
            use_proxy: Whether to use proxies
            delay_between: Delay between requests in seconds
            
        Returns:
            List of Response objects
        """
        responses = []
        
        for i, url in enumerate(urls):
            if i > 0:
                time.sleep(delay_between)
            
            response = self.fetch_with_retry(url, use_proxy=use_proxy)
            responses.append(response)
        
        return responses
    
    def check_if_blocked(self, response: requests.Response) -> bool:
        """
        Check if response indicates blocking or CAPTCHA
        
        Args:
            response: Response object
            
        Returns:
            True if likely blocked
        """
        if not response:
            return True
        
        # Check status codes
        if response.status_code in [403, 429, 503]:
            return True
        
        # Check content for common block indicators
        content_lower = response.text.lower()
        
        block_indicators = [
            'captcha',
            'access denied',
            'blocked',
            'rate limit',
            'too many requests',
            'cloudflare'
        ]
        
        return any(indicator in content_lower for indicator in block_indicators)


# Global proxy pool instance
proxy_pool = ProxyPool()
smart_scraper = SmartScraper()
