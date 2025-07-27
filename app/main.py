from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
from dotenv import load_dotenv

from app.api import cv_router, job_router, match_router, admin_router
from app.core.database import get_database
from app.core.config import settings

# Çevre değişkenlerini yükle
load_dotenv()

# FastAPI uygulaması
app = FastAPI(
    title="TalentMatch NLP",
    description="CV Analizi ve Aday Eşleştirme Sistemi",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Üretimde specific origin'ler ekleyin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API router'ları
app.include_router(cv_router.router, prefix="/api/cv", tags=["CV Management"])
app.include_router(job_router.router, prefix="/api/jobs", tags=["Job Management"])
app.include_router(match_router.router, prefix="/api/matching", tags=["Matching"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["Admin"])

@app.get("/")
async def root():
    """Ana sayfa - sistem durumu"""
    return {
        "message": "TalentMatch NLP API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Sistem sağlık kontrolü"""
    try:
        # Database bağlantısını kontrol et
        db = await get_database()
        await db.list_collection_names()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-07-17T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
