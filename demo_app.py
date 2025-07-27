"""
TalentMatch NLP - Demo Mode
Basit ve güvenilir demo sürümü
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import json
from datetime import datetime
from pathlib import Path

# Import enhanced CV parser
try:
    from enhanced_cv_parser import cv_parser, enhance_skills
except ImportError:
    cv_parser = None
    enhance_skills = lambda x: x

# Demo app
app = FastAPI(
    title="TalentMatch NLP - Demo Mode",
    description="CV Analizi ve Aday Eşleştirme Sistemi - Demo",
    version="1.0.0-demo"
)

# In-memory veri depolama
demo_cvs = []
demo_jobs = []

class CVData(BaseModel):
    name: str
    email: str
    skills: List[str]
    experience_years: int

class JobData(BaseModel):
    title: str
    company: str
    required_skills: List[str]
    description: str
    location: Optional[str] = None
    work_type: Optional[str] = None

@app.post("/demo/cv/upload")
async def upload_cv_file(
    file: UploadFile = File(...),
    name: str = Form(None),
    email: str = Form(None),
    skills: str = Form(None),
    experience: str = Form(None)
):
    """
    CV dosyası yükle ve analiz et
    """
    try:
        # Dosya içeriğini oku
        file_content = await file.read()
        
        if cv_parser:
            # Gelişmiş parser kullan
            parsed_data = cv_parser.parse_file(file_content, file.filename)
            
            if "error" in parsed_data:
                return {"error": parsed_data["error"]}
            
            # Form verilerini parsed data ile birleştir
            cv_data = {
                "name": name or parsed_data.get("name", file.filename.split('.')[0]),
                "email": email or parsed_data.get("email", ""),
                "skills": enhance_skills(
                    (skills.split(',') if skills else []) + parsed_data.get("skills", [])
                ),
                "experience_years": int(experience) if experience else parsed_data.get("experience_years", 0),
                "phone": parsed_data.get("phone", ""),
                "education": parsed_data.get("education", []),
                "languages": parsed_data.get("languages", []),
                "parsing_confidence": parsed_data.get("confidence", 0.0),
                "file_info": {
                    "filename": file.filename,
                    "size": len(file_content),
                    "type": file.content_type
                }
            }
        else:
            # Basit fallback
            cv_data = {
                "name": name or file.filename.split('.')[0],
                "email": email or "",
                "skills": skills.split(',') if skills else [],
                "experience_years": int(experience) if experience else 0
            }
        
        # CV'yi veritabanına ekle
        cv_data["id"] = len(demo_cvs) + 1
        cv_data["added_at"] = datetime.now().isoformat()
        demo_cvs.append(cv_data)
        
        return {
            "message": "CV başarıyla yüklendi ve analiz edildi",
            "cv_id": cv_data["id"],
            "analysis": {
                "extracted_skills": len(cv_data["skills"]),
                "confidence": cv_data.get("parsing_confidence", 0.0),
                "recommendations": _get_cv_recommendations(cv_data)
            },
            "data": cv_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV işleme hatası: {str(e)}")

def _get_cv_recommendations(cv_data: Dict) -> List[str]:
    """CV için öneriler oluştur"""
    recommendations = []
    
    if len(cv_data["skills"]) < 3:
        recommendations.append("Daha fazla teknik beceri eklemeyi düşünün")
    
    if cv_data.get("experience_years", 0) == 0:
        recommendations.append("Deneyim bilgilerinizi ekleyerek profilinizi güçlendirin")
    
    if not cv_data.get("email"):
        recommendations.append("İletişim için e-posta adresinizi eklemeyi unutmayın")
    
    if cv_data.get("parsing_confidence", 0) < 0.7:
        recommendations.append("CV formatınızı iyileştirerek otomatik analizi geliştirebilirsiniz")
    
    return recommendations

@app.get("/")
async def root():
    """Ana sayfa"""
    return {
        "message": "🚀 TalentMatch NLP Demo API",
        "version": "1.0.0-demo",
        "status": "running",
        "features": [
            "CV ekleme",
            "İş ilanı ekleme", 
            "Basit eşleştirme",
            "Demo verileri"
        ],
        "docs": "http://localhost:8000/docs"
    }

@app.get("/health")
async def health():
    """Sistem durumu kontrolü"""
    return {
        "status": "healthy",
        "demo_mode": True,
        "cvs_count": len(demo_cvs),
        "jobs_count": len(demo_jobs),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/demo/cv")
async def add_demo_cv(cv: CVData):
    """Demo CV ekle"""
    cv_dict = cv.dict()
    cv_dict["id"] = len(demo_cvs) + 1
    cv_dict["added_at"] = datetime.now().isoformat()
    
    demo_cvs.append(cv_dict)
    
    return {
        "message": "CV başarıyla eklendi",
        "cv_id": cv_dict["id"],
        "data": cv_dict
    }

@app.post("/demo/job")  
async def add_demo_job(job: JobData):
    """Demo iş ilanı ekle"""
    job_dict = job.dict()
    job_dict["id"] = len(demo_jobs) + 1
    job_dict["added_at"] = datetime.now().isoformat()
    
    demo_jobs.append(job_dict)
    
    return {
        "message": "İş ilanı başarıyla eklendi",
        "job_id": job_dict["id"],
        "data": job_dict
    }

@app.get("/demo/cvs")
async def list_demo_cvs():
    """Demo CV'leri listele"""
    return {
        "cvs": demo_cvs,
        "total": len(demo_cvs)
    }

@app.get("/demo/jobs")
async def list_demo_jobs():
    """Demo iş ilanlarını listele"""
    return {
        "jobs": demo_jobs,
        "total": len(demo_jobs)
    }

@app.get("/demo/match/{job_id}")
async def simple_match(job_id: int):
    """Basit eşleştirme algoritması"""
    try:
        # İş ilanını bul
        job = None
        for j in demo_jobs:
            if j.get("id") == job_id:
                job = j
                break
        
        if not job:
            raise HTTPException(status_code=404, detail="İş ilanı bulunamadı")
        
        # Basit eşleştirme: beceri overlap'ine göre
        matches = []
        job_skills = set(skill.lower() for skill in job.get("required_skills", []))
        
        for cv in demo_cvs:
            cv_skills = set(skill.lower() for skill in cv.get("skills", []))
            
            # Eşleşen beceriler
            matched_skills = job_skills.intersection(cv_skills)
            missing_skills = job_skills - cv_skills
            extra_skills = cv_skills - job_skills
            match_percentage = len(matched_skills) / len(job_skills) * 100 if job_skills else 0
            
            if match_percentage > 0:  # En az 1 beceri eşleşmesi olmalı
                matches.append({
                    "cv_id": cv.get("id"),
                    "candidate_name": cv.get("name", "İsimsiz"),
                    "match_percentage": round(match_percentage, 1),
                    "matched_skills": list(matched_skills),
                    "missing_skills": list(missing_skills),
                    "extra_skills": list(extra_skills),
                    "experience_years": cv.get("experience_years", 0),
                    "cv": cv
                })
        
        # Puana göre sırala
        matches.sort(key=lambda x: x["match_percentage"], reverse=True)
        
        return {
            "job": job,
            "matches": matches,
            "total_candidates": len(matches),
            "total_cvs_checked": len(demo_cvs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eşleştirme hatası: {str(e)}")

@app.get("/demo/analytics")
async def get_analytics():
    """Basit dashboard analitikleri"""
    from collections import Counter
    import statistics
    
    try:
        if not demo_cvs or not demo_jobs:
            return {
                "error": "Analiz için veri bulunamadı. Lütfen önce CV ve İş ilanları ekleyin.",
                "suggestion": "CV Ekle ve İş İlanı Ekle sayfalarını kullanın",
                "cvs_count": len(demo_cvs),
                "jobs_count": len(demo_jobs),
                "summary": {
                    "total_cvs": 0,
                    "total_jobs": 0,
                    "unique_skills": 0,
                    "total_companies": 0,
                    "avg_experience": 0,
                    "avg_salary": 0
                },
                "skills": {
                    "most_common_cv_skills": {},
                    "most_common_job_skills": {},
                    "skill_gaps": {},
                    "skill_surplus": {}
                },
                "experience": {
                    "distribution": {},
                    "categories": {
                        "junior": 0,
                        "mid": 0,
                        "senior": 0
                    }
                },
                "companies": {
                    "top_companies": {},
                    "company_distribution": {}
                },
                "locations": {
                    "job_demand": {},
                    "talent_supply": {}
                },
                "trends": {
                    "hot_skills": [],
                    "growing_areas": ["Machine Learning", "DevOps", "Cloud Computing", "Mobile Development"],
                    "market_insights": {
                        "most_demanded_role": "N/A",
                        "skills_gap_percentage": 0
                    }
                },
                "demographics": {
                    "education_levels": {
                        "bachelor": 0,
                        "master": 0,
                        "phd": 0
                    }
                }
            }
        
        # Beceri istatistikleri
        all_cv_skills = []
        all_job_skills = []
        
        for cv in demo_cvs:
            all_cv_skills.extend(cv.get("skills", []))
        
        for job in demo_jobs:
            all_job_skills.extend(job.get("required_skills", []))
        
        cv_skill_counts = Counter(all_cv_skills)
        job_skill_counts = Counter(all_job_skills)
        
        # Deneyim istatistikleri
        experience_levels = [cv.get("experience_years", 0) for cv in demo_cvs]
        experience_distribution = Counter(experience_levels)
        
        # Şirket istatistikleri
        companies = [job.get("company", "") for job in demo_jobs]
        company_counts = Counter(companies)
        
        # Lokasyon analizi
        cv_locations = [cv.get("location", "Belirtilmemiş") for cv in demo_cvs if cv.get("location")]
        job_locations = [job.get("location", "Belirtilmemiş") for job in demo_jobs if job.get("location")]
        
        location_demand = Counter(job_locations)
        location_supply = Counter(cv_locations)
        
        # Maaş analizi (eğer varsa)
        salary_ranges = []
        for job in demo_jobs:
            salary = job.get("salary_range", "")
            if salary and "-" in salary:
                try:
                    # "15000-25000" formatında maaş aralığını parse et
                    low, high = salary.replace("TL", "").replace("₺", "").split("-")
                    avg_salary = (int(low.strip()) + int(high.strip())) / 2
                    salary_ranges.append(avg_salary)
                except:
                    continue
        
        # Trend beceriler
        trending_skills = ["React", "Python", "JavaScript", "Docker", "AWS", "Kubernetes", 
                          "Machine Learning", "TypeScript", "Vue.js", "Node.js"]
        
        hot_skills_in_jobs = [skill for skill in trending_skills if skill in job_skill_counts]
        
        return {
            "summary": {
                "total_cvs": len(demo_cvs),
                "total_jobs": len(demo_jobs),
                "unique_skills": len(set(all_cv_skills + all_job_skills)),
                "total_companies": len(company_counts),
                "avg_experience": statistics.mean(experience_levels) if experience_levels else 0,
                "median_experience": statistics.median(experience_levels) if experience_levels else 0,
                "avg_salary": statistics.mean(salary_ranges) if salary_ranges else 0
            },
            "skills": {
                "most_common_cv_skills": dict(cv_skill_counts.most_common(15)),
                "most_common_job_skills": dict(job_skill_counts.most_common(15)),
                "skill_gaps": dict((skill, job_skill_counts[skill] - cv_skill_counts.get(skill, 0)) 
                                  for skill in job_skill_counts if job_skill_counts[skill] > cv_skill_counts.get(skill, 0)),
                "skill_surplus": dict((skill, cv_skill_counts[skill] - job_skill_counts.get(skill, 0)) 
                                     for skill in cv_skill_counts if cv_skill_counts[skill] > job_skill_counts.get(skill, 0))
            },
            "experience": {
                "distribution": dict(experience_distribution),
                "categories": {
                    "junior": len([exp for exp in experience_levels if exp <= 2]),
                    "mid": len([exp for exp in experience_levels if 3 <= exp <= 5]),
                    "senior": len([exp for exp in experience_levels if exp > 5])
                }
            },
            "companies": {
                "top_companies": dict(company_counts.most_common(10)),
                "company_distribution": dict(company_counts)
            },
            "locations": {
                "job_demand": dict(location_demand.most_common(10)),
                "talent_supply": dict(location_supply.most_common(10))
            },
            "trends": {
                "hot_skills": hot_skills_in_jobs[:8],
                "growing_areas": ["Machine Learning", "DevOps", "Cloud Computing", "Mobile Development"],
                "market_insights": {
                    "most_demanded_role": max(Counter([job.get("title", "") for job in demo_jobs]).items(), 
                                            key=lambda x: x[1])[0] if demo_jobs else "N/A",
                    "skills_gap_percentage": len([skill for skill in job_skill_counts 
                                                if job_skill_counts[skill] > cv_skill_counts.get(skill, 0)]) / 
                                           len(job_skill_counts) * 100 if job_skill_counts else 0
                }
            },
            "demographics": {
                "education_levels": {
                    "bachelor": len([cv for cv in demo_cvs if any("Lisans" in str(edu) or "Bachelor" in str(edu) 
                                   for edu in cv.get("education", []))]),
                    "master": len([cv for cv in demo_cvs if any("Yüksek Lisans" in str(edu) or "Master" in str(edu) 
                                 for edu in cv.get("education", []))]),
                    "phd": len([cv for cv in demo_cvs if any("Doktora" in str(edu) or "PhD" in str(edu) 
                              for edu in cv.get("education", []))])
                }
            }
        }
    
    except Exception as e:
        print(f"Analytics hatası: {e}")
        return {
            "error": f"Analytics hesaplama hatası: {str(e)}",
            "summary": {"total_cvs": len(demo_cvs), "total_jobs": len(demo_jobs)},
            "data_available": False
        }

if __name__ == "__main__":
    print("🚀 TalentMatch NLP Demo Mode başlatılıyor...")
    print("📍 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("🎯 Sample data yüklemek için: POST /demo/load-sample")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
