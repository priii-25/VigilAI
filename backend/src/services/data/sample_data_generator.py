"""
Sample Data Generator and Dataset Loader
Provides synthetic and sample data for testing and demonstration.
Supports loading from public datasets and generating simulated competitor updates.
"""
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """
    Generates synthetic competitor data for testing and demonstration.
    Based on realistic e-commerce and SaaS patterns.
    """
    
    COMPETITOR_TEMPLATES = [
        {
            "name": "CompetitorAlpha",
            "industry": "E-commerce",
            "domain": "competitoralpha.com",
            "description": "Leading e-commerce platform for SMBs",
        },
        {
            "name": "TechRival Inc",
            "industry": "SaaS",
            "domain": "techrival.io",
            "description": "Enterprise software solutions provider",
        },
        {
            "name": "MarketLeader Pro",
            "industry": "Marketing",
            "domain": "marketleaderpro.com",
            "description": "Marketing automation and analytics platform",
        },
        {
            "name": "DataCorp Solutions",
            "industry": "Data Analytics",
            "domain": "datacorp.ai",
            "description": "AI-powered business intelligence solutions",
        },
        {
            "name": "CloudFirst Systems",
            "industry": "Cloud Infrastructure",
            "domain": "cloudfirst.io",
            "description": "Cloud hosting and infrastructure services",
        }
    ]
    
    PRICING_TIERS = ["Starter", "Professional", "Enterprise", "Custom"]
    
    FEATURE_POOL = [
        "User Management", "Analytics Dashboard", "API Access", "Custom Integrations",
        "Priority Support", "SLA Guarantee", "White Labeling", "SSO/SAML",
        "Advanced Reporting", "Data Export", "Audit Logs", "Team Collaboration",
        "Mobile App", "Webhooks", "Custom Workflows", "AI Insights"
    ]
    
    JOB_DEPARTMENTS = ["Engineering", "Product", "Sales", "Marketing", "Customer Success", 
                       "Design", "Data Science", "Operations", "HR", "Finance"]
    
    JOB_TITLES = {
        "Engineering": ["Senior Software Engineer", "Staff Engineer", "DevOps Engineer", 
                       "Frontend Developer", "Backend Developer", "Engineering Manager"],
        "Product": ["Product Manager", "Senior Product Manager", "Product Designer", "UX Researcher"],
        "Sales": ["Account Executive", "Sales Development Rep", "Enterprise Sales Manager"],
        "Marketing": ["Growth Marketing Manager", "Content Strategist", "Brand Manager"],
        "Data Science": ["Data Scientist", "ML Engineer", "Analytics Engineer"]
    }
    
    def generate_competitor(self, template_index: int = 0) -> Dict[str, Any]:
        """Generate a sample competitor with all data."""
        template = self.COMPETITOR_TEMPLATES[template_index % len(self.COMPETITOR_TEMPLATES)]
        
        return {
            **template,
            "pricing": self.generate_pricing_data(),
            "jobs": self.generate_job_postings(random.randint(5, 25)),
            "news": self.generate_news_items(random.randint(3, 8)),
            "reviews": self.generate_review_data(),
            "social_activity": self.generate_social_data(),
            "seo_metrics": self.generate_seo_data(),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def generate_pricing_data(self) -> Dict[str, Any]:
        """Generate sample pricing structure."""
        plans = []
        base_price = random.choice([9, 19, 29, 49])
        
        for i, tier in enumerate(self.PRICING_TIERS):
            if tier == "Custom":
                price = "Contact Sales"
            else:
                price = f"${base_price * (i + 1)}/month"
            
            # Select features (more features for higher tiers)
            num_features = 4 + i * 3
            features = random.sample(self.FEATURE_POOL, min(num_features, len(self.FEATURE_POOL)))
            
            plans.append({
                "name": tier,
                "price": price,
                "billing": "monthly" if tier != "Custom" else "custom",
                "features": features,
                "popular": tier == "Professional"
            })
        
        return {
            "plans": plans,
            "currency": "USD",
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def generate_job_postings(self, count: int = 10) -> List[Dict]:
        """Generate sample job postings."""
        jobs = []
        locations = ["San Francisco, CA", "New York, NY", "Remote", "Austin, TX", "Seattle, WA", "London, UK"]
        
        for _ in range(count):
            dept = random.choice(self.JOB_DEPARTMENTS)
            titles = self.JOB_TITLES.get(dept, ["Specialist", "Manager", "Lead"])
            
            jobs.append({
                "title": random.choice(titles),
                "department": dept,
                "location": random.choice(locations),
                "job_type": random.choice(["full-time", "full-time", "full-time", "contract"]),
                "posted_date": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                "url": f"https://careers.example.com/jobs/{random.randint(1000, 9999)}"
            })
        
        return jobs
    
    def generate_news_items(self, count: int = 5) -> List[Dict]:
        """Generate sample news items."""
        news_templates = [
            {"title": "{company} Raises ${amount}M in Series {round} Funding", "category": "funding"},
            {"title": "{company} Launches New {feature} for Enterprise Customers", "category": "product"},
            {"title": "{company} Expands to {region} Market", "category": "expansion"},
            {"title": "{company} Partners with {partner} for Enhanced Integration", "category": "partnership"},
            {"title": "{company} Appoints New {role} to Leadership Team", "category": "leadership"},
            {"title": "{company} Reports {growth}% YoY Revenue Growth", "category": "financial"},
        ]
        
        news = []
        for _ in range(count):
            template = random.choice(news_templates)
            title = template["title"].format(
                company="Competitor",
                amount=random.choice([10, 25, 50, 100, 200]),
                round=random.choice(["A", "B", "C", "D"]),
                feature=random.choice(["AI Assistant", "Analytics", "Automation", "Integration Hub"]),
                region=random.choice(["European", "APAC", "Latin American"]),
                partner=random.choice(["Salesforce", "Microsoft", "AWS", "Google"]),
                role=random.choice(["CEO", "CTO", "CFO", "VP of Engineering"]),
                growth=random.randint(30, 150)
            )
            
            news.append({
                "title": title,
                "category": template["category"],
                "source": random.choice(["TechCrunch", "Bloomberg", "Reuters", "Forbes", "VentureBeat"]),
                "published_date": (datetime.utcnow() - timedelta(days=random.randint(1, 60))).isoformat(),
                "url": f"https://news.example.com/{random.randint(10000, 99999)}"
            })
        
        return news
    
    def generate_review_data(self) -> Dict[str, Any]:
        """Generate sample review and rating data."""
        return {
            "overall_rating": round(random.uniform(3.5, 4.8), 1),
            "total_reviews": random.randint(100, 2000),
            "rating_distribution": {
                "5": random.randint(40, 60),
                "4": random.randint(20, 35),
                "3": random.randint(5, 15),
                "2": random.randint(2, 8),
                "1": random.randint(1, 5)
            },
            "sentiment_score": round(random.uniform(6.5, 9.0), 1),
            "top_pros": [
                "Easy to use interface",
                "Great customer support",
                "Powerful integrations"
            ],
            "top_cons": [
                "Expensive for small teams",
                "Learning curve for advanced features",
                "Limited customization"
            ],
            "source": "G2",
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def generate_social_data(self) -> Dict[str, Any]:
        """Generate sample social media metrics."""
        return {
            "twitter": {
                "followers": random.randint(5000, 100000),
                "posts_last_week": random.randint(5, 20),
                "engagement_rate": round(random.uniform(1.0, 5.0), 2)
            },
            "linkedin": {
                "followers": random.randint(10000, 200000),
                "posts_last_week": random.randint(3, 10),
                "engagement_rate": round(random.uniform(2.0, 8.0), 2)
            },
            "recent_posts": [
                {"content": "Excited to announce...", "platform": "twitter", "engagement": random.randint(50, 500)},
                {"content": "Join us for our webinar...", "platform": "linkedin", "engagement": random.randint(100, 1000)}
            ]
        }
    
    def generate_seo_data(self) -> Dict[str, Any]:
        """Generate sample SEO metrics."""
        keywords = ["crm software", "sales automation", "marketing platform", "business analytics"]
        
        return {
            "domain_authority": random.randint(40, 80),
            "organic_traffic": random.randint(50000, 500000),
            "keyword_rankings": [
                {"keyword": kw, "position": random.randint(1, 50), "change": random.randint(-10, 10)}
                for kw in random.sample(keywords, 3)
            ],
            "backlinks": random.randint(1000, 50000),
            "indexed_pages": random.randint(100, 5000)
        }
    
    def generate_simulated_update(self, competitor_data: Dict) -> Dict[str, Any]:
        """
        Generate a simulated update/change for a competitor.
        Used for demonstrating change detection.
        """
        update_types = ["pricing_change", "new_feature", "hiring_spike", "funding_news"]
        update_type = random.choice(update_types)
        
        if update_type == "pricing_change":
            # Simulate price change
            old_pricing = competitor_data.get("pricing", {})
            new_pricing = old_pricing.copy()
            if new_pricing.get("plans"):
                plan_idx = random.randint(0, len(new_pricing["plans"]) - 1)
                old_price = new_pricing["plans"][plan_idx].get("price", "$29/month")
                new_price = "$" + str(int(old_price.replace("$", "").split("/")[0]) + random.randint(-10, 20)) + "/month"
                new_pricing["plans"][plan_idx]["price"] = new_price
            
            return {
                "type": "pricing_change",
                "description": f"Price updated for {new_pricing['plans'][plan_idx]['name']} plan",
                "old_value": old_price,
                "new_value": new_price,
                "impact_score": 7.5,
                "detected_at": datetime.utcnow().isoformat()
            }
        
        elif update_type == "new_feature":
            new_feature = random.choice(["AI Copilot", "Advanced Analytics", "Custom Integrations Hub", "Real-time Collaboration"])
            return {
                "type": "new_feature",
                "description": f"Launched new feature: {new_feature}",
                "feature_name": new_feature,
                "impact_score": 6.0,
                "detected_at": datetime.utcnow().isoformat()
            }
        
        elif update_type == "hiring_spike":
            department = random.choice(["Engineering", "Sales", "Product"])
            count = random.randint(5, 20)
            return {
                "type": "hiring_spike",
                "description": f"Significant hiring increase in {department}",
                "department": department,
                "new_positions": count,
                "impact_score": 5.5,
                "detected_at": datetime.utcnow().isoformat()
            }
        
        else:  # funding_news
            amount = random.choice([25, 50, 100, 200])
            return {
                "type": "funding_news",
                "description": f"Raised ${amount}M in new funding round",
                "amount": amount,
                "impact_score": 8.5,
                "detected_at": datetime.utcnow().isoformat()
            }


class BattlecardSampleGenerator:
    """Generates sample battlecards for demonstration."""
    
    def generate_sample_battlecard(self, competitor_name: str = "Competitor X") -> Dict[str, Any]:
        """Generate a complete sample battlecard."""
        return {
            "competitor_name": competitor_name,
            "last_updated": datetime.utcnow().isoformat(),
            "overview": {
                "description": f"{competitor_name} is a leading provider of enterprise software solutions, focused on digital transformation and automation.",
                "founded": "2015",
                "headquarters": "San Francisco, CA",
                "employees": "500-1000",
                "funding": "$150M (Series C)",
                "target_market": "Mid-market and Enterprise"
            },
            "strengths": [
                "Strong brand recognition in the market",
                "Comprehensive feature set for enterprise use cases",
                "Excellent customer support and onboarding",
                "Robust API and integration ecosystem",
                "Strong mobile experience"
            ],
            "weaknesses": [
                "Higher price point than alternatives",
                "Complex implementation process",
                "Limited customization without professional services",
                "Slower feature release cadence",
                "Less flexible pricing for smaller teams"
            ],
            "talking_points": [
                f"While {competitor_name} has strong enterprise features, our solution offers faster time-to-value with easier implementation.",
                f"Unlike {competitor_name}'s per-seat pricing, we offer predictable flat-rate plans that scale better.",
                f"Our modern architecture provides 3x faster performance compared to {competitor_name}'s legacy platform."
            ],
            "objection_handlers": [
                {
                    "objection": f"We're already evaluating {competitor_name}",
                    "response": f"That's great you're doing your due diligence. Many of our customers evaluated {competitor_name} and chose us because of our faster implementation time and lower total cost of ownership. Would you like to see a side-by-side comparison?"
                },
                {
                    "objection": f"{competitor_name} seems to have more features",
                    "response": "Feature count isn't everything - what matters is having the right features for your use case. Let me understand your key requirements and show you how we address each one specifically."
                },
                {
                    "objection": f"{competitor_name} has better enterprise credentials",
                    "response": "We actually serve 30% of the Fortune 500, including [reference customers]. Our enterprise security, compliance, and scalability are on par or better. Happy to share specific case studies."
                }
            ],
            "win_themes": [
                "Faster implementation (weeks vs months)",
                "Better ROI with transparent pricing",
                "Superior user experience and adoption",
                "More responsive product roadmap"
            ],
            "loss_themes": [
                "Perceived brand recognition gap",
                "Missing specific niche feature",
                "Existing vendor relationship"
            ],
            "key_differentiators": [
                {"area": "Implementation", "us": "Self-serve in days", "them": "6-12 weeks with PS"},
                {"area": "Pricing", "us": "Flat rate, predictable", "them": "Per-seat, grows fast"},
                {"area": "Support", "us": "24/7 included", "them": "Premium tier only"},
                {"area": "Integrations", "us": "200+ native", "them": "100+ with marketplace"}
            ],
            "recent_intel": [
                {"date": "2024-01-15", "type": "Pricing", "detail": "Increased enterprise pricing by 15%"},
                {"date": "2024-01-10", "type": "Product", "detail": "Launched AI assistant feature"},
                {"date": "2024-01-05", "type": "Hiring", "detail": "Expanding sales team in EMEA"}
            ]
        }


# Convenience functions
def get_sample_generator() -> SampleDataGenerator:
    return SampleDataGenerator()


def get_battlecard_sample_generator() -> BattlecardSampleGenerator:
    return BattlecardSampleGenerator()


def generate_test_dataset(num_competitors: int = 5) -> List[Dict]:
    """Generate a test dataset of sample competitors."""
    generator = SampleDataGenerator()
    return [generator.generate_competitor(i) for i in range(num_competitors)]
