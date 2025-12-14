"""
Job Board Integration Service
Fetches structured hiring data from Greenhouse and Lever public APIs.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class JobPosting:
    """Standardized job posting model."""
    id: str
    title: str
    location: str
    department: str
    url: str
    updated_at: datetime
    source: str  # 'greenhouse' or 'lever'

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['updated_at'] = self.updated_at.isoformat()
        return data

class GreenhouseClient:
    """Client for Greenhouse Public Harvest API."""
    
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def fetch_jobs(self, board_token: str) -> List[JobPosting]:
        """
        Fetch jobs from a company's Greenhouse board.
        
        Args:
            board_token: The company's board identifier (e.g., 'stripe', 'airbnb')
            
        Returns:
            List of JobPosting objects
        """
        try:
            url = f"{self.BASE_URL}/{board_token}/jobs?content=true"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 404:
                logger.warning(f"Greenhouse board not found for token: {board_token}")
                return []
                
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for job in data.get('jobs', []):
                # Parse date
                updated_at = datetime.utcnow()
                if job.get('updated_at'):
                    try:
                        updated_at = datetime.fromisoformat(job['updated_at'].replace('Z', '+00:00'))
                    except:
                        pass

                jobs.append(JobPosting(
                    id=str(job.get('id')),
                    title=job.get('title', 'Unknown Role'),
                    location=job.get('location', {}).get('name', 'Remote'),
                    department=job.get('departments', [{}])[0].get('name', 'Uncategorized'),
                    url=job.get('absolute_url', ''),
                    updated_at=updated_at,
                    source='greenhouse'
                ))
            
            logger.info(f"Fetched {len(jobs)} jobs from Greenhouse for {board_token}")
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching Greenhouse jobs for {board_token}: {e}")
            return []

class LeverClient:
    """Client for Lever Postings API."""
    
    BASE_URL = "https://api.lever.co/v0/postings"

    def fetch_jobs(self, company_name: str) -> List[JobPosting]:
        """
        Fetch jobs from a company's Lever board.
        
        Args:
            company_name: The company's name in Lever URL (e.g., 'netflix', 'lyft')
            
        Returns:
            List of JobPosting objects
        """
        try:
            url = f"{self.BASE_URL}/{company_name}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 404:
                logger.warning(f"Lever board not found for company: {company_name}")
                return []
                
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for job in data:
                # convert timestamp ms to datetime
                created_at = datetime.utcnow()
                if job.get('createdAt'):
                    created_at = datetime.fromtimestamp(job['createdAt'] / 1000)

                jobs.append(JobPosting(
                    id=job.get('id'),
                    title=job.get('text', 'Unknown Role'),
                    location=job.get('categories', {}).get('location', 'Remote'),
                    department=job.get('categories', {}).get('team', 'Uncategorized'),
                    url=job.get('hostedUrl', ''),
                    updated_at=created_at,
                    source='lever'
                ))
            
            logger.info(f"Fetched {len(jobs)} jobs from Lever for {company_name}")
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching Lever jobs for {company_name}: {e}")
            return []

class JobBoardAggregator:
    """Unified interface for fetching jobs from multiple boards."""
    
    def __init__(self):
        self.greenhouse = GreenhouseClient()
        self.lever = LeverClient()
        
    def fetch_company_jobs(self, company_id: str, preferred_source: str = 'auto') -> List[Dict]:
        """
        Try to fetch jobs from known sources.
        
        Args:
            company_id: Company identifier (slug)
            preferred_source: 'greenhouse', 'lever', or 'auto'
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        # Simple heuristic: try both if auto, or specific if requested
        # In a real app, you'd store which ATS a competitor uses in the DB
        
        if preferred_source in ['greenhouse', 'auto']:
            gh_jobs = self.greenhouse.fetch_jobs(company_id)
            if gh_jobs:
                jobs.extend(gh_jobs)
                
        if preferred_source in ['lever', 'auto'] and not jobs:
            # Only try Lever if we didn't get Greenhouse jobs (or if specific)
            # Or we could fetch both if we suspect they use both (rare)
            lv_jobs = self.lever.fetch_jobs(company_id)
            if lv_jobs:
                jobs.extend(lv_jobs)
                
        return [j.to_dict() for j in jobs]
