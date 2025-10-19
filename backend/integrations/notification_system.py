"""
Enhanced Multi-Channel Notification System for Nexus Analytics
Integrates with ML-powered alert system to deliver notifications via email, SMS, and Slack
"""

import asyncio
import json
import logging
import smtplib
import ssl
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from enum import Enum

# Import email components properly
try:
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    EMAIL_AVAILABLE = True
except ImportError as e:
    print(f"Email functionality not available: {e}")
    EMAIL_AVAILABLE = False
    MIMEText = None
    MIMEMultipart = None

# Import optional dependencies
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from jinja2 import Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    # Fallback simple template
    class Template:
        def __init__(self, template_str):
            self.template_str = template_str
        def render(self, **kwargs):
            result = self.template_str
            for key, value in kwargs.items():
                result = result.replace(f"{{{{ {key} }}}}", str(value))
            return result

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    READ = "read"

@dataclass
class NotificationConfig:
    """Configuration for notification channels"""
    # Email settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    from_email: str = ""
    
    # SMS settings (Twilio)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    
    # Slack settings
    slack_webhook_url: str = ""
    slack_bot_token: str = ""
    slack_channel: str = "#alerts"
    
    # General settings
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    rate_limit_per_minute: int = 100
    demo_mode: bool = True  # Enable demo mode to simulate successful deliveries

@dataclass
class NotificationRecipient:
    """Recipient information for notifications"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    slack_user_id: Optional[str] = None
    preferred_channels: List[NotificationChannel] = None
    timezone: str = "UTC"
    notification_schedule: Dict[str, bool] = None  # Days of week, hours
    
    def __post_init__(self):
        if self.preferred_channels is None:
            self.preferred_channels = [NotificationChannel.EMAIL]
        if self.notification_schedule is None:
            self.notification_schedule = {
                "monday": True, "tuesday": True, "wednesday": True,
                "thursday": True, "friday": True, "saturday": True, "sunday": True,
                "start_hour": 0, "end_hour": 23
            }

@dataclass
class NotificationTemplate:
    """Template for notification messages"""
    channel: NotificationChannel
    subject_template: str
    body_template: str
    format_type: str = "text"  # text, html, markdown
    
class NotificationMessage:
    """Individual notification message"""
    
    def __init__(self, 
                 alert_id: str,
                 recipient: NotificationRecipient,
                 channel: NotificationChannel,
                 subject: str,
                 content: str,
                 priority: NotificationPriority = NotificationPriority.MEDIUM,
                 metadata: Dict[str, Any] = None):
        self.id = f"notif_{alert_id}_{channel.value}_{int(datetime.now().timestamp())}"
        self.alert_id = alert_id
        self.recipient = recipient
        self.channel = channel
        self.subject = subject
        self.content = content
        self.priority = priority
        self.metadata = metadata or {}
        self.status = NotificationStatus.PENDING
        self.created_at = datetime.now()
        self.sent_at = None
        self.delivered_at = None
        self.error_message = None
        self.retry_count = 0

class NotificationTemplateManager:
    """Manages notification templates for different channels and alert types"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Dict[NotificationChannel, NotificationTemplate]]:
        """Initialize default templates for different alert types"""
        return {
            "revenue_decline": {
                NotificationChannel.EMAIL: NotificationTemplate(
                    channel=NotificationChannel.EMAIL,
                    subject_template="🚨 Revenue Alert: {{ decline_percentage }}% decline detected",
                    body_template="""
                    <html>
                    <body>
                        <h2>Revenue Decline Alert</h2>
                        <p><strong>Alert:</strong> Revenue decline of {{ decline_percentage }}% detected</p>
                        <p><strong>Confidence:</strong> {{ confidence }}%</p>
                        <p><strong>Current Revenue:</strong> ${{ current_revenue }}</p>
                        <p><strong>Expected Revenue:</strong> ${{ expected_revenue }}</p>
                        <p><strong>Impact:</strong> {{ impact_description }}</p>
                        
                        <h3>Recommended Actions:</h3>
                        <ul>
                        {% for action in recommendations %}
                            <li>{{ action }}</li>
                        {% endfor %}
                        </ul>
                        
                        <p><em>Alert generated at {{ timestamp }}</em></p>
                        <p><a href="{{ dashboard_link }}">View Dashboard</a></p>
                    </body>
                    </html>
                    """,
                    format_type="html"
                ),
                NotificationChannel.SLACK: NotificationTemplate(
                    channel=NotificationChannel.SLACK,
                    subject_template="Revenue Alert",
                    body_template="""
                    🚨 *Revenue Decline Alert*
                    
                    📉 *Decline:* {{ decline_percentage }}%
                    🎯 *Confidence:* {{ confidence }}%
                    💰 *Current:* ${{ current_revenue }}
                    📊 *Expected:* ${{ expected_revenue }}
                    
                    *Recommended Actions:*
                    {% for action in recommendations %}
                    • {{ action }}
                    {% endfor %}
                    
                    <{{ dashboard_link }}|View Dashboard>
                    """,
                    format_type="markdown"
                ),
                NotificationChannel.SMS: NotificationTemplate(
                    channel=NotificationChannel.SMS,
                    subject_template="Revenue Alert",
                    body_template="🚨 Revenue declined {{ decline_percentage }}% ({{ confidence }}% confidence). Current: ${{ current_revenue }}. Check dashboard: {{ dashboard_link }}",
                    format_type="text"
                )
            },
            "conversion_anomaly": {
                NotificationChannel.EMAIL: NotificationTemplate(
                    channel=NotificationChannel.EMAIL,
                    subject_template="⚠️ Conversion Rate Anomaly Detected",
                    body_template="""
                    <html>
                    <body>
                        <h2>Conversion Rate Anomaly</h2>
                        <p><strong>Anomaly Score:</strong> {{ anomaly_score }}</p>
                        <p><strong>Current Rate:</strong> {{ current_rate }}%</p>
                        <p><strong>Expected Rate:</strong> {{ expected_rate }}%</p>
                        <p><strong>Deviation:</strong> {{ deviation }}%</p>
                        
                        <h3>Analysis:</h3>
                        <p>{{ analysis_description }}</p>
                        
                        <h3>Recommended Actions:</h3>
                        <ul>
                        {% for action in recommendations %}
                            <li>{{ action }}</li>
                        {% endfor %}
                        </ul>
                        
                        <p><a href="{{ dashboard_link }}">View Dashboard</a></p>
                    </body>
                    </html>
                    """,
                    format_type="html"
                )
            },
            "customer_churn": {
                NotificationChannel.EMAIL: NotificationTemplate(
                    channel=NotificationChannel.EMAIL,
                    subject_template="🔔 Customer Churn Prediction Alert",
                    body_template="""
                    <html>
                    <body>
                        <h2>Customer Churn Prediction</h2>
                        <p><strong>Customers at Risk:</strong> {{ customers_at_risk }}</p>
                        <p><strong>Churn Probability:</strong> {{ churn_probability }}%</p>
                        <p><strong>Revenue Impact:</strong> ${{ revenue_impact }}</p>
                        
                        <h3>High-Risk Segments:</h3>
                        <ul>
                        {% for segment in risk_segments %}
                            <li>{{ segment }}</li>
                        {% endfor %}
                        </ul>
                        
                        <h3>Retention Strategies:</h3>
                        <ul>
                        {% for strategy in retention_strategies %}
                            <li>{{ strategy }}</li>
                        {% endfor %}
                        </ul>
                        
                        <p><a href="{{ dashboard_link }}">View Dashboard</a></p>
                    </body>
                    </html>
                    """,
                    format_type="html"
                )
            },
            "inventory_alert": {
                NotificationChannel.EMAIL: NotificationTemplate(
                    channel=NotificationChannel.EMAIL,
                    subject_template="📦 Inventory Alert: {{ alert_type }}",
                    body_template="""
                    <html>
                    <body>
                        <h2>Inventory Alert</h2>
                        <p><strong>Alert Type:</strong> {{ alert_type }}</p>
                        <p><strong>Products Affected:</strong> {{ products_affected }}</p>
                        <p><strong>Urgency:</strong> {{ urgency_level }}</p>
                        
                        <h3>Product Details:</h3>
                        <ul>
                        {% for product in affected_products %}
                            <li>{{ product.name }}: {{ product.current_stock }} units ({{ product.status }})</li>
                        {% endfor %}
                        </ul>
                        
                        <h3>Recommended Actions:</h3>
                        <ul>
                        {% for action in recommendations %}
                            <li>{{ action }}</li>
                        {% endfor %}
                        </ul>
                        
                        <p><a href="{{ dashboard_link }}">View Dashboard</a></p>
                    </body>
                    </html>
                    """,
                    format_type="html"
                )
            }
        }
    
    def get_template(self, alert_type: str, channel: NotificationChannel) -> Optional[NotificationTemplate]:
        """Get template for specific alert type and channel"""
        return self.templates.get(alert_type, {}).get(channel)
    
    def render_template(self, template: NotificationTemplate, context: Dict[str, Any]) -> tuple[str, str]:
        """Render template with context data"""
        try:
            subject_template = Template(template.subject_template)
            body_template = Template(template.body_template)
            
            subject = subject_template.render(**context)
            content = body_template.render(**context)
            
            return subject, content
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return f"Alert: {context.get('alert_type', 'Unknown')}", str(context)

class NotificationDelivery:
    """Handles actual delivery of notifications through various channels"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        
    async def send_email(self, message: NotificationMessage) -> bool:
        """Send email notification"""
        try:
            # Demo mode - simulate successful delivery
            if self.config.demo_mode:
                await asyncio.sleep(0.1)  # Simulate network delay
                logger.info(f"[DEMO MODE] Email sent successfully to {message.recipient.email}")
                return True
                
            if not EMAIL_AVAILABLE:
                logger.warning("Email functionality not available (missing dependencies)")
                message.error_message = "Email dependencies not available"
                return False
                
            if not all([self.config.smtp_server, self.config.email_username, 
                       self.config.email_password, message.recipient.email]):
                logger.warning("Email configuration incomplete")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = self.config.from_email or self.config.email_username
            msg['To'] = message.recipient.email
            
            # Add content
            if message.metadata.get('format_type') == 'html':
                html_part = MIMEText(message.content, 'html')
                msg.attach(html_part)
            else:
                text_part = MIMEText(message.content, 'plain')
                msg.attach(text_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.email_username, self.config.email_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {message.recipient.email}")
            return True
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            message.error_message = str(e)
            return False
    
    async def send_sms(self, message: NotificationMessage) -> bool:
        """Send SMS notification via Twilio"""
        try:
            # Demo mode - simulate successful delivery
            if self.config.demo_mode:
                await asyncio.sleep(0.1)  # Simulate network delay
                logger.info(f"[DEMO MODE] SMS sent successfully to {message.recipient.phone}")
                return True
                
            if not all([self.config.twilio_account_sid, self.config.twilio_auth_token,
                       self.config.twilio_phone_number, message.recipient.phone]):
                logger.warning("SMS configuration incomplete")
                return False
            
            # Note: In production, you would use the Twilio client
            # For demo purposes, we'll simulate the API call
            twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.config.twilio_account_sid}/Messages.json"
            
            # Simulate SMS sending (replace with actual Twilio client in production)
            logger.info(f"SMS would be sent to {message.recipient.phone}: {message.content[:100]}...")
            return True
            
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            message.error_message = str(e)
            return False
    
    async def send_slack(self, message: NotificationMessage) -> bool:
        """Send Slack notification"""
        try:
            # Demo mode - simulate successful delivery
            if self.config.demo_mode:
                await asyncio.sleep(0.1)  # Simulate network delay
                logger.info(f"[DEMO MODE] Slack notification sent successfully to {self.config.slack_channel}")
                return True
                
            if not AIOHTTP_AVAILABLE:
                logger.warning("Slack functionality not available (missing aiohttp)")
                message.error_message = "aiohttp dependency not available"
                return False
                
            if not self.config.slack_webhook_url:
                logger.warning("Slack webhook URL not configured")
                return False
            
            slack_payload = {
                "channel": self.config.slack_channel,
                "username": "Nexus Analytics",
                "icon_emoji": ":chart_with_upwards_trend:",
                "attachments": [{
                    "color": self._get_color_for_priority(message.priority),
                    "title": message.subject,
                    "text": message.content,
                    "ts": int(message.created_at.timestamp())
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.slack_webhook_url, 
                                      json=slack_payload) as response:
                    if response.status == 200:
                        logger.info("Slack notification sent successfully")
                        return True
                    else:
                        logger.error(f"Slack API error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Slack sending failed: {e}")
            message.error_message = str(e)
            return False
    
    def _get_color_for_priority(self, priority: NotificationPriority) -> str:
        """Get color code for Slack attachments based on priority"""
        color_map = {
            NotificationPriority.LOW: "#36a64f",      # Green
            NotificationPriority.MEDIUM: "#ff9500",   # Orange
            NotificationPriority.HIGH: "#ff0000",     # Red
            NotificationPriority.CRITICAL: "#8B0000"  # Dark Red
        }
        return color_map.get(priority, "#36a64f")

class MultiChannelNotificationSystem:
    """Main notification system that orchestrates multi-channel delivery"""
    
    def __init__(self, config: NotificationConfig = None):
        self.config = config or NotificationConfig()
        self.template_manager = NotificationTemplateManager()
        self.delivery = NotificationDelivery(self.config)
        self.notification_queue: List[NotificationMessage] = []
        self.delivery_history: List[NotificationMessage] = []
        self.recipients: Dict[str, NotificationRecipient] = {}
        
        # Initialize default recipients (in production, load from database)
        self._initialize_default_recipients()
    
    def _initialize_default_recipients(self):
        """Initialize default recipients for demo purposes"""
        self.recipients = {
            "admin": NotificationRecipient(
                name="System Administrator",
                email="admin@nexusanalytics.com",
                phone="+1234567890",
                preferred_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                timezone="UTC"
            ),
            "sales_manager": NotificationRecipient(
                name="Sales Manager",
                email="sales@nexusanalytics.com",
                phone="+1234567891",
                preferred_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
                timezone="UTC"
            ),
            "cto": NotificationRecipient(
                name="Chief Technology Officer",
                email="cto@nexusanalytics.com",
                preferred_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                timezone="UTC"
            )
        }
    
    def add_recipient(self, recipient_id: str, recipient: NotificationRecipient):
        """Add or update a notification recipient"""
        self.recipients[recipient_id] = recipient
    
    def create_notification_from_alert(self, alert_data: Dict[str, Any], 
                                     recipient_ids: List[str] = None) -> List[NotificationMessage]:
        """Create notifications from alert data"""
        notifications = []
        
        # Use all recipients if none specified
        if recipient_ids is None:
            recipient_ids = list(self.recipients.keys())
        
        alert_type = alert_data.get('type', 'general')
        alert_id = alert_data.get('id', f"alert_{int(datetime.now().timestamp())}")
        priority = self._determine_priority(alert_data)
        
        # Prepare template context
        context = {
            'alert_type': alert_type,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            'dashboard_link': "http://localhost:3000/dashboard",
            **alert_data.get('data', {}),
            **alert_data.get('metadata', {})
        }
        
        for recipient_id in recipient_ids:
            recipient = self.recipients.get(recipient_id)
            if not recipient:
                continue
            
            # Create notifications for each preferred channel
            for channel in recipient.preferred_channels:
                template = self.template_manager.get_template(alert_type, channel)
                if not template:
                    # Use generic template
                    template = NotificationTemplate(
                        channel=channel,
                        subject_template="Alert: {{ alert_type }}",
                        body_template="Alert detected: {{ alert_type }}. Check dashboard: {{ dashboard_link }}",
                        format_type="text"
                    )
                
                subject, content = self.template_manager.render_template(template, context)
                
                notification = NotificationMessage(
                    alert_id=alert_id,
                    recipient=recipient,
                    channel=channel,
                    subject=subject,
                    content=content,
                    priority=priority,
                    metadata={'format_type': template.format_type, **alert_data.get('metadata', {})}
                )
                
                notifications.append(notification)
        
        return notifications
    
    def _determine_priority(self, alert_data: Dict[str, Any]) -> NotificationPriority:
        """Determine notification priority based on alert data"""
        priority_score = alert_data.get('priority_score', 5)
        confidence = alert_data.get('confidence', 0.5)
        
        # Combine priority score and confidence
        effective_priority = priority_score * confidence
        
        if effective_priority >= 8:
            return NotificationPriority.CRITICAL
        elif effective_priority >= 6:
            return NotificationPriority.HIGH
        elif effective_priority >= 4:
            return NotificationPriority.MEDIUM
        else:
            return NotificationPriority.LOW
    
    async def send_notifications(self, notifications: List[NotificationMessage]) -> Dict[str, Any]:
        """Send a batch of notifications"""
        results = {
            'total': len(notifications),
            'sent': 0,
            'failed': 0,
            'details': []
        }
        
        for notification in notifications:
            try:
                # Check if recipient should receive notifications at this time
                if not self._should_send_now(notification.recipient):
                    notification.status = NotificationStatus.PENDING
                    continue
                
                # Send notification based on channel
                success = False
                if notification.channel == NotificationChannel.EMAIL:
                    success = await self.delivery.send_email(notification)
                elif notification.channel == NotificationChannel.SMS:
                    success = await self.delivery.send_sms(notification)
                elif notification.channel == NotificationChannel.SLACK:
                    success = await self.delivery.send_slack(notification)
                
                # Update notification status
                if success:
                    notification.status = NotificationStatus.SENT
                    notification.sent_at = datetime.now()
                    results['sent'] += 1
                else:
                    notification.status = NotificationStatus.FAILED
                    results['failed'] += 1
                
                # Add to delivery history
                self.delivery_history.append(notification)
                
                results['details'].append({
                    'notification_id': notification.id,
                    'recipient': notification.recipient.name,
                    'channel': notification.channel.value,
                    'status': notification.status.value,
                    'error': notification.error_message
                })
                
            except Exception as e:
                logger.error(f"Notification delivery error: {e}")
                notification.status = NotificationStatus.FAILED
                notification.error_message = str(e)
                results['failed'] += 1
        
        return results
    
    def _should_send_now(self, recipient: NotificationRecipient) -> bool:
        """Check if notification should be sent based on recipient schedule"""
        # For demo purposes, always return True
        # In production, implement timezone and schedule checking
        return True
    
    async def process_alert(self, alert_data: Dict[str, Any], 
                          recipient_ids: List[str] = None) -> Dict[str, Any]:
        """Complete flow: create notifications from alert and send them"""
        try:
            # Create notifications
            notifications = self.create_notification_from_alert(alert_data, recipient_ids)
            
            # Send notifications
            results = await self.send_notifications(notifications)
            
            logger.info(f"Processed alert {alert_data.get('id')}: {results['sent']} sent, {results['failed']} failed")
            
            return {
                'alert_id': alert_data.get('id'),
                'notifications_created': len(notifications),
                'delivery_results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Alert processing error: {e}")
            return {
                'alert_id': alert_data.get('id'),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_notification_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific notification"""
        for notification in self.delivery_history:
            if notification.id == notification_id:
                return {
                    'id': notification.id,
                    'alert_id': notification.alert_id,
                    'recipient': notification.recipient.name,
                    'channel': notification.channel.value,
                    'status': notification.status.value,
                    'created_at': notification.created_at.isoformat(),
                    'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
                    'error_message': notification.error_message,
                    'retry_count': notification.retry_count
                }
        return None
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery statistics"""
        if not self.delivery_history:
            return {
                'total_notifications': 0,
                'success_rate': 0,
                'channel_stats': {},
                'priority_stats': {}
            }
        
        total = len(self.delivery_history)
        successful = sum(1 for n in self.delivery_history if n.status == NotificationStatus.SENT)
        
        # Channel statistics
        channel_stats = {}
        for channel in NotificationChannel:
            channel_notifications = [n for n in self.delivery_history if n.channel == channel]
            if channel_notifications:
                successful_channel = sum(1 for n in channel_notifications if n.status == NotificationStatus.SENT)
                channel_stats[channel.value] = {
                    'total': len(channel_notifications),
                    'successful': successful_channel,
                    'success_rate': successful_channel / len(channel_notifications) * 100
                }
        
        # Priority statistics
        priority_stats = {}
        for priority in NotificationPriority:
            priority_notifications = [n for n in self.delivery_history if n.priority == priority]
            if priority_notifications:
                successful_priority = sum(1 for n in priority_notifications if n.status == NotificationStatus.SENT)
                priority_stats[priority.value] = {
                    'total': len(priority_notifications),
                    'successful': successful_priority,
                    'success_rate': successful_priority / len(priority_notifications) * 100
                }
        
        return {
            'total_notifications': total,
            'successful_notifications': successful,
            'success_rate': successful / total * 100,
            'channel_stats': channel_stats,
            'priority_stats': priority_stats,
            'recent_notifications': [
                {
                    'id': n.id,
                    'channel': n.channel.value,
                    'status': n.status.value,
                    'created_at': n.created_at.isoformat()
                }
                for n in self.delivery_history[-10:]  # Last 10 notifications
            ]
        }

# Global notification system instance
notification_system = MultiChannelNotificationSystem()

async def demo_notification_system():
    """Demo function to test the notification system"""
    
    # Sample alert data (similar to what our ML alert system generates)
    sample_alert = {
        'id': 'alert_revenue_001',
        'type': 'revenue_decline',
        'priority_score': 8,
        'confidence': 0.75,
        'data': {
            'decline_percentage': 12.5,
            'current_revenue': 85000,
            'expected_revenue': 97143,
            'impact_description': 'Significant revenue decline detected across multiple product categories',
            'recommendations': [
                'Review marketing campaigns for underperforming products',
                'Analyze customer feedback for recent product changes',
                'Consider promotional pricing for key products',
                'Investigate competitor activities'
            ]
        },
        'metadata': {
            'platform': 'multi-platform',
            'detection_time': datetime.now().isoformat(),
            'model_version': '1.0'
        }
    }
    
    # Process the alert
    result = await notification_system.process_alert(sample_alert)
    
    return result

if __name__ == "__main__":
    # Run demo
    result = asyncio.run(demo_notification_system())
    print(json.dumps(result, indent=2))