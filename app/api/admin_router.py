from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, List, Optional
import logging
from datetime import datetime

from app.core.database import get_database
from app.services.embedding_service import get_embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/config")
async def get_system_config():
    """Sistem konfigürasyonunu getir"""
    try:
        return {
            "embedding_model": settings.embedding_model,
            "faiss_dimension": settings.faiss_dimension,
            "max_file_size_mb": settings.max_file_size / 1024 / 1024,
            "allowed_extensions": settings.allowed_extensions,
            "data_retention_days": settings.data_retention_days,
            "spacy_models": {
                "turkish": settings.spacy_model_tr,
                "english": settings.spacy_model_en
            }
        }
    except Exception as e:
        logger.error(f"Config getirme hatası: {e}")
        raise HTTPException(status_code=500, detail="Konfigürasyon alınamadı")

@router.put("/similarity_threshold")
async def update_similarity_threshold(
    threshold_data: Dict[str, float],
    db = Depends(get_database)
):
    """Benzerlik eşik değerlerini güncelle"""
    try:
        # Yeni threshold değerlerini kaydet
        config_doc = {
            "config_type": "similarity_thresholds",
            "values": threshold_data,
            "updated_at": datetime.utcnow(),
            "updated_by": "admin"  # TODO: Authentication eklendiğinde user_id
        }
        
        await db.system_config.replace_one(
            {"config_type": "similarity_thresholds"},
            config_doc,
            upsert=True
        )
        
        return {
            "message": "Benzerlik eşik değerleri güncellendi",
            "new_thresholds": threshold_data
        }
        
    except Exception as e:
        logger.error(f"Threshold güncelleme hatası: {e}")
        raise HTTPException(status_code=500, detail="Eşik değerleri güncellenemedi")

@router.get("/similarity_threshold")
async def get_similarity_threshold(db = Depends(get_database)):
    """Mevcut benzerlik eşik değerlerini getir"""
    try:
        config = await db.system_config.find_one({"config_type": "similarity_thresholds"})
        
        if not config:
            # Varsayılan değerler
            default_thresholds = {
                "excellent_match": 90.0,
                "good_match": 75.0,
                "fair_match": 60.0,
                "minimum_match": 45.0
            }
            return {"thresholds": default_thresholds, "is_default": True}
        
        return {"thresholds": config["values"], "is_default": False}
        
    except Exception as e:
        logger.error(f"Threshold getirme hatası: {e}")
        raise HTTPException(status_code=500, detail="Eşik değerleri alınamadı")

@router.post("/cleanup")
async def cleanup_old_data(
    days_to_keep: int = None,
    db = Depends(get_database)
):
    """Eski verileri temizle (GDPR uyumluluk)"""
    try:
        from datetime import timedelta
        
        if not days_to_keep:
            days_to_keep = settings.data_retention_days
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Eski CV'leri sil
        cv_result = await db.cvs.delete_many({
            "uploaded_at": {"$lt": cutoff_date}
        })
        
        # Eski match history'sini sil
        match_result = await db.match_history.delete_many({
            "search_date": {"$lt": cutoff_date}
        })
        
        # Inactive job'ları sil
        inactive_cutoff = datetime.utcnow() - timedelta(days=days_to_keep * 2)
        job_result = await db.jobs.delete_many({
            "status": "inactive",
            "updated_at": {"$lt": inactive_cutoff}
        })
        
        logger.info(f"Cleanup tamamlandı: {cv_result.deleted_count} CV, {match_result.deleted_count} match, {job_result.deleted_count} job silindi")
        
        return {
            "message": "Veri temizleme tamamlandı",
            "deleted_counts": {
                "cvs": cv_result.deleted_count,
                "match_history": match_result.deleted_count,
                "inactive_jobs": job_result.deleted_count
            },
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cleanup hatası: {e}")
        raise HTTPException(status_code=500, detail="Veri temizleme yapılamadı")

@router.post("/anonymize")
async def anonymize_old_cvs(
    days_threshold: int = None,
    db = Depends(get_database)
):
    """Eski CV'leri anonimleştir (GDPR)"""
    try:
        from datetime import timedelta
        
        if not days_threshold:
            days_threshold = settings.anonymize_after_days
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        # Anonimleştirilecek CV'leri bul
        cvs_to_anonymize = await db.cvs.find({
            "uploaded_at": {"$lt": cutoff_date},
            "anonymized": {"$ne": True}
        }).to_list(length=1000)  # Batch işlem
        
        anonymized_count = 0
        for cv in cvs_to_anonymize:
            # Kişisel bilgileri anonimleştir
            anonymized_data = cv['parsed_data'].copy()
            
            if 'personal_info' in anonymized_data:
                anonymized_data['personal_info'] = {
                    'name': 'ANONYMIZED',
                    'email': 'anonymized@example.com',
                    'phone': 'ANONYMIZED',
                    'linkedin': None
                }
            
            # Raw text'i kısalt
            if 'raw_text' in anonymized_data:
                anonymized_data['raw_text'] = 'ANONYMIZED - Data removed for privacy'
            
            # Güncelle
            await db.cvs.update_one(
                {"cv_id": cv['cv_id']},
                {
                    "$set": {
                        "parsed_data": anonymized_data,
                        "anonymized": True,
                        "anonymized_at": datetime.utcnow()
                    }
                }
            )
            anonymized_count += 1
        
        logger.info(f"Anonimleştirme tamamlandı: {anonymized_count} CV")
        
        return {
            "message": "CV anonimleştirme tamamlandı",
            "anonymized_count": anonymized_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Anonimleştirme hatası: {e}")
        raise HTTPException(status_code=500, detail="Anonimleştirme yapılamadı")

@router.get("/system_health")
async def system_health_check(db = Depends(get_database)):
    """Sistem sağlık durumu kontrolü"""
    try:
        health_status = {
            "database": "healthy",
            "embedding_service": "healthy",
            "faiss_index": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Database kontrolü
        try:
            await db.list_collection_names()
        except Exception as e:
            health_status["database"] = f"unhealthy: {str(e)}"
        
        # Embedding service kontrolü
        try:
            # Get embedding service instance
            embedding_service = get_embedding_service()
            
            if not embedding_service.model:
                health_status["embedding_service"] = "unhealthy: model not loaded"
        except Exception as e:
            health_status["embedding_service"] = f"unhealthy: {str(e)}"
        
        # FAISS index kontrolü
        try:
            cv_index_size = embedding_service.cv_index.ntotal if embedding_service.cv_index else 0
            job_index_size = embedding_service.job_index.ntotal if embedding_service.job_index else 0
            health_status["faiss_index"] = f"cv_index: {cv_index_size}, job_index: {job_index_size}"
        except Exception as e:
            health_status["faiss_index"] = f"unhealthy: {str(e)}"
        
        # Genel durum
        is_healthy = all(
            status == "healthy" or "cv_index:" in status
            for status in health_status.values() 
            if status != health_status["timestamp"]
        )
        
        health_status["overall_status"] = "healthy" if is_healthy else "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check hatası: {e}")
        raise HTTPException(status_code=500, detail="Sağlık kontrolü yapılamadı")

@router.post("/export_data")
async def export_system_data(
    export_type: str = "statistics",
    date_range: Optional[Dict] = None,
    db = Depends(get_database)
):
    """Sistem verilerini dışa aktar"""
    try:
        if export_type == "statistics":
            # İstatistiksel veri dışa aktarımı
            pipeline = [
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$uploaded_at"},
                            "month": {"$month": "$uploaded_at"}
                        },
                        "cv_count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            cv_stats = await db.cvs.aggregate(pipeline).to_list(length=100)
            
            # Job istatistikleri
            job_pipeline = [
                {
                    "$group": {
                        "_id": "$company",
                        "job_count": {"$sum": 1},
                        "avg_required_skills": {"$avg": {"$size": "$required_skills"}}
                    }
                },
                {"$sort": {"job_count": -1}}
            ]
            
            job_stats = await db.jobs.aggregate(job_pipeline).to_list(length=50)
            
            return {
                "export_type": export_type,
                "generated_at": datetime.utcnow().isoformat(),
                "cv_statistics": cv_stats,
                "job_statistics": job_stats
            }
        
        else:
            raise HTTPException(status_code=400, detail="Desteklenmeyen export türü")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export hatası: {e}")
        raise HTTPException(status_code=500, detail="Veri dışa aktarılamadı")
