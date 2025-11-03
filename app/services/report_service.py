"""
Reporting Service
Powered by Erkan ERDEM
"""
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app import db
from app.models.request import BuggyRequest, RequestStatus
from app.models.buggy import Buggy, BuggyStatus
from app.models.location import Location
from typing import Dict, List, Optional, Any


class ReportService:
    """Service for generating reports and analytics"""

    @staticmethod
    def get_daily_summary(hotel_id: int, date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate daily summary report

        Args:
            hotel_id: Hotel ID
            date: Date to report on (defaults to today)

        Returns:
            Dictionary with daily statistics
        """
        if date is None:
            date = datetime.utcnow()

        # Get start and end of day
        start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0)
        end_of_day = start_of_day + timedelta(days=1)

        # Total requests
        total_requests = BuggyRequest.query.filter(
            BuggyRequest.hotel_id == hotel_id,
            BuggyRequest.requested_at >= start_of_day,
            BuggyRequest.requested_at < end_of_day
        ).count()

        # Completed requests
        completed_requests = BuggyRequest.query.filter(
            BuggyRequest.hotel_id == hotel_id,
            BuggyRequest.requested_at >= start_of_day,
            BuggyRequest.requested_at < end_of_day,
            BuggyRequest.status == RequestStatus.COMPLETED
        ).count()

        # Cancelled requests
        cancelled_requests = BuggyRequest.query.filter(
            BuggyRequest.hotel_id == hotel_id,
            BuggyRequest.requested_at >= start_of_day,
            BuggyRequest.requested_at < end_of_day,
            BuggyRequest.status == RequestStatus.CANCELLED
        ).count()

        # Pending requests
        pending_requests = BuggyRequest.query.filter(
            BuggyRequest.hotel_id == hotel_id,
            BuggyRequest.requested_at >= start_of_day,
            BuggyRequest.requested_at < end_of_day,
            BuggyRequest.status == RequestStatus.PENDING
        ).count()

        # Average response time (time to accept)
        completed_with_times = BuggyRequest.query.filter(
            BuggyRequest.hotel_id == hotel_id,
            BuggyRequest.requested_at >= start_of_day,
            BuggyRequest.requested_at < end_of_day,
            BuggyRequest.status == RequestStatus.COMPLETED,
            BuggyRequest.accepted_at.isnot(None)
        ).all()

        avg_response_time = 0
        if completed_with_times:
            total_response_time = sum([
                (req.accepted_at - req.requested_at).total_seconds()
                for req in completed_with_times
            ])
            avg_response_time = total_response_time / len(completed_with_times)

        # Average completion time (time from accept to complete)
        avg_completion_time = 0
        if completed_with_times:
            total_completion_time = sum([
                (req.completed_at - req.accepted_at).total_seconds()
                for req in completed_with_times if req.completed_at
            ])
            avg_completion_time = total_completion_time / len(completed_with_times) if total_completion_time else 0

        return {
            'date': date.strftime('%Y-%m-%d'),
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'cancelled_requests': cancelled_requests,
            'pending_requests': pending_requests,
            'completion_rate': round((completed_requests / total_requests * 100) if total_requests > 0 else 0, 2),
            'avg_response_time_seconds': round(avg_response_time, 2),
            'avg_response_time_minutes': round(avg_response_time / 60, 2),
            'avg_completion_time_seconds': round(avg_completion_time, 2),
            'avg_completion_time_minutes': round(avg_completion_time / 60, 2)
        }

    @staticmethod
    def get_buggy_performance(hotel_id: int,
                             buggy_id: Optional[int] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Generate buggy performance report

        Args:
            hotel_id: Hotel ID
            buggy_id: Specific buggy ID (None for all buggies)
            start_date: Start date (defaults to 7 days ago)
            end_date: End date (defaults to now)

        Returns:
            List of buggy performance dictionaries
        """
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.utcnow()

        # Build query
        query = Buggy.query.filter(Buggy.hotel_id == hotel_id)
        if buggy_id:
            query = query.filter(Buggy.id == buggy_id)

        buggies = query.all()

        results = []
        for buggy in buggies:
            # Get requests for this buggy
            requests = BuggyRequest.query.filter(
                BuggyRequest.buggy_id == buggy.id,
                BuggyRequest.requested_at >= start_date,
                BuggyRequest.requested_at <= end_date
            ).all()

            completed = [r for r in requests if r.status == RequestStatus.COMPLETED]

            # Calculate metrics
            total_requests = len(requests)
            completed_requests = len(completed)

            avg_response = 0
            avg_completion = 0

            if completed:
                response_times = [
                    (r.accepted_at - r.requested_at).total_seconds()
                    for r in completed if r.accepted_at
                ]
                if response_times:
                    avg_response = sum(response_times) / len(response_times)

                completion_times = [
                    (r.completed_at - r.accepted_at).total_seconds()
                    for r in completed if r.completed_at and r.accepted_at
                ]
                if completion_times:
                    avg_completion = sum(completion_times) / len(completion_times)

            results.append({
                'buggy_id': buggy.id,
                'buggy_code': buggy.code,
                'driver_name': buggy.driver.full_name if buggy.driver else None,
                'total_requests': total_requests,
                'completed_requests': completed_requests,
                'completion_rate': round((completed_requests / total_requests * 100) if total_requests > 0 else 0, 2),
                'avg_response_time_minutes': round(avg_response / 60, 2),
                'avg_completion_time_minutes': round(avg_completion / 60, 2),
                'current_status': buggy.status.value if buggy.status else 'offline'
            })

        return results

    @staticmethod
    def get_location_analytics(hotel_id: int,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Generate location analytics report

        Args:
            hotel_id: Hotel ID
            start_date: Start date (defaults to 30 days ago)
            end_date: End date (defaults to now)

        Returns:
            List of location analytics dictionaries
        """
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.utcnow()

        # Get all active locations
        locations = Location.query.filter_by(hotel_id=hotel_id, is_active=True).all()

        results = []
        for location in locations:
            # Get requests from this location
            requests = BuggyRequest.query.filter(
                BuggyRequest.location_id == location.id,
                BuggyRequest.requested_at >= start_date,
                BuggyRequest.requested_at <= end_date
            ).all()

            total_requests = len(requests)
            completed = len([r for r in requests if r.status == RequestStatus.COMPLETED])

            # Calculate average wait time
            completed_with_times = [r for r in requests if r.status == RequestStatus.COMPLETED and r.accepted_at]
            avg_wait = 0
            if completed_with_times:
                wait_times = [(r.accepted_at - r.requested_at).total_seconds() for r in completed_with_times]
                avg_wait = sum(wait_times) / len(wait_times)

            # Hourly distribution
            hourly_dist = {}
            for hour in range(24):
                hourly_dist[f"{hour:02d}:00"] = 0

            for req in requests:
                hour = req.requested_at.hour
                hourly_dist[f"{hour:02d}:00"] += 1

            results.append({
                'location_id': location.id,
                'location_name': location.name,
                'total_requests': total_requests,
                'completed_requests': completed,
                'completion_rate': round((completed / total_requests * 100) if total_requests > 0 else 0, 2),
                'avg_wait_time_minutes': round(avg_wait / 60, 2),
                'hourly_distribution': hourly_dist,
                'peak_hour': max(hourly_dist.items(), key=lambda x: x[1])[0] if hourly_dist else None
            })

        # Sort by total requests descending
        results.sort(key=lambda x: x['total_requests'], reverse=True)

        return results

    @staticmethod
    def get_request_details(hotel_id: int,
                           status: Optional[RequestStatus] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get detailed request list

        Args:
            hotel_id: Hotel ID
            status: Filter by status (None for all)
            start_date: Start date
            end_date: End date
            limit: Maximum number of records

        Returns:
            List of request details
        """
        query = BuggyRequest.query.filter(BuggyRequest.hotel_id == hotel_id)

        if status:
            query = query.filter(BuggyRequest.status == status)

        if start_date:
            query = query.filter(BuggyRequest.requested_at >= start_date)

        if end_date:
            query = query.filter(BuggyRequest.requested_at <= end_date)

        requests = query.order_by(BuggyRequest.requested_at.desc()).limit(limit).all()

        results = []
        for req in requests:
            results.append({
                'id': req.id,
                'location_name': req.location.name if req.location else None,
                'buggy_code': req.buggy.code if req.buggy else None,
                'driver_name': req.buggy.driver.full_name if req.buggy and req.buggy.driver else None,
                'room_number': req.room_number,
                'status': req.status.value,
                'requested_at': req.requested_at.isoformat() if req.requested_at else None,
                'accepted_at': req.accepted_at.isoformat() if req.accepted_at else None,
                'completed_at': req.completed_at.isoformat() if req.completed_at else None,
                'response_time_seconds': (req.accepted_at - req.requested_at).total_seconds() if req.accepted_at else None,
                'completion_time_seconds': (req.completed_at - req.accepted_at).total_seconds() if req.completed_at and req.accepted_at else None,
                'notes': req.notes
            })

        return results


    @staticmethod
    def export_to_excel(data: List[Dict[str, Any]], filename: str, sheet_name: str = 'Report') -> bytes:
        """
        Export data to Excel format
        
        Args:
            data: List of dictionaries to export
            filename: Name of the file
            sheet_name: Name of the sheet
            
        Returns:
            Excel file as bytes
        """
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from io import BytesIO
        
        if not data:
            raise ValueError("No data to export")
        
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name
        
        # Header style
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Write headers
        headers = list(data[0].keys())
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # Write data
        for row_num, row_data in enumerate(data, 2):
            for col_num, header in enumerate(headers, 1):
                value = row_data.get(header, '')
                # Convert datetime to string
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                ws.cell(row=row_num, column=col_num, value=value)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to bytes
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    @staticmethod
    def export_to_pdf(data: List[Dict[str, Any]], title: str, filename: str) -> bytes:
        """
        Export data to PDF format
        
        Args:
            data: List of dictionaries to export
            title: Report title
            filename: Name of the file
            
        Returns:
            PDF file as bytes
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from io import BytesIO
        
        if not data:
            raise ValueError("No data to export")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#366092'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        # Add title
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Prepare table data
        headers = list(data[0].keys())
        table_data = [headers]
        
        for row in data:
            row_data = []
            for header in headers:
                value = row.get(header, '')
                # Convert datetime to string
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                row_data.append(str(value))
            table_data.append(row_data)
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
