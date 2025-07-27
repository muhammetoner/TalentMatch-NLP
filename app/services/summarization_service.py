"""
CV Summarization Service
Extractive summarization ile CV özetleme
"""
from typing import Dict, List, Any, Optional
import logging
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class CVSummarizer:
    """CV özetleme servisi"""
    
    def __init__(self):
        self.setup_nltk()
        self.stemmer = PorterStemmer()
        
        # Türkçe stopwords
        self.turkish_stopwords = {
            'bir', 'bu', 'da', 'de', 'den', 'dır', 'dir', 'için', 'ile', 'ka', 'ki',
            'la', 'le', 'ma', 'me', 'na', 'ne', 'nın', 'nun', 'ra', 're', 'sa', 'se',
            'ta', 'te', 'ya', 'ye', 'yla', 'yle', 'ın', 'in', 'un', 'ün', 'olan',
            'olan', 'olarak', 'oldu', 'olup', 've', 'veya', 'ama', 'ancak', 'çok',
            'daha', 'en', 'gibi', 'her', 'hiç', 'kadar', 'nasıl', 'ne', 'neden',
            'nerede', 'niye', 'şu', 'tüm', 'var', 'yok', 'sonra', 'önce', 'üzere'
        }
    
    def setup_nltk(self):
        """NLTK kaynaklarını indir"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except Exception as e:
            logger.warning(f"NLTK indirme hatası: {e}")
    
    def summarize_cv(self, cv_data: Dict[str, Any], max_sentences: int = 3) -> Dict[str, Any]:
        """
        CV'yi özetle
        """
        try:
            # CV metnini birleştir
            combined_text = self._combine_cv_text(cv_data)
            
            if not combined_text.strip():
                return {"error": "CV'de özetlenecek metin bulunamadı"}
            
            # Cümlelere ayır
            sentences = sent_tokenize(combined_text)
            
            if len(sentences) <= max_sentences:
                return {
                    "summary": combined_text,
                    "sentences": sentences,
                    "method": "full_text"
                }
            
            # Extractive summarization
            summary_sentences = self._extract_important_sentences(
                sentences, 
                max_sentences
            )
            
            # Anahtar kelimeleri çıkar
            keywords = self._extract_keywords(combined_text)
            
            # Beceri analizi
            skills_analysis = self._analyze_skills(cv_data)
            
            return {
                "summary": " ".join(summary_sentences),
                "sentences": summary_sentences,
                "keywords": keywords,
                "skills_analysis": skills_analysis,
                "method": "extractive",
                "original_length": len(sentences),
                "summary_length": len(summary_sentences)
            }
            
        except Exception as e:
            logger.error(f"CV özetleme hatası: {e}")
            return {"error": str(e)}
    
    def _combine_cv_text(self, cv_data: Dict[str, Any]) -> str:
        """CV verilerini tek metin haline getir"""
        text_parts = []
        
        # Kişisel bilgiler
        if cv_data.get('personal_info'):
            personal = cv_data['personal_info']
            if personal.get('name'):
                text_parts.append(f"İsim: {personal['name']}")
            if personal.get('summary'):
                text_parts.append(personal['summary'])
        
        # Eğitim bilgileri
        if cv_data.get('education'):
            for edu in cv_data['education']:
                edu_text = f"{edu.get('degree', '')} {edu.get('field', '')} {edu.get('institution', '')}"
                if edu_text.strip():
                    text_parts.append(edu_text.strip())
        
        # İş tecrübesi
        if cv_data.get('experience'):
            for exp in cv_data['experience']:
                exp_text = f"{exp.get('position', '')} {exp.get('company', '')} {exp.get('description', '')}"
                if exp_text.strip():
                    text_parts.append(exp_text.strip())
        
        # Beceriler
        if cv_data.get('skills'):
            skills_text = "Beceriler: " + ", ".join(cv_data['skills'])
            text_parts.append(skills_text)
        
        # Ham metin
        if cv_data.get('raw_text'):
            text_parts.append(cv_data['raw_text'])
        
        return " ".join(text_parts)
    
    def _extract_important_sentences(self, sentences: List[str], max_sentences: int) -> List[str]:
        """
        TF-IDF ile önemli cümleleri çıkar
        """
        try:
            # TF-IDF vektörleştir
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words=list(self.turkish_stopwords),
                lowercase=True,
                ngram_range=(1, 2)
            )
            
            tfidf_matrix = vectorizer.fit_transform(sentences)
            
            # Cümle skorlarını hesapla
            sentence_scores = {}
            for i, sentence in enumerate(sentences):
                # TF-IDF skorlarının toplamı
                sentence_scores[i] = np.sum(tfidf_matrix[i].toarray())
            
            # En yüksek skorlu cümleleri seç
            top_sentences = sorted(
                sentence_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:max_sentences]
            
            # Orijinal sırada döndür
            selected_indices = sorted([idx for idx, _ in top_sentences])
            
            return [sentences[i] for i in selected_indices]
            
        except Exception as e:
            logger.error(f"Cümle çıkarma hatası: {e}")
            # Fallback: ilk n cümle
            return sentences[:max_sentences]
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Anahtar kelimeleri çıkar
        """
        try:
            # Kelimelere ayır ve temizle
            words = word_tokenize(text.lower())
            words = [word for word in words if word.isalnum() and len(word) > 3]
            words = [word for word in words if word not in self.turkish_stopwords]
            
            # Frekans hesapla
            word_freq = Counter(words)
            
            # En sık kullanılan kelimeleri döndür
            return [word for word, freq in word_freq.most_common(max_keywords)]
            
        except Exception as e:
            logger.error(f"Anahtar kelime çıkarma hatası: {e}")
            return []
    
    def _analyze_skills(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Beceri analizi yap
        """
        try:
            skills = cv_data.get('skills', [])
            
            if not skills:
                return {"total_skills": 0, "categories": {}}
            
            # Beceri kategorileri
            categories = {
                "programming": ["python", "java", "javascript", "c++", "c#", "php", "ruby", "go"],
                "web": ["html", "css", "react", "vue", "angular", "node.js", "django", "flask"],
                "database": ["mysql", "postgresql", "mongodb", "redis", "oracle", "sqlite"],
                "tools": ["git", "docker", "jenkins", "kubernetes", "aws", "azure", "linux"],
                "soft_skills": ["leadership", "communication", "teamwork", "problem solving"]
            }
            
            skill_analysis = {
                "total_skills": len(skills),
                "categories": {}
            }
            
            # Kategorilere göre grupla
            for category, keywords in categories.items():
                category_skills = []
                for skill in skills:
                    if any(keyword in skill.lower() for keyword in keywords):
                        category_skills.append(skill)
                
                if category_skills:
                    skill_analysis["categories"][category] = category_skills
            
            return skill_analysis
            
        except Exception as e:
            logger.error(f"Beceri analizi hatası: {e}")
            return {"error": str(e)}
    
    def generate_cv_recommendations(self, cv_data: Dict[str, Any]) -> List[str]:
        """
        CV için öneriler oluştur
        """
        recommendations = []
        
        try:
            # Beceri eksikliği kontrolü
            skills = cv_data.get('skills', [])
            if len(skills) < 5:
                recommendations.append("Daha fazla teknik beceri ekleyin")
            
            # Tecrübe kontrolü
            experience = cv_data.get('experience', [])
            if not experience:
                recommendations.append("İş tecrübenizi detaylandırın")
            
            # Eğitim kontrolü
            education = cv_data.get('education', [])
            if not education:
                recommendations.append("Eğitim bilgilerinizi ekleyin")
            
            # Kişisel bilgi kontrolü
            personal = cv_data.get('personal_info', {})
            if not personal.get('email'):
                recommendations.append("İletişim bilgilerinizi tamamlayın")
            
            # Proje/portföy önerisi
            if not any('proje' in str(exp).lower() for exp in experience):
                recommendations.append("Proje deneyimlerinizi vurgulayın")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Öneri oluşturma hatası: {e}")
            return ["CV'nizi geliştirmek için daha fazla bilgi ekleyin"]

# Global summarizer instance
cv_summarizer = CVSummarizer()
