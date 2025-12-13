"""
Change Detection Service
Tracks and compares competitor data changes over time.
Implements diff analysis for pricing, features, and content.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib
import difflib
import json
import re

logger = logging.getLogger(__name__)


@dataclass
class ChangeRecord:
    """Represents a detected change."""
    change_id: str
    competitor_id: str
    change_type: str  # pricing, features, content, careers, messaging
    category: str  # addition, removal, modification
    previous_value: Any
    current_value: Any
    diff_summary: str
    impact_score: float
    detected_at: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['detected_at'] = self.detected_at.isoformat()
        return data


class ChangeDetectionService:
    """
    Service for detecting and tracking changes in competitor data.
    Compares current vs previous data snapshots to identify changes.
    """
    
    def __init__(self):
        # In-memory cache of previous states (use Redis in production)
        self._previous_states: Dict[str, Dict] = {}
    
    def generate_content_hash(self, content: Any) -> str:
        """Generate hash for content comparison."""
        if isinstance(content, dict):
            content_str = json.dumps(content, sort_keys=True)
        elif isinstance(content, list):
            content_str = json.dumps(sorted([str(x) for x in content]))
        else:
            content_str = str(content)
        
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def detect_pricing_changes(
        self,
        competitor_id: str,
        current_pricing: Dict[str, Any],
        previous_pricing: Optional[Dict[str, Any]] = None
    ) -> List[ChangeRecord]:
        """
        Detect changes in pricing data.
        
        Args:
            competitor_id: Competitor identifier
            current_pricing: Current pricing structure
            previous_pricing: Previous pricing (or None to use cached)
            
        Returns:
            List of detected changes
        """
        cache_key = f"pricing:{competitor_id}"
        
        if previous_pricing is None:
            previous_pricing = self._previous_states.get(cache_key, {})
        
        changes = []
        
        current_plans = current_pricing.get('plans', [])
        previous_plans = previous_pricing.get('plans', [])
        
        # Build plan maps by name
        current_map = {p.get('name', 'Unknown'): p for p in current_plans}
        previous_map = {p.get('name', 'Unknown'): p for p in previous_plans}
        
        # Detect new plans
        for name, plan in current_map.items():
            if name not in previous_map:
                changes.append(ChangeRecord(
                    change_id=self._generate_change_id(),
                    competitor_id=competitor_id,
                    change_type='pricing',
                    category='addition',
                    previous_value=None,
                    current_value=plan,
                    diff_summary=f"New pricing plan added: {name} - {plan.get('price', 'N/A')}",
                    impact_score=7.0,  # New plans are significant
                    detected_at=datetime.utcnow()
                ))
        
        # Detect removed plans
        for name, plan in previous_map.items():
            if name not in current_map:
                changes.append(ChangeRecord(
                    change_id=self._generate_change_id(),
                    competitor_id=competitor_id,
                    change_type='pricing',
                    category='removal',
                    previous_value=plan,
                    current_value=None,
                    diff_summary=f"Pricing plan removed: {name}",
                    impact_score=8.0,  # Removal is more significant
                    detected_at=datetime.utcnow()
                ))
        
        # Detect price changes
        for name in set(current_map.keys()) & set(previous_map.keys()):
            old_price = str(previous_map[name].get('price', '')).lower()
            new_price = str(current_map[name].get('price', '')).lower()
            
            if old_price != new_price:
                # Calculate impact based on price direction
                impact = self._calculate_price_change_impact(old_price, new_price)
                changes.append(ChangeRecord(
                    change_id=self._generate_change_id(),
                    competitor_id=competitor_id,
                    change_type='pricing',
                    category='modification',
                    previous_value={'name': name, 'price': old_price},
                    current_value={'name': name, 'price': new_price},
                    diff_summary=f"Price change for {name}: {old_price} → {new_price}",
                    impact_score=impact,
                    detected_at=datetime.utcnow()
                ))
            
            # Detect feature changes within plan
            old_features = set(previous_map[name].get('features', []))
            new_features = set(current_map[name].get('features', []))
            
            added_features = new_features - old_features
            removed_features = old_features - new_features
            
            if added_features:
                changes.append(ChangeRecord(
                    change_id=self._generate_change_id(),
                    competitor_id=competitor_id,
                    change_type='features',
                    category='addition',
                    previous_value=None,
                    current_value=list(added_features),
                    diff_summary=f"New features in {name}: {', '.join(added_features)}",
                    impact_score=6.0,
                    detected_at=datetime.utcnow()
                ))
            
            if removed_features:
                changes.append(ChangeRecord(
                    change_id=self._generate_change_id(),
                    competitor_id=competitor_id,
                    change_type='features',
                    category='removal',
                    previous_value=list(removed_features),
                    current_value=None,
                    diff_summary=f"Removed features from {name}: {', '.join(removed_features)}",
                    impact_score=5.0,
                    detected_at=datetime.utcnow()
                ))
        
        # Update cache
        self._previous_states[cache_key] = current_pricing
        
        return changes
    
    def detect_content_changes(
        self,
        competitor_id: str,
        current_content: str,
        previous_content: Optional[str] = None,
        content_type: str = "content"
    ) -> Optional[ChangeRecord]:
        """
        Detect changes in text content (e.g., blog posts, messaging).
        
        Args:
            competitor_id: Competitor identifier
            current_content: Current content text
            previous_content: Previous content (or None to use cached)
            content_type: Type of content being compared
            
        Returns:
            ChangeRecord if changes detected, None otherwise
        """
        cache_key = f"{content_type}:{competitor_id}"
        
        if previous_content is None:
            previous_content = self._previous_states.get(cache_key, "")
        
        if not previous_content:
            self._previous_states[cache_key] = current_content
            return None
        
        # Check if content changed
        if self.generate_content_hash(current_content) == self.generate_content_hash(previous_content):
            return None
        
        # Generate diff
        diff = self._generate_text_diff(previous_content, current_content)
        
        # Calculate impact based on change size
        change_ratio = abs(len(current_content) - len(previous_content)) / max(len(previous_content), 1)
        impact = min(3.0 + change_ratio * 5, 8.0)
        
        change = ChangeRecord(
            change_id=self._generate_change_id(),
            competitor_id=competitor_id,
            change_type=content_type,
            category='modification',
            previous_value=previous_content[:500] + "..." if len(previous_content) > 500 else previous_content,
            current_value=current_content[:500] + "..." if len(current_content) > 500 else current_content,
            diff_summary=diff,
            impact_score=impact,
            detected_at=datetime.utcnow()
        )
        
        # Update cache
        self._previous_states[cache_key] = current_content
        
        return change
    
    def detect_job_posting_changes(
        self,
        competitor_id: str,
        current_jobs: List[Dict],
        previous_jobs: Optional[List[Dict]] = None
    ) -> List[ChangeRecord]:
        """
        Detect changes in job postings.
        
        Args:
            competitor_id: Competitor identifier
            current_jobs: Current job postings
            previous_jobs: Previous job postings
            
        Returns:
            List of detected changes
        """
        cache_key = f"jobs:{competitor_id}"
        
        if previous_jobs is None:
            previous_jobs = self._previous_states.get(cache_key, [])
        
        changes = []
        
        # Build job maps by title (simplified)
        current_titles = set(j.get('title', '') for j in current_jobs)
        previous_titles = set(j.get('title', '') for j in previous_jobs)
        
        # New positions
        new_positions = current_titles - previous_titles
        if new_positions:
            changes.append(ChangeRecord(
                change_id=self._generate_change_id(),
                competitor_id=competitor_id,
                change_type='careers',
                category='addition',
                previous_value=None,
                current_value=list(new_positions),
                diff_summary=f"New job postings: {', '.join(list(new_positions)[:5])}{'...' if len(new_positions) > 5 else ''}",
                impact_score=4.0 + min(len(new_positions) * 0.5, 4.0),
                detected_at=datetime.utcnow()
            ))
        
        # Closed positions
        closed_positions = previous_titles - current_titles
        if closed_positions:
            changes.append(ChangeRecord(
                change_id=self._generate_change_id(),
                competitor_id=competitor_id,
                change_type='careers',
                category='removal',
                previous_value=list(closed_positions),
                current_value=None,
                diff_summary=f"Positions closed/filled: {', '.join(list(closed_positions)[:5])}",
                impact_score=3.0,
                detected_at=datetime.utcnow()
            ))
        
        # Detect hiring trend changes
        prev_count = len(previous_jobs)
        curr_count = len(current_jobs)
        if prev_count > 0:
            growth_rate = (curr_count - prev_count) / prev_count
            if abs(growth_rate) > 0.2:  # >20% change
                changes.append(ChangeRecord(
                    change_id=self._generate_change_id(),
                    competitor_id=competitor_id,
                    change_type='careers',
                    category='modification',
                    previous_value={'total_positions': prev_count},
                    current_value={'total_positions': curr_count},
                    diff_summary=f"Hiring {'increased' if growth_rate > 0 else 'decreased'} by {abs(growth_rate)*100:.0f}%",
                    impact_score=6.0 if abs(growth_rate) > 0.5 else 4.0,
                    detected_at=datetime.utcnow()
                ))
        
        # Update cache
        self._previous_states[cache_key] = current_jobs
        
        return changes
    
    def _calculate_price_change_impact(self, old_price: str, new_price: str) -> float:
        """Calculate impact score for price change."""
        # Try to extract numeric values
        old_num = self._extract_price_number(old_price)
        new_num = self._extract_price_number(new_price)
        
        if old_num and new_num:
            change_pct = abs(new_num - old_num) / old_num
            if change_pct > 0.2:  # >20% change
                return 9.0
            elif change_pct > 0.1:  # >10% change
                return 7.0
            else:
                return 5.0
        
        return 6.0  # Default for non-numeric changes
    
    def _extract_price_number(self, price_str: str) -> Optional[float]:
        """Extract numeric value from price string."""
        numbers = re.findall(r'[\d,]+\.?\d*', price_str.replace(',', ''))
        if numbers:
            try:
                return float(numbers[0])
            except:
                pass
        return None
    
    def _generate_text_diff(self, old_text: str, new_text: str) -> str:
        """Generate human-readable diff summary."""
        old_lines = old_text.split('\n')
        new_lines = new_text.split('\n')
        
        differ = difflib.unified_diff(old_lines, new_lines, lineterm='')
        diff_lines = list(differ)
        
        added = sum(1 for l in diff_lines if l.startswith('+') and not l.startswith('+++'))
        removed = sum(1 for l in diff_lines if l.startswith('-') and not l.startswith('---'))
        
        return f"Content changed: {added} lines added, {removed} lines removed"
    
    def _generate_change_id(self) -> str:
        """Generate unique change ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def get_all_changes(
        self,
        competitor_id: str,
        current_data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect all changes for a competitor across all data types.
        
        Args:
            competitor_id: Competitor identifier
            current_data: Current competitor data snapshot
            previous_data: Previous snapshot (optional)
            
        Returns:
            Comprehensive change analysis
        """
        all_changes = []
        
        # Pricing changes
        if 'pricing' in current_data:
            prev_pricing = previous_data.get('pricing') if previous_data else None
            pricing_changes = self.detect_pricing_changes(
                competitor_id,
                current_data['pricing'],
                prev_pricing
            )
            all_changes.extend(pricing_changes)
        
        # Job posting changes
        if 'jobs' in current_data:
            prev_jobs = previous_data.get('jobs') if previous_data else None
            job_changes = self.detect_job_posting_changes(
                competitor_id,
                current_data['jobs'],
                prev_jobs
            )
            all_changes.extend(job_changes)
        
        # Content changes
        if 'content' in current_data:
            prev_content = previous_data.get('content') if previous_data else None
            content_change = self.detect_content_changes(
                competitor_id,
                current_data['content'],
                prev_content
            )
            if content_change:
                all_changes.append(content_change)
        
        # Calculate overall impact
        max_impact = max([c.impact_score for c in all_changes], default=0)
        avg_impact = sum(c.impact_score for c in all_changes) / len(all_changes) if all_changes else 0
        
        return {
            'competitor_id': competitor_id,
            'total_changes': len(all_changes),
            'changes': [c.to_dict() for c in all_changes],
            'max_impact': max_impact,
            'avg_impact': round(avg_impact, 2),
            'by_type': self._group_by_type(all_changes),
            'analyzed_at': datetime.utcnow().isoformat()
        }
    
    def _group_by_type(self, changes: List[ChangeRecord]) -> Dict[str, int]:
        """Group changes by type."""
        groups = {}
        for change in changes:
            groups[change.change_type] = groups.get(change.change_type, 0) + 1
        return groups


# Singleton instance
_change_detection_service = None


def get_change_detection_service() -> ChangeDetectionService:
    """Get or create change detection service instance."""
    global _change_detection_service
    if _change_detection_service is None:
        _change_detection_service = ChangeDetectionService()
    return _change_detection_service
