"""
FastAPI Ana Uygulama
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import get_settings
from app.database import init_database, test_connection
from app.api.v1 import api_router

# Settings yükle
settings = get_settings()

# Logger yapılandırması
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI uygulaması
app = FastAPI(
    title=settings.APP_NAME,
    description="Modern shuttle çağırma sistemi backend API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG
)

# CORS yapılandırması
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 router'ı ekle
app.include_router(
    api_router,
    prefix="/api/v1"
)


@app.on_event("startup")
async def startup_event():
    """Uygulama başlangıcında çalışır"""
    logger.info("🚀 Shuttle Call API başlatılıyor...")
    logger.info(f"🌍 Ortam: {settings.ENVIRONMENT}")
    logger.info(f"📚 API Dokümantasyonu: http://{settings.HOST}:{settings.PORT}/docs")
    
    # Database bağlantısını başlat
    try:
        logger.info("📊 Database bağlantısı kuruluyor...")
        init_database(
            database_url=settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW
        )
        
        # Bağlantıyı test et
        if test_connection(max_retries=3, retry_delay=2):
            logger.info("✅ Database bağlantısı başarılı!")
        else:
            logger.error("❌ Database bağlantısı başarısız!")
            raise RuntimeError("Database bağlantısı kurulamadı")
            
    except Exception as e:
        logger.error(f"❌ Startup hatası: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapanışında çalışır"""
    logger.info("👋 Shuttle Call API kapatılıyor...")
    logger.info("🔌 Database bağlantıları kapatılıyor...")


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Sistem sağlık kontrolü
    
    Returns:
        dict: Sistem durumu bilgisi
    """
    # Database bağlantısını kontrol et
    db_status = "healthy" if test_connection(max_retries=1, retry_delay=0) else "unhealthy"
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy" if db_status == "healthy" else "degraded",
            "service": "shuttle-call-api",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": db_status
        }
    )


@app.get("/", tags=["Root"])
async def root():
    """
    Ana endpoint - API bilgisi
    
    Returns:
        dict: API bilgileri
    """
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health"
    }
