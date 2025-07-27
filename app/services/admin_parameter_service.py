"""
Admin Parameter Management Service
Benzerlik algoritması parametrelerini yönetme servisi
"""
import logging
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from app.core.database import get_database

logger = logging.getLogger(__name__)

class AdminParameterService:
    """Admin parametre yönetimi servisi"""
    
    def __init__(self):
        self.default_parameters = {
            "matching_algorithm": {
                "similarity_threshold": 0.7,
                "skills_weight": 0.4,
                "experience_weight": 0.3,
                "education_weight": 0.2,
                "other_weight": 0.1,
                "top_k_results": 10,
                "min_score_threshold": 30.0
            },
            "embedding_settings": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "dimension": 384,
                "normalize_embeddings": True,
                "use_cosine_similarity": True
            },
            "cv_parsing": {
                "max_file_size_mb": 10,
                "allowed_extensions": [".pdf", ".docx", ".doc"],
                "extract_skills_threshold": 0.5,
                "language_detection_threshold": 0.8
            },
            "notification_settings": {
                "email_enabled": True,
                "sms_enabled": False,
                "auto_notify_matches": True,
                "notification_threshold": 70.0,
                "batch_notification_enabled": True
            },
            "gdpr_compliance": {
                "data_retention_days": 30,
                "anonymize_after_days": 365,
                "auto_cleanup_enabled": True,
                "consent_required": True
            }
        }
    
    async def get_parameters(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Sistem parametrelerini getir
        """
        try:
            db = await get_database()
            
            # Veritabanından parametreleri al
            params_doc = await db.system_parameters.find_one({"type": "admin_config"})
            
            if params_doc:
                parameters = params_doc.get("parameters", self.default_parameters)
            else:
                parameters = self.default_parameters
            
            # Belirli kategori istenirse
            if category:
                return parameters.get(category, {})
            
            return parameters
            
        except Exception as e:
            logger.error(f"Parametre getirme hatası: {e}")
            return self.default_parameters
    
    async def update_parameters(self, category: str, parameters: Dict[str, Any]) -> bool:
        """
        Sistem parametrelerini güncelle
        """
        try:
            db = await get_database()
            
            # Mevcut parametreleri al
            current_params = await self.get_parameters()
            
            # Yeni parametreleri birleştir
            current_params[category] = {
                **current_params.get(category, {}),
                **parameters
            }
            
            # Veritabanına kaydet
            await db.system_parameters.update_one(
                {"type": "admin_config"},
                {
                    "$set": {
                        "parameters": current_params,
                        "last_updated": datetime.utcnow(),
                        "updated_by": "admin"
                    }
                },
                upsert=True
            )
            
            logger.info(f"Parametreler güncellendi: {category}")
            return True
            
        except Exception as e:
            logger.error(f"Parametre güncelleme hatası: {e}")
            return False
    
    async def reset_parameters(self, category: Optional[str] = None) -> bool:
        """
        Parametreleri varsayılan değerlere sıfırla
        """
        try:
            db = await get_database()
            
            if category:
                # Belirli kategoriyi sıfırla
                reset_params = {category: self.default_parameters[category]}
            else:
                # Tüm parametreleri sıfırla
                reset_params = self.default_parameters
            
            await db.system_parameters.update_one(
                {"type": "admin_config"},
                {
                    "$set": {
                        "parameters": reset_params,
                        "last_updated": datetime.utcnow(),
                        "updated_by": "admin_reset"
                    }
                },
                upsert=True
            )
            
            logger.info(f"Parametreler sıfırlandı: {category or 'all'}")
            return True
            
        except Exception as e:
            logger.error(f"Parametre sıfırlama hatası: {e}")
            return False
    
    async def get_parameter_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Parametre değişiklik geçmişini getir
        """
        try:
            db = await get_database()
            
            history = []
            async for doc in db.parameter_history.find().sort("timestamp", -1).limit(limit):
                history.append({
                    "timestamp": doc["timestamp"],
                    "category": doc["category"],
                    "old_value": doc["old_value"],
                    "new_value": doc["new_value"],
                    "updated_by": doc["updated_by"]
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Parametre geçmişi getirme hatası: {e}")
            return []
    
    async def validate_parameters(self, category: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parametreleri doğrula
        """
        validation_result = {"valid": True, "errors": []}
        
        try:
            if category == "matching_algorithm":
                # Benzerlik algoritması parametreleri
                if "similarity_threshold" in parameters:
                    if not (0.0 <= parameters["similarity_threshold"] <= 1.0):
                        validation_result["errors"].append("similarity_threshold 0.0-1.0 arasında olmalı")
                
                if "skills_weight" in parameters:
                    if not (0.0 <= parameters["skills_weight"] <= 1.0):
                        validation_result["errors"].append("skills_weight 0.0-1.0 arasında olmalı")
                
                # Ağırlıkların toplamı kontrolü
                weights = [
                    parameters.get("skills_weight", 0.4),
                    parameters.get("experience_weight", 0.3),
                    parameters.get("education_weight", 0.2),
                    parameters.get("other_weight", 0.1)
                ]
                
                if abs(sum(weights) - 1.0) > 0.01:
                    validation_result["errors"].append("Ağırlıkların toplamı 1.0 olmalı")
            
            elif category == "cv_parsing":
                # CV parsing parametreleri
                if "max_file_size_mb" in parameters:
                    if parameters["max_file_size_mb"] <= 0:
                        validation_result["errors"].append("max_file_size_mb pozitif olmalı")
                
                if "allowed_extensions" in parameters:
                    valid_extensions = [".pdf", ".docx", ".doc", ".txt", ".rtf"]
                    for ext in parameters["allowed_extensions"]:
                        if ext not in valid_extensions:
                            validation_result["errors"].append(f"Geçersiz uzantı: {ext}")
            
            elif category == "notification_settings":
                # Bildirim ayarları
                if "notification_threshold" in parameters:
                    if not (0.0 <= parameters["notification_threshold"] <= 100.0):
                        validation_result["errors"].append("notification_threshold 0.0-100.0 arasında olmalı")
            
            elif category == "gdpr_compliance":
                # GDPR uyumluluk
                if "data_retention_days" in parameters:
                    if parameters["data_retention_days"] <= 0:
                        validation_result["errors"].append("data_retention_days pozitif olmalı")
                
                if "anonymize_after_days" in parameters:
                    if parameters["anonymize_after_days"] <= 0:
                        validation_result["errors"].append("anonymize_after_days pozitif olmalı")
            
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
        except Exception as e:
            logger.error(f"Parametre doğrulama hatası: {e}")
            validation_result["valid"] = False
            validation_result["errors"].append(f"Doğrulama hatası: {str(e)}")
        
        return validation_result
    
    async def export_parameters(self) -> Dict[str, Any]:
        """
        Tüm parametreleri dışa aktar
        """
        try:
            parameters = await self.get_parameters()
            
            export_data = {
                "export_date": datetime.utcnow().isoformat(),
                "parameters": parameters,
                "version": "1.0"
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Parametre dışa aktarma hatası: {e}")
            return {"error": str(e)}
    
    async def import_parameters(self, import_data: Dict[str, Any]) -> bool:
        """
        Parametreleri içe aktar
        """
        try:
            if "parameters" not in import_data:
                logger.error("İçe aktarma verisinde parameters bulunamadı")
                return False
            
            db = await get_database()
            
            # Mevcut parametreleri yedekle
            current_params = await self.get_parameters()
            backup_data = {
                "type": "parameter_backup",
                "backup_date": datetime.utcnow(),
                "parameters": current_params
            }
            
            await db.parameter_backups.insert_one(backup_data)
            
            # Yeni parametreleri kaydet
            await db.system_parameters.update_one(
                {"type": "admin_config"},
                {
                    "$set": {
                        "parameters": import_data["parameters"],
                        "last_updated": datetime.utcnow(),
                        "updated_by": "admin_import"
                    }
                },
                upsert=True
            )
            
            logger.info("Parametreler başarıyla içe aktarıldı")
            return True
            
        except Exception as e:
            logger.error(f"Parametre içe aktarma hatası: {e}")
            return False

# Global admin parameter service instance
admin_parameter_service = AdminParameterService()
