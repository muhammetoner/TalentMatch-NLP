from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
import logging
from datetime import datetime

from app.core.database import get_database
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/similarity/{cv_id}/{job_id}")
async def calculate_similarity(
    cv_id: str,
    job_id: str,
    db = Depends(get_database)
):
    """İki kayıt arasında benzerlik hesapla"""
    try:
        # CV ve Job verilerini getir
        cv = await db.cvs.find_one({"cv_id": cv_id})
        job = await db.jobs.find_one({"job_id": job_id})
        
        if not cv:
            raise HTTPException(status_code=404, detail="CV bulunamadı")
        if not job:
            raise HTTPException(status_code=404, detail="İş ilanı bulunamadı")
        
        # Embedding service instance
        embedding_service = get_embedding_service()

        # Embedding'leri oluştur ve benzerlik hesapla
        cv_embedding = embedding_service.create_cv_embedding(cv['parsed_data'])
        job_embedding = embedding_service.create_job_embedding(job)
        
        # Cosine similarity hesapla
        import numpy as np
        cv_norm = cv_embedding / np.linalg.norm(cv_embedding)
        job_norm = job_embedding / np.linalg.norm(job_embedding)
        similarity = float(np.dot(cv_norm, job_norm)) * 100
        
        # Detaylı analiz
        match_details = embedding_service.analyze_match_details(cv['parsed_data'], job)
        
        return {
            "cv_id": cv_id,
            "job_id": job_id,
            "similarity_score": round(similarity, 2),
            "match_details": match_details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Benzerlik hesaplama hatası: {e}")
        raise HTTPException(status_code=500, detail="Benzerlik hesaplanamadı")

@router.get("/batch_match")
async def batch_match_cvs_to_jobs(
    job_ids: List[str],
    top_k: int = 5,
    min_score: float = 50.0,
    db = Depends(get_database)
):
    """Birden fazla iş ilanı için CV eşleştirmesi"""
    try:
        all_results = {}
        
        for job_id in job_ids:
            # İş ilanını getir
            job = await db.jobs.find_one({"job_id": job_id})
            if not job:
                all_results[job_id] = {"error": "İş ilanı bulunamadı"}
                continue
            
            # Get embedding service instance
            embedding_service = get_embedding_service()
            
            # Eşleşme yap
            matches = embedding_service.find_matching_cvs(job, top_k)
            
            filtered_matches = []
            for cv_id, score, cv_data in matches:
                if score >= min_score:
                    filtered_matches.append({
                        "cv_id": cv_id,
                        "similarity_score": round(score, 2),
                        "candidate_name": cv_data.get('personal_info', {}).get('name', 'Bilinmiyor')
                    })
            
            all_results[job_id] = {
                "job_title": job.get('title'),
                "matches": filtered_matches,
                "total_matches": len(filtered_matches)
            }
        
        return {
            "batch_results": all_results,
            "parameters": {
                "top_k": top_k,
                "min_score": min_score
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch eşleştirme hatası: {e}")
        raise HTTPException(status_code=500, detail="Batch eşleştirme yapılamadı")

@router.get("/statistics")
async def get_matching_statistics(db = Depends(get_database)):
    """Eşleştirme istatistikleri"""
    try:
        # Temel sayılar
        total_cvs = await db.cvs.count_documents({"status": "processed"})
        total_jobs = await db.jobs.count_documents({"status": "active"})
        total_matches = await db.match_history.count_documents({})
        
        # Son 7 günün istatistikleri
        from datetime import datetime, timedelta
        last_week = datetime.utcnow() - timedelta(days=7)
        
        recent_cvs = await db.cvs.count_documents({
            "uploaded_at": {"$gte": last_week},
            "status": "processed"
        })
        
        recent_jobs = await db.jobs.count_documents({
            "created_at": {"$gte": last_week},
            "status": "active"
        })
        
        recent_matches = await db.match_history.count_documents({
            "search_date": {"$gte": last_week}
        })
        
        # En aktif şirketler
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$company", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_companies = await db.jobs.aggregate(pipeline).to_list(length=5)
        
        # En çok aranan beceriler
        pipeline = [
            {"$match": {"status": "active"}},
            {"$unwind": "$required_skills"},
            {"$group": {"_id": "$required_skills", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_skills = await db.jobs.aggregate(pipeline).to_list(length=10)
        
        return {
            "overview": {
                "total_cvs": total_cvs,
                "total_jobs": total_jobs,
                "total_matches": total_matches
            },
            "recent_activity": {
                "new_cvs_last_week": recent_cvs,
                "new_jobs_last_week": recent_jobs,
                "matches_last_week": recent_matches
            },
            "insights": {
                "top_companies": [{"company": item["_id"], "job_count": item["count"]} for item in top_companies],
                "most_demanded_skills": [{"skill": item["_id"], "demand_count": item["count"]} for item in top_skills]
            },
            "index_status": {
                "cv_index_size": get_embedding_service().cv_index.ntotal if get_embedding_service().cv_index else 0,
                "job_index_size": get_embedding_service().job_index.ntotal if get_embedding_service().job_index else 0
            }
        }
        
    except Exception as e:
        logger.error(f"İstatistik hatası: {e}")
        raise HTTPException(status_code=500, detail="İstatistikler alınamadı")

@router.post("/reindex")
async def reindex_embeddings(db = Depends(get_database)):
    """Tüm embedding'leri yeniden oluştur"""
    try:
        # Get embedding service instance
        embedding_service = get_embedding_service()
        
        # Mevcut index'leri temizle
        embedding_service.cv_index = None
        embedding_service.job_index = None
        embedding_service.cv_metadata = {}
        embedding_service.job_metadata = {}
        
        # CV'leri yeniden indexle
        cv_cursor = db.cvs.find({"status": "processed"})
        cv_count = 0
        async for cv in cv_cursor:
            try:
                embedding_service.add_cv_to_index(cv['cv_id'], cv['parsed_data'])
                cv_count += 1
            except Exception as e:
                logger.warning(f"CV reindex hatası {cv['cv_id']}: {e}")
        
        # Job'ları yeniden indexle
        job_cursor = db.jobs.find({"status": "active"})
        job_count = 0
        async for job in job_cursor:
            try:
                embedding_service.add_job_to_index(job['job_id'], job)
                job_count += 1
            except Exception as e:
                logger.warning(f"Job reindex hatası {job['job_id']}: {e}")
        
        logger.info(f"Reindexing tamamlandı: {cv_count} CV, {job_count} Job")
        
        return {
            "message": "Reindexing başarıyla tamamlandı",
            "indexed_cvs": cv_count,
            "indexed_jobs": job_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Reindexing hatası: {e}")
        raise HTTPException(status_code=500, detail="Reindexing yapılamadı")
