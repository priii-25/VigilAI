"""
Human-in-Loop Approval Workflow
Slack integration for approving high-impact alerts before distribution.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import json
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Alert approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Alert:
    """Represents a competitive intelligence alert."""
    alert_id: str
    title: str
    description: str
    impact_score: float  # 0-10
    category: str  # pricing, feature, hiring, partnership, etc.
    competitor_name: str
    source_url: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['approved_at'] = self.approved_at.isoformat() if self.approved_at else None
        data['status'] = self.status.value
        return data


class ApprovalWorkflow:
    """
    Manages approval workflow for high-impact alerts.
    Routes alerts to appropriate approvers based on impact score and category.
    """
    
    def __init__(self, slack_service, high_impact_threshold: float = 7.0):
        """
        Initialize approval workflow.
        
        Args:
            slack_service: SlackService instance for notifications
            high_impact_threshold: Impact score above which approval is required
        """
        self.slack_service = slack_service
        self.high_impact_threshold = high_impact_threshold
        self.pending_approvals = {}
        self.approval_timeout = timedelta(hours=4)
        
        # Define approvers by category
        self.approvers = {
            'pricing': ['product_marketing_manager', 'sales_director'],
            'feature': ['product_manager', 'product_marketing_manager'],
            'hiring': ['recruiting_lead', 'product_marketing_manager'],
            'partnership': ['business_development', 'product_marketing_manager'],
            'funding': ['executives', 'product_marketing_manager'],
            'acquisition': ['executives', 'product_marketing_manager'],
            'default': ['product_marketing_manager']
        }
    
    def requires_approval(self, impact_score: float) -> bool:
        """Check if an alert requires human approval."""
        return impact_score >= self.high_impact_threshold
    
    def create_alert(
        self,
        title: str,
        description: str,
        impact_score: float,
        category: str,
        competitor_name: str,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """
        Create a new alert for approval.
        
        Args:
            title: Alert title
            description: Detailed description
            impact_score: Impact score (0-10)
            category: Alert category
            competitor_name: Competitor name
            source_url: Source URL if available
            metadata: Additional metadata
            
        Returns:
            Alert object
        """
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            title=title,
            description=description,
            impact_score=impact_score,
            category=category,
            competitor_name=competitor_name,
            source_url=source_url,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        
        if self.requires_approval(impact_score):
            self.pending_approvals[alert.alert_id] = alert
            logger.info(f"Alert {alert.alert_id} requires approval (impact: {impact_score})")
        else:
            # Auto-approve low-impact alerts
            alert.status = ApprovalStatus.APPROVED
            alert.approved_by = 'system'
            alert.approved_at = datetime.utcnow()
            logger.info(f"Alert {alert.alert_id} auto-approved (impact: {impact_score})")
        
        return alert
    
    async def request_approval(self, alert: Alert, channel: str = None) -> Dict[str, Any]:
        """
        Send alert to Slack for approval.
        
        Args:
            alert: Alert to approve
            channel: Slack channel to post to (defaults to #approvals)
            
        Returns:
            Dictionary with request results
        """
        if not self.requires_approval(alert.impact_score):
            return {
                'alert_id': alert.alert_id,
                'requires_approval': False,
                'status': 'auto_approved'
            }
        
        # Get appropriate approvers for this category
        approvers = self.approvers.get(alert.category, self.approvers['default'])
        
        # Build Slack message with interactive buttons
        message_blocks = self._build_approval_message(alert, approvers)
        
        try:
            # Send to Slack
            channel = channel or '#competitive-intel-approvals'
            response = await self.slack_service.send_interactive_message(
                channel=channel,
                blocks=message_blocks,
                text=f"🚨 High Impact Alert: {alert.title}"
            )
            
            logger.info(f"Approval request sent for alert {alert.alert_id}")
            
            return {
                'alert_id': alert.alert_id,
                'requires_approval': True,
                'status': 'pending',
                'slack_ts': response.get('ts'),
                'channel': channel,
                'approvers': approvers
            }
            
        except Exception as e:
            logger.error(f"Error sending approval request: {e}")
            return {
                'alert_id': alert.alert_id,
                'requires_approval': True,
                'status': 'error',
                'error': str(e)
            }
    
    def _build_approval_message(self, alert: Alert, approvers: List[str]) -> List[Dict[str, Any]]:
        """Build Slack message blocks for approval request."""
        
        # Impact score color coding
        if alert.impact_score >= 9:
            impact_emoji = "🔴"
            impact_color = "danger"
        elif alert.impact_score >= 7:
            impact_emoji = "🟡"
            impact_color = "warning"
        else:
            impact_emoji = "🟢"
            impact_color = "good"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{impact_emoji} High Impact Alert Requires Approval"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Competitor:*\n{alert.competitor_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Category:*\n{alert.category.title()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Impact Score:*\n{impact_emoji} {alert.impact_score}/10"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Created:*\n{alert.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{alert.title}*\n\n{alert.description}"
                }
            }
        ]
        
        # Add source URL if available
        if alert.source_url:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Source:* <{alert.source_url}|View Original>"
                }
            })
        
        # Add metadata if present
        if alert.metadata:
            metadata_text = "\n".join([f"• *{k}:* {v}" for k, v in alert.metadata.items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Additional Details:*\n{metadata_text}"
                }
            })
        
        # Add divider
        blocks.append({"type": "divider"})
        
        # Add approval buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Approve & Distribute"
                    },
                    "style": "primary",
                    "value": alert.alert_id,
                    "action_id": f"approve_{alert.alert_id}"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ Reject"
                    },
                    "style": "danger",
                    "value": alert.alert_id,
                    "action_id": f"reject_{alert.alert_id}"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✏️ Edit & Approve"
                    },
                    "value": alert.alert_id,
                    "action_id": f"edit_{alert.alert_id}"
                }
            ]
        })
        
        # Add context
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Alert ID: `{alert.alert_id}` | Approvers: {', '.join(approvers)}"
                }
            ]
        })
        
        return blocks
    
    def approve_alert(
        self,
        alert_id: str,
        approved_by: str,
        modified_content: Optional[Dict[str, str]] = None
    ) -> Alert:
        """
        Approve an alert and optionally modify its content.
        
        Args:
            alert_id: Alert ID
            approved_by: User who approved
            modified_content: Optional modifications (title, description)
            
        Returns:
            Updated Alert object
        """
        alert = self.pending_approvals.get(alert_id)
        
        if not alert:
            raise ValueError(f"Alert {alert_id} not found in pending approvals")
        
        # Apply modifications if provided
        if modified_content:
            if 'title' in modified_content:
                alert.title = modified_content['title']
            if 'description' in modified_content:
                alert.description = modified_content['description']
        
        # Update status
        alert.status = ApprovalStatus.APPROVED
        alert.approved_by = approved_by
        alert.approved_at = datetime.utcnow()
        
        # Remove from pending
        del self.pending_approvals[alert_id]
        
        logger.info(f"Alert {alert_id} approved by {approved_by}")
        
        return alert
    
    def reject_alert(
        self,
        alert_id: str,
        rejected_by: str,
        reason: Optional[str] = None
    ) -> Alert:
        """
        Reject an alert.
        
        Args:
            alert_id: Alert ID
            rejected_by: User who rejected
            reason: Rejection reason
            
        Returns:
            Updated Alert object
        """
        alert = self.pending_approvals.get(alert_id)
        
        if not alert:
            raise ValueError(f"Alert {alert_id} not found in pending approvals")
        
        # Update status
        alert.status = ApprovalStatus.REJECTED
        alert.approved_by = rejected_by
        alert.approved_at = datetime.utcnow()
        alert.rejection_reason = reason
        
        # Remove from pending
        del self.pending_approvals[alert_id]
        
        logger.info(f"Alert {alert_id} rejected by {rejected_by}: {reason}")
        
        return alert
    
    def check_expired_approvals(self) -> List[Alert]:
        """
        Check for approval requests that have expired.
        
        Returns:
            List of expired alerts
        """
        expired = []
        now = datetime.utcnow()
        
        for alert_id, alert in list(self.pending_approvals.items()):
            if now - alert.created_at > self.approval_timeout:
                alert.status = ApprovalStatus.EXPIRED
                expired.append(alert)
                del self.pending_approvals[alert_id]
                logger.warning(f"Alert {alert_id} expired without approval")
        
        return expired
    
    def get_pending_approvals(self, category: Optional[str] = None) -> List[Alert]:
        """
        Get all pending approval requests.
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            List of pending alerts
        """
        alerts = list(self.pending_approvals.values())
        
        if category:
            alerts = [a for a in alerts if a.category == category]
        
        # Sort by impact score (highest first)
        alerts.sort(key=lambda a: a.impact_score, reverse=True)
        
        return alerts
    
    async def distribute_approved_alert(self, alert: Alert, channels: List[str]) -> Dict[str, Any]:
        """
        Distribute an approved alert to specified channels.
        
        Args:
            alert: Approved alert
            channels: List of Slack channels
            
        Returns:
            Distribution results
        """
        if alert.status != ApprovalStatus.APPROVED:
            raise ValueError(f"Alert {alert.alert_id} is not approved for distribution")
        
        distribution_results = []
        
        # Build distribution message
        message_blocks = self._build_distribution_message(alert)
        
        for channel in channels:
            try:
                response = await self.slack_service.send_message(
                    channel=channel,
                    blocks=message_blocks,
                    text=f"📢 {alert.title}"
                )
                
                distribution_results.append({
                    'channel': channel,
                    'success': True,
                    'message_ts': response.get('ts')
                })
                
            except Exception as e:
                logger.error(f"Error distributing alert to {channel}: {e}")
                distribution_results.append({
                    'channel': channel,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'alert_id': alert.alert_id,
            'distributed_at': datetime.utcnow().isoformat(),
            'channels': distribution_results
        }
    
    def _build_distribution_message(self, alert: Alert) -> List[Dict[str, Any]]:
        """Build Slack message blocks for alert distribution."""
        
        impact_emoji = "🔴" if alert.impact_score >= 9 else "🟡"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📢 Competitive Intelligence Update"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{alert.title}*\n\n{alert.description}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Competitor:*\n{alert.competitor_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Impact:*\n{impact_emoji} {alert.impact_score}/10"
                    }
                ]
            }
        ]
        
        if alert.source_url:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{alert.source_url}|View Source>"
                }
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Approved by {alert.approved_by} • {alert.category.title()}"
                }
            ]
        })
        
        return blocks
