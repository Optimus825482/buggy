"""
Report Schemas
--------------
Dashboard istatistikleri, request raporları ve performans metrikleri için Pydantic schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class TimeRangeEnum(str, Enum):
    """Zaman aralığı seçenekleri"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    CUSTOM = "custom"


class RequestStatusStats(BaseModel):
    """Request durum istatistikleri"""
    pending: int = Field(default=0, description="Bekleyen request sayısı")
    accepted: int = Field(default=0, description="Kabul edilen request sayısı")
    completed: int = Field(default=0, description="Tamamlanan request sayısı")
    cancelled: int = Field(default=0, description="İptal edilen request sayısı")
    unanswered: int = Field(default=0, description="Cevaplanmayan request sayısı")
    total: int = Field(default=0, description="Toplam request sayısı")


class ResponseTimeStats(BaseModel):
    """Yanıt süresi istatistikleri"""
    avg_response_time: Optional[float] = Field(None, description="Ortalama yanıt süresi (saniye)")
    min_response_time: Optional[int] = Field(None, description="Minimum yanıt süresi (saniye)")
    max_response_time: Optional[int] = Field(None, description="Maximum yanıt süresi (saniye)")
    median_response_time: Optional[float] = Field(None, description="Medyan yanıt süresi (saniye)")


class CompletionTimeStats(BaseModel):
    """Tamamlanma süresi istatistikleri"""
    avg_completion_time: Optional[float] = Field(None, description="Ortalama tamamlanma süresi (saniye)")
    min_completion_time: Optional[int] = Field(None, description="Minimum tamamlanma süresi (saniye)")
    max_completion_time: Optional[int] = Field(None, description="Maximum tamamlanma süresi (saniye)")
    median_completion_time: Optional[float] = Field(None, description="Medyan tamamlanma süresi (saniye)")


class LocationStats(BaseModel):
    """Lokasyon bazlı istatistikler"""
    location_id: int = Field(..., description="Lokasyon ID")
    location_name: str = Field(..., description="Lokasyon adı")
    request_count: int = Field(default=0, description="Request sayısı")
    avg_response_time: Optional[float] = Field(None, description="Ortalama yanıt süresi")


class ShuttleStats(BaseModel):
    """Shuttle bazlı istatistikler"""
    shuttle_id: int = Field(..., description="Shuttle ID")
    shuttle_code: str = Field(..., description="Shuttle kodu")
    request_count: int = Field(default=0, description="Tamamlanan request sayısı")
    avg_completion_time: Optional[float] = Field(None, description="Ortalama tamamlanma süresi")
    utilization_rate: float = Field(default=0.0, description="Kullanım oranı (%)")


class DriverStats(BaseModel):
    """Sürücü bazlı istatistikler"""
    driver_id: int = Field(..., description="Sürücü ID")
    driver_name: str = Field(..., description="Sürücü adı")
    request_count: int = Field(default=0, description="Kabul edilen request sayısı")
    avg_response_time: Optional[float] = Field(None, description="Ortalama yanıt süresi")
    avg_completion_time: Optional[float] = Field(None, description="Ortalama tamamlanma süresi")


class DashboardStats(BaseModel):
    """
    Dashboard istatistikleri
    
    Genel sistem istatistiklerini içerir:
    - Request durum dağılımı
    - Yanıt ve tamamlanma süreleri
    - Aktif shuttle ve sürücü sayıları
    """
    # Request istatistikleri
    request_stats: RequestStatusStats = Field(..., description="Request durum istatistikleri")
    
    # Zaman istatistikleri
    response_time_stats: ResponseTimeStats = Field(..., description="Yanıt süresi istatistikleri")
    completion_time_stats: CompletionTimeStats = Field(..., description="Tamamlanma süresi istatistikleri")
    
    # Aktif kaynaklar
    active_shuttles: int = Field(default=0, description="Aktif shuttle sayısı")
    active_drivers: int = Field(default=0, description="Aktif sürücü sayısı")
    available_shuttles: int = Field(default=0, description="Müsait shuttle sayısı")
    
    # Lokasyon istatistikleri (top 5)
    top_locations: List[LocationStats] = Field(default_factory=list, description="En çok kullanılan lokasyonlar")
    
    # Zaman aralığı
    time_range: str = Field(..., description="İstatistik zaman aralığı")
    start_date: datetime = Field(..., description="Başlangıç tarihi")
    end_date: datetime = Field(..., description="Bitiş tarihi")

    class Config:
        json_schema_extra = {
            "example": {
                "request_stats": {
                    "pending": 5,
                    "accepted": 3,
                    "completed": 120,
                    "cancelled": 2,
                    "unanswered": 1,
                    "total": 131
                },
                "response_time_stats": {
                    "avg_response_time": 45.5,
                    "min_response_time": 10,
                    "max_response_time": 180,
                    "median_response_time": 40.0
                },
                "completion_time_stats": {
                    "avg_completion_time": 300.5,
                    "min_completion_time": 120,
                    "max_completion_time": 600,
                    "median_completion_time": 280.0
                },
                "active_shuttles": 4,
                "active_drivers": 6,
                "available_shuttles": 2,
                "top_locations": [
                    {
                        "location_id": 1,
                        "location_name": "Havuz Alanı",
                        "request_count": 45,
                        "avg_response_time": 42.3
                    }
                ],
                "time_range": "last_7_days",
                "start_date": "2024-11-10T00:00:00",
                "end_date": "2024-11-17T23:59:59"
            }
        }


class RequestReportFilter(BaseModel):
    """Request raporu filtreleme parametreleri"""
    time_range: Optional[TimeRangeEnum] = Field(TimeRangeEnum.LAST_7_DAYS, description="Zaman aralığı")
    start_date: Optional[date] = Field(None, description="Başlangıç tarihi (custom için)")
    end_date: Optional[date] = Field(None, description="Bitiş tarihi (custom için)")
    location_id: Optional[int] = Field(None, description="Lokasyon ID filtresi")
    shuttle_id: Optional[int] = Field(None, description="Shuttle ID filtresi")
    driver_id: Optional[int] = Field(None, description="Sürücü ID filtresi")
    status: Optional[str] = Field(None, description="Request durumu filtresi")
    page: int = Field(1, ge=1, description="Sayfa numarası")
    page_size: int = Field(50, ge=1, le=100, description="Sayfa başına kayıt sayısı")


class RequestReportItem(BaseModel):
    """Request raporu tek satır"""
    request_id: int = Field(..., description="Request ID")
    requested_at: datetime = Field(..., description="Talep zamanı")
    location_name: str = Field(..., description="Lokasyon adı")
    room_number: Optional[str] = Field(None, description="Oda numarası")
    guest_name: Optional[str] = Field(None, description="Misafir adı")
    shuttle_code: Optional[str] = Field(None, description="Shuttle kodu")
    driver_name: Optional[str] = Field(None, description="Sürücü adı")
    status: str = Field(..., description="Request durumu")
    response_time: Optional[int] = Field(None, description="Yanıt süresi (saniye)")
    completion_time: Optional[int] = Field(None, description="Tamamlanma süresi (saniye)")
    accepted_at: Optional[datetime] = Field(None, description="Kabul zamanı")
    completed_at: Optional[datetime] = Field(None, description="Tamamlanma zamanı")


class RequestReport(BaseModel):
    """
    Request raporu
    
    Filtrelenmiş request listesi ve özet istatistikler içerir.
    """
    items: List[RequestReportItem] = Field(..., description="Request listesi")
    total_count: int = Field(..., description="Toplam kayıt sayısı")
    page: int = Field(..., description="Mevcut sayfa")
    page_size: int = Field(..., description="Sayfa başına kayıt")
    total_pages: int = Field(..., description="Toplam sayfa sayısı")
    
    # Özet istatistikler
    summary: RequestStatusStats = Field(..., description="Özet istatistikler")
    avg_response_time: Optional[float] = Field(None, description="Ortalama yanıt süresi")
    avg_completion_time: Optional[float] = Field(None, description="Ortalama tamamlanma süresi")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "request_id": 123,
                        "requested_at": "2024-11-17T10:30:00",
                        "location_name": "Havuz Alanı",
                        "room_number": "305",
                        "guest_name": "Ahmet Yılmaz",
                        "shuttle_code": "B01",
                        "driver_name": "Mehmet Demir",
                        "status": "COMPLETED",
                        "response_time": 45,
                        "completion_time": 280,
                        "accepted_at": "2024-11-17T10:30:45",
                        "completed_at": "2024-11-17T10:35:25"
                    }
                ],
                "total_count": 120,
                "page": 1,
                "page_size": 50,
                "total_pages": 3,
                "summary": {
                    "pending": 5,
                    "accepted": 3,
                    "completed": 110,
                    "cancelled": 2,
                    "unanswered": 0,
                    "total": 120
                },
                "avg_response_time": 45.5,
                "avg_completion_time": 300.2
            }
        }


class PerformanceMetrics(BaseModel):
    """
    Performans metrikleri
    
    Shuttle ve sürücü performans istatistiklerini içerir.
    """
    # Shuttle performansı
    shuttle_metrics: List[ShuttleStats] = Field(default_factory=list, description="Shuttle performans metrikleri")
    
    # Sürücü performansı
    driver_metrics: List[DriverStats] = Field(default_factory=list, description="Sürücü performans metrikleri")
    
    # Genel metrikler
    total_requests: int = Field(default=0, description="Toplam request sayısı")
    completion_rate: float = Field(default=0.0, description="Tamamlanma oranı (%)")
    avg_response_time: Optional[float] = Field(None, description="Ortalama yanıt süresi")
    avg_completion_time: Optional[float] = Field(None, description="Ortalama tamamlanma süresi")
    
    # Zaman aralığı
    time_range: str = Field(..., description="Metrik zaman aralığı")
    start_date: datetime = Field(..., description="Başlangıç tarihi")
    end_date: datetime = Field(..., description="Bitiş tarihi")

    class Config:
        json_schema_extra = {
            "example": {
                "shuttle_metrics": [
                    {
                        "shuttle_id": 1,
                        "shuttle_code": "B01",
                        "request_count": 45,
                        "avg_completion_time": 285.5,
                        "utilization_rate": 75.5
                    }
                ],
                "driver_metrics": [
                    {
                        "driver_id": 5,
                        "driver_name": "Mehmet Demir",
                        "request_count": 38,
                        "avg_response_time": 42.3,
                        "avg_completion_time": 290.1
                    }
                ],
                "total_requests": 120,
                "completion_rate": 91.7,
                "avg_response_time": 45.5,
                "avg_completion_time": 300.2,
                "time_range": "last_7_days",
                "start_date": "2024-11-10T00:00:00",
                "end_date": "2024-11-17T23:59:59"
            }
        }
