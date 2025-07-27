import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict
from jinja2 import Template
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    """Email ve SMS bildirim servisi"""
    
    def __init__(self):
        self.smtp_server = None
        self._setup_email()
    
    def _setup_email(self):
        """Email konfigürasyonunu ayarla"""
        try:
            if settings.email_username and settings.email_password:
                self.smtp_server = smtplib.SMTP(settings.email_host, settings.email_port)
                self.smtp_server.starttls()
                self.smtp_server.login(settings.email_username, settings.email_password)
                logger.info("Email servisi yapılandırıldı")
            else:
                logger.warning("Email credentials yapılandırılmamış")
        except Exception as e:
            logger.error(f"Email setup hatası: {e}")
    
    async def send_match_notification(
        self,
        candidate_email: str,
        candidate_name: str,
        job_data: Dict,
        match_score: float,
        match_details: Dict
    ):
        """Eşleşme bildirimi gönder"""
        try:
            if not self.smtp_server:
                logger.warning("Email servisi kullanılamıyor")
                return False
            
            # Email template
            email_template = """
            <html>
            <body>
                <h2>🎯 Yeni İş Fırsatı Eşleşmesi!</h2>
                
                <p>Merhaba {{ candidate_name }},</p>
                
                <p>Size uygun bir iş fırsatı bulduk!</p>
                
                <div style="border: 1px solid #ddd; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <h3>{{ job_title }}</h3>
                    <p><strong>Şirket:</strong> {{ company }}</p>
                    <p><strong>Konum:</strong> {{ location }}</p>
                    <p><strong>Eşleşme Oranı:</strong> <span style="color: #28a745; font-weight: bold;">%{{ match_score }}</span></p>
                </div>
                
                <h4>📊 Eşleşme Detayları:</h4>
                <ul>
                    {% if matched_skills %}
                    <li><strong>Eşleşen Beceriler:</strong> {{ matched_skills|join(', ') }}</li>
                    {% endif %}
                    
                    {% if missing_skills %}
                    <li><strong>Geliştirebileceğiniz Alanlar:</strong> {{ missing_skills|join(', ') }}</li>
                    {% endif %}
                    
                    {% if extra_skills %}
                    <li><strong>Ekstra Becerileriniz:</strong> {{ extra_skills|join(', ') }}</li>
                    {% endif %}
                </ul>
                
                <div style="margin: 30px 0;">
                    <a href="mailto:hr@{{ company|lower|replace(' ', '') }}.com" 
                       style="background-color: #007bff; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        🚀 Hemen Başvur
                    </a>
                </div>
                
                <p style="color: #666; font-size: 12px;">
                    Bu email TalentMatch NLP sistemi tarafından otomatik olarak gönderilmiştir.<br>
                    Tarih: {{ current_date }}
                </p>
            </body>
            </html>
            """
            
            # Template değerlerini hazırla
            template_vars = {
                'candidate_name': candidate_name,
                'job_title': job_data.get('title', 'Belirtilmemiş'),
                'company': job_data.get('company', 'Belirtilmemiş'),
                'location': job_data.get('location', 'Belirtilmemiş'),
                'match_score': round(match_score, 0),
                'matched_skills': match_details.get('skills_analysis', {}).get('matched_skills', []),
                'missing_skills': match_details.get('skills_analysis', {}).get('missing_skills', []),
                'extra_skills': match_details.get('skills_analysis', {}).get('extra_skills', []),
                'current_date': datetime.now().strftime("%d.%m.%Y %H:%M")
            }
            
            # HTML render et
            template = Template(email_template)
            html_content = template.render(**template_vars)
            
            # Email oluştur
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🎯 %{match_score:.0f} Uyumlu İş Fırsatı - {job_data.get('title', '')}"
            msg['From'] = settings.email_username
            msg['To'] = candidate_email
            
            # HTML içeriği ekle
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Email gönder
            self.smtp_server.send_message(msg)
            
            logger.info(f"Eşleşme bildirimi gönderildi: {candidate_email}")
            return True
            
        except Exception as e:
            logger.error(f"Email gönderme hatası: {e}")
            return False
    
    async def send_job_posted_notification(
        self,
        hr_email: str,
        job_data: Dict,
        potential_matches: int
    ):
        """İş ilanı yayınlandığında HR'a bildirim gönder"""
        try:
            if not self.smtp_server:
                return False
            
            email_template = """
            <html>
            <body>
                <h2>✅ İş İlanınız Başarıyla Yayınlandı!</h2>
                
                <p>Merhaba,</p>
                
                <p>İş ilanınız TalentMatch NLP sisteminde başarıyla yayınlandı ve aday eşleştirme işlemi başlatıldı.</p>
                
                <div style="border: 1px solid #ddd; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <h3>{{ job_title }}</h3>
                    <p><strong>Şirket:</strong> {{ company }}</p>
                    <p><strong>Yayın Tarihi:</strong> {{ publish_date }}</p>
                    <p><strong>Potansiyel Aday Sayısı:</strong> <span style="color: #28a745; font-weight: bold;">{{ potential_matches }}</span></p>
                </div>
                
                <h4>📋 İlan Detayları:</h4>
                <ul>
                    <li><strong>Aranan Beceriler:</strong> {{ required_skills|join(', ') }}</li>
                    <li><strong>İstihdam Türü:</strong> {{ employment_type }}</li>
                    {% if location %}
                    <li><strong>Konum:</strong> {{ location }}</li>
                    {% endif %}
                </ul>
                
                <p>Sistem otomatik olarak en uygun adayları bulacak ve size bildirim gönderecektir.</p>
                
                <div style="margin: 30px 0;">
                    <a href="http://localhost:8000/api/jobs/{{ job_id }}/matches" 
                       style="background-color: #28a745; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        👀 Eşleşmeleri Görüntüle
                    </a>
                </div>
                
                <p style="color: #666; font-size: 12px;">
                    TalentMatch NLP - Akıllı Aday Eşleştirme Sistemi
                </p>
            </body>
            </html>
            """
            
            template_vars = {
                'job_title': job_data.get('title', ''),
                'company': job_data.get('company', ''),
                'job_id': job_data.get('job_id', ''),
                'publish_date': datetime.now().strftime("%d.%m.%Y %H:%M"),
                'potential_matches': potential_matches,
                'required_skills': job_data.get('required_skills', []),
                'employment_type': job_data.get('employment_type', ''),
                'location': job_data.get('location', '')
            }
            
            template = Template(email_template)
            html_content = template.render(**template_vars)
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"✅ İş İlanı Yayınlandı - {job_data.get('title', '')}"
            msg['From'] = settings.email_username
            msg['To'] = hr_email
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            self.smtp_server.send_message(msg)
            
            logger.info(f"İş ilanı bildirimi gönderildi: {hr_email}")
            return True
            
        except Exception as e:
            logger.error(f"İş ilanı bildirimi hatası: {e}")
            return False
    
    async def send_weekly_report(
        self,
        admin_email: str,
        stats: Dict
    ):
        """Haftalık rapor gönder"""
        try:
            if not self.smtp_server:
                return False
            
            email_template = """
            <html>
            <body>
                <h2>📊 TalentMatch NLP - Haftalık Rapor</h2>
                
                <p>Merhaba Admin,</p>
                
                <p>Son 7 günün özet raporu:</p>
                
                <div style="display: flex; gap: 20px; margin: 20px 0;">
                    <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1;">
                        <h4 style="color: #007bff;">📄 CV'ler</h4>
                        <p style="font-size: 24px; margin: 0;"><strong>{{ new_cvs }}</strong></p>
                        <p style="color: #666; margin: 0;">Yeni CV</p>
                    </div>
                    
                    <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1;">
                        <h4 style="color: #28a745;">💼 İş İlanları</h4>
                        <p style="font-size: 24px; margin: 0;"><strong>{{ new_jobs }}</strong></p>
                        <p style="color: #666; margin: 0;">Yeni İlan</p>
                    </div>
                    
                    <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1;">
                        <h4 style="color: #ffc107;">🎯 Eşleşmeler</h4>
                        <p style="font-size: 24px; margin: 0;"><strong>{{ total_matches }}</strong></p>
                        <p style="color: #666; margin: 0;">Toplam Eşleşme</p>
                    </div>
                </div>
                
                <h4>🏆 En Aktif Şirketler:</h4>
                <ul>
                    {% for company in top_companies %}
                    <li>{{ company.company }} - {{ company.job_count }} ilan</li>
                    {% endfor %}
                </ul>
                
                <h4>🔥 En Çok Aranan Beceriler:</h4>
                <ul>
                    {% for skill in top_skills %}
                    <li>{{ skill.skill }} - {{ skill.demand_count }} kez arandı</li>
                    {% endfor %}
                </ul>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Rapor Tarihi: {{ report_date }}<br>
                    TalentMatch NLP - Otomatik Rapor Sistemi
                </p>
            </body>
            </html>
            """
            
            template_vars = {
                'new_cvs': stats.get('recent_activity', {}).get('new_cvs_last_week', 0),
                'new_jobs': stats.get('recent_activity', {}).get('new_jobs_last_week', 0),
                'total_matches': stats.get('recent_activity', {}).get('matches_last_week', 0),
                'top_companies': stats.get('insights', {}).get('top_companies', [])[:3],
                'top_skills': stats.get('insights', {}).get('most_demanded_skills', [])[:5],
                'report_date': datetime.now().strftime("%d.%m.%Y")
            }
            
            template = Template(email_template)
            html_content = template.render(**template_vars)
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📊 TalentMatch NLP Haftalık Rapor - {datetime.now().strftime('%d.%m.%Y')}"
            msg['From'] = settings.email_username
            msg['To'] = admin_email
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            self.smtp_server.send_message(msg)
            
            logger.info(f"Haftalık rapor gönderildi: {admin_email}")
            return True
            
        except Exception as e:
            logger.error(f"Haftalık rapor hatası: {e}")
            return False
    
    def close(self):
        """SMTP bağlantısını kapat"""
        try:
            if self.smtp_server:
                self.smtp_server.quit()
        except Exception as e:
            logger.error(f"SMTP kapatma hatası: {e}")

# Global notification service instance
notification_service = NotificationService()
