"""
Tests for web scraping services
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.scrapers.web_scraper import (
    WebScraper, PricingScraper, CareersScraper, ContentScraper
)


class TestWebScraper:
    """Tests for base WebScraper class"""
    
    def test_init(self):
        """Test WebScraper initialization"""
        scraper = WebScraper()
        assert scraper.session is not None
        assert 'User-Agent' in scraper.headers
    
    @patch('requests.Session.get')
    def test_fetch_page_success(self, mock_get):
        """Test successful page fetch"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>Test</body></html>'
        mock_get.return_value = mock_response
        
        scraper = WebScraper()
        content = scraper.fetch_page('https://example.com')
        
        assert content == '<html><body>Test</body></html>'
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_fetch_page_failure(self, mock_get):
        """Test page fetch failure handling"""
        mock_get.side_effect = Exception("Connection error")
        
        scraper = WebScraper()
        content = scraper.fetch_page('https://example.com')
        
        assert content is None
    
    @patch('requests.Session.head')
    def test_check_page_modified(self, mock_head):
        """Test page modification check"""
        mock_response = Mock()
        mock_response.headers = {'Last-Modified': 'Wed, 21 Oct 2023 07:28:00 GMT'}
        mock_head.return_value = mock_response
        
        scraper = WebScraper()
        modified = scraper.check_page_modified('https://example.com')
        
        assert modified is True


class TestPricingScraper:
    """Tests for PricingScraper"""
    
    @patch.object(WebScraper, 'fetch_page')
    def test_scrape_pricing(self, mock_fetch):
        """Test pricing page scraping"""
        mock_fetch.return_value = '''
        <html>
        <body>
            <div class="pricing-plan">
                <h3>Basic</h3>
                <span class="price">$29/mo</span>
                <ul>
                    <li>Feature 1</li>
                    <li>Feature 2</li>
                </ul>
            </div>
            <div class="pricing-plan">
                <h3>Pro</h3>
                <span class="price">$99/mo</span>
                <ul>
                    <li>All Basic features</li>
                    <li>Advanced analytics</li>
                </ul>
            </div>
        </body>
        </html>
        '''
        
        scraper = PricingScraper()
        result = scraper.scrape_pricing('https://example.com/pricing')
        
        assert 'plans' in result
        assert len(result['plans']) >= 1
    
    @patch.object(WebScraper, 'fetch_page')
    def test_scrape_pricing_empty_page(self, mock_fetch):
        """Test handling of empty pricing page"""
        mock_fetch.return_value = '<html><body></body></html>'
        
        scraper = PricingScraper()
        result = scraper.scrape_pricing('https://example.com/pricing')
        
        assert 'plans' in result
        assert len(result['plans']) == 0


class TestCareersScraper:
    """Tests for CareersScraper"""
    
    @patch.object(WebScraper, 'fetch_page')
    def test_scrape_careers(self, mock_fetch):
        """Test careers page scraping"""
        mock_fetch.return_value = '''
        <html>
        <body>
            <div class="job-listing">
                <h3>Senior Software Engineer</h3>
                <span class="department">Engineering</span>
                <span class="location">San Francisco, CA</span>
            </div>
            <div class="job-listing">
                <h3>Product Manager</h3>
                <span class="department">Product</span>
                <span class="location">Remote</span>
            </div>
        </body>
        </html>
        '''
        
        scraper = CareersScraper()
        result = scraper.scrape_careers('https://example.com/careers')
        
        assert 'job_postings' in result
        assert 'hiring_trends' in result
    
    @patch.object(WebScraper, 'fetch_page')
    def test_analyze_hiring_trends(self, mock_fetch):
        """Test hiring trend analysis"""
        mock_fetch.return_value = '''
        <html>
        <body>
            <div class="job-listing">
                <h3>ML Engineer</h3>
                <span class="department">AI/ML</span>
            </div>
            <div class="job-listing">
                <h3>Data Scientist</h3>
                <span class="department">AI/ML</span>
            </div>
            <div class="job-listing">
                <h3>Backend Developer</h3>
                <span class="department">Engineering</span>
            </div>
        </body>
        </html>
        '''
        
        scraper = CareersScraper()
        result = scraper.scrape_careers('https://example.com/careers')
        
        # Verify hiring trends are analyzed
        assert 'hiring_trends' in result


class TestContentScraper:
    """Tests for ContentScraper"""
    
    @patch.object(WebScraper, 'fetch_page')
    def test_scrape_blog(self, mock_fetch):
        """Test blog content scraping"""
        mock_fetch.return_value = '''
        <html>
        <body>
            <article>
                <h2>New Product Launch</h2>
                <p>We're excited to announce our new AI features...</p>
                <time>2023-10-15</time>
            </article>
            <article>
                <h2>Partnership Announcement</h2>
                <p>Today we partnered with...</p>
                <time>2023-10-10</time>
            </article>
        </body>
        </html>
        '''
        
        scraper = ContentScraper()
        result = scraper.scrape_blog('https://example.com/blog')
        
        assert 'articles' in result
    
    @patch.object(WebScraper, 'fetch_page')
    def test_scrape_blog_no_articles(self, mock_fetch):
        """Test handling of blog with no articles"""
        mock_fetch.return_value = '<html><body>No content</body></html>'
        
        scraper = ContentScraper()
        result = scraper.scrape_blog('https://example.com/blog')
        
        assert 'articles' in result
        assert len(result['articles']) == 0
