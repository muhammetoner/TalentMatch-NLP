from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
import uuid
from datetime import datetime
import logging

from app.core.database import get_database
from app.services.embedding_service import get_embedding_service
from app.models.job_models import JobCreate, JobResponse, JobUpdate

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    db = Depends(get_database)
):
    """Yeni iş ilanı oluştur"""
    try:
        # Unique ID oluştur
        job_id = str(uuid.uuid4())
        
        # İş ilanı dokümanı oluştur
        job_document = {
            "job_id": job_id,
            "title": job_data.title,
            "company": job_data.company,
            "description": job_data.description,
            "requirements": job_data.requirements,
            "required_skills": job_data.required_skills,
            "location": job_data.location,
            "salary_range": job_data.salary_range,
            "employment_type": job_data.employment_type,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        }
        
        # Veritabanına kaydet
        await db.jobs.insert_one(job_document)
        
        # Embedding oluştur ve index'e ekle
        try:
            # Get embedding service instance
            embedding_service = get_embedding_service()
            embedding_service.add_job_to_index(job_id, job_document)
        except Exception as e:
            logger.warning(f"Job embedding oluşturulamadı: {e}")
        
        logger.info(f"İş ilanı oluşturuldu: {job_id}")
        
        return JobResponse(**job_document)
        
    except Exception as e:
        logger.error(f"İş ilanı oluşturma hatası: {e}")
        raise HTTPException(status_code=500, detail=f"İş ilanı oluşturulamadı: {str(e)}")

@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    limit: int = 10,
    skip: int = 0,
    company: Optional[str] = None,
    location: Optional[str] = None,
    db = Depends(get_database)
):
    """İş ilanlarını listele"""
    try:
        # Filtre oluştur
        filter_dict = {"status": "active"}
        if company:
            filter_dict["company"] = {"$regex": company, "$options": "i"}
        if location:
            filter_dict["location"] = {"$regex": location, "$options": "i"}
        
        # İş ilanlarını getir
        cursor = db.jobs.find(filter_dict).sort("created_at", -1).skip(skip).limit(limit)
        jobs = await cursor.to_list(length=limit)
        
        return [JobResponse(**job) for job in jobs]
        
    except Exception as e:
        logger.error(f"İş ilanı listeleme hatası: {e}")
        raise HTTPException(status_code=500, detail="İş ilanları getirilemedi")

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db = Depends(get_database)):
    """Belirli bir iş ilanını getir"""
    try:
        job = await db.jobs.find_one({"job_id": job_id})
        
        if not job:
            raise HTTPException(status_code=404, detail="İş ilanı bulunamadı")
        
        return JobResponse(**job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"İş ilanı getirme hatası: {e}")
        raise HTTPException(status_code=500, detail="İş ilanı bilgileri alınamadı")

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    db = Depends(get_database)
):
    """İş ilanını güncelle"""
    try:
        # Mevcut iş ilanını kontrol et
        existing_job = await db.jobs.find_one({"job_id": job_id})
        if not existing_job:
            raise HTTPException(status_code=404, detail="İş ilanı bulunamadı")
        
        # Güncelleme verilerini hazırla
        update_data = {k: v for k, v in job_update.dict(exclude_unset=True).items()}
        update_data["updated_at"] = datetime.utcnow()
        
        # Veritabanını güncelle
        await db.jobs.update_one(
            {"job_id": job_id},
            {"$set": update_data}
        )
        
        # Güncellenmiş iş ilanını getir
        updated_job = await db.jobs.find_one({"job_id": job_id})
        
        # Embedding'i yeniden oluştur
        try:
            # Get embedding service instance
            embedding_service = get_embedding_service()
            embedding_service.add_job_to_index(job_id, updated_job)
        except Exception as e:
            logger.warning(f"Job embedding güncellenemedi: {e}")
        
        return JobResponse(**updated_job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"İş ilanı güncelleme hatası: {e}")
        raise HTTPException(status_code=500, detail="İş ilanı güncellenemedi")

@router.delete("/{job_id}")
async def delete_job(job_id: str, db = Depends(get_database)):
    """İş ilanını sil"""
    try:
        # İş ilanını soft delete (status = inactive)
        result = await db.jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "inactive", "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="İş ilanı bulunamadı")
        
        # TODO: FAISS index'den de kaldır
        
        return {"message": "İş ilanı başarıyla silindi"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"İş ilanı silme hatası: {e}")
        raise HTTPException(status_code=500, detail="İş ilanı silinemedi")

@router.get("/{job_id}/matches")
async def get_job_matches(
    job_id: str,
    top_k: int = 10,
    min_score: float = 0.0,
    db = Depends(get_database)
):
    """İş ilanına uygun adayları bul"""
    try:
        # İş ilanını getir
        job = await db.jobs.find_one({"job_id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="İş ilanı bulunamadı")
        
        # Get embedding service instance
        embedding_service = get_embedding_service()
        
        # Eşleşen CV'leri bul
        matches = embedding_service.find_matching_cvs(job, top_k)
        
        results = []
        for cv_id, score, cv_data in matches:
            if score >= min_score:
                # CV bilgilerini veritabanından getir
                cv_doc = await db.cvs.find_one({"cv_id": cv_id})
                
                # Detaylı analiz
                match_details = embedding_service.analyze_match_details(cv_data, job)
                
                # Eksik beceriler için açıklama oluştur
                missing_skills = match_details.get('skills_analysis', {}).get('missing_skills', [])
                explanation = f"%{score:.0f} uyum"
                if missing_skills:
                    explanation += f", eksik beceriler: {', '.join(missing_skills[:3])}"
                
                results.append({
                    "cv_id": cv_id,
                    "similarity_score": round(score, 2),
                    "explanation": explanation,
                    "candidate_name": cv_data.get('personal_info', {}).get('name', 'Bilinmiyor'),
                    "candidate_email": cv_data.get('personal_info', {}).get('email', ''),
                    "match_details": match_details,
                    "uploaded_at": cv_doc.get('uploaded_at') if cv_doc else None
                })
        
        # Eşleştirme sonucunu kaydet
        match_record = {
            "job_id": job_id,
            "search_date": datetime.utcnow(),
            "total_candidates": len(results),
            "search_parameters": {
                "top_k": top_k,
                "min_score": min_score
            }
        }
        await db.match_history.insert_one(match_record)
        
        return {
            "job_id": job_id,
            "job_title": job.get('title'),
            "company": job.get('company'),
            "matches": results,
            "total_matches": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"İş eşleştirme hatası: {e}")
        raise HTTPException(status_code=500, detail="Eşleştirme yapılamadı")

@router.post("/{job_id}/search")
async def advanced_job_search(
    job_id: str,
    search_params: dict,
    db = Depends(get_database)
):
    """Gelişmiş aday arama"""
    try:
        # İş ilanını getir
        job = await db.jobs.find_one({"job_id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="İş ilanı bulunamadı")
        
        # Arama parametreleri
        top_k = search_params.get('top_k', 20)
        min_score = search_params.get('min_score', 50.0)
        required_skills = search_params.get('required_skills', [])
        experience_years = search_params.get('experience_years', 0)
        education_level = search_params.get('education_level', '')
        
        # Get embedding service instance
        embedding_service = get_embedding_service()
        
        # Temel eşleştirme
        matches = embedding_service.find_matching_cvs(job, top_k * 2)  # Daha fazla sonuç al
        
        # Filtreleri uygula
        filtered_results = []
        for cv_id, score, cv_data in matches:
            if score < min_score:
                continue
            
            # Beceri filtresi
            if required_skills:
                cv_skills = [skill.lower() for skill in cv_data.get('skills', [])]
                required_matched = sum(1 for skill in required_skills if skill.lower() in cv_skills)
                if required_matched < len(required_skills) * 0.7:  # %70 eşleşme gerekli
                    continue
            
            # Tecrübe filtresi
            if experience_years > 0:
                cv_experience = len(cv_data.get('experience', []))
                if cv_experience < experience_years:
                    continue
            
            # Eğitim filtresi (basit)
            if education_level:
                cv_education = cv_data.get('education', [])
                education_match = any(education_level.lower() in edu.get('degree', '').lower() 
                                    for edu in cv_education)
                if not education_match:
                    continue
            
            filtered_results.append((cv_id, score, cv_data))
        
        # Sonuçları sınırla
        filtered_results = filtered_results[:top_k]
        
        # Detayları hazırla
        results = []
        for cv_id, score, cv_data in filtered_results:
            match_details = embedding_service.analyze_match_details(cv_data, job)
            
            results.append({
                "cv_id": cv_id,
                "similarity_score": round(score, 2),
                "candidate_name": cv_data.get('personal_info', {}).get('name', 'Bilinmiyor'),
                "candidate_email": cv_data.get('personal_info', {}).get('email', ''),
                "match_details": match_details
            })
        
        return {
            "job_id": job_id,
            "search_params": search_params,
            "matches": results,
            "total_matches": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gelişmiş arama hatası: {e}")
        raise HTTPException(status_code=500, detail="Arama yapılamadı")
