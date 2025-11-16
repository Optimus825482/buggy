"""
Database bağlantı ve session yönetimi
SQLAlchemy ile PostgreSQL bağlantısı
"""
from sqlalchemy import create_engine, event, exc, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool
import logging
import time
from typing import Generator

# Base'i models'den import et
from app.models.base import Base

logger = logging.getLogger(__name__)

# Global engine ve SessionLocal
engine = None
SessionLocal = None


def init_database(database_url: str, pool_size: int = 20, max_overflow: int = 40):
    """
    Database engine'i başlat
    
    Args:
        database_url: PostgreSQL bağlantı URL'i
        pool_size: Connection pool boyutu
        max_overflow: Maksimum overflow connection sayısı
    """
    global engine, SessionLocal
    
    try:
        # SQLAlchemy engine oluştur
        engine = create_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Bağlantı kontrolü
            pool_recycle=3600,   # 1 saat sonra connection'ı yenile
            echo=False,          # SQL loglarını gösterme (production)
        )
        
        # Session factory
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        # Connection pool event listeners
        @event.listens_for(Pool, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Yeni bağlantı oluşturulduğunda"""
            logger.debug("📊 Yeni database bağlantısı oluşturuldu")
        
        @event.listens_for(Pool, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Connection pool'dan bağlantı alındığında"""
            logger.debug("🔌 Connection pool'dan bağlantı alındı")
        
        logger.info("✅ Database engine başarıyla oluşturuldu")
        logger.info(f"📊 Pool size: {pool_size}, Max overflow: {max_overflow}")
        
    except Exception as e:
        logger.error(f"❌ Database engine oluşturma hatası: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency
    FastAPI endpoint'lerinde kullanılır
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    if SessionLocal is None:
        raise RuntimeError("Database henüz başlatılmadı. init_database() çağrılmalı.")
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"❌ Database session hatası: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def test_connection(max_retries: int = 3, retry_delay: int = 2) -> bool:
    """
    Database bağlantısını test et (retry mekanizması ile)
    
    Args:
        max_retries: Maksimum deneme sayısı
        retry_delay: Denemeler arası bekleme süresi (saniye)
        
    Returns:
        bool: Bağlantı başarılı mı?
    """
    if engine is None:
        logger.error("❌ Engine henüz oluşturulmadı")
        return False
    
    for attempt in range(1, max_retries + 1):
        try:
            # Basit bir sorgu ile bağlantıyı test et
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"✅ Database bağlantısı başarılı (Deneme {attempt}/{max_retries})")
            return True
            
        except exc.OperationalError as e:
            logger.warning(f"⚠️ Database bağlantı hatası (Deneme {attempt}/{max_retries}): {e}")
            
            if attempt < max_retries:
                logger.info(f"⏳ {retry_delay} saniye sonra tekrar denenecek...")
                time.sleep(retry_delay)
            else:
                logger.error(f"❌ Database bağlantısı {max_retries} denemeden sonra başarısız")
                return False
                
        except Exception as e:
            logger.error(f"❌ Beklenmeyen database hatası: {e}")
            return False
    
    return False


def create_tables():
    """
    Tüm tabloları oluştur (development için)
    Production'da Alembic migration kullanılmalı
    """
    if engine is None:
        raise RuntimeError("Engine henüz oluşturulmadı")
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tabloları oluşturuldu")
    except Exception as e:
        logger.error(f"❌ Tablo oluşturma hatası: {e}")
        raise


def drop_tables():
    """
    Tüm tabloları sil (SADECE DEVELOPMENT!)
    ⚠️ DİKKAT: Production'da kullanma!
    """
    if engine is None:
        raise RuntimeError("Engine henüz oluşturulmadı")
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("⚠️ Tüm database tabloları silindi!")
    except Exception as e:
        logger.error(f"❌ Tablo silme hatası: {e}")
        raise
