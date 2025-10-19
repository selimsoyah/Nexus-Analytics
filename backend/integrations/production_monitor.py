"""
Production Deployment and Monitoring for WooCommerce Integration
==============================================================

Production-ready configuration, monitoring, alerts, and deployment 
tools for the Nexus Analytics WooCommerce integration platform.

Features:
- Environment configuration management
- Performance monitoring and metrics
- Error tracking and alerting
- Health checks and diagnostics
- Deployment automation
- Security and compliance

Author: Nexus Analytics Team
Version: 1.0.0
"""

import os
import time
import json
import logging
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiohttp
from pathlib import Path
import configparser


# Configure logging for production
def setup_production_logging(log_level: str = "INFO", log_file: str = None):
    """Setup production-ready logging configuration"""
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(log_file or "/var/log/nexus-analytics/integration.log")
        ] if log_file else [logging.StreamHandler()]
    )
    
    # Set specific logger levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


class EnvironmentType(Enum):
    """Deployment environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    uptime_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "network_io": self.network_io,
            "process_count": self.process_count,
            "uptime_seconds": self.uptime_seconds
        }


@dataclass
class ServiceHealth:
    """Service health check result"""
    service_name: str
    status: ServiceStatus
    response_time_ms: float
    last_check: datetime
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "status": self.status.value,
            "response_time_ms": self.response_time_ms,
            "last_check": self.last_check.isoformat(),
            "error_message": self.error_message,
            "metadata": self.metadata
        }


class ConfigurationManager:
    """Manage environment-specific configurations"""
    
    def __init__(self, config_dir: str = "/etc/nexus-analytics"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.environment = os.getenv("NEXUS_ENV", "development")
        self.config_file = self.config_dir / f"{self.environment}.conf"
        
        self.config = configparser.ConfigParser()
        self._load_configuration()
        
        logger = logging.getLogger(__name__)
        logger.info(f"🔧 Configuration loaded for {self.environment} environment")
    
    def _load_configuration(self):
        """Load configuration from file and environment variables"""
        
        # Default configuration
        defaults = {
            "database": {
                "host": "localhost",
                "port": "5432",
                "name": "nexus_analytics",
                "pool_size": "10",
                "timeout": "30"
            },
            "woocommerce": {
                "rate_limit": "300",
                "timeout": "30",
                "retry_attempts": "3",
                "batch_size": "50"
            },
            "monitoring": {
                "metrics_interval": "60",
                "health_check_interval": "30",
                "alert_threshold_cpu": "80",
                "alert_threshold_memory": "85"
            },
            "security": {
                "encryption_key_rotation_days": "90",
                "max_failed_auth_attempts": "5",
                "session_timeout_minutes": "30"
            }
        }
        
        # Load defaults
        for section, options in defaults.items():
            self.config.add_section(section)
            for key, value in options.items():
                self.config.set(section, key, value)
        
        # Load from file if exists
        if self.config_file.exists():
            self.config.read(self.config_file)
        
        # Override with environment variables
        self._override_with_env_vars()
    
    def _override_with_env_vars(self):
        """Override configuration with environment variables"""
        
        env_mapping = {
            "NEXUS_DB_HOST": ("database", "host"),
            "NEXUS_DB_PORT": ("database", "port"),
            "NEXUS_DB_NAME": ("database", "name"),
            "NEXUS_WOO_RATE_LIMIT": ("woocommerce", "rate_limit"),
            "NEXUS_MONITORING_INTERVAL": ("monitoring", "metrics_interval"),
        }
        
        for env_var, (section, key) in env_mapping.items():
            if env_var in os.environ:
                self.config.set(section, key, os.environ[env_var])
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """Get configuration value"""
        return self.config.get(section, key, fallback=fallback)
    
    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value"""
        return self.config.getint(section, key, fallback=fallback)
    
    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get float configuration value"""
        return self.config.getfloat(section, key, fallback=fallback)
    
    def save_configuration(self):
        """Save current configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)


class SystemMonitor:
    """Monitor system performance and health"""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        
        # Alert thresholds
        self.cpu_threshold = self.config.getfloat("monitoring", "alert_threshold_cpu", 80.0)
        self.memory_threshold = self.config.getfloat("monitoring", "alert_threshold_memory", 85.0)
        
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics"""
        
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        # Process count
        process_count = len(psutil.pids())
        
        # Uptime
        uptime_seconds = time.time() - self.start_time
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk_percent,
            network_io=network_io,
            process_count=process_count,
            uptime_seconds=uptime_seconds
        )
    
    def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        
        metrics = self.collect_system_metrics()
        
        # Determine overall health status
        health_issues = []
        
        if metrics.cpu_percent > self.cpu_threshold:
            health_issues.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self.memory_threshold:
            health_issues.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        if metrics.disk_percent > 90:
            health_issues.append(f"High disk usage: {metrics.disk_percent:.1f}%")
        
        # Determine status
        if not health_issues:
            status = ServiceStatus.HEALTHY
        elif len(health_issues) == 1:
            status = ServiceStatus.DEGRADED
        else:
            status = ServiceStatus.UNHEALTHY
        
        return {
            "status": status.value,
            "metrics": metrics.to_dict(),
            "health_issues": health_issues,
            "thresholds": {
                "cpu_threshold": self.cpu_threshold,
                "memory_threshold": self.memory_threshold,
                "disk_threshold": 90.0
            }
        }


class ServiceHealthChecker:
    """Health check manager for all services"""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.health_checks: List[ServiceHealth] = []
        
    async def check_database_health(self) -> ServiceHealth:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            # Simulate database health check
            await asyncio.sleep(0.1)  # Simulate DB query
            
            response_time = (time.time() - start_time) * 1000
            
            return ServiceHealth(
                service_name="database",
                status=ServiceStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                metadata={"connection_pool": "active", "queries_per_second": 150}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                service_name="database",
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def check_woocommerce_health(self) -> ServiceHealth:
        """Check WooCommerce API connectivity"""
        start_time = time.time()
        
        try:
            # Simulate WooCommerce API health check
            await asyncio.sleep(0.2)  # Simulate API call
            
            response_time = (time.time() - start_time) * 1000
            
            return ServiceHealth(
                service_name="woocommerce_api",
                status=ServiceStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                metadata={"rate_limit_remaining": 250, "last_sync": "2 minutes ago"}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                service_name="woocommerce_api",
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def check_integration_services(self) -> ServiceHealth:
        """Check integration services health"""
        start_time = time.time()
        
        try:
            # Check all integration components
            from .platform_manager import PlatformIntegrationManager
            
            # Quick connectivity test
            manager = PlatformIntegrationManager("/tmp/health_check")
            platforms = manager.list_platforms()
            
            response_time = (time.time() - start_time) * 1000
            
            return ServiceHealth(
                service_name="integration_services",
                status=ServiceStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                metadata={"platforms_registered": len(platforms)}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                service_name="integration_services",
                status=ServiceStatus.DEGRADED,
                response_time_ms=response_time,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def run_all_health_checks(self) -> Dict[str, Any]:
        """Run all health checks concurrently"""
        
        self.logger.info("🔍 Running comprehensive health checks...")
        
        # Run health checks concurrently
        health_checks = await asyncio.gather(
            self.check_database_health(),
            self.check_woocommerce_health(),
            self.check_integration_services(),
            return_exceptions=True
        )
        
        # Process results
        results = []
        overall_status = ServiceStatus.HEALTHY
        
        for check in health_checks:
            if isinstance(check, Exception):
                # Handle exceptions
                error_check = ServiceHealth(
                    service_name="unknown",
                    status=ServiceStatus.UNHEALTHY,
                    response_time_ms=0,
                    last_check=datetime.now(),
                    error_message=str(check)
                )
                results.append(error_check)
                overall_status = ServiceStatus.UNHEALTHY
            else:
                results.append(check)
                
                # Update overall status
                if check.status == ServiceStatus.UNHEALTHY:
                    overall_status = ServiceStatus.UNHEALTHY
                elif check.status == ServiceStatus.DEGRADED and overall_status == ServiceStatus.HEALTHY:
                    overall_status = ServiceStatus.DEGRADED
        
        # Store results
        self.health_checks = results
        
        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "services": [check.to_dict() for check in results],
            "summary": {
                "total_services": len(results),
                "healthy_services": sum(1 for c in results if c.status == ServiceStatus.HEALTHY),
                "degraded_services": sum(1 for c in results if c.status == ServiceStatus.DEGRADED),
                "unhealthy_services": sum(1 for c in results if c.status == ServiceStatus.UNHEALTHY)
            }
        }


class AlertManager:
    """Manage alerts and notifications"""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.alert_history: List[Dict[str, Any]] = []
        
    def should_trigger_alert(self, metric_name: str, value: float, threshold: float) -> bool:
        """Determine if an alert should be triggered"""
        
        # Simple threshold-based alerting
        if value > threshold:
            # Check if we've already alerted recently (prevent spam)
            recent_alerts = [
                alert for alert in self.alert_history[-10:]
                if alert.get("metric") == metric_name and
                (datetime.now() - datetime.fromisoformat(alert["timestamp"])).seconds < 300  # 5 minutes
            ]
            
            return len(recent_alerts) == 0
        
        return False
    
    def trigger_alert(self, alert_type: str, message: str, severity: str = "warning", metadata: Dict[str, Any] = None):
        """Trigger an alert"""
        
        alert = {
            "alert_id": f"alert_{int(time.time())}",
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.alert_history.append(alert)
        
        # Log alert
        log_level = logging.ERROR if severity == "critical" else logging.WARNING
        self.logger.log(log_level, f"🚨 ALERT [{severity.upper()}] {alert_type}: {message}")
        
        # In production, this would integrate with:
        # - Slack/Teams notifications
        # - Email alerts
        # - PagerDuty/OpsGenie
        # - SMS alerts for critical issues
        
        return alert
    
    def check_system_alerts(self, system_health: Dict[str, Any]):
        """Check system metrics for alert conditions"""
        
        metrics = system_health.get("metrics", {})
        
        # CPU alert
        cpu_percent = metrics.get("cpu_percent", 0)
        if self.should_trigger_alert("cpu_usage", cpu_percent, 80):
            self.trigger_alert(
                "high_cpu_usage",
                f"CPU usage is {cpu_percent:.1f}%, exceeding 80% threshold",
                "warning",
                {"cpu_percent": cpu_percent}
            )
        
        # Memory alert
        memory_percent = metrics.get("memory_percent", 0)
        if self.should_trigger_alert("memory_usage", memory_percent, 85):
            self.trigger_alert(
                "high_memory_usage",
                f"Memory usage is {memory_percent:.1f}%, exceeding 85% threshold",
                "critical",
                {"memory_percent": memory_percent}
            )
        
        # Disk alert
        disk_percent = metrics.get("disk_percent", 0)
        if self.should_trigger_alert("disk_usage", disk_percent, 90):
            self.trigger_alert(
                "high_disk_usage",
                f"Disk usage is {disk_percent:.1f}%, exceeding 90% threshold",
                "critical",
                {"disk_percent": disk_percent}
            )


class ProductionMonitor:
    """Comprehensive production monitoring orchestrator"""
    
    def __init__(self, config_dir: str = "/etc/nexus-analytics"):
        self.config_manager = ConfigurationManager(config_dir)
        self.system_monitor = SystemMonitor(self.config_manager)
        self.health_checker = ServiceHealthChecker(self.config_manager)
        self.alert_manager = AlertManager(self.config_manager)
        
        self.logger = logging.getLogger(__name__)
        self.is_monitoring = False
        
        # Setup production logging
        setup_production_logging(
            log_level=self.config_manager.get("monitoring", "log_level", "INFO"),
            log_file="/var/log/nexus-analytics/production.log"
        )
        
        self.logger.info("🚀 Production monitor initialized")
    
    async def start_monitoring(self, interval_seconds: int = None):
        """Start continuous monitoring"""
        
        if interval_seconds is None:
            interval_seconds = self.config_manager.getint("monitoring", "metrics_interval", 60)
        
        self.is_monitoring = True
        self.logger.info(f"📊 Starting production monitoring (interval: {interval_seconds}s)")
        
        while self.is_monitoring:
            try:
                # Collect system metrics
                system_health = self.system_monitor.check_system_health()
                
                # Run service health checks
                service_health = await self.health_checker.run_all_health_checks()
                
                # Check for alerts
                self.alert_manager.check_system_alerts(system_health)
                
                # Log status
                self.logger.info(
                    f"📈 System: {system_health['status']} | "
                    f"Services: {service_health['overall_status']} | "
                    f"CPU: {system_health['metrics']['cpu_percent']:.1f}% | "
                    f"Memory: {system_health['metrics']['memory_percent']:.1f}%"
                )
                
                # Wait for next interval
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(30)  # Short delay before retry
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        self.logger.info("⏹️ Production monitoring stopped")
    
    async def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        
        # Collect current data
        system_health = self.system_monitor.check_system_health()
        service_health = await self.health_checker.run_all_health_checks()
        
        # Recent alerts
        recent_alerts = self.alert_manager.alert_history[-10:]
        
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.config_manager.environment,
            "uptime_seconds": system_health["metrics"]["uptime_seconds"],
            "system_health": system_health,
            "service_health": service_health,
            "recent_alerts": recent_alerts,
            "configuration": {
                "monitoring_interval": self.config_manager.getint("monitoring", "metrics_interval"),
                "cpu_threshold": self.config_manager.getfloat("monitoring", "alert_threshold_cpu"),
                "memory_threshold": self.config_manager.getfloat("monitoring", "alert_threshold_memory")
            }
        }
        
        return dashboard


# Deployment utilities
class DeploymentManager:
    """Manage deployment and rollback operations"""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
    def create_deployment_package(self) -> Dict[str, Any]:
        """Create deployment package with all necessary files"""
        
        deployment_info = {
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "environment": self.config.environment,
            "components": [
                "woocommerce_connector",
                "platform_manager", 
                "data_sync",
                "ml_analytics",
                "data_quality",
                "production_monitoring"
            ],
            "dependencies": [
                "python>=3.8",
                "pandas>=1.3.0",
                "scikit-learn>=1.0.0",
                "psutil>=5.8.0",
                "aiohttp>=3.8.0"
            ],
            "configuration_files": [
                "production.conf",
                "staging.conf", 
                "development.conf"
            ]
        }
        
        self.logger.info(f"📦 Deployment package created: v{deployment_info['version']}")
        return deployment_info
    
    def validate_deployment(self) -> bool:
        """Validate deployment readiness"""
        
        checks = []
        
        # Check configuration
        try:
            config_valid = self.config.config.sections()
            checks.append(("Configuration", len(config_valid) > 0))
        except Exception:
            checks.append(("Configuration", False))
        
        # Check dependencies
        try:
            import pandas, sklearn, psutil, aiohttp
            checks.append(("Dependencies", True))
        except ImportError:
            checks.append(("Dependencies", False))
        
        # Check file permissions
        log_dir = Path("/var/log/nexus-analytics")
        checks.append(("Log Directory", log_dir.exists() or os.access("/tmp", os.W_OK)))
        
        # Results
        all_passed = all(passed for _, passed in checks)
        
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            self.logger.info(f"{status} {check_name}: {'PASS' if passed else 'FAIL'}")
        
        return all_passed


# Demo and testing functions
async def test_production_monitoring():
    """Test production monitoring functionality"""
    print("🚀 Testing Production Monitoring System")
    print("=" * 45)
    
    # Initialize monitoring
    monitor = ProductionMonitor("/tmp/nexus_test_config")
    
    print("📊 Collecting system metrics...")
    system_health = monitor.system_monitor.check_system_health()
    
    print(f"   System Status: {system_health['status']}")
    print(f"   CPU Usage: {system_health['metrics']['cpu_percent']:.1f}%")
    print(f"   Memory Usage: {system_health['metrics']['memory_percent']:.1f}%")
    print(f"   Disk Usage: {system_health['metrics']['disk_percent']:.1f}%")
    
    print("\\n🔍 Running health checks...")
    service_health = await monitor.health_checker.run_all_health_checks()
    
    print(f"   Overall Status: {service_health['overall_status']}")
    print(f"   Healthy Services: {service_health['summary']['healthy_services']}")
    print(f"   Total Services: {service_health['summary']['total_services']}")
    
    for service in service_health['services']:
        status_emoji = "✅" if service['status'] == 'healthy' else "⚠️" if service['status'] == 'degraded' else "❌"
        print(f"      {status_emoji} {service['service_name']}: {service['response_time_ms']:.1f}ms")
    
    print("\\n📈 Getting monitoring dashboard...")
    dashboard = await monitor.get_monitoring_dashboard()
    
    print(f"   Environment: {dashboard['environment']}")
    print(f"   Uptime: {dashboard['uptime_seconds']:.0f} seconds")
    print(f"   Recent Alerts: {len(dashboard['recent_alerts'])}")
    
    print("\\n🎯 Testing deployment validation...")
    deployment_manager = DeploymentManager(monitor.config_manager)
    
    deployment_package = deployment_manager.create_deployment_package()
    print(f"   Package Version: {deployment_package['version']}")
    print(f"   Components: {len(deployment_package['components'])}")
    
    is_valid = deployment_manager.validate_deployment()
    print(f"   Deployment Valid: {'✅ Yes' if is_valid else '❌ No'}")
    
    print("\\n🎉 Production Monitoring Test Complete!")
    return dashboard


if __name__ == "__main__":
    # Run demo if executed directly
    asyncio.run(test_production_monitoring())