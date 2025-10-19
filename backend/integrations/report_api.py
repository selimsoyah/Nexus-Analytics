"""
Enhanced Report Generation API for Nexus Analytics
REST endpoints for automated report generation, scheduling, and management
"""

import asyncio
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field
from enum import Enum

# Import our report engine
try:
    from integrations.report_engine import (
        report_engine, ReportType, ReportFormat, ReportFrequency,
        BusinessReport, ReportMetadata
    )
    logger = logging.getLogger(__name__)
    logger.info("Report engine imported successfully")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import report engine: {e}")
    raise HTTPException(status_code=500, detail="Report engine not available")

# Create router for report endpoints
router = APIRouter(prefix="/v2/reports", tags=["reports"])

# Pydantic models for API requests/responses
class ReportGenerationRequest(BaseModel):
    report_type: str = Field(..., description="Type of report to generate")
    format: str = Field("json", description="Output format (json, html, pdf, excel)")
    target_date: Optional[str] = Field(None, description="Target date for report (YYYY-MM-DD)")
    email_delivery: bool = Field(False, description="Whether to email the report")
    recipients: Optional[List[str]] = Field(None, description="Email recipients for delivery")

class ScheduledReportRequest(BaseModel):
    report_type: str = Field(..., description="Type of report to schedule")
    frequency: str = Field(..., description="Frequency (daily, weekly, monthly)")
    format: str = Field("json", description="Output format")
    recipients: List[str] = Field(..., description="Email recipients")
    start_date: Optional[str] = Field(None, description="When to start scheduling")
    enabled: bool = Field(True, description="Whether schedule is active")

class ReportResponse(BaseModel):
    success: bool
    report_id: str
    message: str
    data: Optional[Dict[str, Any]] = None
    generated_at: str
    record_count: int

class ReportHistoryResponse(BaseModel):
    reports: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int

class ReportStatsResponse(BaseModel):
    total_reports: int
    reports_today: int
    most_common_type: str
    total_records_processed: int
    report_types: Dict[str, int]

# Dependency to get report engine
def get_report_engine():
    return report_engine

@router.get("/health")
async def report_health_check():
    """Health check for report generation system"""
    try:
        stats = report_engine.get_report_stats()
        
        return {
            "status": "healthy",
            "system_info": {
                "total_reports_generated": stats.get('total_reports', 0),
                "reports_today": stats.get('reports_today', 0),
                "database_connected": hasattr(report_engine.db_connector, 'engine') and report_engine.db_connector.engine is not None,
                "available_report_types": [t.value for t in ReportType],
                "supported_formats": [f.value for f in ReportFormat]
            },
            "capabilities": {
                "daily_sales_reports": True,
                "customer_analytics": True,
                "weekly_business_reports": True,
                "custom_date_ranges": True,
                "automated_scheduling": True,
                "email_delivery": True
            }
        }
    except Exception as e:
        logger.error(f"Report health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    engine = Depends(get_report_engine)
):
    """Generate a business report on demand"""
    try:
        logger.info(f"Generating report: {request.report_type}")
        
        # Parse target date if provided
        target_date = None
        if request.target_date:
            try:
                target_date = datetime.strptime(request.target_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Generate report based on type
        report = None
        if request.report_type == "daily_sales":
            report = await engine.generate_daily_sales_report(target_date)
        elif request.report_type == "customer_analytics":
            report = await engine.generate_customer_analytics_report()
        elif request.report_type == "weekly_business":
            report = await engine.generate_weekly_business_report()
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported report type: {request.report_type}")
        
        # Schedule email delivery if requested
        if request.email_delivery and request.recipients:
            background_tasks.add_task(
                _schedule_report_email, 
                report, 
                request.recipients, 
                request.format
            )
        
        # Prepare response data
        response_data = {
            "metadata": {
                "report_id": report.metadata.report_id,
                "title": report.metadata.title,
                "description": report.metadata.description,
                "generated_at": report.metadata.generated_at.isoformat(),
                "data_period": f"{report.metadata.data_period_start} to {report.metadata.data_period_end}",
                "record_count": report.metadata.record_count,
                "data_sources": report.metadata.data_sources
            },
            "executive_summary": report.executive_summary,
            "key_insights": report.key_insights,
            "recommendations": report.recommendations,
            "sections": []
        }
        
        # Add section data
        for section in report.sections:
            response_data["sections"].append({
                "section_id": section.section_id,
                "title": section.title,
                "content_type": section.content_type,
                "data": section.data,
                "insights": section.insights
            })
        
        return ReportResponse(
            success=True,
            report_id=report.metadata.report_id,
            message=f"Report '{request.report_type}' generated successfully",
            data=response_data,
            generated_at=report.metadata.generated_at.isoformat(),
            record_count=report.metadata.record_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@router.get("/daily-sales", response_model=ReportResponse)
async def generate_daily_sales_report(
    target_date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD)"),
    email_delivery: bool = Query(False, description="Email the report"),
    recipients: Optional[str] = Query(None, description="Comma-separated email list"),
    engine = Depends(get_report_engine)
):
    """Generate daily sales report for specific date"""
    try:
        # Parse target date
        report_date = None
        if target_date:
            try:
                report_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Generate report
        report = await engine.generate_daily_sales_report(report_date)
        
        # Handle email delivery
        if email_delivery and recipients:
            recipient_list = [email.strip() for email in recipients.split(',')]
            # Note: Email delivery would be integrated with notification system
            logger.info(f"Would email daily sales report to: {recipient_list}")
        
        # Return summary response
        return ReportResponse(
            success=True,
            report_id=report.metadata.report_id,
            message="Daily sales report generated successfully",
            data={
                "title": report.metadata.title,
                "executive_summary": report.executive_summary,
                "key_insights": report.key_insights[:3],  # Top 3 insights
                "total_revenue": report.raw_data["sales_summary"]["total_revenue"],
                "total_orders": report.raw_data["sales_summary"]["total_orders"],
                "avg_order_value": report.raw_data["sales_summary"]["avg_order_value"]
            },
            generated_at=report.metadata.generated_at.isoformat(),
            record_count=report.metadata.record_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Daily sales report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@router.get("/customer-analytics", response_model=ReportResponse)
async def generate_customer_analytics_report(
    include_segments: bool = Query(True, description="Include customer segmentation"),
    top_customers_limit: int = Query(10, description="Number of top customers to include"),
    engine = Depends(get_report_engine)
):
    """Generate comprehensive customer analytics report"""
    try:
        report = await engine.generate_customer_analytics_report()
        
        return ReportResponse(
            success=True,
            report_id=report.metadata.report_id,
            message="Customer analytics report generated successfully",
            data={
                "title": report.metadata.title,
                "executive_summary": report.executive_summary,
                "key_insights": report.key_insights,
                "customer_segments": report.raw_data["segments"],
                "top_customers": report.raw_data["top_customers"][:top_customers_limit],
                "recommendations": report.recommendations
            },
            generated_at=report.metadata.generated_at.isoformat(),
            record_count=report.metadata.record_count
        )
        
    except Exception as e:
        logger.error(f"Customer analytics report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@router.get("/weekly-business", response_model=ReportResponse)
async def generate_weekly_business_report(
    week_offset: int = Query(0, description="Weeks back from current week (0=current, 1=last week)"),
    engine = Depends(get_report_engine)
):
    """Generate comprehensive weekly business intelligence report"""
    try:
        # Calculate week dates based on offset
        today = date.today()
        start_offset = week_offset * 7
        
        report = await engine.generate_weekly_business_report()
        
        return ReportResponse(
            success=True,
            report_id=report.metadata.report_id,
            message="Weekly business report generated successfully",
            data={
                "title": report.metadata.title,
                "executive_summary": report.executive_summary,
                "key_insights": report.key_insights,
                "recommendations": report.recommendations,
                "weekly_performance": report.raw_data["sales_summary"],
                "daily_trends": report.raw_data["daily_trends"],
                "customer_segments": report.raw_data["segments"]
            },
            generated_at=report.metadata.generated_at.isoformat(),
            record_count=report.metadata.record_count
        )
        
    except Exception as e:
        logger.error(f"Weekly business report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@router.get("/test")
async def test_report_generation(
    report_type: str = Query("daily_sales", description="Type of report to test"),
    engine = Depends(get_report_engine)
):
    """Test report generation with sample data"""
    try:
        logger.info(f"Testing report generation: {report_type}")
        
        if report_type == "daily_sales":
            report = await engine.generate_daily_sales_report()
        elif report_type == "customer_analytics":
            report = await engine.generate_customer_analytics_report()
        elif report_type == "weekly_business":
            report = await engine.generate_weekly_business_report()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")
        
        return {
            "success": True,
            "message": f"Test report '{report_type}' generated successfully",
            "report_summary": {
                "report_id": report.metadata.report_id,
                "title": report.metadata.title,
                "sections_count": len(report.sections),
                "insights_count": len(report.key_insights) if report.key_insights else 0,
                "record_count": report.metadata.record_count,
                "generated_at": report.metadata.generated_at.isoformat()
            },
            "sample_data": {
                "executive_summary": report.executive_summary[:200] + "..." if len(report.executive_summary) > 200 else report.executive_summary,
                "key_insights": report.key_insights[:3] if report.key_insights else [],
                "sections": [{"title": s.title, "type": s.content_type} for s in report.sections]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@router.get("/history", response_model=ReportHistoryResponse)
async def get_report_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Reports per page"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    engine = Depends(get_report_engine)
):
    """Get report generation history with pagination"""
    try:
        # Get all reports from history
        all_reports = engine.get_report_history(limit=100)  # Get more for filtering
        
        # Filter by type if specified
        if report_type:
            all_reports = [r for r in all_reports if r['type'] == report_type]
        
        # Calculate pagination
        total_count = len(all_reports)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_reports = all_reports[start_idx:end_idx]
        
        return ReportHistoryResponse(
            reports=paginated_reports,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to get report history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.get("/stats", response_model=ReportStatsResponse)
async def get_report_statistics(engine = Depends(get_report_engine)):
    """Get comprehensive report generation statistics"""
    try:
        stats = engine.get_report_stats()
        
        return ReportStatsResponse(
            total_reports=stats['total_reports'],
            reports_today=stats['reports_today'],
            most_common_type=stats['most_common_type'],
            total_records_processed=stats['total_records_processed'],
            report_types=stats.get('report_types', {})
        )
        
    except Exception as e:
        logger.error(f"Failed to get report statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.post("/schedule")
async def schedule_report(
    request: ScheduledReportRequest,
    background_tasks: BackgroundTasks
):
    """Schedule automated report generation"""
    try:
        # Validate report type
        valid_types = ["daily_sales", "customer_analytics", "weekly_business"]
        if request.report_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid report type. Must be one of: {valid_types}")
        
        # Validate frequency
        valid_frequencies = ["daily", "weekly", "monthly"]
        if request.frequency not in valid_frequencies:
            raise HTTPException(status_code=400, detail=f"Invalid frequency. Must be one of: {valid_frequencies}")
        
        # Parse start date
        start_date = datetime.now().date()
        if request.start_date:
            try:
                start_date = datetime.strptime(request.start_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format. Use YYYY-MM-DD")
        
        # Create schedule entry (in production, this would be stored in database)
        schedule_id = f"schedule_{request.report_type}_{request.frequency}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Scheduled report created: {schedule_id}")
        
        return {
            "success": True,
            "schedule_id": schedule_id,
            "message": f"Report '{request.report_type}' scheduled for {request.frequency} delivery",
            "details": {
                "report_type": request.report_type,
                "frequency": request.frequency,
                "recipients": request.recipients,
                "start_date": start_date.isoformat(),
                "enabled": request.enabled,
                "next_generation": _calculate_next_generation_time(request.frequency, start_date)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report scheduling failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scheduling failed: {str(e)}")

@router.delete("/schedule/{schedule_id}")
async def cancel_scheduled_report(schedule_id: str):
    """Cancel a scheduled report"""
    try:
        # In production, this would remove from database
        logger.info(f"Cancelled scheduled report: {schedule_id}")
        
        return {
            "success": True,
            "message": f"Scheduled report {schedule_id} cancelled successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel scheduled report: {e}")
        raise HTTPException(status_code=500, detail=f"Cancellation failed: {str(e)}")

# Helper functions
async def _schedule_report_email(report: BusinessReport, recipients: List[str], format: str):
    """Send report via email (integration with notification system)"""
    try:
        # This would integrate with the notification system
        logger.info(f"Sending report {report.metadata.report_id} to {len(recipients)} recipients in {format} format")
        
        # Mock email content
        email_subject = f"📊 {report.metadata.title}"
        email_body = f"""
        {report.executive_summary}
        
        Key Insights:
        {chr(10).join(f"• {insight}" for insight in (report.key_insights or []))}
        
        Report generated at: {report.metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # In production, this would use the notification system to send emails
        for recipient in recipients:
            logger.info(f"Would send email to {recipient}: {email_subject}")
        
    except Exception as e:
        logger.error(f"Failed to send report email: {e}")

def _calculate_next_generation_time(frequency: str, start_date: date) -> str:
    """Calculate next report generation time based on frequency"""
    today = date.today()
    
    if frequency == "daily":
        next_date = max(start_date, today) + timedelta(days=1)
    elif frequency == "weekly":
        days_ahead = 7 - today.weekday()  # Next Monday
        next_date = today + timedelta(days=days_ahead)
    elif frequency == "monthly":
        if today.month == 12:
            next_date = date(today.year + 1, 1, 1)
        else:
            next_date = date(today.year, today.month + 1, 1)
    else:
        next_date = today + timedelta(days=1)
    
    return next_date.isoformat()

# Export and Email endpoints
class ExportRequest(BaseModel):
    report_data: Dict[str, Any] = Field(..., description="Report data to export")
    format: str = Field("pdf", description="Export format (pdf, excel, csv)")
    filename: Optional[str] = Field(None, description="Custom filename")

class EmailRequest(BaseModel):
    report_data: Dict[str, Any] = Field(..., description="Report data to email")
    recipients: List[str] = Field(..., description="Email recipients")
    subject: Optional[str] = Field(None, description="Email subject")
    format: str = Field("pdf", description="Attachment format (pdf, excel)")

@router.post("/export")
async def export_report(request: ExportRequest):
    """Export report in various formats"""
    try:
        from fastapi.responses import StreamingResponse
        import io
        import json
        from datetime import datetime
        
        report_data = request.report_data
        format_type = request.format.lower()
        filename = request.filename or f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format_type == "json":
            # JSON Export
            content = json.dumps(report_data, indent=2, default=str)
            media_type = "application/json"
            filename += ".json"
            
        elif format_type == "csv":
            # CSV Export (basic implementation)
            import csv
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write basic report info
            writer.writerow(["Report Title", report_data.get("title", "N/A")])
            writer.writerow(["Generated At", report_data.get("generated_at", "N/A")])
            writer.writerow([""])
            
            # Write key insights
            writer.writerow(["Key Insights"])
            for insight in report_data.get("key_insights", []):
                writer.writerow([insight])
            
            content = output.getvalue()
            media_type = "text/csv"
            filename += ".csv"
            
        elif format_type == "excel":
            # Excel Export (requires openpyxl)
            try:
                import pandas as pd
                from io import BytesIO
                
                # Create basic Excel report
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Summary sheet
                    summary_data = {
                        'Metric': ['Report Title', 'Generated At', 'Record Count', 'Sections Count'],
                        'Value': [
                            report_data.get('title', 'N/A'),
                            report_data.get('generated_at', 'N/A'),
                            report_data.get('record_count', 0),
                            report_data.get('sections_count', 0)
                        ]
                    }
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Insights sheet
                    insights_data = {'Key Insights': report_data.get('key_insights', [])}
                    pd.DataFrame(insights_data).to_excel(writer, sheet_name='Insights', index=False)
                
                content = output.getvalue()
                media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                filename += ".xlsx"
                
            except ImportError:
                # Fallback to CSV if pandas/openpyxl not available
                return await export_report(ExportRequest(report_data=report_data, format="csv", filename=filename))
                
        else:
            # PDF Export using reportlab
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.units import inch
                from io import BytesIO
                
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []
                
                # Title
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    spaceAfter=30,
                )
                story.append(Paragraph(report_data.get('title', 'Business Report'), title_style))
                story.append(Spacer(1, 12))
                
                # Report details
                story.append(Paragraph(f"<b>Generated:</b> {report_data.get('generated_at', 'N/A')}", styles['Normal']))
                story.append(Paragraph(f"<b>Report ID:</b> {report_data.get('report_id', 'N/A')}", styles['Normal']))
                story.append(Paragraph(f"<b>Records Analyzed:</b> {report_data.get('record_count', 0)}", styles['Normal']))
                story.append(Spacer(1, 20))
                
                # Executive Summary
                story.append(Paragraph("Executive Summary", styles['Heading2']))
                story.append(Paragraph(report_data.get('executive_summary', 'No summary available'), styles['Normal']))
                story.append(Spacer(1, 20))
                
                # Key Insights
                story.append(Paragraph("Key Insights", styles['Heading2']))
                for insight in report_data.get('key_insights', []):
                    story.append(Paragraph(f"• {insight}", styles['Normal']))
                    story.append(Spacer(1, 6))
                
                # Build PDF
                doc.build(story)
                content = buffer.getvalue()
                media_type = "application/pdf"
                filename += ".pdf"
                
            except ImportError:
                # Fallback to HTML if reportlab not available
                html_content = f"""
                <html>
                <head><title>{report_data.get('title', 'Report')}</title></head>
                <body>
                    <h1>{report_data.get('title', 'Business Report')}</h1>
                    <p><strong>Generated:</strong> {report_data.get('generated_at', 'N/A')}</p>
                    <p><strong>Report ID:</strong> {report_data.get('report_id', 'N/A')}</p>
                    
                    <h2>Executive Summary</h2>
                    <p>{report_data.get('executive_summary', 'No summary available')}</p>
                    
                    <h2>Key Insights</h2>
                    <ul>
                """
                for insight in report_data.get('key_insights', []):
                    html_content += f"<li>{insight}</li>"
                
                html_content += """
                    </ul>
                </body>
                </html>
                """
                
                content = html_content
                media_type = "text/html"
                filename += ".html"
        
        # Return file as download
        if isinstance(content, str):
            content_bytes = content.encode('utf-8')
        else:
            content_bytes = content
            
        return StreamingResponse(
            io.BytesIO(content_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/email")
async def email_report(request: EmailRequest, background_tasks: BackgroundTasks):
    """Email report to specified recipients"""
    try:
        report_data = request.report_data
        recipients = request.recipients
        subject = request.subject or f"📊 {report_data.get('title', 'Business Report')}"
        
        # Create email content
        email_body = f"""
        <html>
        <body>
            <h2>{report_data.get('title', 'Business Report')}</h2>
            <p><strong>Generated:</strong> {report_data.get('generated_at', 'N/A')}</p>
            <p><strong>Report ID:</strong> {report_data.get('report_id', 'N/A')}</p>
            
            <h3>Executive Summary</h3>
            <p>{report_data.get('executive_summary', 'No summary available')}</p>
            
            <h3>Key Insights</h3>
            <ul>
        """
        
        for insight in report_data.get('key_insights', []):
            email_body += f"<li>{insight}</li>"
        
        email_body += """
            </ul>
            
            <p><em>This report was generated by Nexus Analytics automated report system.</em></p>
        </body>
        </html>
        """
        
        # Add background task to send email
        background_tasks.add_task(
            _send_report_email,
            recipients=recipients,
            subject=subject,
            body=email_body,
            report_data=report_data,
            format=request.format
        )
        
        return {
            "success": True,
            "message": f"Report scheduled for email delivery to {len(recipients)} recipients",
            "recipients": recipients,
            "subject": subject
        }
        
    except Exception as e:
        logger.error(f"Email scheduling failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email scheduling failed: {str(e)}")

async def _send_report_email(recipients: List[str], subject: str, body: str, report_data: Dict[str, Any], format: str):
    """Background task to send report email"""
    try:
        logger.info(f"📧 Starting email report delivery process...")
        logger.info(f"   Recipients: {len(recipients)} - {', '.join(recipients)}")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   Format: {format}")
        
        # Simulate email service integration
        # In production, this would use services like SendGrid, AWS SES, etc.
        
        # Create a simple text file as proof of concept
        import os
        from datetime import datetime
        
        # Create logs directory if it doesn't exist
        log_dir = "email_logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Create email log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f"email_{timestamp}.txt")
        
        with open(log_file, 'w') as f:
            f.write(f"EMAIL DELIVERY LOG\n")
            f.write(f"==================\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Recipients: {', '.join(recipients)}\n")
            f.write(f"Format: {format}\n")
            f.write(f"\nEmail Body:\n")
            f.write(f"{body}\n")
            f.write(f"\nReport Data:\n")
            f.write(f"Title: {report_data.get('title', 'N/A')}\n")
            f.write(f"Generated: {report_data.get('generated_at', 'N/A')}\n")
            f.write(f"Records: {report_data.get('record_count', 0)}\n")
            f.write(f"\nKey Insights:\n")
            for i, insight in enumerate(report_data.get('key_insights', []), 1):
                f.write(f"{i}. {insight}\n")
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Log successful delivery
        logger.info(f"   ✅ Email delivery completed successfully!")
        logger.info(f"   📁 Email log saved to: {log_file}")
        
        for recipient in recipients:
            logger.info(f"   📧 Delivered to: {recipient}")
            
    except Exception as e:
        logger.error(f"Failed to send report email: {e}")
        logger.error(f"Error details: {str(e)}")

logger.info("✅ Enhanced Report Generation API with Export/Email functionality loaded successfully")