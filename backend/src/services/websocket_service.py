"""
WebSocket Service for Real-time Updates
Push notifications for scraping completion and high-impact alerts.
"""
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of real-time notifications."""
    SCRAPE_STARTED = "scrape_started"
    SCRAPE_COMPLETED = "scrape_completed"
    SCRAPE_FAILED = "scrape_failed"
    HIGH_IMPACT_ALERT = "high_impact_alert"
    BATTLECARD_UPDATED = "battlecard_updated"
    ANOMALY_DETECTED = "anomaly_detected"
    COMPETITOR_ADDED = "competitor_added"
    APPROVAL_REQUIRED = "approval_required"


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts messages.
    Supports user-specific and broadcast notifications.
    """
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
            metadata: Optional connection metadata
        """
        await websocket.accept()
        
        # Add to user's connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            'user_id': user_id,
            'connected_at': datetime.utcnow(),
            'metadata': metadata or {}
        }
        
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {self.get_connection_count()}")
        
        # Send welcome message
        await self.send_personal_message(websocket, {
            'type': 'connection_established',
            'message': 'Connected to VigilAI real-time updates',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        metadata = self.connection_metadata.get(websocket)
        if metadata:
            user_id = metadata['user_id']
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            del self.connection_metadata[websocket]
            logger.info(f"WebSocket disconnected for user {user_id}. Total connections: {self.get_connection_count()}")
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Send a message to a specific connection.
        
        Args:
            websocket: Target WebSocket
            message: Message to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """
        Send a message to all connections of a specific user.
        
        Args:
            user_id: Target user ID
            message: Message to send
        """
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn)
    
    async def broadcast(self, message: Dict[str, Any], exclude_user: Optional[str] = None):
        """
        Broadcast a message to all connected users.
        
        Args:
            message: Message to broadcast
            exclude_user: Optional user ID to exclude from broadcast
        """
        disconnected = []
        
        for user_id, connections in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
                
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_user_count(self) -> int:
        """Get number of unique connected users."""
        return len(self.active_connections)
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user has any active connections."""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


class NotificationService:
    """
    Service for creating and sending real-time notifications.
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
    
    async def notify_scrape_started(
        self,
        user_id: str,
        competitor_name: str,
        competitor_id: int
    ):
        """Notify user that scraping has started."""
        await self.manager.send_to_user(user_id, {
            'type': NotificationType.SCRAPE_STARTED.value,
            'title': 'Scraping Started',
            'message': f'Started scraping {competitor_name}',
            'data': {
                'competitor_id': competitor_id,
                'competitor_name': competitor_name
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def notify_scrape_completed(
        self,
        user_id: str,
        competitor_name: str,
        competitor_id: int,
        changes_found: int
    ):
        """Notify user that scraping completed successfully."""
        await self.manager.send_to_user(user_id, {
            'type': NotificationType.SCRAPE_COMPLETED.value,
            'title': 'Scraping Completed',
            'message': f'Successfully scraped {competitor_name}. Found {changes_found} changes.',
            'data': {
                'competitor_id': competitor_id,
                'competitor_name': competitor_name,
                'changes_found': changes_found
            },
            'timestamp': datetime.utcnow().isoformat(),
            'action': {
                'label': 'View Changes',
                'url': f'/competitors/{competitor_id}'
            }
        })
    
    async def notify_scrape_failed(
        self,
        user_id: str,
        competitor_name: str,
        competitor_id: int,
        error: str
    ):
        """Notify user that scraping failed."""
        await self.manager.send_to_user(user_id, {
            'type': NotificationType.SCRAPE_FAILED.value,
            'title': 'Scraping Failed',
            'message': f'Failed to scrape {competitor_name}: {error}',
            'data': {
                'competitor_id': competitor_id,
                'competitor_name': competitor_name,
                'error': error
            },
            'timestamp': datetime.utcnow().isoformat(),
            'severity': 'error'
        })
    
    async def notify_high_impact_alert(
        self,
        user_id: str,
        alert_title: str,
        alert_description: str,
        impact_score: float,
        competitor_name: str,
        category: str
    ):
        """Notify user of a high-impact competitive intelligence alert."""
        await self.manager.send_to_user(user_id, {
            'type': NotificationType.HIGH_IMPACT_ALERT.value,
            'title': '🚨 High Impact Alert',
            'message': alert_title,
            'data': {
                'description': alert_description,
                'impact_score': impact_score,
                'competitor_name': competitor_name,
                'category': category
            },
            'timestamp': datetime.utcnow().isoformat(),
            'severity': 'critical' if impact_score >= 9 else 'high',
            'action': {
                'label': 'View Details',
                'url': f'/alerts'
            }
        })
    
    async def notify_battlecard_updated(
        self,
        user_id: str,
        battlecard_title: str,
        battlecard_id: int,
        competitor_name: str,
        auto_generated: bool = False
    ):
        """Notify user that a battlecard was updated."""
        await self.manager.send_to_user(user_id, {
            'type': NotificationType.BATTLECARD_UPDATED.value,
            'title': 'Battlecard Updated',
            'message': f'{"AI updated" if auto_generated else "Updated"} battlecard: {battlecard_title}',
            'data': {
                'battlecard_id': battlecard_id,
                'battlecard_title': battlecard_title,
                'competitor_name': competitor_name,
                'auto_generated': auto_generated
            },
            'timestamp': datetime.utcnow().isoformat(),
            'action': {
                'label': 'View Battlecard',
                'url': f'/battlecards/{battlecard_id}'
            }
        })
    
    async def notify_anomaly_detected(
        self,
        user_id: str,
        anomaly_description: str,
        severity: str,
        affected_component: str
    ):
        """Notify user of a system anomaly."""
        await self.manager.send_to_user(user_id, {
            'type': NotificationType.ANOMALY_DETECTED.value,
            'title': 'Anomaly Detected',
            'message': anomaly_description,
            'data': {
                'severity': severity,
                'affected_component': affected_component
            },
            'timestamp': datetime.utcnow().isoformat(),
            'severity': severity,
            'action': {
                'label': 'View Logs',
                'url': '/logs'
            }
        })
    
    async def notify_approval_required(
        self,
        user_id: str,
        alert_id: str,
        alert_title: str,
        impact_score: float
    ):
        """Notify user that an alert requires approval."""
        await self.manager.send_to_user(user_id, {
            'type': NotificationType.APPROVAL_REQUIRED.value,
            'title': 'Approval Required',
            'message': f'High-impact alert requires your approval: {alert_title}',
            'data': {
                'alert_id': alert_id,
                'alert_title': alert_title,
                'impact_score': impact_score
            },
            'timestamp': datetime.utcnow().isoformat(),
            'severity': 'warning',
            'action': {
                'label': 'Review & Approve',
                'url': f'/approvals/{alert_id}'
            }
        })
    
    async def broadcast_competitor_added(
        self,
        competitor_name: str,
        competitor_id: int,
        added_by_user: str
    ):
        """Broadcast that a new competitor was added."""
        await self.manager.broadcast({
            'type': NotificationType.COMPETITOR_ADDED.value,
            'title': 'New Competitor Added',
            'message': f'{competitor_name} has been added to monitoring',
            'data': {
                'competitor_id': competitor_id,
                'competitor_name': competitor_name,
                'added_by': added_by_user
            },
            'timestamp': datetime.utcnow().isoformat()
        }, exclude_user=added_by_user)


# Global connection manager instance
manager = ConnectionManager()
notification_service = NotificationService(manager)


async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint handler.
    
    Args:
        websocket: WebSocket connection
        user_id: Authenticated user ID
    """
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle ping/pong for connection keepalive
                if message.get('type') == 'ping':
                    await manager.send_personal_message(websocket, {
                        'type': 'pong',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                # Handle subscription updates
                elif message.get('type') == 'subscribe':
                    # Future: Handle topic subscriptions
                    pass
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from {user_id}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket)


# Helper function for periodic connection health checks
async def connection_health_check():
    """
    Periodically check connection health and clean up stale connections.
    Run this as a background task.
    """
    while True:
        try:
            # Check each connection
            for user_id, connections in list(manager.active_connections.items()):
                for conn in list(connections):
                    try:
                        # Send ping
                        await manager.send_personal_message(conn, {
                            'type': 'ping',
                            'timestamp': datetime.utcnow().isoformat()
                        })
                    except Exception:
                        manager.disconnect(conn)
            
            # Wait 30 seconds before next check
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in connection health check: {e}")
            await asyncio.sleep(30)
