"""
Email notification service for competitive intelligence alerts
Supports weekly digests, alerts, and custom notifications
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional, Dict, Any
from io import BytesIO
from datetime import datetime
from loguru import logger
from src.core.config import settings


class EmailService:
    """Email notification service using SMTP"""
    
    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        from_email: str = None
    ):
        self.smtp_host = smtp_host or getattr(settings, 'SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or getattr(settings, 'SMTP_PORT', 587)
        self.smtp_user = smtp_user or getattr(settings, 'SMTP_USER', '')
        self.smtp_password = smtp_password or getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = from_email or getattr(settings, 'EMAIL_FROM', 'vigilai@example.com')
        self.enabled = bool(self.smtp_user and self.smtp_password)
    
    def _create_connection(self) -> smtplib.SMTP:
        """Create SMTP connection"""
        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        server.starttls()
        server.login(self.smtp_user, self.smtp_password)
        return server
    
    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send email with optional attachments
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML body content
            text_content: Plain text fallback (optional)
            attachments: List of dicts with 'filename' and 'content' (BytesIO)
        """
        if not self.enabled:
            logger.warning("Email service not configured. Skipping email send.")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # Add text content
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            
            # Add HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEApplication(
                        attachment['content'].read(),
                        Name=attachment['filename']
                    )
                    part['Content-Disposition'] = f'attachment; filename="{attachment["filename"]}"'
                    msg.attach(part)
            
            # Send email
            with self._create_connection() as server:
                server.sendmail(self.from_email, to_emails, msg.as_string())
            
            logger.info(f"Email sent to {len(to_emails)} recipients: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    async def send_competitor_alert(
        self,
        to_emails: List[str],
        competitor_name: str,
        update: Dict[str, Any]
    ) -> bool:
        """Send competitor update alert email"""
        
        severity_colors = {
            'critical': '#dc2626',
            'high': '#ea580c',
            'medium': '#ca8a04',
            'low': '#16a34a'
        }
        
        color = severity_colors.get(update.get('severity', 'low'), '#16a34a')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1a365d, #2b6cb0); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; }}
                .severity {{ display: inline-block; padding: 4px 12px; border-radius: 20px; color: white; background: {color}; font-size: 12px; }}
                .metric {{ background: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #2b6cb0; }}
                .footer {{ padding: 15px; text-align: center; color: #64748b; font-size: 12px; }}
                .btn {{ display: inline-block; padding: 10px 20px; background: #2b6cb0; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0;">🔔 Competitor Update Alert</h1>
                    <p style="margin:5px 0 0 0;">{competitor_name}</p>
                </div>
                <div class="content">
                    <p><span class="severity">{update.get('severity', 'low').upper()}</span></p>
                    <h2>{update.get('title', 'Update Detected')}</h2>
                    
                    <div class="metric">
                        <strong>Update Type:</strong> {update.get('update_type', 'Unknown')}<br>
                        <strong>Impact Score:</strong> {update.get('impact_score', 'N/A')}/10
                    </div>
                    
                    <h3>Summary</h3>
                    <p>{update.get('summary', 'No summary available.')}</p>
                    
                    <h3>Recommended Action</h3>
                    <p>{update.get('recommended_action', 'Review the update and assess impact.')}</p>
                    
                    <p style="text-align: center; margin-top: 20px;">
                        <a href="{update.get('source_url', '#')}" class="btn">View Details →</a>
                    </p>
                </div>
                <div class="footer">
                    <p>Sent by VigilAI Competitive Intelligence Platform</p>
                    <p>Detected at {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        subject = f"[VigilAI] {update.get('severity', 'low').upper()}: {competitor_name} - {update.get('title', 'Update')}"
        
        return await self.send_email(to_emails, subject, html_content)
    
    async def send_weekly_digest(
        self,
        to_emails: List[str],
        digest: Dict[str, Any]
    ) -> bool:
        """Send weekly competitive intelligence digest"""
        
        updates_html = ""
        for update in digest.get('top_updates', [])[:10]:
            updates_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{update.get('title', 'N/A')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: center;">{update.get('impact_score', 'N/A')}/10</td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 650px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1a365d, #2b6cb0); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }}
                .content {{ background: #f8fafc; padding: 25px; border: 1px solid #e2e8f0; }}
                .stat-grid {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat {{ text-align: center; padding: 15px; background: white; border-radius: 8px; min-width: 120px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                .stat-value {{ font-size: 32px; font-weight: bold; color: #2b6cb0; }}
                .stat-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #2b6cb0; color: white; padding: 12px; text-align: left; }}
                .footer {{ padding: 20px; text-align: center; color: #64748b; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0;">📊 Weekly Intelligence Digest</h1>
                    <p style="margin:10px 0 0 0;">Week of {datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                <div class="content">
                    <div style="display: flex; justify-content: space-around; margin: 20px 0;">
                        <div class="stat">
                            <div class="stat-value">{digest.get('total_updates', 0)}</div>
                            <div class="stat-label">Total Updates</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" style="color: #dc2626;">{digest.get('high_priority_count', 0)}</div>
                            <div class="stat-label">High Priority</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" style="color: #16a34a;">{digest.get('competitors_tracked', 0)}</div>
                            <div class="stat-label">Competitors</div>
                        </div>
                    </div>
                    
                    <h3>Key Highlights</h3>
                    <p>{digest.get('summary', 'No significant updates this week.')}</p>
                    
                    <h3>Top Updates This Week</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Update</th>
                                <th style="width: 100px; text-align: center;">Impact</th>
                            </tr>
                        </thead>
                        <tbody>
                            {updates_html if updates_html else '<tr><td colspan="2" style="padding: 20px; text-align: center;">No updates this week</td></tr>'}
                        </tbody>
                    </table>
                </div>
                <div class="footer">
                    <p>VigilAI - Competitive Intelligence Platform</p>
                    <p>This is an automated weekly digest. <a href="#">Manage preferences</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        subject = f"[VigilAI] Weekly Competitive Intelligence Digest - {datetime.now().strftime('%B %d, %Y')}"
        
        return await self.send_email(to_emails, subject, html_content)
    
    async def send_incident_alert(
        self,
        to_emails: List[str],
        incident: Dict[str, Any]
    ) -> bool:
        """Send system incident alert email"""
        
        severity_colors = {
            'critical': '#dc2626',
            'high': '#ea580c',
            'medium': '#ca8a04',
            'low': '#16a34a'
        }
        
        color = severity_colors.get(incident.get('severity', 'medium'), '#ca8a04')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; }}
                .section {{ background: white; padding: 15px; border-radius: 8px; margin: 10px 0; }}
                .footer {{ padding: 15px; text-align: center; color: #64748b; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0;">🚨 System Incident Alert</h1>
                    <p style="margin:5px 0 0 0;">Severity: {incident.get('severity', 'medium').upper()}</p>
                </div>
                <div class="content">
                    <h2>{incident.get('title', 'Incident Detected')}</h2>
                    
                    <div class="section">
                        <strong>Status:</strong> {incident.get('status', 'Investigating')}<br>
                        <strong>Detected:</strong> {incident.get('detected_at', datetime.now().strftime('%Y-%m-%d %H:%M'))}
                    </div>
                    
                    <div class="section">
                        <h3 style="margin-top:0;">Root Cause Analysis</h3>
                        <p>{incident.get('root_cause', 'Analysis in progress...')}</p>
                    </div>
                    
                    <div class="section">
                        <h3 style="margin-top:0;">Recommended Actions</h3>
                        <p>{incident.get('recommendations', 'Monitoring the situation.')}</p>
                    </div>
                </div>
                <div class="footer">
                    <p>VigilAI AIOps Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        subject = f"🚨 [VigilAI] {incident.get('severity', 'MEDIUM').upper()} Incident: {incident.get('title', 'System Alert')}"
        
        return await self.send_email(to_emails, subject, html_content)


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
