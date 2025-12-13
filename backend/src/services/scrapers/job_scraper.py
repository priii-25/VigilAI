"""
Job Posting API Integration Service
Collects hiring data from Greenhouse, Lever APIs and job board scraping fallbacks.
Tracks competitor hiring trends for strategic intelligence.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict, field
import json
import time
import re

logger = logging.getLogger(__name__)


@dataclass
class JobPosting:
    """Represents a job posting."""
    title: str
    department: str
    location: str
    job_type: str  # full-time, contract, etc.
    url: str
    company: str
    source: str  # greenhouse, lever, indeed, linkedin
    description_snippet: str = ""
    posted_date: Optional[datetime] = None
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['posted_date'] = self.posted_date.isoformat() if self.posted_date else None
        data['detected_at'] = self.detected_at.isoformat()
        return data


@dataclass
class HiringTrends:
    """Aggregated hiring trends for a company."""
    company: str
    total_openings: int
    departments: Dict[str, int]
    locations: Dict[str, int]
    job_types: Dict[str, int]
    growth_areas: List[str]
    strategic_signals: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class GreenhouseJobScraper:
    """
    Greenhouse Job Board API integration.
    Uses the free public job board API: https://developers.greenhouse.io/job-board.html
    """
    
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'VigilAI Competitive Intelligence/1.0'
        })
    
    def get_jobs(self, board_token: str, content: bool = True) -> Dict[str, Any]:
        """
        Fetch all jobs from a Greenhouse job board.
        
        Args:
            board_token: Company's Greenhouse board token (e.g., 'figma', 'stripe')
            content: Whether to include full job descriptions
            
        Returns:
            Dict containing jobs and metadata
        """
        try:
            url = f"{self.BASE_URL}/{board_token}/jobs"
            params = {'content': 'true' if content else 'false'}
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get('jobs', [])
            
            return {
                'success': True,
                'source': 'greenhouse',
                'board_token': board_token,
                'total_jobs': len(jobs),
                'jobs': [self._parse_job(job, board_token) for job in jobs],
                'fetched_at': datetime.utcnow().isoformat()
            }
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Greenhouse board not found: {board_token}")
                return {'success': False, 'error': 'Board not found', 'source': 'greenhouse'}
            raise
        except Exception as e:
            logger.error(f"Error fetching Greenhouse jobs for {board_token}: {str(e)}")
            return {'success': False, 'error': str(e), 'source': 'greenhouse'}
    
    def _parse_job(self, job_data: Dict, board_token: str) -> JobPosting:
        """Parse Greenhouse job data into JobPosting."""
        location = job_data.get('location', {}).get('name', 'Remote')
        
        # Extract department from departments array
        departments = job_data.get('departments', [])
        department = departments[0].get('name', 'General') if departments else 'General'
        
        # Get first paragraph of content as snippet
        content = job_data.get('content', '')
        soup = BeautifulSoup(content, 'html.parser')
        snippet = soup.get_text()[:300] if soup else ''
        
        # Parse updated_at as posted date
        updated_at = job_data.get('updated_at')
        posted_date = None
        if updated_at:
            try:
                posted_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except:
                pass
        
        return JobPosting(
            title=job_data.get('title', 'Unknown Position'),
            department=department,
            location=location,
            job_type='full-time',  # Greenhouse doesn't always specify
            url=job_data.get('absolute_url', ''),
            company=board_token,
            source='greenhouse',
            description_snippet=snippet,
            posted_date=posted_date
        )
    
    def get_departments(self, board_token: str) -> List[Dict]:
        """Get all departments for a board."""
        try:
            url = f"{self.BASE_URL}/{board_token}/departments"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json().get('departments', [])
        except Exception as e:
            logger.error(f"Error fetching departments: {str(e)}")
            return []


class LeverJobScraper:
    """
    Lever Job Postings API integration.
    Uses the public postings API: https://hire.lever.co/v0/postings/{company}
    """
    
    BASE_URL = "https://api.lever.co/v0/postings"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'VigilAI Competitive Intelligence/1.0'
        })
    
    def get_jobs(self, company_slug: str, mode: str = 'json') -> Dict[str, Any]:
        """
        Fetch all jobs from a Lever postings page.
        
        Args:
            company_slug: Company's Lever slug (e.g., 'netflix', 'twitch')
            mode: Response format ('json' or 'html')
            
        Returns:
            Dict containing jobs and metadata
        """
        try:
            url = f"{self.BASE_URL}/{company_slug}"
            params = {'mode': mode}
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            jobs_data = response.json()
            
            if not isinstance(jobs_data, list):
                return {'success': False, 'error': 'Unexpected response format'}
            
            return {
                'success': True,
                'source': 'lever',
                'company_slug': company_slug,
                'total_jobs': len(jobs_data),
                'jobs': [self._parse_job(job, company_slug) for job in jobs_data],
                'fetched_at': datetime.utcnow().isoformat()
            }
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Lever company not found: {company_slug}")
                return {'success': False, 'error': 'Company not found', 'source': 'lever'}
            raise
        except Exception as e:
            logger.error(f"Error fetching Lever jobs for {company_slug}: {str(e)}")
            return {'success': False, 'error': str(e), 'source': 'lever'}
    
    def _parse_job(self, job_data: Dict, company_slug: str) -> JobPosting:
        """Parse Lever job data into JobPosting."""
        categories = job_data.get('categories', {})
        
        # Parse created timestamp
        created_at = job_data.get('createdAt')
        posted_date = None
        if created_at:
            try:
                posted_date = datetime.fromtimestamp(created_at / 1000)
            except:
                pass
        
        return JobPosting(
            title=job_data.get('text', 'Unknown Position'),
            department=categories.get('department', 'General'),
            location=categories.get('location', 'Remote'),
            job_type=categories.get('commitment', 'Full-time'),
            url=job_data.get('hostedUrl', ''),
            company=company_slug,
            source='lever',
            description_snippet=job_data.get('descriptionPlain', '')[:300],
            posted_date=posted_date
        )


class IndeedScraper:
    """
    Indeed job scraper as fallback for companies without ATS APIs.
    Uses web scraping (respect robots.txt and rate limits).
    """
    
    BASE_URL = "https://www.indeed.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
        })
    
    def search_company_jobs(
        self, 
        company_name: str, 
        location: str = "",
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        Search for jobs at a specific company on Indeed.
        
        Args:
            company_name: Company name to search
            location: Optional location filter
            limit: Maximum jobs to return
            
        Returns:
            Dict containing jobs and metadata
        """
        try:
            # Build search URL
            params = {
                'q': f'company:"{company_name}"',
                'l': location,
                'sort': 'date',
            }
            
            url = f"{self.BASE_URL}/jobs"
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.find_all('div', class_=re.compile(r'job_seen_beacon|jobsearch-SerpJobCard'))[:limit]
            
            jobs = []
            for card in job_cards:
                job = self._parse_job_card(card, company_name)
                if job:
                    jobs.append(job)
            
            return {
                'success': True,
                'source': 'indeed',
                'company': company_name,
                'total_jobs': len(jobs),
                'jobs': jobs,
                'fetched_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scraping Indeed for {company_name}: {str(e)}")
            return {'success': False, 'error': str(e), 'source': 'indeed'}
    
    def _parse_job_card(self, card, company_name: str) -> Optional[JobPosting]:
        """Parse Indeed job card into JobPosting."""
        try:
            # Extract title
            title_elem = card.find(['h2', 'a'], class_=re.compile(r'jobTitle|title'))
            title = title_elem.get_text(strip=True) if title_elem else 'Unknown'
            
            # Extract location
            loc_elem = card.find('div', class_=re.compile(r'companyLocation|location'))
            location = loc_elem.get_text(strip=True) if loc_elem else 'Remote'
            
            # Extract URL
            link_elem = card.find('a', href=True)
            url = f"{self.BASE_URL}{link_elem['href']}" if link_elem else ''
            
            # Extract snippet
            snippet_elem = card.find('div', class_=re.compile(r'job-snippet'))
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
            
            return JobPosting(
                title=title,
                department=self._infer_department(title),
                location=location,
                job_type='full-time',
                url=url,
                company=company_name,
                source='indeed',
                description_snippet=snippet[:300]
            )
        except Exception as e:
            logger.debug(f"Error parsing job card: {str(e)}")
            return None
    
    def _infer_department(self, title: str) -> str:
        """Infer department from job title."""
        title_lower = title.lower()
        
        department_keywords = {
            'Engineering': ['engineer', 'developer', 'software', 'devops', 'sre', 'architect'],
            'Product': ['product manager', 'product owner', 'pm'],
            'Design': ['designer', 'ux', 'ui', 'creative'],
            'Sales': ['sales', 'account executive', 'sdr', 'bdr'],
            'Marketing': ['marketing', 'growth', 'brand', 'content'],
            'People': ['hr', 'recruiter', 'people', 'talent'],
            'Finance': ['finance', 'accounting', 'controller'],
            'Operations': ['operations', 'ops', 'supply chain'],
            'Data': ['data scientist', 'data analyst', 'analytics', 'ml', 'machine learning'],
            'Customer Success': ['customer success', 'support', 'implementation'],
        }
        
        for dept, keywords in department_keywords.items():
            if any(kw in title_lower for kw in keywords):
                return dept
        
        return 'General'


class JobPostingAggregator:
    """
    Unified job posting service that aggregates data from multiple sources.
    Provides hiring trend analysis and strategic signals.
    """
    
    def __init__(self):
        self.greenhouse = GreenhouseJobScraper()
        self.lever = LeverJobScraper()
        self.indeed = IndeedScraper()
    
    def collect_competitor_jobs(
        self,
        company_name: str,
        greenhouse_token: Optional[str] = None,
        lever_slug: Optional[str] = None,
        use_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Collect job postings from all available sources for a competitor.
        
        Args:
            company_name: Company name
            greenhouse_token: Optional Greenhouse board token
            lever_slug: Optional Lever company slug
            use_fallback: Whether to use Indeed as fallback
            
        Returns:
            Aggregated job data with hiring trends
        """
        all_jobs = []
        sources_used = []
        
        # Try Greenhouse
        if greenhouse_token:
            gh_result = self.greenhouse.get_jobs(greenhouse_token)
            if gh_result.get('success'):
                all_jobs.extend(gh_result['jobs'])
                sources_used.append('greenhouse')
                logger.info(f"Fetched {len(gh_result['jobs'])} jobs from Greenhouse")
        
        # Try Lever
        if lever_slug:
            lever_result = self.lever.get_jobs(lever_slug)
            if lever_result.get('success'):
                all_jobs.extend(lever_result['jobs'])
                sources_used.append('lever')
                logger.info(f"Fetched {len(lever_result['jobs'])} jobs from Lever")
        
        # Fallback to Indeed if no ATS data
        if use_fallback and not sources_used:
            logger.info(f"Using Indeed fallback for {company_name}")
            indeed_result = self.indeed.search_company_jobs(company_name)
            if indeed_result.get('success'):
                all_jobs.extend(indeed_result['jobs'])
                sources_used.append('indeed')
        
        # Analyze hiring trends
        trends = self._analyze_hiring_trends(company_name, all_jobs)
        
        return {
            'company': company_name,
            'total_openings': len(all_jobs),
            'sources': sources_used,
            'jobs': [j.to_dict() if isinstance(j, JobPosting) else j for j in all_jobs],
            'hiring_trends': trends.to_dict() if trends else None,
            'fetched_at': datetime.utcnow().isoformat()
        }
    
    def _analyze_hiring_trends(
        self, 
        company_name: str, 
        jobs: List[JobPosting]
    ) -> Optional[HiringTrends]:
        """Analyze job postings to identify hiring trends and strategic signals."""
        if not jobs:
            return None
        
        # Count by department
        departments = {}
        locations = {}
        job_types = {}
        
        for job in jobs:
            if isinstance(job, JobPosting):
                dept = job.department
                loc = job.location
                jtype = job.job_type
            else:
                dept = job.get('department', 'General')
                loc = job.get('location', 'Unknown')
                jtype = job.get('job_type', 'full-time')
            
            departments[dept] = departments.get(dept, 0) + 1
            locations[loc] = locations.get(loc, 0) + 1
            job_types[jtype] = job_types.get(jtype, 0) + 1
        
        # Identify growth areas (departments with 3+ openings)
        growth_areas = [dept for dept, count in departments.items() if count >= 3]
        
        # Generate strategic signals
        strategic_signals = self._generate_strategic_signals(departments, locations, len(jobs))
        
        return HiringTrends(
            company=company_name,
            total_openings=len(jobs),
            departments=departments,
            locations=locations,
            job_types=job_types,
            growth_areas=growth_areas,
            strategic_signals=strategic_signals
        )
    
    def _generate_strategic_signals(
        self, 
        departments: Dict[str, int], 
        locations: Dict[str, int],
        total: int
    ) -> List[str]:
        """Generate strategic intelligence signals from hiring data."""
        signals = []
        
        # Engineering focus
        eng_count = departments.get('Engineering', 0) + departments.get('Data', 0)
        if eng_count > total * 0.4:
            signals.append("Heavy engineering investment - likely building new products/features")
        
        # Sales expansion
        sales_count = departments.get('Sales', 0)
        if sales_count > total * 0.3:
            signals.append("Sales expansion - preparing for market push or new segments")
        
        # International expansion
        intl_locations = [loc for loc in locations if 'remote' not in loc.lower()]
        if len(intl_locations) > 3:
            signals.append(f"Geographic expansion to {len(intl_locations)} locations")
        
        # AI/ML focus
        ml_keywords = ['ml', 'machine learning', 'ai', 'data scientist']
        data_count = departments.get('Data', 0)
        if data_count >= 3:
            signals.append("AI/ML capability buildout detected")
        
        # Customer Success scaling
        cs_count = departments.get('Customer Success', 0)
        if cs_count >= 3:
            signals.append("Customer Success scaling - likely preparing for enterprise growth")
        
        if not signals:
            signals.append("Standard hiring activity - no major strategic shifts detected")
        
        return signals


# Convenience function for pipeline integration
async def collect_job_data(
    company_name: str,
    greenhouse_token: Optional[str] = None,
    lever_slug: Optional[str] = None
) -> Dict[str, Any]:
    """
    Async wrapper for job data collection.
    
    Args:
        company_name: Name of the competitor
        greenhouse_token: Optional Greenhouse board token
        lever_slug: Optional Lever company slug
        
    Returns:
        Dict containing job postings and hiring trends
    """
    aggregator = JobPostingAggregator()
    return aggregator.collect_competitor_jobs(
        company_name=company_name,
        greenhouse_token=greenhouse_token,
        lever_slug=lever_slug
    )
