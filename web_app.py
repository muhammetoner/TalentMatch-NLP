"""
TalentMatch NLP - Web Arayüzü
Flask ile kullanıcı dostu arayüz
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import requests
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import os

app = Flask(__name__)
app.secret_key = 'demo-secret-key'

# FastAPI backend URL
API_BASE = "http://localhost:8000"

# Email konfigürasyonu
EMAIL_CONFIG = {
    'host': 'smtp.gmail.com',
    'port': 587,
    'username': os.getenv('EMAIL_USERNAME', 'your-email@gmail.com'),
    'password': os.getenv('EMAIL_PASSWORD', 'your-app-password')
}

def send_email(to_email, subject, html_content):
    """E-posta gönderme fonksiyonu"""
    try:
        # SMTP sunucusuna bağlan
        server = smtplib.SMTP(EMAIL_CONFIG['host'], EMAIL_CONFIG['port'])
        server.starttls()
        server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
        
        # Email oluştur
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG['username']
        msg['To'] = to_email
        
        # HTML içeriği ekle
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Email gönder
        server.send_message(msg)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Email gönderme hatası: {e}")
        return False

def get_match_notification_template(candidate_name, job_data, match_score):
    """Eşleşme bildirimi template'i"""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #4CAF50;">🎯 Yeni İş Fırsatı Eşleşmesi!</h2>
        
        <p>Merhaba <strong>{candidate_name}</strong>,</p>
        
        <p>Size uygun bir iş fırsatı bulduk!</p>
        
        <div style="border: 1px solid #ddd; padding: 15px; margin: 20px 0; border-radius: 5px; background-color: #f9f9f9;">
            <h3 style="color: #333; margin-top: 0;">{job_data.get('title', 'Belirtilmemiş')}</h3>
            <p><strong>Şirket:</strong> {job_data.get('company', 'Belirtilmemiş')}</p>
            <p><strong>Eşleşme Oranı:</strong> <span style="color: #28a745; font-weight: bold; font-size: 18px;">%{match_score:.0f}</span></p>
            <p><strong>Açıklama:</strong> {job_data.get('description', 'Detay bulunmuyor')[:200]}...</p>
        </div>
        
        <div style="margin: 30px 0; text-align: center;">
            <a href="http://localhost:5000/jobs" 
               style="background-color: #007bff; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                🚀 Tüm İş İlanlarını Görüntüle
            </a>
        </div>
        
        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            Bu email TalentMatch NLP sistemi tarafından otomatik olarak gönderilmiştir.<br>
            Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}
        </p>
    </body>
    </html>
    """

def get_job_posted_template(job_data):
    """İş ilanı yayınlandı template'i"""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #28a745;">✅ İş İlanınız Başarıyla Yayınlandı!</h2>
        
        <p>Merhaba,</p>
        
        <p>İş ilanınız TalentMatch NLP sisteminde başarıyla yayınlandı.</p>
        
        <div style="border: 1px solid #ddd; padding: 15px; margin: 20px 0; border-radius: 5px; background-color: #f9f9f9;">
            <h3 style="color: #333; margin-top: 0;">{job_data.get('title', '')}</h3>
            <p><strong>Şirket:</strong> {job_data.get('company', '')}</p>
            <p><strong>Yayın Tarihi:</strong> {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>
            <p><strong>Aranan Beceriler:</strong> {', '.join(job_data.get('required_skills', []))}</p>
        </div>
        
        <p>Sistem otomatik olarak en uygun adayları bulacak ve size bildirim gönderecektir.</p>
        
        <div style="margin: 30px 0; text-align: center;">
            <a href="http://localhost:5000/jobs" 
               style="background-color: #28a745; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                👀 İş İlanlarını Görüntüle
            </a>
        </div>
        
        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            TalentMatch NLP - Akıllı Aday Eşleştirme Sistemi
        </p>
    </body>
    </html>
    """

@app.route('/')
def index():
    """Ana sayfa"""
    try:
        # API durumunu kontrol et
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            api_status = response.json()
            # Doğrudan cvs_count ve jobs_count varsa kullan
            if 'cvs_count' not in api_status:
                # API response'dan CV ve Job sayılarını al
                if 'mongodb' in api_status and 'collections' in api_status['mongodb']:
                    collections = api_status['mongodb']['collections']
                    api_status['cvs_count'] = collections.get('demo_cvs', 0)
                    api_status['jobs_count'] = collections.get('demo_jobs', 0)
                else:
                    api_status['cvs_count'] = 0
                    api_status['jobs_count'] = 0
        else:
            api_status = {
                'status': 'error',
                'cvs_count': 0,
                'jobs_count': 0
            }
    except Exception as e:
        api_status = {
            'status': 'error',
            'cvs_count': 0,
            'jobs_count': 0,
            'error': str(e)
        }
    
    return render_template('index.html', api_status=api_status)

@app.route('/cvs')
def list_cvs():
    """CV listesi"""
    try:
        response = requests.get(f"{API_BASE}/demo/cvs")
        if response.status_code == 200:
            data = response.json()
            cvs = data.get('cvs', [])
        else:
            cvs = []
            flash('CV\'ler yüklenirken hata oluştu', 'error')
    except Exception as e:
        cvs = []
        flash(f'API bağlantı hatası: {str(e)}', 'error')
    
    return render_template('cvs.html', cvs=cvs)

@app.route('/jobs')
def list_jobs():
    """İş ilanları listesi"""
    try:
        response = requests.get(f"{API_BASE}/demo/jobs")
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
        else:
            jobs = []
            flash('İş ilanları yüklenirken hata oluştu', 'error')
    except Exception as e:
        jobs = []
        flash(f'API bağlantı hatası: {str(e)}', 'error')
    
    return render_template('jobs.html', jobs=jobs)

@app.route('/add-cv', methods=['GET', 'POST'])
def add_cv():
    """CV ekleme"""
    if request.method == 'POST':
        try:
            cv_data = {
                'name': request.form['name'],
                'email': request.form['email'],
                'skills': [skill.strip() for skill in request.form['skills'].split(',')],
                'experience_years': int(request.form['experience_years'])
            }
            
            response = requests.post(f"{API_BASE}/demo/cv", json=cv_data)
            
            if response.status_code == 200:
                flash('CV başarıyla eklendi!', 'success')
                
                # Eşleşen işler için e-posta gönder
                try:
                    match_response = requests.get(f"{API_BASE}/demo/cvs")
                    if match_response.status_code == 200:
                        # Basit eşleşme kontrolü - gerçek sistemde AI matching kullanılır
                        jobs_response = requests.get(f"{API_BASE}/demo/jobs")
                        if jobs_response.status_code == 200:
                            jobs_data = jobs_response.json()
                            jobs = jobs_data.get('jobs', [])
                            
                            # En uygun işi bul (basit eşleşme)
                            best_match = None
                            best_score = 0
                            
                            for job in jobs:
                                job_skills = job.get('required_skills', [])
                                cv_skills = cv_data['skills']
                                
                                # Basit eşleşme skoru hesapla
                                matched_skills = set(job_skills) & set(cv_skills)
                                if job_skills:
                                    score = (len(matched_skills) / len(job_skills)) * 100
                                    if score > best_score:
                                        best_score = score
                                        best_match = job
                            
                            # En az %30 eşleşme varsa e-posta gönder
                            if best_match and best_score >= 30:
                                email_content = get_match_notification_template(
                                    cv_data['name'], 
                                    best_match, 
                                    best_score
                                )
                                
                                email_sent = send_email(
                                    cv_data['email'],
                                    f"🎯 %{best_score:.0f} Uyumlu İş Fırsatı - {best_match.get('title', '')}",
                                    email_content
                                )
                                
                                if email_sent:
                                    flash('Eşleşen iş fırsatı için e-posta gönderildi!', 'success')
                                else:
                                    flash('E-posta gönderilemedi (ayarları kontrol edin)', 'warning')
                
                except Exception as e:
                    print(f"E-posta gönderme hatası: {e}")
                    flash('E-posta gönderilemedi', 'warning')
                
                return redirect(url_for('list_cvs'))
            else:
                flash('CV eklenirken hata oluştu', 'error')
        except Exception as e:
            flash(f'Hata: {str(e)}', 'error')
    
    return render_template('add_cv.html')

@app.route('/add-job', methods=['GET', 'POST'])
def add_job():
    """İş ilanı ekleme"""
    if request.method == 'POST':
        try:
            job_data = {
                'title': request.form['title'],
                'company': request.form['company'],
                'description': request.form['description'],
                'required_skills': [skill.strip() for skill in request.form['required_skills'].split(',')]
            }
            
            response = requests.post(f"{API_BASE}/demo/job", json=job_data)
            
            if response.status_code == 200:
                flash('İş ilanı başarıyla eklendi!', 'success')
                
                # HR e-postası varsa bildirim gönder
                hr_email = request.form.get('hr_email')
                if hr_email and hr_email.strip():
                    try:
                        email_content = get_job_posted_template(job_data)
                        
                        email_sent = send_email(
                            hr_email,
                            f"✅ İş İlanı Yayınlandı - {job_data.get('title', '')}",
                            email_content
                        )
                        
                        if email_sent:
                            flash('HR bildirim e-postası gönderildi!', 'success')
                        else:
                            flash('HR e-postası gönderilemedi (ayarları kontrol edin)', 'warning')
                    
                    except Exception as e:
                        print(f"HR e-posta hatası: {e}")
                        flash('HR e-postası gönderilemedi', 'warning')
                
                return redirect(url_for('list_jobs'))
            else:
                flash('İş ilanı eklenirken hata oluştu', 'error')
        except Exception as e:
            flash(f'Hata: {str(e)}', 'error')
    
    return render_template('add_job.html')

@app.route('/match/<int:job_id>')
def view_matches(job_id):
    """Eşleşmeleri görüntüle"""
    try:
        response = requests.get(f"{API_BASE}/demo/match/{job_id}")
        
        if response.status_code == 200:
            data = response.json()
            job = data.get('job', {})
            matches = data.get('matches', [])
        else:
            job = {}
            matches = []
            flash('Eşleşmeler yüklenirken hata oluştu', 'error')
    except Exception as e:
        job = {}
        matches = []
        flash(f'API bağlantı hatası: {str(e)}', 'error')
    
    return render_template('matches.html', job=job, matches=matches)

@app.route('/api/add-cv', methods=['POST'])
def api_add_cv():
    """API endpoint for CV upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Dosya seçilmedi'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400
        
        # For demo, we'll create CV data from form
        cv_data = {
            'name': request.form.get('name', file.filename.split('.')[0]),
            'email': request.form.get('email', f"{file.filename.split('.')[0]}@example.com"),
            'skills': [skill.strip() for skill in request.form.get('skills', 'Python,JavaScript').split(',') if skill.strip()],
            'experience_years': int(request.form.get('experience', '2'))
        }
        
        # Send to demo API
        response = requests.post(f"{API_BASE}/demo/cv", json=cv_data)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'CV yükleme başarısız'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-job', methods=['POST'])
def api_add_job():
    """API endpoint for job creation"""
    try:
        data = request.get_json()
        
        # Send to demo API
        response = requests.post(f"{API_BASE}/demo/job", json=data)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'İş ilanı ekleme başarısız'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """Analytics dashboard"""
    try:
        response = requests.get(f"{API_BASE}/demo/analytics")
        analytics = response.json() if response.status_code == 200 else None
    except Exception as e:
        analytics = None
        flash(f'Analytics verisi alınamadı: {str(e)}', 'error')
    
    return render_template('dashboard.html', analytics=analytics)

@app.route('/jobs')
def jobs():
    """İş ilanları listesi (alias for list_jobs)"""
    return list_jobs()

@app.route('/cvs')  
def cvs():
    """CV'ler listesi (alias for list_cvs)"""
    return list_cvs()

@app.route('/api-docs')
def api_docs():
    """API dokümantasyonuna yönlendir"""
    return redirect(f"{API_BASE}/docs")

@app.route('/send-email', methods=['GET', 'POST'])
def send_email_page():
    """E-posta gönderme sayfası"""
    if request.method == 'POST':
        try:
            to_email = request.form['to_email']
            subject = request.form['subject']
            message = request.form['message']
            
            # HTML template ile e-posta içeriği hazırla
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #007bff;">TalentMatch NLP</h2>
                <div style="border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 5px;">
                    {message.replace('\\n', '<br>')}
                </div>
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Bu email TalentMatch NLP sistemi tarafından gönderilmiştir.<br>
                    Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}
                </p>
            </body>
            </html>
            """
            
            email_sent = send_email(to_email, subject, html_content)
            
            if email_sent:
                flash('E-posta başarıyla gönderildi!', 'success')
            else:
                flash('E-posta gönderilemedi! E-posta ayarlarını kontrol edin.', 'error')
                
        except Exception as e:
            flash(f'Hata: {str(e)}', 'error')
    
    return render_template('send_email.html')

@app.route('/email-settings', methods=['GET', 'POST'])
def email_settings():
    """E-posta ayarları"""
    if request.method == 'POST':
        try:
            # Ayarları güncelle (gerçek uygulamada veritabanında saklanır)
            EMAIL_CONFIG['username'] = request.form['username']
            EMAIL_CONFIG['password'] = request.form['password']
            EMAIL_CONFIG['host'] = request.form.get('host', 'smtp.gmail.com')
            EMAIL_CONFIG['port'] = int(request.form.get('port', 587))
            
            # Test e-postası gönder
            test_email = request.form.get('test_email')
            if test_email:
                test_content = """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #28a745;">✅ E-posta Ayarları Test Edildi</h2>
                    <p>Tebrikler! E-posta ayarlarınız doğru şekilde yapılandırılmış.</p>
                    <p>TalentMatch NLP sistemi artık e-posta gönderebilir.</p>
                </body>
                </html>
                """
                
                if send_email(test_email, "TalentMatch NLP - E-posta Test", test_content):
                    flash('E-posta ayarları kaydedildi ve test e-postası gönderildi!', 'success')
                else:
                    flash('Ayarlar kaydedildi ancak test e-postası gönderilemedi!', 'warning')
            else:
                flash('E-posta ayarları kaydedildi!', 'success')
                
        except Exception as e:
            flash(f'Hata: {str(e)}', 'error')
    
    return render_template('email_settings.html', config=EMAIL_CONFIG)

@app.route('/admin/parameters')
def admin_parameters():
    """Admin parametre yönetimi"""
    try:
        # API'den parametreleri al
        response = requests.get(f"{API_BASE}/admin/parameters/matching_algorithm")
        if response.status_code == 200:
            parameters = response.json()
        else:
            parameters = {}
            flash('Parametreler yüklenemedi', 'error')
    except Exception as e:
        parameters = {}
        flash(f'API bağlantı hatası: {str(e)}', 'error')
    
    return render_template('admin_parameters.html', parameters=parameters)

@app.route('/admin/analytics')
def admin_analytics():
    """Admin analitik dashboard"""
    try:
        # Kapsamlı analitik al
        response = requests.get(f"{API_BASE}/demo/analytics")
        if response.status_code == 200:
            analytics = response.json()
        else:
            analytics = {}
            flash('Analitik veriler yüklenemedi', 'error')
    except Exception as e:
        analytics = {}
        flash(f'API bağlantı hatası: {str(e)}', 'error')
    
    return render_template('admin_analytics.html', analytics=analytics)

@app.route('/admin/system')
def admin_system():
    """Admin sistem yönetimi"""
    try:
        # Sistem durumu al
        response = requests.get(f"{API_BASE}/admin/system/health")
        if response.status_code == 200:
            system_health = response.json()
        else:
            # Örnek sistem durumu
            system_health = {
                'database': {
                    'collections': 8,
                    'total_size': 52428800,  # 50 MB
                    'index_size': 10485760   # 10 MB
                },
                'collections': {
                    'cvs': {'count': 150, 'size': 20971520, 'avgObjSize': 139810},
                    'jobs': {'count': 45, 'size': 5242880, 'avgObjSize': 116508},
                    'matches': {'count': 320, 'size': 15728640, 'avgObjSize': 49152},
                    'embeddings': {'count': 150, 'size': 8388608, 'avgObjSize': 55924},
                    'notifications': {'count': 280, 'size': 2097152, 'avgObjSize': 7490}
                }
            }
            flash('Sistem durumu yüklenemedi, örnek veri gösteriliyor', 'warning')
    except Exception as e:
        # Hata durumunda örnek veri
        system_health = {
            'database': {
                'collections': 8,
                'total_size': 52428800,  # 50 MB
                'index_size': 10485760   # 10 MB
            },
            'collections': {
                'cvs': {'count': 150, 'size': 20971520, 'avgObjSize': 139810},
                'jobs': {'count': 45, 'size': 5242880, 'avgObjSize': 116508},
                'matches': {'count': 320, 'size': 15728640, 'avgObjSize': 49152},
                'embeddings': {'count': 150, 'size': 8388608, 'avgObjSize': 55924},
                'notifications': {'count': 280, 'size': 2097152, 'avgObjSize': 7490}
            }
        }
        flash(f'API bağlantı hatası: {str(e)}', 'error')
    
    return render_template('admin_system.html', system_health=system_health)

if __name__ == '__main__':
    print("🌐 TalentMatch NLP Web Arayüzü başlatılıyor...")
    print("📍 Web UI: http://localhost:5000")
    print("📍 API: http://localhost:8000")
    print("💡 Önce demo_app.py'yi çalıştırdığınızdan emin olun!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
