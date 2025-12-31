"""
Social Media Monitoring Service
Twitter/LinkedIn scraper for competitor product announcements and updates.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import time
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class SocialPost:
    """Represents a social media post."""
    platform: str  # 'twitter' or 'linkedin'
    author: str
    author_handle: str
    content: str
    url: str
    timestamp: datetime
    engagement: Dict[str, int]  # likes, shares, comments
    post_type: str  # announcement, update, thought_leadership, hiring, etc.
    detected_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['detected_at'] = self.detected_at.isoformat()
        return data


class TwitterScraper:
    """
    Production-grade Twitter monitoring for competitor activity.
    Note: For production, use Twitter API v2 with elevated access.
    """
    
    def __init__(self, bearer_token: Optional[str] = None):
        """
        Initialize Twitter scraper.
        
        Args:
            bearer_token: Twitter API bearer token for authentication
        """
        self.bearer_token = bearer_token
        self.base_url = "https://api.twitter.com/2"
        self.session = requests.Session()
        
        if self.bearer_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.bearer_token}',
                'User-Agent': 'VigilAI-CompetitorMonitor/1.0'
            })
    
    def search_tweets(
        self,
        query: str,
        max_results: int = 10,
        start_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Search recent tweets using Twitter API v2.
        
        Args:
            query: Search query (supports operators like from:, to:, etc.)
            max_results: Maximum number of tweets to return (10-100)
            start_time: Only return tweets after this time
            
        Returns:
            List of tweet data
        """
        if not self.bearer_token:
            logger.error("Twitter API bearer token not configured")
            return []
        
        try:
            endpoint = f"{self.base_url}/tweets/search/recent"
            
            params = {
                'query': query,
                'max_results': min(max_results, 100),
                'tweet.fields': 'created_at,public_metrics,author_id,entities',
                'expansions': 'author_id',
                'user.fields': 'username,name,verified'
            }
            
            if start_time:
                params['start_time'] = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Create user lookup
            users = {}
            if 'includes' in data and 'users' in data['includes']:
                for user in data['includes']['users']:
                    users[user['id']] = user
            
            tweets = []
            if 'data' in data:
                for tweet in data['data']:
                    author = users.get(tweet['author_id'], {})
                    
                    tweets.append({
                        'id': tweet['id'],
                        'text': tweet['text'],
                        'author_id': tweet['author_id'],
                        'author_name': author.get('name', 'Unknown'),
                        'author_username': author.get('username', 'unknown'),
                        'author_verified': author.get('verified', False),
                        'created_at': tweet['created_at'],
                        'metrics': tweet.get('public_metrics', {}),
                        'url': f"https://twitter.com/{author.get('username', 'i')}/status/{tweet['id']}"
                    })
            
            logger.info(f"Found {len(tweets)} tweets for query: {query}")
            return tweets
            
        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            return []
    
    def monitor_competitor_account(
        self,
        username: str,
        since_hours: int = 24
    ) -> List[SocialPost]:
        """
        Monitor a competitor's Twitter account for recent posts.
        
        Args:
            username: Twitter username (without @)
            since_hours: Look back this many hours
            
        Returns:
            List of SocialPost objects
        """
        start_time = datetime.utcnow() - timedelta(hours=since_hours)
        query = f"from:{username} -is:retweet"
        
        tweets = self.search_tweets(query, max_results=50, start_time=start_time)
        
        posts = []
        for tweet in tweets:
            post_type = self._classify_tweet(tweet['text'])
            
            post = SocialPost(
                platform='twitter',
                author=tweet['author_name'],
                author_handle=f"@{tweet['author_username']}",
                content=tweet['text'],
                url=tweet['url'],
                timestamp=datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00')),
                engagement={
                    'likes': tweet['metrics'].get('like_count', 0),
                    'retweets': tweet['metrics'].get('retweet_count', 0),
                    'replies': tweet['metrics'].get('reply_count', 0)
                },
                post_type=post_type,
                detected_at=datetime.utcnow()
            )
            posts.append(post)
        
        return posts
    
    def _classify_tweet(self, text: str) -> str:
        """Classify tweet type based on content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['launch', 'releasing', 'announce', 'introducing']):
            return 'product_announcement'
        elif any(word in text_lower for word in ['hiring', 'join our team', 'we\'re hiring']):
            return 'hiring'
        elif any(word in text_lower for word in ['partnership', 'partner with', 'teaming up']):
            return 'partnership'
        elif any(word in text_lower for word in ['funding', 'raised', 'series', 'investment']):
            return 'funding'
        elif any(word in text_lower for word in ['update', 'new feature', 'improvement']):
            return 'product_update'
        else:
            return 'general'


class LinkedInScraper:
    """
    LinkedIn monitoring for competitor company updates.
    Note: LinkedIn has strict scraping policies. Use official API for production.
    """
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize LinkedIn scraper.
        
        Args:
            access_token: LinkedIn API access token
        """
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_company_posts(
        self,
        company_id: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent company posts from LinkedIn.
        
        For production, use LinkedIn API:
        https://docs.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares
        
        Args:
            company_id: LinkedIn company ID or vanity name
            max_results: Maximum posts to return
            
        Returns:
            List of post data
        """
        if not self.access_token:
            logger.warning("LinkedIn API access token not configured. Using fallback method.")
            return self._scrape_company_posts(company_id, max_results)
        
        try:
            # LinkedIn API implementation
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            # This is a simplified example - actual implementation needs proper LinkedIn API setup
            endpoint = f"https://api.linkedin.com/v2/shares?q=owners&owners=urn:li:organization:{company_id}"
            
            response = self.session.get(endpoint, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            # Parse LinkedIn API response
            if 'elements' in data:
                for element in data['elements'][:max_results]:
                    posts.append({
                        'id': element.get('id'),
                        'text': element.get('text', {}).get('text', ''),
                        'created_at': element.get('created', {}).get('time'),
                        'metrics': element.get('statistics', {})
                    })
            
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching LinkedIn posts: {e}")
            return []
    
    def _scrape_company_posts(
        self,
        company_name: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fallback monitoring using Google News RSS for company updates.
        This provides a safe, production-ready alternative to direct scraping.
        """
        logger.info(f"Using Google News fallback for {company_name}")
        
        try:
            # Use Google News RSS feed for the company
            rss_url = f"https://news.google.com/rss/search?q={company_name}+site:linkedin.com&hl=en-US&gl=US&ceid=US:en"
            
            response = requests.get(rss_url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch news RSS for {company_name}")
                return []
                
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:max_results]
            
            posts = []
            for item in items:
                title = item.find('title').text if item.find('title') else ''
                link = item.find('link').text if item.find('link') else ''
                pub_date = item.find('pubDate').text if item.find('pubDate') else ''
                
                # Parse date
                try:
                    dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                except:
                    dt = datetime.utcnow()
                
                posts.append({
                    'id': link,
                    'text': title,
                    'created_at': int(dt.timestamp() * 1000),
                    'metrics': {'likeCount': 0, 'commentCount': 0, 'shareCount': 0}
                })
                
            return posts
            
        except Exception as e:
            logger.error(f"Error in fallback news scraping: {e}")
            return []
    
    def monitor_competitor_linkedin(
        self,
        company_id: str,
        company_name: str
    ) -> List[SocialPost]:
        """
        Monitor competitor's LinkedIn company page.
        
        Args:
            company_id: LinkedIn company ID
            company_name: Company name for display
            
        Returns:
            List of SocialPost objects
        """
        linkedin_posts = self.get_company_posts(company_id, max_results=20)
        
        posts = []
        for post_data in linkedin_posts:
            post_type = self._classify_linkedin_post(post_data.get('text', ''))
            
            post = SocialPost(
                platform='linkedin',
                author=company_name,
                author_handle=company_id,
                content=post_data.get('text', ''),
                url=f"https://www.linkedin.com/company/{company_id}",
                timestamp=datetime.fromtimestamp(post_data.get('created_at', 0) / 1000) if post_data.get('created_at') else datetime.utcnow(),
                engagement={
                    'likes': post_data.get('metrics', {}).get('likeCount', 0),
                    'comments': post_data.get('metrics', {}).get('commentCount', 0),
                    'shares': post_data.get('metrics', {}).get('shareCount', 0)
                },
                post_type=post_type,
                detected_at=datetime.utcnow()
            )
            posts.append(post)
        
        return posts
    
    def _classify_linkedin_post(self, text: str) -> str:
        """Classify LinkedIn post type."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['excited to announce', 'proud to announce', 'thrilled to share']):
            return 'announcement'
        elif any(word in text_lower for word in ['hiring', 'join our team', 'career opportunity']):
            return 'hiring'
        elif any(word in text_lower for word in ['thought leadership', 'insights', 'trends']):
            return 'thought_leadership'
        elif any(word in text_lower for word in ['partnership', 'collaboration', 'working with']):
            return 'partnership'
        elif any(word in text_lower for word in ['award', 'recognition', 'honored']):
            return 'achievement'
        else:
            return 'general'


class SocialMediaMonitor:
    """
    Unified social media monitoring service.
    Aggregates data from Twitter and LinkedIn.
    """
    
    def __init__(
        self,
        twitter_bearer_token: Optional[str] = None,
        linkedin_access_token: Optional[str] = None
    ):
        self.twitter = TwitterScraper(twitter_bearer_token)
        self.linkedin = LinkedInScraper(linkedin_access_token)
    
    def monitor_competitor(
        self,
        competitor_name: str,
        twitter_handle: Optional[str] = None,
        linkedin_company_id: Optional[str] = None,
        since_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Monitor all social channels for a competitor.
        
        Args:
            competitor_name: Competitor name
            twitter_handle: Twitter username (without @)
            linkedin_company_id: LinkedIn company ID
            since_hours: Look back this many hours
            
        Returns:
            Dictionary with aggregated social media data
        """
        all_posts = []
        
        # Monitor Twitter
        if twitter_handle:
            try:
                twitter_posts = self.twitter.monitor_competitor_account(
                    twitter_handle,
                    since_hours=since_hours
                )
                all_posts.extend(twitter_posts)
                logger.info(f"Found {len(twitter_posts)} Twitter posts for {competitor_name}")
            except Exception as e:
                logger.error(f"Error monitoring Twitter for {competitor_name}: {e}")
        
        # Monitor LinkedIn
        if linkedin_company_id:
            try:
                linkedin_posts = self.linkedin.monitor_competitor_linkedin(
                    linkedin_company_id,
                    competitor_name
                )
                all_posts.extend(linkedin_posts)
                logger.info(f"Found {len(linkedin_posts)} LinkedIn posts for {competitor_name}")
            except Exception as e:
                logger.error(f"Error monitoring LinkedIn for {competitor_name}: {e}")
        
        # Categorize and analyze posts
        by_type = {}
        high_engagement = []
        
        for post in all_posts:
            # Group by type
            if post.post_type not in by_type:
                by_type[post.post_type] = []
            by_type[post.post_type].append(post.to_dict())
            
            # Flag high engagement posts
            total_engagement = sum(post.engagement.values())
            if total_engagement > 100:  # Threshold for "high engagement"
                high_engagement.append({
                    **post.to_dict(),
                    'total_engagement': total_engagement
                })
        
        # Sort high engagement posts
        high_engagement.sort(key=lambda x: x['total_engagement'], reverse=True)
        
        return {
            'competitor': competitor_name,
            'total_posts': len(all_posts),
            'time_range_hours': since_hours,
            'posts_by_type': by_type,
            'high_engagement_posts': high_engagement[:5],  # Top 5
            'platforms': {
                'twitter': len([p for p in all_posts if p.platform == 'twitter']),
                'linkedin': len([p for p in all_posts if p.platform == 'linkedin'])
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def detect_product_announcements(self, posts: List[SocialPost]) -> List[SocialPost]:
        """
        Filter posts to find product announcements.
        
        Args:
            posts: List of social posts
            
        Returns:
            Filtered list of announcement posts
        """
        announcement_types = {'product_announcement', 'product_update', 'announcement'}
        announcements = [p for p in posts if p.post_type in announcement_types]
        
        logger.info(f"Detected {len(announcements)} product announcements from {len(posts)} posts")
        return announcements
    
    def calculate_sentiment_score(self, posts: List[SocialPost]) -> float:
        """
        Calculate overall sentiment score based on engagement metrics.
        
        Args:
            posts: List of social posts
            
        Returns:
            Sentiment score (0-10)
        """
        if not posts:
            return 5.0  # Neutral
        
        total_engagement = 0
        total_posts = len(posts)
        
        for post in posts:
            engagement = sum(post.engagement.values())
            total_engagement += engagement
        
        # Normalize score (higher engagement = higher sentiment)
        avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
        
        # Map to 0-10 scale (logarithmic to handle large ranges)
        import math
        score = min(10, (math.log1p(avg_engagement) / 10) * 10)
        
        return round(score, 2)


def get_social_monitor() -> SocialMediaMonitor:
    """
    Factory function to create SocialMediaMonitor with config settings.
    
    Loads Twitter and LinkedIn credentials from environment variables.
    
    Returns:
        Configured SocialMediaMonitor instance
    """
    try:
        from src.core.config import settings
        return SocialMediaMonitor(
            twitter_bearer_token=settings.TWITTER_BEARER_TOKEN or None,
            linkedin_access_token=settings.LINKEDIN_ACCESS_TOKEN or None
        )
    except ImportError:
        logger.warning("Could not import settings, creating SocialMediaMonitor without credentials")
        return SocialMediaMonitor()

