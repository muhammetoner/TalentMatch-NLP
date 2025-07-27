"""
Enhanced Admin Router
Gelişmiş admin özellikler ile
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.core.database import get_database
from app.services.admin_parameter_service import admin_parameter_service
from app.services.analytics_service import analytics_service
from app.services.summarization_service import cv_summarizer
from app.services.sms_service import sms_service
from app.services.storage_service import get_gridfs_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Parametre yönetimi endpoints
@router.get("/parameters/{category}")
async def get_parameters(category: str):
    """Belirli kategori parametrelerini getir"""
    try:
        parameters = await admin_parameter_service.get_parameters(category)
        return {"category": category, "parameters": parameters}
    except Exception as e:
        logger.error(f"Parametre getirme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/parameters/{category}")
async def update_parameters(
    category: str,
    parameters: Dict[str, Any] = Body(...)
):
    """Parametreleri güncelle"""
    try:
        # Parametreleri doğrula
        validation = await admin_parameter_service.validate_parameters(category, parameters)
        
        if not validation["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Parametre doğrulama hatası: {validation['errors']}"
            )
        
        # Parametreleri güncelle
        success = await admin_parameter_service.update_parameters(category, parameters)
        
        if success:
            return {"message": f"{category} parametreleri başarıyla güncellendi"}
        else:
            raise HTTPException(status_code=500, detail="Parametre güncellenemedi")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parametre güncelleme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parameters/{category}/reset")
async def reset_parameters(category: str):
    """Parametreleri sıfırla"""
    try:
        success = await admin_parameter_service.reset_parameters(category)
        
        if success:
            return {"message": f"{category} parametreleri sıfırlandı"}
        else:
            raise HTTPException(status_code=500, detail="Parametreler sıfırlanamadı")
            
    except Exception as e:
        logger.error(f"Parametre sıfırlama hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/parameters/export")
async def export_parameters():
    """Tüm parametreleri dışa aktar"""
    try:
        export_data = await admin_parameter_service.export_parameters()
        return export_data
    except Exception as e:
        logger.error(f"Parametre dışa aktarma hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parameters/import")
async def import_parameters(import_data: Dict[str, Any] = Body(...)):
    """Parametreleri içe aktar"""
    try:
        success = await admin_parameter_service.import_parameters(import_data)
        
        if success:
            return {"message": "Parametreler başarıyla içe aktarıldı"}
        else:
            raise HTTPException(status_code=500, detail="Parametreler içe aktarılamadı")
            
    except Exception as e:
        logger.error(f"Parametre içe aktarma hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analitik endpoints
@router.get("/analytics/comprehensive")
async def get_comprehensive_analytics(days: int = Query(30, ge=1, le=365)):
    """Kapsamlı analitik raporu"""
    try:
        analytics = await analytics_service.get_comprehensive_analytics(days)
        return analytics
    except Exception as e:
        logger.error(f"Kapsamlı analitik hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/weekly-report")
async def get_weekly_report():
    """Haftalık rapor"""
    try:
        report = await analytics_service.generate_weekly_report()
        return report
    except Exception as e:
        logger.error(f"Haftalık rapor hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CV özetleme endpoints
@router.post("/cv/{cv_id}/summarize")
async def summarize_cv(cv_id: str, max_sentences: int = Query(3, ge=1, le=10), db = Depends(get_database)):
    """CV özetini oluştur"""
    try:
        # CV'yi getir
        cv = await db.cvs.find_one({"cv_id": cv_id})
        if not cv:
            raise HTTPException(status_code=404, detail="CV bulunamadı")
        
        # Özetleme
        summary = cv_summarizer.summarize_cv(cv["parsed_data"], max_sentences)
        
        return {
            "cv_id": cv_id,
            "summary": summary,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV özetleme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cv/{cv_id}/recommendations")
async def get_cv_recommendations(cv_id: str, db = Depends(get_database)):
    """CV için öneriler"""
    try:
        # CV'yi getir
        cv = await db.cvs.find_one({"cv_id": cv_id})
        if not cv:
            raise HTTPException(status_code=404, detail="CV bulunamadı")
        
        # Öneriler
        recommendations = cv_summarizer.generate_cv_recommendations(cv["parsed_data"])
        
        return {
            "cv_id": cv_id,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV öneriler hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# SMS endpoints
@router.post("/sms/send")
async def send_sms(
    phone_number: str = Body(...),
    message: str = Body(...)
):
    """SMS gönder"""
    try:
        success = await sms_service.send_custom_sms(phone_number, message)
        
        if success:
            return {"message": "SMS başarıyla gönderildi"}
        else:
            raise HTTPException(status_code=500, detail="SMS gönderilemedi")
            
    except Exception as e:
        logger.error(f"SMS gönderme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sms/test")
async def test_sms_connection():
    """SMS API bağlantısını test et"""
    try:
        result = sms_service.test_connection()
        return result
    except Exception as e:
        logger.error(f"SMS test hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# GridFS dosya yönetimi endpoints
@router.get("/files")
async def list_files(
    filename_pattern: Optional[str] = None,
    limit: int = Query(50, ge=1, le=1000),
    db = Depends(get_database)
):
    """Yüklenen dosyaları listele"""
    try:
        gridfs_service = await get_gridfs_service(db)
        files = await gridfs_service.list_files(filename_pattern)
        
        return {
            "files": files[:limit],
            "total": len(files),
            "pattern": filename_pattern
        }
        
    except Exception as e:
        logger.error(f"Dosya listeleme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{file_id}/metadata")
async def get_file_metadata(file_id: str, db = Depends(get_database)):
    """Dosya metadata'sı"""
    try:
        gridfs_service = await get_gridfs_service(db)
        metadata = await gridfs_service.get_file_metadata(file_id)
        
        if metadata:
            return metadata
        else:
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dosya metadata hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{file_id}")
async def delete_file(file_id: str, db = Depends(get_database)):
    """Dosyayı sil"""
    try:
        gridfs_service = await get_gridfs_service(db)
        success = await gridfs_service.delete_file(file_id)
        
        if success:
            return {"message": "Dosya başarıyla silindi"}
        else:
            raise HTTPException(status_code=500, detail="Dosya silinemedi")
            
    except Exception as e:
        logger.error(f"Dosya silme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Sistem bakım endpoints
@router.post("/maintenance/cleanup")
async def system_cleanup(
    days_old: int = Query(30, ge=1, le=365),
    db = Depends(get_database)
):
    """Sistem temizliği"""
    try:
        cleanup_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Eski logları temizle
        deleted_logs = await db.api_logs.delete_many({
            "timestamp": {"$lt": cleanup_date}
        })
        
        # Eski geçici dosyaları temizle
        deleted_temp = await db.temp_files.delete_many({
            "created_at": {"$lt": cleanup_date}
        })
        
        # Eski match logları temizle
        deleted_matches = await db.match_logs.delete_many({
            "timestamp": {"$lt": cleanup_date}
        })
        
        return {
            "message": "Sistem temizliği tamamlandı",
            "deleted_logs": deleted_logs.deleted_count,
            "deleted_temp_files": deleted_temp.deleted_count,
            "deleted_match_logs": deleted_matches.deleted_count,
            "cleanup_date": cleanup_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Sistem temizlik hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/health")
async def system_health(db = Depends(get_database)):
    """Detaylı sistem sağlığı"""
    try:
        # Veritabanı durumu
        db_stats = await db.command("dbStats")
        
        # Koleksiyon durumları
        collections = await db.list_collection_names()
        collection_stats = {}
        
        for collection in collections:
            stats = await db.command("collStats", collection)
            collection_stats[collection] = {
                "count": stats.get("count", 0),
                "size": stats.get("size", 0),
                "avgObjSize": stats.get("avgObjSize", 0)
            }
        
        # Sistem durumu
        system_health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "collections": len(collections),
                "total_size": db_stats.get("dataSize", 0),
                "index_size": db_stats.get("indexSize", 0)
            },
            "collections": collection_stats
        }
        
        return system_health
        
    except Exception as e:
        logger.error(f"Sistem sağlık kontrolü hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))
