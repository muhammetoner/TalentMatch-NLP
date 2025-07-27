from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EmploymentType(str, Enum):
    """İstihdam türü"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"

class JobStatus(str, Enum):
    """İş ilanı durumu"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"
    DRAFT = "draft"

class SalaryRange(BaseModel):
    """Maaş aralığı"""
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    currency: str = "TRY"

class JobCreate(BaseModel):
    """İş ilanı oluşturma modeli"""
    title: str = Field(..., min_length=3, max_length=200, description="İş pozisyonu başlığı")
    company: str = Field(..., min_length=2, max_length=100, description="Şirket adı")
    description: str = Field(..., min_length=50, description="İş tanımı")
    requirements: List[str] = Field(default=[], description="İş gereksinimleri")
    required_skills: List[str] = Field(default=[], description="Aranan beceriler")
    location: Optional[str] = Field(None, max_length=100, description="İş yeri")
    salary_range: Optional[SalaryRange] = None
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    
    @field_validator('required_skills')
    @classmethod
    def validate_skills(cls, v):
        if len(v) > 50:
            raise ValueError('En fazla 50 beceri eklenebilir')
        return v

class JobUpdate(BaseModel):
    """İş ilanı güncelleme modeli"""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    company: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, min_length=50)
    requirements: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None
    location: Optional[str] = Field(None, max_length=100)
    salary_range: Optional[SalaryRange] = None
    employment_type: Optional[EmploymentType] = None
    status: Optional[JobStatus] = None

class JobResponse(BaseModel):
    """İş ilanı yanıt modeli"""
    job_id: str
    title: str
    company: str
    description: str
    requirements: List[str]
    required_skills: List[str]
    location: Optional[str]
    salary_range: Optional[SalaryRange]
    employment_type: EmploymentType
    created_at: datetime
    updated_at: datetime
    status: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class JobMatchResult(BaseModel):
    """İş eşleştirme sonucu"""
    cv_id: str
    similarity_score: float
    explanation: str
    candidate_name: str
    candidate_email: str
    match_details: Dict[str, Any]
    uploaded_at: Optional[datetime] = None
