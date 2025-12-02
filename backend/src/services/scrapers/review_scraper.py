"""
Review and sentiment scraping service for G2, Gartner, etc.
Production-ready with rate limiting and robust parsing
"""
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from loguru import logger
from src.core.config import settings
import time
import json


class ReviewScraper:
    """Scraper for product review sites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.rate_limit_delay = 2  # seconds between requests
    
    def scrape_g2_reviews(self, product_url: str, limit: int = 20) -> Dict:
        """
        Scrape G2 reviews for a competitor product
        
        Args:
            product_url: G2 product page URL
            limit: Maximum number of reviews to fetch
            
        Returns:
            Dict containing reviews, ratings, and metadata
        """
        logger.info(f"Starting G2 review scrape for {product_url}")
        
        reviews_data = {
            'url': product_url,
            'scraped_at': datetime.utcnow().isoformat(),
            'platform': 'G2',
            'reviews': [],
            'summary': {
                'total_reviews': 0,
                'average_rating': 0.0,
                'rating_distribution': {},
                'sentiment_score': 0.0
            }
        }
        
        try:
            time.sleep(self.rate_limit_delay)
            response = self.session.get(product_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract overall rating
            rating_elem = soup.find('div', class_=['fw-semibold', 'rating'])
            if rating_elem:
                try:
                    reviews_data['summary']['average_rating'] = float(rating_elem.get_text(strip=True))
                except (ValueError, AttributeError):
                    pass
            
            # Extract total review count
            count_elem = soup.find('span', class_=['fw-semibold', 'reviews-count'])
            if not count_elem:
                # Alternative selectors
                count_elem = soup.find(['span', 'div'], string=lambda t: t and 'reviews' in t.lower())
            
            if count_elem:
                text = count_elem.get_text(strip=True)
                try:
                    reviews_data['summary']['total_reviews'] = int(''.join(filter(str.isdigit, text)))
                except ValueError:
                    pass
            
            # Extract individual reviews
            review_cards = soup.find_all(['div', 'article'], class_=lambda x: x and 'review' in str(x).lower())[:limit]
            
            for card in review_cards:
                review = self._extract_g2_review(card)
                if review and review.get('text'):
                    reviews_data['reviews'].append(review)
            
            # Calculate sentiment
            if reviews_data['reviews']:
                reviews_data['summary']['sentiment_score'] = self._calculate_sentiment_score(reviews_data['reviews'])
                reviews_data['summary']['rating_distribution'] = self._calculate_rating_distribution(reviews_data['reviews'])
            
            logger.info(f"Extracted {len(reviews_data['reviews'])} reviews from G2")
            
        except requests.RequestException as e:
            logger.error(f"Error scraping G2 reviews: {str(e)}")
        
        return reviews_data
    
    def _extract_g2_review(self, card) -> Optional[Dict]:
        """Extract individual G2 review data"""
        try:
            review = {}
            
            # Rating
            rating_elem = card.find(['div', 'span'], class_=lambda x: x and 'star' in str(x).lower())
            if rating_elem:
                rating_text = rating_elem.get('aria-label', '') or rating_elem.get_text()
                try:
                    review['rating'] = float(''.join(filter(lambda c: c.isdigit() or c == '.', rating_text))[:3])
                except (ValueError, AttributeError):
                    review['rating'] = None
            
            # Review title
            title_elem = card.find(['h3', 'h4', 'strong'], class_=lambda x: x and 'title' in str(x).lower())
            if title_elem:
                review['title'] = title_elem.get_text(strip=True)[:200]
            
            # Review text
            text_elem = card.find(['p', 'div'], class_=lambda x: x and ('review' in str(x).lower() or 'comment' in str(x).lower()))
            if text_elem:
                review['text'] = text_elem.get_text(strip=True)[:1000]
            
            # Reviewer info
            reviewer_elem = card.find(['span', 'div'], class_=lambda x: x and 'reviewer' in str(x).lower())
            if reviewer_elem:
                review['reviewer'] = reviewer_elem.get_text(strip=True)[:100]
            
            # Date
            date_elem = card.find(['time', 'span'], class_=lambda x: x and 'date' in str(x).lower())
            if date_elem:
                review['date'] = date_elem.get('datetime', '') or date_elem.get_text(strip=True)
            
            # Pros/Cons
            pros_elem = card.find(string=lambda t: t and 'pros' in t.lower())
            if pros_elem:
                pros_parent = pros_elem.find_parent(['div', 'section'])
                if pros_parent:
                    review['pros'] = pros_parent.get_text(strip=True).replace('Pros:', '').strip()[:500]
            
            cons_elem = card.find(string=lambda t: t and 'cons' in t.lower())
            if cons_elem:
                cons_parent = cons_elem.find_parent(['div', 'section'])
                if cons_parent:
                    review['cons'] = cons_parent.get_text(strip=True).replace('Cons:', '').strip()[:500]
            
            return review if review.get('text') else None
            
        except Exception as e:
            logger.warning(f"Error extracting G2 review: {str(e)}")
            return None
    
    def scrape_capterra_reviews(self, product_url: str, limit: int = 20) -> Dict:
        """Scrape Capterra reviews"""
        logger.info(f"Starting Capterra review scrape for {product_url}")
        
        reviews_data = {
            'url': product_url,
            'scraped_at': datetime.utcnow().isoformat(),
            'platform': 'Capterra',
            'reviews': [],
            'summary': {}
        }
        
        try:
            time.sleep(self.rate_limit_delay)
            response = self.session.get(product_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Similar extraction logic to G2 but with Capterra-specific selectors
            review_cards = soup.find_all('div', class_=lambda x: x and 'review' in str(x).lower())[:limit]
            
            for card in review_cards:
                review = self._extract_capterra_review(card)
                if review:
                    reviews_data['reviews'].append(review)
            
            logger.info(f"Extracted {len(reviews_data['reviews'])} reviews from Capterra")
            
        except requests.RequestException as e:
            logger.error(f"Error scraping Capterra reviews: {str(e)}")
        
        return reviews_data
    
    def _extract_capterra_review(self, card) -> Optional[Dict]:
        """Extract individual Capterra review"""
        # Similar to G2 extraction
        return self._extract_g2_review(card)
    
    def _calculate_sentiment_score(self, reviews: List[Dict]) -> float:
        """
        Calculate overall sentiment score from reviews
        
        Returns:
            Float between 0-10 (10 = most positive)
        """
        if not reviews:
            return 0.0
        
        total_score = 0
        count = 0
        
        for review in reviews:
            rating = review.get('rating')
            if rating:
                # Normalize rating to 0-10 scale (assuming 5-star system)
                normalized = (rating / 5.0) * 10.0
                total_score += normalized
                count += 1
        
        return round(total_score / count, 2) if count > 0 else 0.0
    
    def _calculate_rating_distribution(self, reviews: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of ratings"""
        distribution = {'5': 0, '4': 0, '3': 0, '2': 0, '1': 0}
        
        for review in reviews:
            rating = review.get('rating')
            if rating:
                key = str(int(rating))
                if key in distribution:
                    distribution[key] += 1
        
        return distribution
    
    def extract_common_complaints(self, reviews: List[Dict], limit: int = 5) -> List[str]:
        """
        Extract most common complaints from reviews
        Simple keyword-based extraction
        """
        complaints = []
        complaint_keywords = [
            'bug', 'slow', 'crash', 'error', 'issue', 'problem',
            'difficult', 'complicated', 'confusing', 'poor', 'lack',
            'missing', 'expensive', 'costly', 'overpriced'
        ]
        
        for review in reviews:
            cons = review.get('cons', '')
            text = review.get('text', '')
            
            combined_text = (cons + ' ' + text).lower()
            
            for keyword in complaint_keywords:
                if keyword in combined_text:
                    # Extract sentence containing keyword
                    sentences = combined_text.split('.')
                    for sentence in sentences:
                        if keyword in sentence and len(sentence.strip()) > 10:
                            complaints.append(sentence.strip()[:200])
                            break
        
        # Return unique complaints
        return list(set(complaints))[:limit]
    
    def extract_praised_features(self, reviews: List[Dict], limit: int = 5) -> List[str]:
        """Extract most praised features from reviews"""
        praises = []
        praise_keywords = [
            'easy', 'simple', 'fast', 'great', 'excellent', 'love',
            'helpful', 'intuitive', 'powerful', 'reliable', 'best'
        ]
        
        for review in reviews:
            pros = review.get('pros', '')
            text = review.get('text', '')
            
            combined_text = (pros + ' ' + text).lower()
            
            for keyword in praise_keywords:
                if keyword in combined_text:
                    sentences = combined_text.split('.')
                    for sentence in sentences:
                        if keyword in sentence and len(sentence.strip()) > 10:
                            praises.append(sentence.strip()[:200])
                            break
        
        return list(set(praises))[:limit]


class SentimentAnalyzer:
    """Production-ready sentiment analysis service"""
    
    def __init__(self):
        self.positive_words = [
            'excellent', 'great', 'amazing', 'love', 'best', 'easy',
            'fantastic', 'wonderful', 'perfect', 'helpful', 'intuitive'
        ]
        self.negative_words = [
            'bad', 'terrible', 'worst', 'hate', 'poor', 'difficult',
            'complicated', 'slow', 'expensive', 'buggy', 'broken'
        ]
    
    def analyze_review_text(self, text: str) -> Dict:
        """
        Analyze sentiment of review text
        
        Returns:
            Dict with sentiment classification and score
        """
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        # Calculate sentiment score (-1 to 1)
        total = positive_count + negative_count
        if total == 0:
            sentiment_score = 0
        else:
            sentiment_score = (positive_count - negative_count) / total
        
        # Classify sentiment
        if sentiment_score > 0.3:
            sentiment = 'positive'
        elif sentiment_score < -0.3:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': sentiment_score,
            'positive_indicators': positive_count,
            'negative_indicators': negative_count
        }
    
    def analyze_reviews_batch(self, reviews: List[Dict]) -> Dict:
        """Analyze sentiment for batch of reviews"""
        results = {
            'overall_sentiment': 'neutral',
            'positive_ratio': 0.0,
            'negative_ratio': 0.0,
            'neutral_ratio': 0.0,
            'sentiment_trend': []
        }
        
        if not reviews:
            return results
        
        sentiments = []
        for review in reviews:
            text = review.get('text', '') + ' ' + review.get('pros', '') + ' ' + review.get('cons', '')
            analysis = self.analyze_review_text(text)
            sentiments.append(analysis['sentiment'])
            results['sentiment_trend'].append({
                'date': review.get('date', ''),
                'sentiment': analysis['sentiment'],
                'score': analysis['score']
            })
        
        # Calculate ratios
        total = len(sentiments)
        results['positive_ratio'] = round(sentiments.count('positive') / total, 2)
        results['negative_ratio'] = round(sentiments.count('negative') / total, 2)
        results['neutral_ratio'] = round(sentiments.count('neutral') / total, 2)
        
        # Overall sentiment
        if results['positive_ratio'] > 0.5:
            results['overall_sentiment'] = 'positive'
        elif results['negative_ratio'] > 0.3:
            results['overall_sentiment'] = 'negative'
        
        return results
