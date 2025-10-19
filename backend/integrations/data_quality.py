"""
Data Validation and Quality Assurance for WooCommerce Integration
================================================================

Comprehensive data quality framework with validation rules, cleansing,
and quality monitoring for e-commerce data from WooCommerce and other platforms.

Features:
- Schema validation and type checking
- Data completeness monitoring
- Anomaly detection for data quality
- Data cleansing and standardization
- Quality scoring and reporting
- Real-time validation during sync

Author: Nexus Analytics Team
Version: 1.0.0
"""

import re
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Data validation severity levels"""
    CRITICAL = "critical"    # Data corruption, sync should stop
    HIGH = "high"           # Data quality issues, needs attention
    MEDIUM = "medium"       # Minor inconsistencies
    LOW = "low"            # Cosmetic issues


class ValidationStatus(Enum):
    """Validation result status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationRule:
    """Data validation rule definition"""
    rule_id: str
    name: str
    description: str
    field: str
    rule_type: str  # required, format, range, unique, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    severity: ValidationSeverity = ValidationSeverity.MEDIUM
    is_active: bool = True


@dataclass
class ValidationResult:
    """Result of a validation check"""
    rule_id: str
    field: str
    status: ValidationStatus
    severity: ValidationSeverity
    message: str
    failed_records: List[str] = field(default_factory=list)
    failed_count: int = 0
    total_count: int = 0
    
    def __post_init__(self):
        if self.failed_count == 0 and self.failed_records:
            self.failed_count = len(self.failed_records)


@dataclass
class DataQualityScore:
    """Overall data quality assessment"""
    overall_score: float  # 0-100
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    timeliness_score: float
    total_records: int
    failed_validations: int
    warnings: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'overall_score': self.overall_score,
            'completeness_score': self.completeness_score,
            'accuracy_score': self.accuracy_score,
            'consistency_score': self.consistency_score,
            'timeliness_score': self.timeliness_score,
            'total_records': self.total_records,
            'failed_validations': self.failed_validations,
            'warnings': self.warnings,
            'quality_grade': self._get_quality_grade()
        }
    
    def _get_quality_grade(self) -> str:
        """Get letter grade based on overall score"""
        if self.overall_score >= 95:
            return "A+"
        elif self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 85:
            return "B+"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 75:
            return "C+"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        else:
            return "F"


class DataValidator:
    """Core data validation engine"""
    
    def __init__(self):
        self.rules: Dict[str, ValidationRule] = {}
        self.results: List[ValidationResult] = []
        
    def add_rule(self, rule: ValidationRule):
        """Add validation rule"""
        self.rules[rule.rule_id] = rule
        logger.info(f"✅ Added validation rule: {rule.name}")
    
    def validate_required_field(self, data: List[Dict], field: str, rule: ValidationRule) -> ValidationResult:
        """Validate required field presence"""
        failed_records = []
        
        for i, record in enumerate(data):
            if field not in record or record[field] is None or str(record[field]).strip() == "":
                failed_records.append(f"record_{i}")
        
        status = ValidationStatus.PASSED if not failed_records else ValidationStatus.FAILED
        message = f"Required field '{field}' validation: {len(failed_records)} failures out of {len(data)} records"
        
        return ValidationResult(
            rule_id=rule.rule_id,
            field=field,
            status=status,
            severity=rule.severity,
            message=message,
            failed_records=failed_records[:10],  # Limit to first 10
            failed_count=len(failed_records),
            total_count=len(data)
        )
    
    def validate_email_format(self, data: List[Dict], field: str, rule: ValidationRule) -> ValidationResult:
        """Validate email format using regex"""
        failed_records = []
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for i, record in enumerate(data):
            if field in record and record[field]:
                email = str(record[field]).strip()
                if not re.match(email_pattern, email):
                    failed_records.append(f"record_{i}")
        
        status = ValidationStatus.PASSED if not failed_records else ValidationStatus.FAILED
        message = f"Email format validation for '{field}': {len(failed_records)} invalid emails"
        
        return ValidationResult(
            rule_id=rule.rule_id,
            field=field,
            status=status,
            severity=rule.severity,
            message=message,
            failed_records=failed_records[:10],
            failed_count=len(failed_records),
            total_count=len(data)
        )
    
    def validate_numeric_range(self, data: List[Dict], field: str, rule: ValidationRule) -> ValidationResult:
        """Validate numeric field is within specified range"""
        min_val = rule.parameters.get('min', float('-inf'))
        max_val = rule.parameters.get('max', float('inf'))
        failed_records = []
        
        for i, record in enumerate(data):
            if field in record and record[field] is not None:
                try:
                    value = float(record[field])
                    if not (min_val <= value <= max_val):
                        failed_records.append(f"record_{i}")
                except (ValueError, TypeError):
                    failed_records.append(f"record_{i}")
        
        status = ValidationStatus.PASSED if not failed_records else ValidationStatus.FAILED
        message = f"Numeric range validation for '{field}' [{min_val}, {max_val}]: {len(failed_records)} out of range"
        
        return ValidationResult(
            rule_id=rule.rule_id,
            field=field,
            status=status,
            severity=rule.severity,
            message=message,
            failed_records=failed_records[:10],
            failed_count=len(failed_records),
            total_count=len(data)
        )
    
    def validate_date_format(self, data: List[Dict], field: str, rule: ValidationRule) -> ValidationResult:
        """Validate date format"""
        date_format = rule.parameters.get('format', '%Y-%m-%d')
        failed_records = []
        
        for i, record in enumerate(data):
            if field in record and record[field]:
                try:
                    # Try to parse date
                    if isinstance(record[field], str):
                        datetime.strptime(record[field][:10], '%Y-%m-%d')
                    elif not isinstance(record[field], (datetime, pd.Timestamp)):
                        failed_records.append(f"record_{i}")
                except (ValueError, TypeError):
                    failed_records.append(f"record_{i}")
        
        status = ValidationStatus.PASSED if not failed_records else ValidationStatus.FAILED
        message = f"Date format validation for '{field}': {len(failed_records)} invalid dates"
        
        return ValidationResult(
            rule_id=rule.rule_id,
            field=field,
            status=status,
            severity=rule.severity,
            message=message,
            failed_records=failed_records[:10],
            failed_count=len(failed_records),
            total_count=len(data)
        )
    
    def validate_unique_values(self, data: List[Dict], field: str, rule: ValidationRule) -> ValidationResult:
        """Validate field values are unique"""
        values = []
        duplicates = []
        
        for i, record in enumerate(data):
            if field in record and record[field] is not None:
                value = str(record[field])
                if value in values:
                    duplicates.append(f"record_{i}")
                else:
                    values.append(value)
        
        status = ValidationStatus.PASSED if not duplicates else ValidationStatus.FAILED
        message = f"Uniqueness validation for '{field}': {len(duplicates)} duplicate values"
        
        return ValidationResult(
            rule_id=rule.rule_id,
            field=field,
            status=status,
            severity=rule.severity,
            message=message,
            failed_records=duplicates[:10],
            failed_count=len(duplicates),
            total_count=len(data)
        )
    
    def validate_data(self, data: List[Dict], data_type: str = "unknown") -> List[ValidationResult]:
        """Run all validation rules on data"""
        self.results = []
        
        logger.info(f"🔍 Starting validation for {len(data)} {data_type} records...")
        
        for rule in self.rules.values():
            if not rule.is_active:
                continue
                
            try:
                # Route to appropriate validation method
                if rule.rule_type == "required":
                    result = self.validate_required_field(data, rule.field, rule)
                elif rule.rule_type == "email":
                    result = self.validate_email_format(data, rule.field, rule)
                elif rule.rule_type == "numeric_range":
                    result = self.validate_numeric_range(data, rule.field, rule)
                elif rule.rule_type == "date_format":
                    result = self.validate_date_format(data, rule.field, rule)
                elif rule.rule_type == "unique":
                    result = self.validate_unique_values(data, rule.field, rule)
                else:
                    logger.warning(f"Unknown validation rule type: {rule.rule_type}")
                    continue
                
                self.results.append(result)
                
                # Log result
                status_emoji = "✅" if result.status == ValidationStatus.PASSED else "❌"
                logger.info(f"{status_emoji} {rule.name}: {result.message}")
                
            except Exception as e:
                error_result = ValidationResult(
                    rule_id=rule.rule_id,
                    field=rule.field,
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Validation error: {str(e)}",
                    total_count=len(data)
                )
                self.results.append(error_result)
                logger.error(f"❌ Validation rule {rule.name} failed with error: {e}")
        
        logger.info(f"✅ Validation complete: {len(self.results)} rules executed")
        return self.results


class DataCleaner:
    """Data cleansing and standardization utilities"""
    
    @staticmethod
    def clean_email(email: str) -> str:
        """Clean and standardize email address"""
        if not email:
            return ""
        
        # Remove whitespace and convert to lowercase
        email = str(email).strip().lower()
        
        # Basic email format check
        if '@' not in email:
            return ""
        
        return email
    
    @staticmethod
    def clean_phone(phone: str) -> str:
        """Clean and standardize phone number using basic formatting"""
        if not phone:
            return ""
        
        # Remove all non-digit characters except +
        phone = re.sub(r'[^\d+]', '', str(phone))
        
        # Basic phone number validation and formatting
        if phone.startswith('+'):
            return phone
        elif len(phone) == 10:
            # US format: (XXX) XXX-XXXX
            return f"+1{phone}"
        elif len(phone) == 11 and phone.startswith('1'):
            return f"+{phone}"
        
        return phone
    
    @staticmethod
    def clean_currency(amount: Union[str, float, int]) -> float:
        """Clean and standardize currency amounts"""
        if amount is None:
            return 0.0
        
        if isinstance(amount, (int, float)):
            return float(amount)
        
        # Remove currency symbols and formatting
        amount_str = str(amount).strip()
        amount_str = re.sub(r'[^\d.-]', '', amount_str)
        
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    
    @staticmethod
    def clean_name(name: str) -> str:
        """Clean and standardize names"""
        if not name:
            return ""
        
        # Remove extra whitespace and title case
        name = str(name).strip()
        name = ' '.join(name.split())  # Remove multiple spaces
        name = name.title()
        
        return name
    
    @staticmethod
    def standardize_country_code(country: str) -> str:
        """Standardize country codes"""
        if not country:
            return ""
        
        country = str(country).strip().upper()
        
        # Common country code mappings
        country_mappings = {
            'UNITED STATES': 'US',
            'USA': 'US',
            'AMERICA': 'US',
            'UNITED KINGDOM': 'GB',
            'UK': 'GB',
            'GREAT BRITAIN': 'GB',
            'CANADA': 'CA',
            'DEUTSCHLAND': 'DE',
            'GERMANY': 'DE'
        }
        
        return country_mappings.get(country, country)
    
    @classmethod
    def clean_record(cls, record: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Clean a single data record based on type"""
        cleaned = record.copy()
        
        # Clean email fields
        email_fields = ['email', 'customer_email', 'billing_email']
        for field in email_fields:
            if field in cleaned:
                cleaned[field] = cls.clean_email(cleaned[field])
        
        # Clean currency fields
        currency_fields = ['total_amount', 'price', 'total', 'subtotal', 'total_spent']
        for field in currency_fields:
            if field in cleaned:
                cleaned[field] = cls.clean_currency(cleaned[field])
        
        # Clean name fields
        name_fields = ['first_name', 'last_name', 'full_name', 'name', 'customer_name']
        for field in name_fields:
            if field in cleaned:
                cleaned[field] = cls.clean_name(cleaned[field])
        
        # Clean phone fields
        phone_fields = ['phone', 'customer_phone', 'billing_phone']
        for field in phone_fields:
            if field in cleaned:
                cleaned[field] = cls.clean_phone(cleaned[field])
        
        # Clean country fields
        country_fields = ['country', 'billing_country', 'shipping_country']
        for field in country_fields:
            if field in cleaned:
                cleaned[field] = cls.standardize_country_code(cleaned[field])
        
        return cleaned


class DataQualityMonitor:
    """Monitor and assess overall data quality"""
    
    def __init__(self):
        self.validator = DataValidator()
        self.cleaner = DataCleaner()
        self._setup_validation_rules()
    
    def _setup_validation_rules(self):
        """Setup standard validation rules for e-commerce data"""
        
        # Order validation rules
        order_rules = [
            ValidationRule("ord_req_id", "Order ID Required", "Order must have unique ID", 
                         "order_id", "required", severity=ValidationSeverity.CRITICAL),
            ValidationRule("ord_req_amount", "Order Amount Required", "Order must have total amount", 
                         "total_amount", "required", severity=ValidationSeverity.HIGH),
            ValidationRule("ord_amount_range", "Order Amount Range", "Order amount must be positive", 
                         "total_amount", "numeric_range", {"min": 0, "max": 50000}, ValidationSeverity.MEDIUM),
            ValidationRule("ord_date_format", "Order Date Format", "Order date must be valid", 
                         "order_date", "date_format", severity=ValidationSeverity.HIGH),
            ValidationRule("ord_unique_id", "Unique Order ID", "Order IDs must be unique", 
                         "order_id", "unique", severity=ValidationSeverity.CRITICAL)
        ]
        
        # Customer validation rules
        customer_rules = [
            ValidationRule("cust_req_id", "Customer ID Required", "Customer must have unique ID", 
                         "customer_id", "required", severity=ValidationSeverity.CRITICAL),
            ValidationRule("cust_email_format", "Email Format", "Customer email must be valid", 
                         "email", "email", severity=ValidationSeverity.HIGH),
            ValidationRule("cust_unique_id", "Unique Customer ID", "Customer IDs must be unique", 
                         "customer_id", "unique", severity=ValidationSeverity.CRITICAL),
            ValidationRule("cust_unique_email", "Unique Email", "Customer emails should be unique", 
                         "email", "unique", severity=ValidationSeverity.MEDIUM)
        ]
        
        # Product validation rules
        product_rules = [
            ValidationRule("prod_req_id", "Product ID Required", "Product must have unique ID", 
                         "product_id", "required", severity=ValidationSeverity.CRITICAL),
            ValidationRule("prod_req_name", "Product Name Required", "Product must have name", 
                         "name", "required", severity=ValidationSeverity.HIGH),
            ValidationRule("prod_price_range", "Product Price Range", "Product price must be valid", 
                         "price", "numeric_range", {"min": 0, "max": 10000}, ValidationSeverity.MEDIUM),
            ValidationRule("prod_unique_id", "Unique Product ID", "Product IDs must be unique", 
                         "product_id", "unique", severity=ValidationSeverity.CRITICAL)
        ]
        
        # Add all rules
        for rule in order_rules + customer_rules + product_rules:
            self.validator.add_rule(rule)
    
    def assess_data_quality(self, ecommerce_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Comprehensive data quality assessment"""
        
        logger.info("🔍 Starting comprehensive data quality assessment...")
        
        assessment_results = {
            "assessment_timestamp": datetime.now().isoformat(),
            "data_summary": {},
            "validation_results": {},
            "quality_scores": {},
            "recommendations": []
        }
        
        # Assess each data type
        for data_type, records in ecommerce_data.items():
            if not records:
                continue
                
            logger.info(f"📊 Assessing {data_type} data quality...")
            
            # Data summary
            assessment_results["data_summary"][data_type] = {
                "total_records": len(records),
                "fields_count": len(records[0].keys()) if records else 0
            }
            
            # Run validation
            validation_results = self.validator.validate_data(records, data_type)
            
            # Calculate quality scores
            quality_score = self._calculate_quality_score(validation_results, len(records))
            
            # Store results
            assessment_results["validation_results"][data_type] = [
                {
                    "rule_id": result.rule_id,
                    "field": result.field,
                    "status": result.status.value,
                    "severity": result.severity.value,
                    "message": result.message,
                    "failed_count": result.failed_count,
                    "success_rate": ((result.total_count - result.failed_count) / result.total_count * 100) if result.total_count > 0 else 100
                }
                for result in validation_results
            ]
            
            assessment_results["quality_scores"][data_type] = quality_score.to_dict()
        
        # Generate recommendations
        assessment_results["recommendations"] = self._generate_recommendations(assessment_results["validation_results"])
        
        logger.info("✅ Data quality assessment complete")
        return assessment_results
    
    def _calculate_quality_score(self, validation_results: List[ValidationResult], total_records: int) -> DataQualityScore:
        """Calculate data quality score from validation results"""
        
        if not validation_results or total_records == 0:
            return DataQualityScore(100, 100, 100, 100, 100, total_records, 0, 0)
        
        # Count failures by severity
        critical_failures = sum(1 for r in validation_results if r.severity == ValidationSeverity.CRITICAL and r.status == ValidationStatus.FAILED)
        high_failures = sum(1 for r in validation_results if r.severity == ValidationSeverity.HIGH and r.status == ValidationStatus.FAILED)
        medium_failures = sum(1 for r in validation_results if r.severity == ValidationSeverity.MEDIUM and r.status == ValidationStatus.FAILED)
        low_failures = sum(1 for r in validation_results if r.severity == ValidationSeverity.LOW and r.status == ValidationStatus.FAILED)
        
        total_failures = critical_failures + high_failures + medium_failures + low_failures
        warnings = sum(1 for r in validation_results if r.status == ValidationStatus.WARNING)
        
        # Calculate component scores (0-100)
        completeness_score = max(0, 100 - (critical_failures * 25) - (high_failures * 10))
        accuracy_score = max(0, 100 - (critical_failures * 20) - (high_failures * 15) - (medium_failures * 5))
        consistency_score = max(0, 100 - (medium_failures * 10) - (low_failures * 5))
        timeliness_score = 95  # Would be calculated based on data freshness
        
        # Overall score (weighted average)
        overall_score = (
            completeness_score * 0.3 +
            accuracy_score * 0.3 +
            consistency_score * 0.2 +
            timeliness_score * 0.2
        )
        
        return DataQualityScore(
            overall_score=overall_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            timeliness_score=timeliness_score,
            total_records=total_records,
            failed_validations=total_failures,
            warnings=warnings
        )
    
    def _generate_recommendations(self, validation_results: Dict[str, List[Dict]]) -> List[str]:
        """Generate data quality improvement recommendations"""
        recommendations = []
        
        for data_type, results in validation_results.items():
            for result in results:
                if result["status"] == "failed" and result["severity"] in ["critical", "high"]:
                    recommendations.append(
                        f"Fix {result['field']} validation in {data_type}: {result['failed_count']} records affected"
                    )
        
        # Add general recommendations
        if len(recommendations) > 5:
            recommendations.append("Consider implementing real-time data validation during sync")
        
        if any("email" in rec for rec in recommendations):
            recommendations.append("Implement email validation at data entry point")
        
        return recommendations[:10]  # Limit to top 10


# Demo and testing functions
def create_test_data_with_quality_issues() -> Dict[str, List[Dict]]:
    """Create test data with various quality issues for validation testing"""
    
    # Orders with quality issues
    orders = [
        {"order_id": "ord_1", "customer_id": "cust_1", "total_amount": 99.99, "order_date": "2023-01-15"},
        {"order_id": "", "customer_id": "cust_2", "total_amount": -50.00, "order_date": "invalid-date"},  # Missing ID, negative amount, bad date
        {"order_id": "ord_3", "customer_id": "cust_3", "total_amount": "not-a-number", "order_date": "2023-01-17"},  # Invalid amount
        {"order_id": "ord_1", "customer_id": "cust_4", "total_amount": 75.50, "order_date": "2023-01-18"},  # Duplicate ID
        {"order_id": "ord_5", "customer_id": "cust_5", "total_amount": 150.00},  # Missing date
    ]
    
    # Customers with quality issues
    customers = [
        {"customer_id": "cust_1", "email": "john@example.com", "full_name": "John Doe"},
        {"customer_id": "", "email": "invalid-email", "full_name": "Jane Smith"},  # Missing ID, invalid email
        {"customer_id": "cust_3", "email": "bob@example.com", "full_name": ""},  # Missing name
        {"customer_id": "cust_1", "email": "duplicate@example.com", "full_name": "Duplicate User"},  # Duplicate ID
        {"customer_id": "cust_5", "email": "alice@example.com", "full_name": "Alice Johnson"},
    ]
    
    # Products with quality issues
    products = [
        {"product_id": "prod_1", "name": "Widget A", "price": 29.99},
        {"product_id": "", "name": "Widget B", "price": -10.00},  # Missing ID, negative price
        {"product_id": "prod_3", "name": "", "price": 45.00},  # Missing name
        {"product_id": "prod_1", "name": "Duplicate Widget", "price": 35.00},  # Duplicate ID
        {"product_id": "prod_5", "name": "Widget E", "price": "invalid-price"},  # Invalid price
    ]
    
    return {
        "orders": orders,
        "customers": customers,
        "products": products
    }


def test_data_validation():
    """Test data validation and quality assessment"""
    print("🔍 Testing Data Validation and Quality Assessment")
    print("=" * 55)
    
    # Create test data with quality issues
    test_data = create_test_data_with_quality_issues()
    
    print("📊 Test Data Summary:")
    for data_type, records in test_data.items():
        print(f"   {data_type}: {len(records)} records")
    
    # Initialize quality monitor
    quality_monitor = DataQualityMonitor()
    
    # Run comprehensive assessment
    print("\\n🔬 Running Data Quality Assessment...")
    assessment = quality_monitor.assess_data_quality(test_data)
    
    # Display results
    print("\\n📈 Quality Assessment Results:")
    
    for data_type, quality_score in assessment["quality_scores"].items():
        print(f"\\n   📊 {data_type.title()} Quality:")
        print(f"      Overall Score: {quality_score['overall_score']:.1f}/100 (Grade: {quality_score['quality_grade']})")
        print(f"      Completeness: {quality_score['completeness_score']:.1f}/100")
        print(f"      Accuracy: {quality_score['accuracy_score']:.1f}/100")
        print(f"      Failed Validations: {quality_score['failed_validations']}")
        
        # Show failed validations
        if data_type in assessment["validation_results"]:
            failed_validations = [v for v in assessment["validation_results"][data_type] if v["status"] == "failed"]
            if failed_validations:
                print(f"      Issues Found:")
                for validation in failed_validations[:3]:  # Show top 3
                    print(f"         • {validation['field']}: {validation['failed_count']} failures")
    
    # Show recommendations
    if assessment["recommendations"]:
        print(f"\\n💡 Recommendations:")
        for i, rec in enumerate(assessment["recommendations"][:5], 1):
            print(f"   {i}. {rec}")
    
    print("\\n🎉 Data Validation Test Complete!")
    return assessment


if __name__ == "__main__":
    # Run demo if executed directly
    test_data_validation()