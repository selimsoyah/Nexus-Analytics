"""
Multi-Platform Integration Manager for Nexus Analytics
=====================================================

Unified management system for all e-commerce platform integrations.
Supports WooCommerce, Shopify, Magento, and custom platform connectors.

Features:
- Platform registry and discovery
- Unified authentication management
- Cross-platform data synchronization
- Shared configuration and credentials
- Platform-agnostic analytics pipeline

Author: Nexus Analytics Team
Version: 1.0.0
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# Import platform-specific connectors
from .woocommerce_connector import WooCommerceConnector
from .woocommerce_schema_mapper import WooCommerceSchemaMapper
from .woocommerce_data_sync import WooCommerceDataSyncManager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """Supported e-commerce platforms"""
    WOOCOMMERCE = "woocommerce"
    SHOPIFY = "shopify"
    MAGENTO = "magento"
    BIGCOMMERCE = "bigcommerce"
    CUSTOM = "custom"


class IntegrationStatus(Enum):
    """Integration status states"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SYNCING = "syncing"
    PENDING = "pending"


@dataclass
class PlatformConfig:
    """Configuration for a platform integration"""
    platform_id: str
    platform_type: PlatformType
    store_name: str
    api_endpoint: str
    credentials: Dict[str, str]
    sync_settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_sync: Optional[datetime] = None
    status: IntegrationStatus = IntegrationStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncSummary:
    """Summary of cross-platform synchronization"""
    total_platforms: int
    successful_syncs: int
    failed_syncs: int
    total_records: Dict[str, int]  # {data_type: count}
    sync_duration: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BasePlatformConnector:
    """Base class for all platform connectors"""
    
    def __init__(self, config: PlatformConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.platform_type.value}")
    
    async def test_connection(self) -> bool:
        """Test platform connection"""
        raise NotImplementedError("Subclasses must implement test_connection")
    
    async def sync_data(self, data_types: List[str] = None) -> Dict[str, Any]:
        """Synchronize data from platform"""
        raise NotImplementedError("Subclasses must implement sync_data")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        raise NotImplementedError("Subclasses must implement get_sync_status")


class WooCommercePlatformConnector(BasePlatformConnector):
    """WooCommerce platform connector wrapper"""
    
    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        
        # Initialize WooCommerce connector directly with credentials
        if config.credentials and config.credentials.get('consumer_key'):
            try:
                self.woo_connector = WooCommerceConnector(
                    store_url=config.api_endpoint,
                    consumer_key=config.credentials.get('consumer_key'),
                    consumer_secret=config.credentials.get('consumer_secret')
                )
                self.woo_sync = WooCommerceDataSyncManager(config.platform_id)
                self.logger.info(f"✅ WooCommerce connector initialized for {config.store_name}")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize WooCommerce connector: {e}")
                self.woo_connector = None
                self.woo_sync = None
        else:
            self.logger.warning("⚠️ No WooCommerce credentials provided")
            self.woo_connector = None
            self.woo_sync = None
    
    async def test_connection(self) -> bool:
        """Test WooCommerce connection"""
        if not self.woo_connector:
            self.logger.error("WooCommerce connector not initialized")
            return False
        
        try:
            result = await asyncio.to_thread(self.woo_connector.test_connection)
            return result.get('status') == 'success'
        except Exception as e:
            self.logger.error(f"WooCommerce connection test failed: {e}")
            return False
    
    async def sync_data(self, data_types: List[str] = None) -> Dict[str, Any]:
        """Synchronize WooCommerce data"""
        if not self.woo_sync:
            return {"status": "error", "error": "WooCommerce sync manager not initialized"}
        
        try:
            return await self.woo_sync.sync_full_store()
        except Exception as e:
            self.logger.error(f"WooCommerce sync failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get WooCommerce sync status"""
        if not self.woo_sync:
            return {"is_syncing": False, "connection_status": "not_initialized"}
        
        return self.woo_sync.get_sync_status()


class ShopifyPlatformConnector(BasePlatformConnector):
    """Shopify platform connector (placeholder for future implementation)"""
    
    async def test_connection(self) -> bool:
        self.logger.info("Shopify connector - coming soon!")
        return False
    
    async def sync_data(self, data_types: List[str] = None) -> Dict[str, Any]:
        return {"status": "not_implemented", "message": "Shopify integration coming soon"}
    
    def get_sync_status(self) -> Dict[str, Any]:
        return {"is_syncing": False, "connection_status": "not_implemented"}


class MagentoPlatformConnector(BasePlatformConnector):
    """Magento platform connector (placeholder for future implementation)"""
    
    async def test_connection(self) -> bool:
        self.logger.info("Magento connector - coming soon!")
        return False
    
    async def sync_data(self, data_types: List[str] = None) -> Dict[str, Any]:
        return {"status": "not_implemented", "message": "Magento integration coming soon"}
    
    def get_sync_status(self) -> Dict[str, Any]:
        return {"is_syncing": False, "connection_status": "not_implemented"}


class PlatformIntegrationManager:
    """
    Unified manager for all e-commerce platform integrations
    
    Features:
    - Multi-platform registration and management
    - Unified authentication and configuration
    - Cross-platform data synchronization
    - Analytics data aggregation
    - Error handling and monitoring
    """
    
    CONNECTOR_MAP = {
        PlatformType.WOOCOMMERCE: WooCommercePlatformConnector,
        PlatformType.SHOPIFY: ShopifyPlatformConnector,
        PlatformType.MAGENTO: MagentoPlatformConnector,
    }
    
    def __init__(self, config_dir: str = "/tmp/nexus_integrations"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.platforms: Dict[str, PlatformConfig] = {}
        self.connectors: Dict[str, BasePlatformConnector] = {}
        self.sync_history: List[SyncSummary] = []
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🔧 Platform Integration Manager initialized")
        
        # Load existing configurations
        self._load_configurations()
    
    def register_platform(
        self, 
        platform_id: str, 
        platform_type: PlatformType, 
        store_name: str,
        api_endpoint: str, 
        credentials: Dict[str, str],
        sync_settings: Dict[str, Any] = None
    ) -> bool:
        """Register a new platform integration"""
        try:
            config = PlatformConfig(
                platform_id=platform_id,
                platform_type=platform_type,
                store_name=store_name,
                api_endpoint=api_endpoint,
                credentials=credentials,
                sync_settings=sync_settings or {}
            )
            
            # Create connector instance
            connector_class = self.CONNECTOR_MAP.get(platform_type)
            if not connector_class:
                raise ValueError(f"Unsupported platform type: {platform_type}")
            
            connector = connector_class(config)
            
            # Store configuration and connector
            self.platforms[platform_id] = config
            self.connectors[platform_id] = connector
            
            # Save configuration
            self._save_configuration(config)
            
            self.logger.info(f"✅ Registered {platform_type.value} platform: {store_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to register platform {platform_id}: {e}")
            return False
    
    def unregister_platform(self, platform_id: str) -> bool:
        """Remove a platform integration"""
        try:
            if platform_id in self.platforms:
                # Remove from memory
                del self.platforms[platform_id]
                if platform_id in self.connectors:
                    del self.connectors[platform_id]
                
                # Remove config file
                config_file = self.config_dir / f"{platform_id}.json"
                if config_file.exists():
                    config_file.unlink()
                
                self.logger.info(f"🗑️ Unregistered platform: {platform_id}")
                return True
            else:
                self.logger.warning(f"Platform not found: {platform_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to unregister platform {platform_id}: {e}")
            return False
    
    def list_platforms(self) -> Dict[str, Dict[str, Any]]:
        """Get list of all registered platforms"""
        platform_list = {}
        
        for platform_id, config in self.platforms.items():
            connector = self.connectors.get(platform_id)
            status_info = connector.get_sync_status() if connector else {}
            
            platform_list[platform_id] = {
                "platform_type": config.platform_type.value,
                "store_name": config.store_name,
                "api_endpoint": config.api_endpoint,
                "status": config.status.value,
                "created_at": config.created_at.isoformat(),
                "last_sync": config.last_sync.isoformat() if config.last_sync else None,
                "sync_status": status_info,
                "metadata": config.metadata
            }
        
        return platform_list
    
    async def test_platform_connection(self, platform_id: str) -> bool:
        """Test connection for a specific platform"""
        if platform_id not in self.connectors:
            self.logger.error(f"Platform not found: {platform_id}")
            return False
        
        try:
            connector = self.connectors[platform_id]
            is_connected = await connector.test_connection()
            
            # Update platform status
            config = self.platforms[platform_id]
            config.status = IntegrationStatus.ACTIVE if is_connected else IntegrationStatus.ERROR
            
            self.logger.info(f"🔗 Connection test {platform_id}: {'✅ Success' if is_connected else '❌ Failed'}")
            return is_connected
            
        except Exception as e:
            self.logger.error(f"❌ Connection test failed for {platform_id}: {e}")
            return False
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Test connections for all registered platforms"""
        results = {}
        
        for platform_id in self.platforms.keys():
            results[platform_id] = await self.test_platform_connection(platform_id)
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        self.logger.info(f"🔗 Connection tests completed: {success_count}/{total_count} successful")
        return results
    
    async def sync_platform(self, platform_id: str, data_types: List[str] = None) -> Dict[str, Any]:
        """Synchronize data for a specific platform"""
        if platform_id not in self.connectors:
            return {"status": "error", "error": f"Platform not found: {platform_id}"}
        
        try:
            # Update platform status
            config = self.platforms[platform_id]
            config.status = IntegrationStatus.SYNCING
            
            # Perform sync
            connector = self.connectors[platform_id]
            result = await connector.sync_data(data_types)
            
            # Update status based on result
            config.status = IntegrationStatus.ACTIVE if result.get('status') == 'success' else IntegrationStatus.ERROR
            config.last_sync = datetime.now()
            
            self.logger.info(f"🔄 Sync completed for {platform_id}: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            config = self.platforms[platform_id]
            config.status = IntegrationStatus.ERROR
            error_msg = f"Sync failed for {platform_id}: {e}"
            self.logger.error(f"❌ {error_msg}")
            return {"status": "error", "error": error_msg}
    
    async def sync_all_platforms(self, data_types: List[str] = None) -> SyncSummary:
        """Synchronize data across all registered platforms"""
        start_time = datetime.now()
        
        total_platforms = len(self.platforms)
        successful_syncs = 0
        failed_syncs = 0
        total_records = {}
        errors = []
        warnings = []
        
        self.logger.info(f"🚀 Starting cross-platform sync for {total_platforms} platforms...")
        
        # Sync each platform
        for platform_id in self.platforms.keys():
            try:
                result = await self.sync_platform(platform_id, data_types)
                
                if result.get('status') == 'success':
                    successful_syncs += 1
                    
                    # Aggregate record counts
                    sync_stats = result.get('sync_statistics', {})
                    for key, value in sync_stats.items():
                        if isinstance(value, int):
                            total_records[key] = total_records.get(key, 0) + value
                else:
                    failed_syncs += 1
                    errors.append(f"{platform_id}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                failed_syncs += 1
                errors.append(f"{platform_id}: {str(e)}")
        
        # Create sync summary
        duration = (datetime.now() - start_time).total_seconds()
        summary = SyncSummary(
            total_platforms=total_platforms,
            successful_syncs=successful_syncs,
            failed_syncs=failed_syncs,
            total_records=total_records,
            sync_duration=duration,
            errors=errors,
            warnings=warnings
        )
        
        # Store sync history
        self.sync_history.append(summary)
        
        self.logger.info(f"✅ Cross-platform sync completed: {successful_syncs}/{total_platforms} successful")
        return summary
    
    def get_platform_analytics(self) -> Dict[str, Any]:
        """Get analytics across all platforms"""
        analytics = {
            "platform_summary": {
                "total_platforms": len(self.platforms),
                "active_platforms": sum(1 for config in self.platforms.values() 
                                      if config.status == IntegrationStatus.ACTIVE),
                "platform_types": {}
            },
            "sync_history": [],
            "recent_activity": {}
        }
        
        # Count platform types
        for config in self.platforms.values():
            platform_type = config.platform_type.value
            analytics["platform_summary"]["platform_types"][platform_type] = \
                analytics["platform_summary"]["platform_types"].get(platform_type, 0) + 1
        
        # Recent sync history
        analytics["sync_history"] = [
            {
                "total_platforms": summary.total_platforms,
                "successful_syncs": summary.successful_syncs,
                "failed_syncs": summary.failed_syncs,
                "total_records": summary.total_records,
                "sync_duration": summary.sync_duration,
                "errors": summary.errors
            }
            for summary in self.sync_history[-10:]  # Last 10 syncs
        ]
        
        return analytics
    
    def _load_configurations(self):
        """Load platform configurations from disk"""
        try:
            config_files = list(self.config_dir.glob("*.json"))
            
            for config_file in config_files:
                try:
                    with open(config_file, 'r') as f:
                        data = json.load(f)
                    
                    # Reconstruct PlatformConfig
                    config = PlatformConfig(
                        platform_id=data['platform_id'],
                        platform_type=PlatformType(data['platform_type']),
                        store_name=data['store_name'],
                        api_endpoint=data['api_endpoint'],
                        credentials=data['credentials'],
                        sync_settings=data.get('sync_settings', {}),
                        created_at=datetime.fromisoformat(data['created_at']),
                        last_sync=datetime.fromisoformat(data['last_sync']) if data.get('last_sync') else None,
                        status=IntegrationStatus(data.get('status', 'pending')),
                        metadata=data.get('metadata', {})
                    )
                    
                    # Create connector
                    connector_class = self.CONNECTOR_MAP.get(config.platform_type)
                    if connector_class:
                        connector = connector_class(config)
                        self.connectors[config.platform_id] = connector
                    
                    self.platforms[config.platform_id] = config
                    
                except Exception as e:
                    self.logger.error(f"Failed to load config {config_file}: {e}")
            
            self.logger.info(f"📁 Loaded {len(self.platforms)} platform configurations")
            
        except Exception as e:
            self.logger.error(f"Failed to load configurations: {e}")
    
    def _save_configuration(self, config: PlatformConfig):
        """Save platform configuration to disk"""
        try:
            config_file = self.config_dir / f"{config.platform_id}.json"
            
            data = {
                "platform_id": config.platform_id,
                "platform_type": config.platform_type.value,
                "store_name": config.store_name,
                "api_endpoint": config.api_endpoint,
                "credentials": config.credentials,
                "sync_settings": config.sync_settings,
                "created_at": config.created_at.isoformat(),
                "last_sync": config.last_sync.isoformat() if config.last_sync else None,
                "status": config.status.value,
                "metadata": config.metadata
            }
            
            with open(config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")


# Demo and testing functions
def create_demo_platform_manager() -> Dict[str, Any]:
    """Create demo platform manager with sample integrations"""
    try:
        manager = PlatformIntegrationManager()
        
        # Register demo WooCommerce store
        woo_success = manager.register_platform(
            platform_id="demo-woo-store",
            platform_type=PlatformType.WOOCOMMERCE,
            store_name="Demo WooCommerce Store",
            api_endpoint="https://demo-woo.nexusanalytics.com",
            credentials={
                "consumer_key": "ck_demo12345",
                "consumer_secret": "cs_demo67890"
            },
            sync_settings={
                "auto_sync": True,
                "sync_interval": 3600,  # 1 hour
                "data_types": ["products", "customers", "orders"]
            }
        )
        
        # Register placeholder Shopify store
        shopify_success = manager.register_platform(
            platform_id="demo-shopify-store",
            platform_type=PlatformType.SHOPIFY,
            store_name="Demo Shopify Store",
            api_endpoint="https://demo-shop.myshopify.com",
            credentials={
                "api_key": "demo_api_key",
                "api_secret": "demo_api_secret"
            }
        )
        
        # Get platform analytics
        analytics = manager.get_platform_analytics()
        
        return {
            "status": "success",
            "manager": manager,
            "registrations": {
                "woocommerce": woo_success,
                "shopify": shopify_success
            },
            "analytics": analytics,
            "platforms": manager.list_platforms()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "manager": None
        }


async def test_multi_platform_sync():
    """Test cross-platform synchronization"""
    print("🔄 Testing Multi-Platform Integration Manager")
    print("=" * 50)
    
    # Create demo manager
    demo_result = create_demo_platform_manager()
    
    if demo_result["status"] != "success":
        print(f"❌ Failed to create demo manager: {demo_result['error']}")
        return
    
    manager = demo_result["manager"]
    
    print("✅ Platform Manager Created:")
    platforms = demo_result["platforms"]
    for platform_id, info in platforms.items():
        print(f"   📱 {info['store_name']} ({info['platform_type']})")
        print(f"      Status: {info['status']}")
        print(f"      Endpoint: {info['api_endpoint']}")
    
    # Test connections
    print("\n🔗 Testing Platform Connections...")
    connection_results = await manager.test_all_connections()
    
    for platform_id, success in connection_results.items():
        status = "✅ Connected" if success else "❌ Failed"
        print(f"   {platform_id}: {status}")
    
    # Test synchronization for WooCommerce (only active platform)
    print("\n🔄 Testing Platform Synchronization...")
    sync_summary = await manager.sync_all_platforms()
    
    print(f"   Total Platforms: {sync_summary.total_platforms}")
    print(f"   Successful Syncs: {sync_summary.successful_syncs}")
    print(f"   Failed Syncs: {sync_summary.failed_syncs}")
    print(f"   Duration: {sync_summary.sync_duration:.2f}s")
    
    if sync_summary.total_records:
        print("   Records Synchronized:")
        for data_type, count in sync_summary.total_records.items():
            print(f"      {data_type}: {count}")
    
    if sync_summary.errors:
        print("   Errors:")
        for error in sync_summary.errors:
            print(f"      ❌ {error}")
    
    # Get final analytics
    print("\n📊 Platform Analytics:")
    analytics = manager.get_platform_analytics()
    summary = analytics["platform_summary"]
    
    print(f"   Total Platforms: {summary['total_platforms']}")
    print(f"   Active Platforms: {summary['active_platforms']}")
    print(f"   Platform Types: {summary['platform_types']}")
    
    print("\n🎉 Multi-Platform Integration Manager Ready!")
    return manager


if __name__ == "__main__":
    # Run demo if executed directly
    asyncio.run(test_multi_platform_sync())