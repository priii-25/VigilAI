"""
Salesforce CRM integration service
Push battlecard kill points and competitor intel to Salesforce opportunities
Production-ready with OAuth2 authentication and circuit breaker protection
"""
from typing import Dict, List, Optional
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed
from loguru import logger
from src.core.config import settings
from src.core.circuit_breaker import with_circuit_breaker, CIRCUIT_BREAKERS
from datetime import datetime
import json
import requests


class SalesforceService:
    """
    Salesforce CRM integration for competitive intelligence.
    
    Uses OAuth2 authentication (not SOAP) for compatibility with
    newer Salesforce orgs that have SOAP API disabled.
    """
    
    def __init__(self):
        self.client_id = settings.SALESFORCE_CLIENT_ID
        self.client_secret = settings.SALESFORCE_CLIENT_SECRET
        self.username = settings.SALESFORCE_USERNAME
        self.password = settings.SALESFORCE_PASSWORD
        self.security_token = settings.SALESFORCE_SECURITY_TOKEN
        self.sf = None
        self._enabled = False
        
        if self._is_configured():
            self._connect()
    
    def _is_configured(self) -> bool:
        """Check if Salesforce credentials are configured"""
        # OAuth2 flow requires client_id and client_secret
        return bool(
            self.client_id and
            self.client_secret and
            self.username and
            self.password
        )
    
    def is_enabled(self) -> bool:
        """Check if Salesforce is connected"""
        return self._enabled and self.sf is not None
    
    def is_healthy(self) -> bool:
        """Check circuit breaker health"""
        breaker = CIRCUIT_BREAKERS.get("salesforce_api")
        if breaker:
            return breaker.state.value == "closed"
        return True
    
    def _connect(self):
        """Establish connection to Salesforce using OAuth2"""
        try:
            logger.info("Connecting to Salesforce via OAuth2...")
            
            # OAuth2 Password Grant flow
            token_url = "https://login.salesforce.com/services/oauth2/token"
            
            # Combine password with security token
            password_with_token = f"{self.password}{self.security_token}" if self.security_token else self.password
            
            payload = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": password_with_token
            }
            
            response = requests.post(token_url, data=payload, timeout=30)
            
            if response.status_code == 200:
                auth_data = response.json()
                access_token = auth_data["access_token"]
                instance_url = auth_data["instance_url"]
                
                # Connect using the access token
                self.sf = Salesforce(
                    instance_url=instance_url,
                    session_id=access_token
                )
                
                self._enabled = True
                logger.info(f"Successfully connected to Salesforce: {instance_url}")
            else:
                error = response.json().get("error_description", response.text)
                logger.error(f"Salesforce OAuth2 failed: {error}")
                self.sf = None
                self._enabled = False
            
        except SalesforceAuthenticationFailed as e:
            logger.error(f"Salesforce authentication failed: {str(e)}")
            self.sf = None
            self._enabled = False
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error connecting to Salesforce: {str(e)}")
            self.sf = None
            self._enabled = False
        except Exception as e:
            logger.error(f"Error connecting to Salesforce: {str(e)}")
            self.sf = None
            self._enabled = False
    
    @with_circuit_breaker("salesforce_api")
    def push_kill_points_to_opportunity(
        self,
        opportunity_id: str,
        competitor_name: str,
        kill_points: List[str]
    ) -> bool:
        """
        Push battlecard kill points to a Salesforce opportunity
        
        Args:
            opportunity_id: Salesforce opportunity ID
            competitor_name: Name of competitor
            kill_points: List of kill points/talking points
            
        Returns:
            Boolean indicating success
        """
        if not self.sf:
            logger.warning("Salesforce not connected")
            return False
        
        try:
            # Format kill points
            kill_points_text = f"Competitive Intelligence for {competitor_name}:\n\n"
            for i, point in enumerate(kill_points, 1):
                kill_points_text += f"{i}. {point}\n"
            
            kill_points_text += f"\n\nGenerated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
            
            # Update opportunity description or custom field
            # Assuming custom field: Competitive_Intelligence__c
            update_data = {
                'Competitive_Intelligence__c': kill_points_text
            }
            
            # Alternative: Add as a note/comment
            # self._add_opportunity_note(opportunity_id, kill_points_text)
            
            self.sf.Opportunity.update(opportunity_id, update_data)
            
            logger.info(f"Updated opportunity {opportunity_id} with kill points for {competitor_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating Salesforce opportunity: {str(e)}")
            return False
    
    def find_opportunities_by_competitor(
        self,
        competitor_name: str
    ) -> List[Dict]:
        """
        Find opportunities mentioning a specific competitor
        
        Args:
            competitor_name: Name of competitor to search for
            
        Returns:
            List of opportunity records
        """
        if not self.sf:
            return []
        
        try:
            # Query opportunities
            # This assumes competitor info is in Description or custom field
            query = f"""
                SELECT Id, Name, StageName, Amount, CloseDate, AccountId, Account.Name
                FROM Opportunity
                WHERE Description LIKE '%{competitor_name}%'
                OR Competitor__c = '{competitor_name}'
                AND IsClosed = false
                ORDER BY CloseDate ASC
                LIMIT 50
            """
            
            result = self.sf.query(query)
            opportunities = result.get('records', [])
            
            logger.info(f"Found {len(opportunities)} opportunities for {competitor_name}")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error querying Salesforce opportunities: {str(e)}")
            return []
    
    def create_competitor_contact(
        self,
        account_id: str,
        competitor_name: str,
        intel_summary: str
    ) -> Optional[str]:
        """
        Create a competitor intelligence record in Salesforce
        
        Args:
            account_id: Salesforce account ID
            competitor_name: Name of competitor
            intel_summary: Summary of intelligence
            
        Returns:
            Created record ID or None
        """
        if not self.sf:
            return None
        
        try:
            # Create custom object record (assuming Competitor_Intel__c exists)
            data = {
                'Name': f"Intel: {competitor_name}",
                'Account__c': account_id,
                'Competitor_Name__c': competitor_name,
                'Intelligence_Summary__c': intel_summary,
                'Date__c': datetime.utcnow().strftime('%Y-%m-%d')
            }
            
            result = self.sf.Competitor_Intel__c.create(data)
            record_id = result.get('id')
            
            logger.info(f"Created competitor intel record: {record_id}")
            return record_id
            
        except Exception as e:
            logger.error(f"Error creating competitor intel record: {str(e)}")
            return None
    
    def update_account_competitor_field(
        self,
        account_id: str,
        competitor_names: List[str]
    ) -> bool:
        """
        Update account with list of competitors
        
        Args:
            account_id: Salesforce account ID
            competitor_names: List of competitor names
            
        Returns:
            Boolean indicating success
        """
        if not self.sf:
            return False
        
        try:
            competitors_text = '; '.join(competitor_names)
            
            update_data = {
                'Competitors__c': competitors_text
            }
            
            self.sf.Account.update(account_id, update_data)
            
            logger.info(f"Updated account {account_id} with competitors")
            return True
            
        except Exception as e:
            logger.error(f"Error updating Salesforce account: {str(e)}")
            return False
    
    def _add_opportunity_note(
        self,
        opportunity_id: str,
        note_text: str
    ) -> bool:
        """Add a note to an opportunity"""
        try:
            note_data = {
                'ParentId': opportunity_id,
                'Title': 'Competitive Intelligence',
                'Body': note_text
            }
            
            self.sf.Note.create(note_data)
            return True
            
        except Exception as e:
            logger.error(f"Error adding note to opportunity: {str(e)}")
            return False
    
    def get_competitor_mentions_count(
        self,
        competitor_name: str
    ) -> Dict:
        """
        Get count of competitor mentions across Salesforce
        
        Args:
            competitor_name: Name of competitor
            
        Returns:
            Dict with counts by object type
        """
        if not self.sf:
            return {}
        
        counts = {
            'opportunities': 0,
            'accounts': 0,
            'cases': 0
        }
        
        try:
            # Count in opportunities
            opp_query = f"""
                SELECT COUNT() 
                FROM Opportunity 
                WHERE Description LIKE '%{competitor_name}%'
                OR Competitor__c = '{competitor_name}'
            """
            counts['opportunities'] = self.sf.query(opp_query).get('totalSize', 0)
            
            # Count in accounts
            acc_query = f"""
                SELECT COUNT()
                FROM Account
                WHERE Description LIKE '%{competitor_name}%'
                OR Competitors__c LIKE '%{competitor_name}%'
            """
            counts['accounts'] = self.sf.query(acc_query).get('totalSize', 0)
            
            logger.info(f"Competitor mention counts: {counts}")
            
        except Exception as e:
            logger.error(f"Error counting competitor mentions: {str(e)}")
        
        return counts
    
    def batch_update_opportunities(
        self,
        updates: List[Dict]
    ) -> Dict:
        """
        Batch update multiple opportunities
        
        Args:
            updates: List of dicts with 'id' and update fields
            
        Returns:
            Dict with success/failure counts
        """
        if not self.sf:
            return {'success': 0, 'failed': 0}
        
        results = {'success': 0, 'failed': 0, 'errors': []}
        
        try:
            # Salesforce bulk API
            for update in updates:
                try:
                    opp_id = update.pop('id')
                    self.sf.Opportunity.update(opp_id, update)
                    results['success'] += 1
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(str(e))
            
            logger.info(f"Batch update results: {results['success']} success, {results['failed']} failed")
            
        except Exception as e:
            logger.error(f"Error in batch update: {str(e)}")
        
        return results
    
    def test_connection(self) -> bool:
        """Test Salesforce connection"""
        if not self.sf:
            return False
        
        try:
            # Simple query to test connection
            self.sf.query("SELECT Id FROM User LIMIT 1")
            logger.info("Salesforce connection test successful")
            return True
        except Exception as e:
            logger.error(f"Salesforce connection test failed: {str(e)}")
            return False


class CRMEnrichmentService:
    """Service to enrich CRM with competitive intelligence"""
    
    def __init__(self):
        self.sf_service = SalesforceService()
    
    def enrich_opportunity_with_battlecard(
        self,
        opportunity_id: str,
        battlecard: Dict
    ) -> bool:
        """
        Enrich Salesforce opportunity with battlecard data
        
        Args:
            opportunity_id: Salesforce opportunity ID
            battlecard: Battlecard dict with kill points, weaknesses, etc.
            
        Returns:
            Boolean indicating success
        """
        competitor_name = battlecard.get('competitor_name', 'Unknown')
        kill_points = battlecard.get('kill_points', [])
        weaknesses = battlecard.get('weaknesses', [])
        
        # Combine kill points and weaknesses
        combined_intel = kill_points + [f"Weakness: {w}" for w in weaknesses]
        
        return self.sf_service.push_kill_points_to_opportunity(
            opportunity_id,
            competitor_name,
            combined_intel[:10]  # Top 10 points
        )
    
    def auto_enrich_relevant_opportunities(
        self,
        competitor_name: str,
        battlecard: Dict
    ) -> int:
        """
        Automatically enrich all relevant opportunities with updated battlecard
        
        Args:
            competitor_name: Name of competitor
            battlecard: Updated battlecard data
            
        Returns:
            Number of opportunities enriched
        """
        # Find relevant opportunities
        opportunities = self.sf_service.find_opportunities_by_competitor(competitor_name)
        
        enriched_count = 0
        
        for opp in opportunities:
            opp_id = opp.get('Id')
            if opp_id:
                success = self.enrich_opportunity_with_battlecard(opp_id, battlecard)
                if success:
                    enriched_count += 1
        
        logger.info(f"Auto-enriched {enriched_count} opportunities for {competitor_name}")
        return enriched_count
