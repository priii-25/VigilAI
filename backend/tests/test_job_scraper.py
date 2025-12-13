"""
Tests for Job Posting API Integration
Tests Greenhouse, Lever, and Indeed scrapers
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.services.scrapers.job_scraper import (
    GreenhouseJobScraper,
    LeverJobScraper,
    IndeedScraper,
    JobPostingAggregator,
    JobPosting,
    HiringTrends
)


class TestJobPosting:
    """Test JobPosting dataclass"""
    
    def test_job_posting_creation(self):
        """Test creating a JobPosting"""
        job = JobPosting(
            title="Senior Engineer",
            department="Engineering",
            location="San Francisco, CA",
            job_type="full-time",
            url="https://example.com/job/123",
            company="TestCorp",
            source="greenhouse"
        )
        
        assert job.title == "Senior Engineer"
        assert job.department == "Engineering"
        assert job.source == "greenhouse"
    
    def test_job_posting_to_dict(self):
        """Test serialization to dict"""
        job = JobPosting(
            title="Product Manager",
            department="Product",
            location="Remote",
            job_type="full-time",
            url="https://example.com/job/456",
            company="TestCorp",
            source="lever"
        )
        
        data = job.to_dict()
        assert data['title'] == "Product Manager"
        assert 'detected_at' in data
        assert data['source'] == "lever"


class TestGreenhouseJobScraper:
    """Test Greenhouse API integration"""
    
    @pytest.fixture
    def scraper(self):
        return GreenhouseJobScraper()
    
    @patch('requests.Session.get')
    def test_get_jobs_success(self, mock_get, scraper):
        """Test successful job fetch from Greenhouse"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'jobs': [
                {
                    'title': 'Software Engineer',
                    'location': {'name': 'New York'},
                    'departments': [{'name': 'Engineering'}],
                    'absolute_url': 'https://boards.greenhouse.io/test/jobs/123',
                    'updated_at': '2024-01-15T10:00:00Z',
                    'content': '<p>Job description here</p>'
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = scraper.get_jobs('testcompany')
        
        assert result['success'] is True
        assert result['total_jobs'] == 1
        assert len(result['jobs']) == 1
        assert result['jobs'][0].title == 'Software Engineer'
    
    @patch('requests.Session.get')
    def test_get_jobs_not_found(self, mock_get, scraper):
        """Test handling of 404 errors"""
        from requests.exceptions import HTTPError
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        result = scraper.get_jobs('nonexistent')
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()


class TestLeverJobScraper:
    """Test Lever API integration"""
    
    @pytest.fixture
    def scraper(self):
        return LeverJobScraper()
    
    @patch('requests.Session.get')
    def test_get_jobs_success(self, mock_get, scraper):
        """Test successful job fetch from Lever"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                'text': 'Data Scientist',
                'categories': {
                    'department': 'Data',
                    'location': 'Remote',
                    'commitment': 'Full-time'
                },
                'hostedUrl': 'https://jobs.lever.co/test/123',
                'createdAt': 1704067200000,
                'descriptionPlain': 'Looking for a data scientist...'
            }
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = scraper.get_jobs('testcompany')
        
        assert result['success'] is True
        assert result['total_jobs'] == 1
        assert result['jobs'][0].title == 'Data Scientist'
        assert result['jobs'][0].department == 'Data'


class TestIndeedScraper:
    """Test Indeed web scraping"""
    
    @pytest.fixture
    def scraper(self):
        return IndeedScraper()
    
    def test_infer_department_engineering(self, scraper):
        """Test department inference for engineering roles"""
        assert scraper._infer_department("Software Engineer") == "Engineering"
        assert scraper._infer_department("DevOps Engineer") == "Engineering"
        assert scraper._infer_department("Backend Developer") == "Engineering"
    
    def test_infer_department_sales(self, scraper):
        """Test department inference for sales roles"""
        assert scraper._infer_department("Account Executive") == "Sales"
        assert scraper._infer_department("Sales Development Rep") == "Sales"
    
    def test_infer_department_general(self, scraper):
        """Test department inference falls back to General"""
        assert scraper._infer_department("Office Manager") == "General"


class TestJobPostingAggregator:
    """Test unified job aggregation"""
    
    @pytest.fixture
    def aggregator(self):
        return JobPostingAggregator()
    
    def test_analyze_hiring_trends(self, aggregator):
        """Test hiring trend analysis"""
        jobs = [
            JobPosting("Engineer", "Engineering", "NYC", "full-time", "", "Test", "test"),
            JobPosting("Engineer 2", "Engineering", "SF", "full-time", "", "Test", "test"),
            JobPosting("Engineer 3", "Engineering", "Remote", "full-time", "", "Test", "test"),
            JobPosting("PM", "Product", "NYC", "full-time", "", "Test", "test"),
        ]
        
        trends = aggregator._analyze_hiring_trends("TestCorp", jobs)
        
        assert trends.total_openings == 4
        assert trends.departments['Engineering'] == 3
        assert trends.departments['Product'] == 1
        assert 'Engineering' in trends.growth_areas
    
    def test_generate_strategic_signals_engineering(self, aggregator):
        """Test strategic signal generation for engineering focus"""
        departments = {'Engineering': 5, 'Product': 1, 'Sales': 1}
        locations = {'NYC': 3, 'SF': 2, 'Remote': 2}
        
        signals = aggregator._generate_strategic_signals(departments, locations, 7)
        
        assert any('engineering' in s.lower() for s in signals)
    
    def test_generate_strategic_signals_sales(self, aggregator):
        """Test strategic signal generation for sales focus"""
        departments = {'Sales': 5, 'Engineering': 2}
        locations = {'NYC': 7}
        
        signals = aggregator._generate_strategic_signals(departments, locations, 7)
        
        assert any('sales' in s.lower() for s in signals)


class TestHiringTrends:
    """Test HiringTrends dataclass"""
    
    def test_hiring_trends_to_dict(self):
        """Test serialization"""
        trends = HiringTrends(
            company="TestCorp",
            total_openings=10,
            departments={"Engineering": 5, "Sales": 3},
            locations={"NYC": 7, "Remote": 3},
            job_types={"full-time": 10},
            growth_areas=["Engineering"],
            strategic_signals=["Heavy engineering investment"]
        )
        
        data = trends.to_dict()
        assert data['company'] == "TestCorp"
        assert data['total_openings'] == 10
        assert 'timestamp' in data
