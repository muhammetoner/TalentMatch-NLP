 
"""
TalentMatch NLP - Embedding Service
SBERT ve FAISS tabanlı vektör embedding ve benzerlik hesaplama servisi
"""

from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import logging
from pathlib import Path
import json
import time

logger = logging.getLogger(__name__)

# Global embedding service instance
embedding_service = None

def get_embedding_service():
    global embedding_service
    if embedding_service is None:
        embedding_service = EmbeddingService()
    return embedding_service

class EmbeddingService:
    """Vektör embedding ve benzerlik hesaplama servisi"""
    
    def __init__(self, 
                 model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                 index_dir: str = "data/embeddings"):
        """
        Service initialization
        Args:
            model_name: Kullanılacak SBERT model adı
            index_dir: FAISS index ve metadata dosyalarının konumu
        """
        self.model_name = model_name
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.dimension = 384  # MiniLM model dimension
        self.cv_index = None
        self.job_index = None
        self.cv_metadata = {}
        self.job_metadata = {}
        
        self._load_model()
    
    def _load_model(self):
        """Sentence transformer modelini yükle"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model yüklendi: {self.model_name}")
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}")
            raise
    
    def create_cv_embedding(self, cv_data: Dict) -> np.ndarray:
        """CV verisinden embedding oluştur"""
        try:
            # CV metnini birleştir
            text_parts = []
            
            # Kişisel bilgiler
            if cv_data.get('personal_info'):
                personal = cv_data['personal_info']
                if personal.get('name'):
                    text_parts.append(f"İsim: {personal['name']}")
            
            # Eğitim
            if cv_data.get('education'):
                edu_texts = []
                for edu in cv_data['education']:
                    edu_text = f"{edu.get('degree', '')} {edu.get('field', '')} {edu.get('institution', '')}"
                    edu_texts.append(edu_text.strip())
                if edu_texts:
                    text_parts.append("Eğitim: " + " ".join(edu_texts))
            
            # Tecrübe
            if cv_data.get('experience'):
                exp_texts = []
                for exp in cv_data['experience']:
                    exp_text = f"{exp.get('position', '')} {exp.get('company', '')} {exp.get('description', '')}"
                    exp_texts.append(exp_text.strip())
                if exp_texts:
                    text_parts.append("Tecrübe: " + " ".join(exp_texts))
            
            # Beceriler
            if cv_data.get('skills'):
                skills_text = "Beceriler: " + " ".join(cv_data['skills'])
                text_parts.append(skills_text)
            
            # Ham metin de ekle
            if cv_data.get('raw_text'):
                text_parts.append(cv_data['raw_text'][:1000])  # İlk 1000 karakter
            
            combined_text = " ".join(text_parts)
            
            if not combined_text.strip():
                raise ValueError("CV'den embedding oluşturmak için yeterli metin bulunamadı")
            
            # Embedding oluştur
            embedding = self.model.encode([combined_text])
            return embedding[0]
            
        except Exception as e:
            logger.error(f"CV embedding oluşturma hatası: {e}")
            raise
    
    def create_job_embedding(self, job_data: Dict) -> np.ndarray:
        """İş ilanından embedding oluştur"""
        try:
            text_parts = []
            
            # İş başlığı
            if job_data.get('title'):
                text_parts.append(f"Pozisyon: {job_data['title']}")
            
            # Şirket
            if job_data.get('company'):
                text_parts.append(f"Şirket: {job_data['company']}")
            
            # Açıklama
            if job_data.get('description'):
                text_parts.append(f"Açıklama: {job_data['description']}")
            
            # Gereken beceriler
            if job_data.get('required_skills'):
                skills_text = "Gereken Beceriler: " + " ".join(job_data['required_skills'])
                text_parts.append(skills_text)
            
            combined_text = " ".join(text_parts)
            
            if not combined_text.strip():
                raise ValueError("İş ilanından embedding oluşturmak için yeterli metin bulunamadı")
            
            embedding = self.model.encode([combined_text])
            return embedding[0]
            
        except Exception as e:
            logger.error(f"İş ilanı embedding oluşturma hatası: {e}")
            raise
    
    def build_faiss_index(self, embeddings: List[np.ndarray], metadata: List[Dict], index_type: str = "cv"):
        """FAISS index oluştur ve metadata ile eşleştir"""
        try:
            index = faiss.IndexFlatL2(self.dimension)
            index.add(np.array(embeddings, dtype=np.float32))
            if index_type == "cv":
                self.cv_index = index
                self.cv_metadata = {i: m for i, m in enumerate(metadata)}
            else:
                self.job_index = index
                self.job_metadata = {i: m for i, m in enumerate(metadata)}
            logger.info(f"FAISS index oluşturuldu: {index_type}")
        except Exception as e:
            logger.error(f"FAISS index oluşturma hatası: {e}")
            raise
    
    def search_similar(self, query_embedding: np.ndarray, top_k: int = 5, index_type: str = "cv") -> List[Dict]:
        """Benzer embedding araması yap"""
        try:
            if index_type == "cv" and self.cv_index:
                D, I = self.cv_index.search(np.array([query_embedding], dtype=np.float32), top_k)
                results = [self.cv_metadata[i] for i in I[0]]
                return results
            elif index_type == "job" and self.job_index:
                D, I = self.job_index.search(np.array([query_embedding], dtype=np.float32), top_k)
                results = [self.job_metadata[i] for i in I[0]]
                return results
            else:
                raise ValueError("FAISS index bulunamadı")
        except Exception as e:
            logger.error(f"Benzerlik arama hatası: {e}")
            raise
    
    def save_index(self, path: str, index_type: str = "cv"):
        """FAISS index ve metadata kaydet"""
        try:
            if index_type == "cv" and self.cv_index:
                faiss.write_index(self.cv_index, path)
                with open(path + ".meta", "wb") as f:
                    pickle.dump(self.cv_metadata, f)
            elif index_type == "job" and self.job_index:
                faiss.write_index(self.job_index, path)
                with open(path + ".meta", "wb") as f:
                    pickle.dump(self.job_metadata, f)
            logger.info(f"FAISS index kaydedildi: {path}")
        except Exception as e:
            logger.error(f"FAISS index kaydetme hatası: {e}")
            raise
    
    def load_index(self, path: str, index_type: str = "cv"):
        """FAISS index ve metadata yükle"""
        try:
            if index_type == "cv":
                self.cv_index = faiss.read_index(path)
                with open(path + ".meta", "rb") as f:
                    self.cv_metadata = pickle.load(f)
            elif index_type == "job":
                self.job_index = faiss.read_index(path)
                with open(path + ".meta", "rb") as f:
                    self.job_metadata = pickle.load(f)
            logger.info(f"FAISS index yüklendi: {path}")
        except Exception as e:
            logger.error(f"FAISS index yükleme hatası: {e}")
            raise
