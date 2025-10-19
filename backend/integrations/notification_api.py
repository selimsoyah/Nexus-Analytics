"""
API endpoints for Multi-Channel Notification System
Provides REST API for notification management and delivery
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from .notification_system import (
    MultiChannelNotificationSystem, 
    NotificationConfig,
    NotificationRecipient,
    NotificationChannel,
    NotificationPriority,
    notification_system
)

# Setup logging
logger = logging.getLogger(__name__)

# API Router
router = APIRouter(prefix="/notifications", tags=["Enhanced Notifications"])

# Pydantic models for API
class NotificationConfigModel(BaseModel):
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_username: str = ""
    from_email: str = ""
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    max_retries: int = 3
    rate_limit_per_minute: int = 100

class RecipientModel(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    slack_user_id: Optional[str] = None
    preferred_channels: List[str] = ["email"]
    timezone: str = "UTC"

class AlertDataModel(BaseModel):
    id: str = Field(..., description="Unique alert identifier")
    type: str = Field(..., description="Alert type (revenue_decline, conversion_anomaly, etc.)")
    priority_score: float = Field(5.0, ge=0, le=10, description="Priority score 0-10")
    confidence: float = Field(0.5, ge=0, le=1, description="Confidence level 0-1")
    data: Dict[str, Any] = Field(default_factory=dict, description="Alert-specific data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class NotificationRequestModel(BaseModel):
    alert_data: AlertDataModel
    recipient_ids: Optional[List[str]] = None
    immediate: bool = False

class ManualNotificationModel(BaseModel):
    recipients: List[str]
    channels: List[str]
    subject: str
    content: str
    priority: str = "medium"

# Dependency to get notification system
def get_notification_system() -> MultiChannelNotificationSystem:
    return notification_system

@router.get("/health")
async def notification_health_check():
    """Health check for notification system"""
    try:
        stats = notification_system.get_delivery_stats()
        
        return {
            "status": "healthy",
            "system_info": {
                "recipients_configured": len(notification_system.recipients),
                "notification_history": stats.get('total_notifications', 0),
                "success_rate": round(stats.get('success_rate', 0), 2),
                "channels_available": [channel.value for channel in NotificationChannel],
                "templates_loaded": len(notification_system.template_manager.templates),
                "demo_mode": notification_system.config.demo_mode
            },
            "config_status": {
                "email_configured": bool(notification_system.config.email_username) or notification_system.config.demo_mode,
                "slack_configured": bool(notification_system.config.slack_webhook_url) or notification_system.config.demo_mode,
                "sms_configured": bool(notification_system.config.twilio_account_sid) or notification_system.config.demo_mode
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/send")
async def send_notification(
    request: NotificationRequestModel,
    background_tasks: BackgroundTasks,
    system: MultiChannelNotificationSystem = Depends(get_notification_system)
):
    """Send notifications for an alert"""
    try:
        if request.immediate:
            # Send immediately
            result = await system.process_alert(
                alert_data=request.alert_data.dict(),
                recipient_ids=request.recipient_ids
            )
            return result
        else:
            # Send in background
            background_tasks.add_task(
                system.process_alert,
                alert_data=request.alert_data.dict(),
                recipient_ids=request.recipient_ids
            )
            return {
                "message": "Notification queued for background processing",
                "alert_id": request.alert_data.id,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Send notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

@router.post("/send-manual")
async def send_manual_notification(
    request: ManualNotificationModel,
    system: MultiChannelNotificationSystem = Depends(get_notification_system)
):
    """Send manual notification to specified recipients"""
    try:
        # Create alert data from manual notification
        alert_data = {
            'id': f"manual_{int(datetime.now().timestamp())}",
            'type': 'manual',
            'priority_score': {'low': 3, 'medium': 5, 'high': 7, 'critical': 9}.get(request.priority, 5),
            'confidence': 1.0,
            'data': {
                'subject': request.subject,
                'content': request.content,
                'channels': request.channels
            },
            'metadata': {
                'manual_notification': True,
                'sent_at': datetime.now().isoformat()
            }
        }
        
        result = await system.process_alert(alert_data, request.recipients)
        return result
        
    except Exception as e:
        logger.error(f"Manual notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send manual notification: {str(e)}")

@router.get("/status/{notification_id}")
async def get_notification_status(
    notification_id: str,
    system: MultiChannelNotificationSystem = Depends(get_notification_system)
):
    """Get status of a specific notification"""
    try:
        status = system.get_notification_status(notification_id)
        if not status:
            raise HTTPException(status_code=404, detail="Notification not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get notification status failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get notification status: {str(e)}")

@router.get("/stats")
async def get_delivery_statistics(
    system: MultiChannelNotificationSystem = Depends(get_notification_system)
):
    """Get delivery statistics and performance metrics"""
    try:
        stats = system.get_delivery_stats()
        return stats
    except Exception as e:
        logger.error(f"Get delivery statistics failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get delivery statistics: {str(e)}")

@router.get("/recipients")
async def list_recipients(
    system: MultiChannelNotificationSystem = Depends(get_notification_system)
):
    """List all configured notification recipients"""
    try:
        recipients = {}
        for recipient_id, recipient in system.recipients.items():
            recipients[recipient_id] = {
                'name': recipient.name,
                'email': recipient.email,
                'phone': recipient.phone,
                'preferred_channels': [channel.value for channel in recipient.preferred_channels],
                'timezone': recipient.timezone
            }
        return {
            'recipients': recipients,
            'total_count': len(recipients)
        }
    except Exception as e:
        logger.error(f"List recipients failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list recipients: {str(e)}")

@router.post("/recipients/{recipient_id}")
async def add_recipient(
    recipient_id: str,
    recipient_data: RecipientModel,
    system: MultiChannelNotificationSystem = Depends(get_notification_system)
):
    """Add or update a notification recipient"""
    try:
        # Convert string channels to enum
        preferred_channels = []
        for channel_str in recipient_data.preferred_channels:
            try:
                channel = NotificationChannel(channel_str.lower())
                preferred_channels.append(channel)
            except ValueError:
                logger.warning(f"Invalid channel: {channel_str}")
        
        recipient = NotificationRecipient(
            name=recipient_data.name,
            email=recipient_data.email,
            phone=recipient_data.phone,
            slack_user_id=recipient_data.slack_user_id,
            preferred_channels=preferred_channels,
            timezone=recipient_data.timezone
        )
        
        system.add_recipient(recipient_id, recipient)
        
        return {
            'message': f'Recipient {recipient_id} added/updated successfully',
            'recipient_id': recipient_id,
            'recipient': {
                'name': recipient.name,
                'email': recipient.email,
                'preferred_channels': [c.value for c in recipient.preferred_channels]
            }
        }
        
    except Exception as e:
        logger.error(f"Add recipient failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add recipient: {str(e)}")

@router.get("/templates")
async def list_notification_templates(
    system: MultiChannelNotificationSystem = Depends(get_notification_system)
):
    """List all available notification templates"""
    try:
        templates = {}
        for alert_type, channel_templates in system.template_manager.templates.items():
            templates[alert_type] = {}
            for channel, template in channel_templates.items():
                templates[alert_type][channel.value] = {
                    'subject_template': template.subject_template,
                    'format_type': template.format_type,
                    'body_preview': template.body_template[:200] + "..." if len(template.body_template) > 200 else template.body_template
                }
        
        return {
            'templates': templates,
            'alert_types': list(templates.keys()),
            'channels': [channel.value for channel in NotificationChannel]
        }
        
    except Exception as e:
        logger.error(f"List templates failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")

@router.post("/test")
async def test_notification_system():
    """Test the notification system with sample data"""
    try:
        # Create a test alert
        test_alert = {
            'id': f'test_alert_{int(datetime.now().timestamp())}',
            'type': 'revenue_decline',
            'priority_score': 7.5,
            'confidence': 0.8,
            'data': {
                'decline_percentage': 8.5,
                'current_revenue': 92000,
                'expected_revenue': 100000,
                'impact_description': 'Test revenue decline for notification system validation',
                'recommendations': [
                    'This is a test notification',
                    'Verify email delivery',
                    'Check Slack integration',
                    'Validate SMS capabilities'
                ]
            },
            'metadata': {
                'test_notification': True,
                'platform': 'test',
                'detection_time': datetime.now().isoformat()
            }
        }
        
        # Send to all recipients
        result = await notification_system.process_alert(test_alert)
        
        return {
            'message': 'Test notification sent successfully',
            'test_alert_id': test_alert['id'],
            'result': result,
            'delivery_stats': notification_system.get_delivery_stats()
        }
        
    except Exception as e:
        logger.error(f"Test notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test notification failed: {str(e)}")

@router.get("/history")
async def get_notification_history(
    limit: int = 50,
    offset: int = 0,
    channel: Optional[str] = None,
    status: Optional[str] = None,
    system: MultiChannelNotificationSystem = Depends(get_notification_system)
):
    """Get notification delivery history with filtering"""
    try:
        history = system.delivery_history.copy()
        
        # Apply filters
        if channel:
            try:
                channel_enum = NotificationChannel(channel.lower())
                history = [n for n in history if n.channel == channel_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid channel: {channel}")
        
        if status:
            history = [n for n in history if n.status.value == status.lower()]
        
        # Apply pagination
        total = len(history)
        history = history[offset:offset + limit]
        
        # Format response
        formatted_history = []
        for notification in history:
            formatted_history.append({
                'id': notification.id,
                'alert_id': notification.alert_id,
                'recipient_name': notification.recipient.name,
                'channel': notification.channel.value,
                'status': notification.status.value,
                'priority': notification.priority.value,
                'subject': notification.subject,
                'created_at': notification.created_at.isoformat(),
                'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
                'error_message': notification.error_message,
                'retry_count': notification.retry_count
            })
        
        return {
            'history': formatted_history,
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            },
            'filters': {
                'channel': channel,
                'status': status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get notification history failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get notification history: {str(e)}")

@router.post("/config")
async def update_notification_config(
    config: NotificationConfigModel,
    system: MultiChannelNotificationSystem = Depends(get_notification_system)
):
    """Update notification system configuration"""
    try:
        # Update the configuration
        system.config.smtp_server = config.smtp_server
        system.config.smtp_port = config.smtp_port
        system.config.email_username = config.email_username
        system.config.from_email = config.from_email
        system.config.slack_webhook_url = config.slack_webhook_url
        system.config.slack_channel = config.slack_channel
        system.config.max_retries = config.max_retries
        system.config.rate_limit_per_minute = config.rate_limit_per_minute
        
        return {
            'message': 'Configuration updated successfully',
            'config': {
                'smtp_server': system.config.smtp_server,
                'smtp_port': system.config.smtp_port,
                'slack_channel': system.config.slack_channel,
                'max_retries': system.config.max_retries,
                'rate_limit_per_minute': system.config.rate_limit_per_minute
            }
        }
        
    except Exception as e:
        logger.error(f"Update config failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")

# Integration endpoint to work with the alert system
@router.post("/integrate/alert")
async def process_alert_notification(
    alert_data: Dict[str, Any],
    recipient_ids: Optional[List[str]] = None,
    system: MultiChannelNotificationSystem = Depends(get_notification_system)
):
    """Process alert and send notifications (used by alert system integration)"""
    try:
        result = await system.process_alert(alert_data, recipient_ids)
        return result
    except Exception as e:
        logger.error(f"Alert integration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Alert integration failed: {str(e)}")

# Export router for inclusion in main API
__all__ = ['router']