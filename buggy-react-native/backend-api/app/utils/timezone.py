"""
Timezone helper fonksiyonları
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional


def get_timezone_now(timezone: str = "Europe/Istanbul") -> datetime:
    """
    Belirtilen timezone'a göre şu anki zamanı döndürür
    
    Args:
        timezone: Timezone string (örn: "Europe/Istanbul")
        
    Returns:
        Timezone-aware datetime object
    """
    try:
        tz = ZoneInfo(timezone)
        return datetime.now(tz)
    except Exception:
        # Fallback: UTC kullan
        return datetime.now(ZoneInfo("UTC"))


def convert_to_timezone(
    dt: datetime,
    timezone: str = "Europe/Istanbul"
) -> datetime:
    """
    Datetime objesini belirtilen timezone'a çevirir
    
    Args:
        dt: Datetime object
        timezone: Hedef timezone string
        
    Returns:
        Timezone-aware datetime object
    """
    try:
        tz = ZoneInfo(timezone)
        
        # Eğer datetime naive ise, UTC olarak kabul et
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        
        return dt.astimezone(tz)
    except Exception:
        # Fallback: UTC'ye çevir
        if dt.tzinfo is None:
            return dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.astimezone(ZoneInfo("UTC"))


def get_utc_now() -> datetime:
    """
    UTC timezone'da şu anki zamanı döndürür
    
    Returns:
        UTC timezone-aware datetime object
    """
    return datetime.now(ZoneInfo("UTC"))
