from typing import Dict, List, Optional, Tuple
import spacy
import re
import fitz  # PyMuPDF
from docx import Document
import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CVParser:
    """CV parsing servisi - spaCy ve regex tabanlı"""
    
    def __init__(self):
        self.nlp_tr = None
        self.nlp_en = None
        self._load_models()
    
    def _load_models(self):
        """spaCy modellerini yükle"""
        try:
            self.nlp_tr = spacy.load("tr_core_news_lg")
            self.nlp_en = spacy.load("en_core_web_lg")
            logger.info("spaCy modelleri yüklendi")
        except OSError as e:
            logger.error(f"spaCy model yükleme hatası: {e}")
            logger.info("Modelleri indirmek için: python -m spacy download tr_core_news_lg")
    
    async def parse_cv_file(self, file_content: bytes, filename: str) -> Dict:
        """CV dosyasını parse et"""
        try:
            # Dosya türüne göre metin çıkar
            if filename.endswith('.pdf'):
                text = self._extract_text_from_pdf(file_content)
            elif filename.endswith(('.docx', '.doc')):
                text = self._extract_text_from_docx(file_content)
            else:
                raise ValueError(f"Desteklenmeyen dosya türü: {filename}")
            
            if not text.strip():
                raise ValueError("Dosyadan metin çıkarılamadı")
            
            # CV bileşenlerini parse et
            parsed_data = await self._parse_cv_content(text)
            parsed_data['raw_text'] = text
            parsed_data['filename'] = filename
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"CV parsing hatası: {e}")
            raise
    
    def _extract_text_from_pdf(self, content: bytes) -> str:
        """PDF'den metin çıkar"""
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"PDF metin çıkarma hatası: {e}")
            raise
    
    def _extract_text_from_docx(self, content: bytes) -> str:
        """DOCX'den metin çıkar"""
        try:
            doc = Document(io.BytesIO(content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"DOCX metin çıkarma hatası: {e}")
            raise
    
    async def _parse_cv_content(self, text: str) -> Dict:
        """CV içeriğini parse et"""
        # Dil tespiti
        language = self._detect_language(text)
        nlp = self.nlp_tr if language == 'tr' else self.nlp_en
        
        if not nlp:
            raise ValueError("spaCy modeli yüklenmemiş")
        
        doc = nlp(text)
        
        parsed_data = {
            'personal_info': self._extract_personal_info(text, doc),
            'education': self._extract_education(text, doc),
            'experience': self._extract_experience(text, doc),
            'skills': self._extract_skills(text, doc),
            'language': language
        }
        
        return parsed_data
    
    def _detect_language(self, text: str) -> str:
        """Basit dil tespiti"""
        # Türkçe karakterler
        turkish_chars = ['ç', 'ğ', 'ı', 'İ', 'ö', 'ş', 'ü', 'Ç', 'Ğ', 'Ö', 'Ş', 'Ü']
        turkish_score = sum(1 for char in text if char in turkish_chars)
        
        return 'tr' if turkish_score > 10 else 'en'
    
    def _extract_personal_info(self, text: str, doc) -> Dict:
        """Kişisel bilgileri çıkar"""
        personal_info = {}
        
        # İsim (NER ile)
        names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        if names:
            personal_info['name'] = names[0]
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            personal_info['email'] = emails[0]
        
        # Telefon
        phone_patterns = [
            r'(\+90|0)?\s?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}',  # Türk telefon
            r'(\+\d{1,3})?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'  # Genel format
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                personal_info['phone'] = phones[0] if isinstance(phones[0], str) else ''.join(phones[0])
                break
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin_matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_matches:
            personal_info['linkedin'] = f"https://{linkedin_matches[0]}"
        
        return personal_info
    
    def _extract_education(self, text: str, doc) -> List[Dict]:
        """Eğitim bilgilerini çıkar"""
        education = []
        
        # Eğitim anahtar kelimeleri
        edu_keywords = [
            'üniversite', 'university', 'fakülte', 'faculty', 'bölüm', 'department',
            'lisans', 'bachelor', 'yüksek lisans', 'master', 'doktora', 'phd',
            'diploma', 'derece', 'degree', 'mezun', 'graduate'
        ]
        
        lines = text.split('\n')
        current_education = {}
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Eğitim bölümü başlangıcı
            if any(keyword in line_lower for keyword in edu_keywords):
                if current_education:
                    education.append(current_education)
                
                current_education = {
                    'institution': self._clean_text(line),
                    'degree': '',
                    'field': '',
                    'year': self._extract_year(line)
                }
            
            # Yıl bilgisi
            elif current_education and re.search(r'\b(19|20)\d{2}\b', line):
                if not current_education.get('year'):
                    current_education['year'] = self._extract_year(line)
        
        if current_education:
            education.append(current_education)
        
        return education
    
    def _extract_experience(self, text: str, doc) -> List[Dict]:
        """İş tecrübesi bilgilerini çıkar"""
        experience = []
        
        # Tecrübe anahtar kelimeleri
        exp_keywords = [
            'deneyim', 'experience', 'tecrübe', 'çalıştı', 'worked', 'görev',
            'position', 'pozisyon', 'şirket', 'company', 'iş', 'job', 'kariyer'
        ]
        
        lines = text.split('\n')
        current_job = {}
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if any(keyword in line_lower for keyword in exp_keywords):
                if current_job:
                    experience.append(current_job)
                
                current_job = {
                    'position': self._clean_text(line),
                    'company': '',
                    'duration': self._extract_year(line),
                    'description': ''
                }
            
            elif current_job and len(line.strip()) > 20:
                current_job['description'] += line + ' '
        
        if current_job:
            experience.append(current_job)
        
        return experience
    
    def _extract_skills(self, text: str, doc) -> List[str]:
        """Beceri listesini çıkar"""
        skills = []
        
        # Bilinen teknoloji/beceri listeleri
        tech_skills = [
            'python', 'java', 'javascript', 'html', 'css', 'sql', 'mongodb',
            'fastapi', 'django', 'flask', 'react', 'vue', 'angular', 'node.js',
            'docker', 'kubernetes', 'aws', 'azure', 'git', 'linux', 'windows',
            'machine learning', 'deep learning', 'nlp', 'tensorflow', 'pytorch',
            'spacy', 'transformers', 'opencv', 'pandas', 'numpy', 'scikit-learn'
        ]
        
        soft_skills = [
            'leadership', 'liderlik', 'takım çalışması', 'team work', 'iletişim',
            'communication', 'problem solving', 'analitik düşünce', 'yaratıcılık',
            'creativity', 'proje yönetimi', 'project management'
        ]
        
        text_lower = text.lower()
        
        # Teknik beceriler
        for skill in tech_skills:
            if skill.lower() in text_lower:
                skills.append(skill.title())
        
        # Soft skills
        for skill in soft_skills:
            if skill.lower() in text_lower:
                skills.append(skill.title())
        
        # NER ile ek skills
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT"] and len(ent.text) > 2:
                skills.append(ent.text)
        
        return list(set(skills))  # Duplicates'i kaldır
    
    def _extract_year(self, text: str) -> Optional[str]:
        """Metinden yıl çıkar"""
        year_matches = re.findall(r'\b(19|20)\d{2}\b', text)
        return year_matches[0] if year_matches else None
    
    def _clean_text(self, text: str) -> str:
        """Metni temizle"""
        return re.sub(r'\s+', ' ', text.strip())
