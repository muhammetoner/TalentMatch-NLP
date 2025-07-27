"""
SMS Notification Service
SMS ile bildirim gönderme servisi
"""
import logging
from typing import Dict, Any, Optional
import requests
from app.core.config import settings

logger = logging.getLogger(__name__)

class SMSService:
    """SMS bildirim servisi"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'sms_api_key', None)
        self.api_url = getattr(settings, 'sms_api_url', 'https://api.netgsm.com.tr/sms/send/get')
        self.sender_name = getattr(settings, 'sms_sender_name', 'TalentMatch')
    
    async def send_match_notification(
        self, 
        phone_number: str, 
        candidate_name: str, 
        job_title: str, 
        company: str,
        match_score: float
    ) -> bool:
        """
        İş eşleşmesi SMS bildirimi gönder
        """
        try:
            if not self.api_key:
                logger.warning("SMS API key yapılandırılmamış")
                return False
            
            # SMS mesajı hazırla
            message = f"""
🎯 TalentMatch NLP

Merhaba {candidate_name},

Size uygun bir iş fırsatı bulundu!

📋 Pozisyon: {job_title}
🏢 Şirket: {company}
📊 Uyum: %{match_score:.0f}

Detaylar için: http://localhost:5000/jobs

TalentMatch NLP
            """.strip()
            
            return await self._send_sms(phone_number, message)
            
        except Exception as e:
            logger.error(f"SMS eşleşme bildirimi hatası: {e}")
            return False
    
    async def send_job_posted_notification(
        self,
        phone_number: str,
        job_title: str,
        company: str
    ) -> bool:
        """
        İş ilanı yayınlandı SMS bildirimi
        """
        try:
            if not self.api_key:
                logger.warning("SMS API key yapılandırılmamış")
                return False
            
            message = f"""
✅ TalentMatch NLP

İş ilanınız yayınlandı!

📋 {job_title}
🏢 {company}

Sistem otomatik olarak uygun adayları bulup bildirim gönderecektir.

TalentMatch NLP
            """.strip()
            
            return await self._send_sms(phone_number, message)
            
        except Exception as e:
            logger.error(f"SMS iş ilanı bildirimi hatası: {e}")
            return False
    
    async def send_custom_sms(self, phone_number: str, message: str) -> bool:
        """
        Özel SMS gönder
        """
        try:
            if not self.api_key:
                logger.warning("SMS API key yapılandırılmamış")
                return False
            
            return await self._send_sms(phone_number, message)
            
        except Exception as e:
            logger.error(f"Özel SMS gönderimi hatası: {e}")
            return False
    
    async def _send_sms(self, phone_number: str, message: str) -> bool:
        """
        SMS gönderme işlemi (NetGSM API örneği)
        """
        try:
            # Telefon numarasını temizle
            phone_number = self._clean_phone_number(phone_number)
            
            if not phone_number:
                logger.error("Geçersiz telefon numarası")
                return False
            
            # API parametreleri
            params = {
                'usercode': self.api_key,
                'password': getattr(settings, 'sms_password', ''),
                'gsmno': phone_number,
                'message': message,
                'msgheader': self.sender_name,
                'filter': '0',
                'startdate': '',
                'stopdate': ''
            }
            
            # SMS gönder
            response = requests.get(self.api_url, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.text.strip()
                
                # NetGSM response kodları
                if result.startswith('00'):
                    logger.info(f"SMS başarıyla gönderildi: {phone_number}")
                    return True
                else:
                    logger.error(f"SMS gönderim hatası: {result}")
                    return False
            else:
                logger.error(f"SMS API hatası: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"SMS gönderim hatası: {e}")
            return False
    
    def _clean_phone_number(self, phone_number: str) -> Optional[str]:
        """
        Telefon numarasını temizle ve doğrula
        """
        try:
            # Sadece rakamları al
            clean_number = ''.join(filter(str.isdigit, phone_number))
            
            # Türkiye telefon numarası formatı
            if clean_number.startswith('0'):
                clean_number = '90' + clean_number[1:]
            elif clean_number.startswith('90'):
                pass
            elif len(clean_number) == 10:
                clean_number = '90' + clean_number
            
            # Uzunluk kontrolü
            if len(clean_number) != 12:
                return None
            
            return clean_number
            
        except Exception as e:
            logger.error(f"Telefon numarası temizleme hatası: {e}")
            return None
    
    def test_connection(self) -> Dict[str, Any]:
        """
        SMS API bağlantısını test et
        """
        try:
            if not self.api_key:
                return {
                    "status": "error",
                    "message": "SMS API key yapılandırılmamış"
                }
            
            # Test kredisi sorgula (NetGSM örneği)
            credit_url = "https://api.netgsm.com.tr/balance/list/get"
            params = {
                'usercode': self.api_key,
                'password': getattr(settings, 'sms_password', '')
            }
            
            response = requests.get(credit_url, params=params, timeout=10)
            
            if response.status_code == 200:
                credit = response.text.strip()
                
                return {
                    "status": "success",
                    "message": "SMS API bağlantısı başarılı",
                    "credit": credit
                }
            else:
                return {
                    "status": "error",
                    "message": f"SMS API bağlantı hatası: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"SMS API test hatası: {str(e)}"
            }

# Global SMS service instance
sms_service = SMSService()
