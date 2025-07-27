"""
Yardımcı fonksiyonlar
"""

import hashlib
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def generate_hash(text: str) -> str:
    """Metin için hash oluştur"""
    return hashlib.md5(text.encode()).hexdigest()

def clean_filename(filename: str) -> str:
    """Dosya adını temizle"""
    # Türkçe karakterleri değiştir
    char_map = {
        'ç': 'c', 'ğ': 'g', 'ı': 'i', 'İ': 'I', 'ö': 'o', 'ş': 's', 'ü': 'u',
        'Ç': 'C', 'Ğ': 'G', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
    }
    
    for turkish, english in char_map.items():
        filename = filename.replace(turkish, english)
    
    # Özel karakterleri kaldır
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    return filename

def extract_skills_from_text(text: str) -> List[str]:
    """Metinden beceri listesi çıkar"""
    # Yaygın teknoloji becerilerinin listesi
    skill_keywords = [
        # Programming Languages
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
        'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html', 'css', 'sass', 'less',
        
        # Frameworks & Libraries
        'react', 'angular', 'vue', 'svelte', 'django', 'flask', 'fastapi', 'express',
        'spring', 'laravel', 'rails', 'asp.net', 'tensorflow', 'pytorch', 'keras',
        'scikit-learn', 'pandas', 'numpy', 'opencv', 'bootstrap', 'jquery',
        
        # Databases
        'mongodb', 'postgresql', 'mysql', 'sqlite', 'redis', 'elasticsearch', 'cassandra',
        'dynamodb', 'oracle', 'mariadb',
        
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github',
        'terraform', 'ansible', 'chef', 'puppet', 'helm',
        
        # Tools & Others
        'git', 'svn', 'linux', 'windows', 'macos', 'nginx', 'apache', 'postman',
        'jira', 'confluence', 'slack', 'teams', 'figma', 'sketch',
        
        # Methodologies
        'agile', 'scrum', 'kanban', 'devops', 'ci/cd', 'tdd', 'bdd', 'microservices',
        
        # Turkish Tech Terms
        'bilgisayar', 'yazılım', 'donanım', 'ağ', 'güvenlik', 'veri tabanı', 'web tasarım'
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in skill_keywords:
        if skill.lower() in text_lower:
            found_skills.append(skill.title())
    
    return list(set(found_skills))  # Duplicates'i kaldır

def calculate_experience_years(experience_list: List[Dict]) -> int:
    """Tecrübe yılını hesapla"""
    total_months = 0
    
    for exp in experience_list:
        duration = exp.get('duration', '')
        
        # Yıl bilgisini çıkarmaya çalış
        years = re.findall(r'(\d{4})', duration)
        if len(years) >= 2:
            try:
                start_year = int(years[0])
                end_year = int(years[-1])
                months = (end_year - start_year) * 12
                total_months += months
            except ValueError:
                # Varsayılan olarak 1 yıl say
                total_months += 12
        else:
            # Tek yıl varsa veya format tanımlanamıyorsa 1 yıl say
            total_months += 12
    
    return max(total_months // 12, 1)  # En az 1 yıl

def normalize_company_name(company: str) -> str:
    """Şirket adını normalize et"""
    # Yaygın ekleri kaldır
    suffixes = ['ltd', 'ltd.', 'a.ş.', 'a.ş', 'inc', 'inc.', 'corp', 'corp.', 
                'llc', 'gmbh', 'şti', 'şti.', 'co', 'co.']
    
    company_clean = company.lower().strip()
    
    for suffix in suffixes:
        if company_clean.endswith(' ' + suffix):
            company_clean = company_clean[:-len(suffix)-1]
        elif company_clean.endswith(suffix):
            company_clean = company_clean[:-len(suffix)]
    
    return company_clean.title().strip()

def calculate_text_similarity(text1: str, text2: str) -> float:
    """İki metin arasında basit benzerlik hesapla"""
    # Kelimelere ayır ve normalize et
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    
    # Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def format_salary_range(salary_range: Optional[Dict]) -> str:
    """Maaş aralığını formatla"""
    if not salary_range:
        return "Belirtilmemiş"
    
    min_sal = salary_range.get('min_salary')
    max_sal = salary_range.get('max_salary') 
    currency = salary_range.get('currency', 'TRY')
    
    if min_sal and max_sal:
        return f"{min_sal:,} - {max_sal:,} {currency}"
    elif min_sal:
        return f"{min_sal:,}+ {currency}"
    elif max_sal:
        return f"Maksimum {max_sal:,} {currency}"
    else:
        return "Belirtilmemiş"

def is_valid_email(email: str) -> bool:
    """Email formatını kontrol et"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_phone(phone: str) -> bool:
    """Telefon formatını kontrol et (Türkiye)"""
    # Türk telefon numarası formatları
    patterns = [
        r'^\+90\s?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}$',
        r'^0\s?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}$',
        r'^5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}$'
    ]
    
    phone_clean = re.sub(r'[^\d+]', '', phone)
    
    for pattern in patterns:
        if re.match(pattern, phone):
            return True
    
    return False

def get_file_extension(filename: str) -> str:
    """Dosya uzantısını al"""
    return filename.split('.')[-1].lower() if '.' in filename else ''

def is_recent_date(date_obj: datetime, days: int = 30) -> bool:
    """Tarih belirtilen gün sayısından daha yeni mi"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    return date_obj > cutoff

def truncate_text(text: str, max_length: int = 200) -> str:
    """Metni belirtilen uzunlukta kes"""
    if len(text) <= max_length:
        return text
    
    # Kelime sınırında kes
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + "..."

def log_api_call(endpoint: str, user_info: Dict = None):
    """API çağrısını logla"""
    log_data = {
        'endpoint': endpoint,
        'timestamp': datetime.utcnow().isoformat(),
        'user_info': user_info or {}
    }
    
    logger.info(f"API Call: {log_data}")

def sanitize_input(text: str) -> str:
    """Kullanıcı girdisini temizle"""
    if not text:
        return ""
    
    # HTML tag'lerini kaldır
    text = re.sub(r'<[^>]+>', '', text)
    
    # SQL injection pattern'lerini kaldır  
    dangerous_patterns = [
        r'(select|union|insert|update|delete|drop|create|alter)\s',
        r'(script|javascript|onload|onerror)',
        r'(<|>|&lt;|&gt;)'
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()

class DateTimeEncoder:
    """JSON serialization için datetime encoder"""
    
    @staticmethod
    def default(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
