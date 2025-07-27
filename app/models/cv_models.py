from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PersonalInfo(BaseModel):
    """Kişisel bilgi modeli"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None

class Education(BaseModel):
    """Eğitim modeli"""
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    year: Optional[str] = None

class Experience(BaseModel):
    """İş tecrübesi modeli"""
    position: str
    company: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None

class CVData(BaseModel):
    """CV verisi modeli"""
    personal_info: PersonalInfo
    education: List[Education] = []
    experience: List[Experience] = []
    skills: List[str] = []
    language: str = "tr"
    raw_text: Optional[str] = None
    filename: Optional[str] = None

class CVUploadResponse(BaseModel):
    """CV yükleme yanıt modeli"""
    cv_id: str
    filename: str
    status: str
    message: str
    parsed_data: CVData

class CVResponse(BaseModel):
    """CV yanıt modeli"""
    cv_id: str
    filename: str
    uploaded_at: datetime
    file_size: int
    parsed_data: CVData
    status: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CVMatchResult(BaseModel):
    """CV eşleştirme sonucu"""
    job_id: str
    similarity_score: float
    job_title: str
    company: str
    match_details: Dict[str, Any]
