from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
from datetime import datetime
from pathlib import Path
import logging

from app.core.database import get_database
from app.services.cv_parser import CVParser
from app.services.embedding_service import get_embedding_service
from app.models.cv_models import CVResponse, CVUploadResponse
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# CV Parser instance
cv_parser = CVParser()

@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(
    file: UploadFile = File(...),
    db = Depends(get_database)
):
    """CV dosyası yükle ve parse et"""
    try:
        # Dosya validasyonu
        if not file.filename:
            raise HTTPException(status_code=400, detail="Dosya adı bulunamadı")
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Desteklenmeyen dosya türü. İzin verilen: {settings.allowed_extensions}"
            )
        
        # Dosya boyutu kontrolü
        file_content = await file.read()
        if len(file_content) > settings.max_file_size:
            raise HTTPException(
                status_code=400, 
                detail=f"Dosya çok büyük. Maksimum boyut: {settings.max_file_size/1024/1024:.1f}MB"
            )
        
        # CV'yi parse et
        parsed_cv = await cv_parser.parse_cv_file(file_content, file.filename)
        
        # Unique ID oluştur
        cv_id = str(uuid.uuid4())
        
        # Veritabanına kaydet
        cv_document = {
            "cv_id": cv_id,
            "filename": file.filename,
            "uploaded_at": datetime.utcnow(),
            "file_size": len(file_content),
            "parsed_data": parsed_cv,
            "status": "processed"
        }
        
        await db.cvs.insert_one(cv_document)
        
        # Embedding oluştur ve index'e ekle
        try:
            # Get embedding service instance
            embedding_service = get_embedding_service()
            embedding_service.add_cv_to_index(cv_id, parsed_cv)
        except Exception as e:
            logger.warning(f"CV embedding oluşturulamadı: {e}")
        
        # Dosyayı kaydet (GridFS veya local storage)
        await _save_file(file_content, cv_id, file.filename)
        
        logger.info(f"CV başarıyla yüklendi: {cv_id}")
        
        return CVUploadResponse(
            cv_id=cv_id,
            filename=file.filename,
            status="success",
            message="CV başarıyla yüklendi ve işlendi",
            parsed_data=parsed_cv
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV yükleme hatası: {e}")
        raise HTTPException(status_code=500, detail=f"CV işleme hatası: {str(e)}")

@router.get("/list")
async def list_cvs(
    limit: int = 10,
    skip: int = 0,
    db = Depends(get_database)
):
    """Yüklenen CV'leri listele"""
    try:
        # CV'leri getir
        cursor = db.cvs.find({}, {"file_content": 0}).sort("uploaded_at", -1).skip(skip).limit(limit)
        cvs = await cursor.to_list(length=limit)
        
        # Toplam sayıyı al
        total = await db.cvs.count_documents({})
        
        return {
            "cvs": cvs,
            "total": total,
            "limit": limit,
            "skip": skip
        }
        
    except Exception as e:
        logger.error(f"CV listeleme hatası: {e}")
        raise HTTPException(status_code=500, detail="CV'ler getirilemedi")

@router.get("/{cv_id}", response_model=CVResponse)
async def get_cv(cv_id: str, db = Depends(get_database)):
    """Belirli bir CV'yi getir"""
    try:
        cv = await db.cvs.find_one({"cv_id": cv_id}, {"file_content": 0})
        
        if not cv:
            raise HTTPException(status_code=404, detail="CV bulunamadı")
        
        return CVResponse(**cv)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV getirme hatası: {e}")
        raise HTTPException(status_code=500, detail="CV bilgileri alınamadı")

@router.delete("/{cv_id}")
async def delete_cv(cv_id: str, db = Depends(get_database)):
    """CV'yi sil"""
    try:
        # CV'yi veritabanından sil
        result = await db.cvs.delete_one({"cv_id": cv_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="CV bulunamadı")
        
        # Dosyayı sil
        await _delete_file(cv_id)
        
        # TODO: FAISS index'den de kaldır
        
        return {"message": "CV başarıyla silindi"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV silme hatası: {e}")
        raise HTTPException(status_code=500, detail="CV silinemedi")

@router.get("/{cv_id}/matches")
async def get_cv_matches(
    cv_id: str, 
    top_k: int = 10,
    db = Depends(get_database)
):
    """CV'ye uygun iş ilanlarını bul"""
    try:
        # CV'yi getir
        cv = await db.cvs.find_one({"cv_id": cv_id})
        if not cv:
            raise HTTPException(status_code=404, detail="CV bulunamadı")
        
        # Get embedding service instance
        embedding_service = get_embedding_service()
        
        # Eşleşen iş ilanlarını bul
        matches = embedding_service.find_matching_jobs(cv['parsed_data'], top_k)
        
        results = []
        for job_id, score, job_data in matches:
            # Detaylı analiz
            match_details = embedding_service.analyze_match_details(cv['parsed_data'], job_data)
            
            results.append({
                "job_id": job_id,
                "similarity_score": round(score, 2),
                "job_title": job_data.get('title', ''),
                "company": job_data.get('company', ''),
                "match_details": match_details
            })
        
        return {
            "cv_id": cv_id,
            "matches": results,
            "total_matches": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV eşleştirme hatası: {e}")
        raise HTTPException(status_code=500, detail="Eşleştirme yapılamadı")

async def _save_file(content: bytes, cv_id: str, filename: str):
    """Dosyayı kaydet"""
    try:
        # Upload klasörünü oluştur
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(exist_ok=True)
        
        # Dosyayı kaydet
        file_path = upload_dir / f"{cv_id}_{filename}"
        with open(file_path, "wb") as f:
            f.write(content)
            
    except Exception as e:
        logger.error(f"Dosya kaydetme hatası: {e}")

async def _delete_file(cv_id: str):
    """Dosyayı sil"""
    try:
        upload_dir = Path(settings.upload_dir)
        for file_path in upload_dir.glob(f"{cv_id}_*"):
            file_path.unlink()
    except Exception as e:
        logger.error(f"Dosya silme hatası: {e}")
