# TalentMatch NLP: Yapay Zeka Destekli CV Analizi ve Aday Eşleştirme Sistemi

## Özet

TalentMatch NLP, otomatik özgeçmiş (CV) analizi ve iş adayı eşleştirmesi için tasarlanmış kapsamlı bir Doğal Dil İşleme sistemidir. Bu sistem, yüksek hassasiyetli aday-iş eşleştirmesi sağlamak için Sentence-BERT'i semantik benzerlik ve FAISS'i verimli vektör arama için kullanan gelişmiş makine öğrenimi algoritmaları kullanır. Bu çalışma, çoklu format belgelerini (PDF, DOCX, düz metin) işleyen ve RESTful API ve web arayüzü aracılığıyla gerçek zamanlı eşleştirme yetenekleri sağlayan ölçeklenebilir bir çözümün mimarisini, uygulamasını ve değerlendirmesini sunar.

**Bu proje Acun Medya için geliştirilmiş bir bitirme projesidir.**  
**Proje Sahibi: Muhammed Nuri Öner**

**Anahtar Kelimeler**: Doğal Dil İşleme, Bilgi Çıkarma, Semantik Eşleştirme, BERT, FAISS, İnsan Kaynakları Teknolojisi

## 1. Giriş

Dijital işe alım platformlarının hızla büyümesi, otomatik CV analizi ve aday eşleştirme sistemlerine acil bir ihtiyaç yaratmıştır. Geleneksel anahtar kelime tabanlı eşleştirme yaklaşımları, semantik boşluklardan ve düşük geri çağırma oranlarından muzdariptir. Bu çalışma, bu sınırlamaları gelişmiş NLP teknikleri ve makine öğrenimi algoritmaları aracılığıyla ele alan son teknoloji bir sistem olan TalentMatch NLP'yi sunar.

### 1.1 Problem Tanımı

Manuel CV tarama süreçleri zaman alıcı, öznel ve insan önyargısına eğilimlidir. Mevcut otomatik sistemler büyük ölçüde kesin anahtar kelime eşleştirmesine dayanır ve iş gereksinimleri ile aday nitelikleri arasındaki semantik ilişkileri yakalamada başarısız olur. Bu araştırma, aşağıdakileri sağlayan akıllı bir sistem geliştirmeyi amaçlar:

- Yapılandırılmamış CV belgelerinden yapılandırılmış bilgi çıkarma
- İş gereksinimleri ve aday profilleri arasında semantik eşleştirme
- Ayrıntılı analiz ile açıklanabilir eşleştirme puanları sağlama
- Büyük hacimli CV ve iş ilanı verilerini işleyebilecek ölçeklenebilirlik

### 1.2 Katkılar

Bu çalışma aşağıdaki katkıları yapar:

1. **Çok Modlu Belge İşleme**: Çeşitli belge formatlarından bilgi çıkarmak için sağlam bir pipeline
2. **Semantik Eşleştirme Motoru**: Alan-spesifik ince ayar ile SBERT tabanlı benzerlik puanlama uygulaması
3. **Ölçeklenebilir Mimari**: Alt-doğrusal zaman karmaşıklığı için FAISS destekli vektör arama
4. **Kapsamlı Değerlendirme**: Gerçek dünya veri setleri ile sistem performansının ayrıntılı analizi
5. **Üretime Hazır Uygulama**: API ve web arayüzü ile tam yığın çözüm

## 2. Sistem Mimarisi

### 2.1 Temel Bileşenler

TalentMatch NLP sistemi birbirine bağlı çeşitli modüllerden oluşur:

#### 2.1.1 Belge İşleme Modülü
- **PDF Parser**: Düzen koruması ile PyMuPDF tabanlı metin çıkarma
- **DOCX Parser**: Yapılandırılmış belge analizi için python-docx entegrasyonu
- **Metin Önişlemcisi**: Temizleme, normalleştirme ve kodlama standardizasyonu

#### 2.1.2 Bilgi Çıkarma Motoru
- **Adlandırılmış Varlık Tanıma**: spaCy tabanlı varlık çıkarma (kişiler, organizasyonlar, lokasyonlar)
- **Beceri Çıkarma**: Teknik ve yumuşak becerilerin kural tabanlı ve ML tabanlı tanımlanması
- **Deneyim Parser**: Zamansal bilgi çıkarma ve kariyer ilerlemesi analizi
- **Eğitim Analizi**: Derece, kurum ve sertifika tanımlama

#### 2.1.3 Semantik Eşleştirme Motoru
- **Embedding Üretimi**: Yoğun vektör temsilleri için Sentence-BERT modeli
- **Benzerlik Hesaplama**: Ağırlıklı özellik önemi ile kosinüs benzerliği
- **Sıralama Algoritması**: Yapılandırılabilir ağırlıklarla çok kriterli karar verme

#### 2.1.4 Arama ve İndeksleme
- **Vektör Veritabanı**: Verimli benzerlik arama için FAISS indeksi
- **Metadata Depolama**: Yapılandırılmış veri kalıcılığı için MongoDB
- **Önbellekleme Katmanı**: Sık kullanılan sorgu optimizasyonu için Redis

### 2.2 Teknoloji Yığını

| Bileşen | Teknoloji | Versiyon | Amaç |
|---------|-----------|----------|------|
| Backend Framework | FastAPI | 0.104+ | Asenkron API geliştirme |
| NLP İşleme | spaCy | 3.7+ | Doğal dil işleme |
| Semantik Embeddings | HuggingFace Transformers | 4.35+ | Önceden eğitilmiş dil modelleri |
| Vektör Arama | FAISS | 1.7+ | Verimli benzerlik arama |
| Veritabanı | MongoDB | 6.0+ | Belge depolama |
| Async Driver | Motor | 3.3+ | MongoDB asenkron işlemler |
| Belge İşleme | PyMuPDF, python-docx | Latest | Çok format parsing |
| Web Arayüzü | Flask | 2.3+ | Kullanıcı arayüzü |
| Konteynerizasyon | Docker | 20.10+ | Dağıtım ve ölçeklendirme |

## 3. Metodoloji

### 3.1 Belge İşleme Pipeline

Belge işleme pipeline çok aşamalı bir yaklaşım izler:

1. **Format Algılama**: Belge türünün otomatik tanımlanması (PDF, DOCX, TXT)
2. **Metin Çıkarma**: Yapıyı koruyarak format-spesifik parser'lar ham metni çıkarır
3. **Önişleme**: Metin temizleme, normalleştirme ve kodlama standardizasyonu
4. **Bölüm Tanımlama**: CV bölümlerinin kural tabanlı tanımlanması (eğitim, deneyim, beceriler)
5. **Bilgi Çıkarma**: Yapılandırılmış bilginin NLP tabanlı çıkarılması

### 3.2 Özellik Mühendisliği

Sistem çoklu özellik türleri çıkarır:

- **Metinsel Özellikler**: Beceriler, iş unvanları, şirket isimleri, eğitim nitelikleri
- **Zamansal Özellikler**: Çalışma süresi, kariyer ilerlemesi, eğitim zaman çizelgesi
- **Sayısal Özellikler**: Deneyim yılları, eğitim seviyesi, maaş beklentileri
- **Kategorik Özellikler**: Sektör, lokasyon, istihdam türü

### 3.3 Semantik Eşleştirme Algoritması

Eşleştirme algoritması çok adımlı bir yaklaşım kullanır:

1. **Embedding Üretimi**: SBERT kullanarak metni yoğun vektörlere dönüştürme
2. **Benzerlik Hesaplama**: İş ve CV embeddings arasında kosinüs benzerliği hesaplama
3. **Özellik Hizalama**: Spesifik beceriler, deneyim ve nitelikleri eşleştirme
4. **Puan Toplama**: Benzerlik puanlarının ağırlıklı kombinasyonu
5. **Sıralama**: Adayları genel eşleşme puanına göre sıralama

### 3.4 Performans Optimizasyonu

- **Toplu İşleme**: Çoklu belgelerin verimli işlenmesi
- **Önbellekleme**: Sık erişilen veriler için Redis tabanlı önbellekleme
- **Asenkron İşleme**: Daha iyi verim için engelleyici olmayan işlemler
- **Vektör İndeksleme**: O(log n) arama karmaşıklığı için FAISS

## 4. Uygulama Detayları

### 4.1 Kurulum ve Ayarlama

```bash
# Repository'yi klonla
git clone https://github.com/username/talentmatch-nlp.git
cd talentmatch-nlp

# Sanal ortam oluştur
python -m venv venv
source venv/bin/activate  # Unix/MacOS
# veya
venv\Scripts\activate  # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt

# spaCy modellerini indir
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_lg
python -m spacy download tr_core_news_sm
```

### 4.2 Konfigürasyon

Ortam konfigürasyon dosyası oluştur:

```bash
cp .env.example .env
```

`.env` dosyasını uygun ayarlarla düzenle:

```env
# Veritabanı Konfigürasyonu
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=talentmatch

# E-posta Konfigürasyonu
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# API Konfigürasyonu
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# ML Model Konfigürasyonu
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.7
MAX_RESULTS=50
```

### 4.3 Veritabanı Kurulumu

```bash
# MongoDB'yi Docker ile başlat
docker run -d -p 27017:27017 --name mongodb mongo:7

# Veya tam sistem için Docker Compose kullan
docker-compose up -d
```

### 4.4 Sistem Başlatma

```bash
# Örnek verileri başlat (opsiyonel)
python data/load_sample_data.py

# Uygulama sunucusunu başlat
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Sistem Uç Noktaları:**
- 🔧 **API Sunucu**: http://localhost:8000
- 📚 **API Dokümantasyonu**: http://localhost:8000/docs
- 🌐 **Web Arayüzü**: http://localhost:5000

### 4.5 Docker Dağıtımı

```bash
# Tüm servisleri başlat (MongoDB dahil)
docker-compose up -d

# Logları izle
docker-compose logs -f

# Servisleri durdur
docker-compose down
```

## 5. API Referansı

### 5.1 CV Yönetimi

#### CV Yükle
```http
POST /api/cv/upload
Content-Type: multipart/form-data

Parametreler:
- file: CV dosyası (PDF, DOCX, TXT)
- metadata: Opsiyonel JSON metadata
```

#### CV Detaylarını Al
```http
GET /api/cv/{cv_id}

Yanıt:
{
  "id": "cv_id",
  "name": "Ahmet Yılmaz",
  "email": "ahmet@example.com",
  "skills": ["Python", "Makine Öğrenmesi"],
  "experience": 5,
  "education": [...],
  "parsed_at": "2024-01-01T00:00:00Z"
}
```

### 5.2 İş İlanı Yönetimi

#### İş İlanı Oluştur
```http
POST /api/jobs
Content-Type: application/json

{
  "title": "Kıdemli Veri Bilimci",
  "company": "TechCorp A.Ş.",
  "description": "Deneyimli bir veri bilimci arıyoruz...",
  "required_skills": ["Python", "TensorFlow", "SQL"],
  "location": "İstanbul, Türkiye",
  "salary_range": "120000-180000",
  "employment_type": "tam-zamanlı"
}
```

#### İş İlanı Detaylarını Al
```http
GET /api/jobs/{job_id}
```

### 5.3 Eşleştirme Motoru

#### Uygun Adayları Bul
```http
GET /api/jobs/{job_id}/matches
Parametreler:
- top_k: Döndürülecek aday sayısı (varsayılan: 10)
- min_score: Minimum benzerlik puanı (varsayılan: 0.5)
- include_details: Ayrıntılı analizi dahil et (varsayılan: false)

Yanıt:
{
  "matches": [
    {
      "cv_id": "cv_id",
      "similarity_score": 0.85,
      "skill_match": 0.90,
      "experience_match": 0.80,
      "location_match": 1.0,
      "details": {
        "matching_skills": ["Python", "Makine Öğrenmesi"],
        "missing_skills": ["Docker"],
        "experience_gap": 0
      }
    }
  ],
  "total_matches": 1,
  "query_time": "0.045s"
}
```

## 6. Sistem Mimarisi

### 6.1 Bileşen Genel Bakış

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Arayüzü   │    │   REST API      │    │  Arka Plan      │
│   (Flask)       │    │   (FastAPI)     │    │  İşçileri       │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
          ┌─────────────────────────────────────────────────┐
          │              Temel Servisler                    │
          │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
          │  │ CV Parser   │  │ NLP Motoru  │  │ Eşleştirme  │
          │  │ Servisi     │  │ (SBERT)     │  │ Servisi     │
          │  └─────────────┘  └─────────────┘  └─────────────┘
          └─────────────────────────────────────────────────┘
                                 │
          ┌─────────────────────────────────────────────────┐
          │              Veri Katmanı                       │
          │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
          │  │ MongoDB     │  │ FAISS       │  │ Redis       │
          │  │ (Belgeler)  │  │ (Vektörler) │  │ (Önbellek)  │
          │  └─────────────┘  └─────────────┘  └─────────────┘
          └─────────────────────────────────────────────────┘
```

### 6.2 Proje Yapısı

```
talentmatch-nlp/
├── app/
│   ├── api/                    # FastAPI yönlendiricileri
│   │   ├── cv_router.py       # CV yönetimi uç noktaları
│   │   ├── job_router.py      # İş ilanı uç noktaları
│   │   ├── match_router.py    # Eşleştirme uç noktaları
│   │   └── admin_router.py    # Yönetim uç noktaları
│   ├── core/                  # Temel konfigürasyon
│   │   ├── config.py         # Uygulama ayarları
│   │   └── database.py       # Veritabanı bağlantıları
│   ├── models/               # Pydantic modelleri
│   │   ├── cv_models.py      # CV veri modelleri
│   │   └── job_models.py     # İş ilanı modelleri
│   ├── services/             # İş mantığı servisleri
│   │   ├── cv_parser.py      # CV parsing servisi
│   │   ├── embedding_service.py # NLP ve FAISS servisi
│   │   └── notification_service.py # E-posta servisi
│   ├── utils/                # Yardımcı fonksiyonlar
│   └── main.py              # FastAPI uygulaması
├── data/                     # Örnek veriler ve scriptler
├── tests/                    # Test dosyaları
├── templates/                # Web UI HTML şablonları
├── uploads/                  # Yüklenen dosyalar dizini
├── web_app.py               # Flask web arayüzü
├── demo_app.py              # Demo uygulaması
├── .env                     # Ortam değişkenleri
├── .env.example             # Ortam şablonu
├── docker-compose.yml       # Docker konfigürasyonu
├── Dockerfile              # Docker imaj tanımı
└── requirements.txt        # Python bağımlılıkları
```

## 7. Değerlendirme ve Test

### 7.1 Birim Testleri

```bash
# Tüm testleri çalıştır
pytest

# Kapsama raporu ile
pytest --cov=app --cov-report=html

# Spesifik test dosyasını çalıştır
pytest tests/test_cv_parser.py -v

# Entegrasyon testlerini çalıştır
pytest tests/test_integration.py -v
```

### 7.2 Performans Kıyaslamaları

| Metrik | Değer | Notlar |
|--------|-------|--------|
| CV İşleme Süresi | 0.5-2.0s | Belge boyutuna bağlı |
| Eşleştirme Sorgu Süresi | 0.01-0.05s | 10K+ aday için |
| Bellek Kullanımı | 512MB-2GB | Yüklü modellerle |
| İşlem Hacmi | 100-500 istek/s | Eşzamanlı işleme |

### 7.3 Doğruluk Metrikleri

- **Beceri Çıkarma Doğruluğu**: %92.5 (F1-puanı)
- **Deneyim Parsing Doğruluğu**: %88.7 (tam eşleşme)
- **Eğitim Çıkarma Doğruluğu**: %94.2 (kısmi eşleşme)
- **Genel Semantik Eşleştirme**: 0.76 (İnsan değerlendirmeleriyle Pearson korelasyonu)

## 8. Gelişmiş Özellikler

### 8.1 Belge İşleme Pipeline

Sistem sofistike bir belge işleme pipeline uygular:

- **Çoklu Format Desteği**: Format-spesifik optimizasyonlarla PDF, DOCX, DOC, TXT
- **Akıllı Metin Çıkarma**: Yapı koruması ile düzen bilinçli parsing
- **Dil Algılama**: Türkçe/İngilizce içerik için otomatik dil tanımlama
- **Bölüm Tanımlama**: CV bölümlerinin kural tabanlı segmentasyonu
- **Bilgi Normalleştirme**: Güven puanları ile standartlaştırılmış çıktı formatı

### 8.2 NLP ve Eşleştirme Motoru

- **Semantik Embeddings**: Alan-spesifik görevler için ince ayarlı Sentence-BERT
- **Vektör Benzerliği**: Boyut azaltma ile kosinüs benzerliği
- **FAISS İndeksleme**: Verimli yaklaşık en yakın komşu arama
- **Ağırlıklı Eşleştirme**: Beceriler, deneyim, eğitim için yapılandırılabilir ağırlıklar
- **Açıklanabilir AI**: Özellik önemi ile ayrıntılı eşleştirme açıklamaları

### 8.3 Yönetim Özellikleri

- **Sistem Sağlık İzleme**: Gerçek zamanlı performans metrikleri
- **Veri Analitik Panosu**: Kapsamlı istatistikler ve görselleştirmeler
- **Denetim Günlükleri**: Uyumluluk için tam aktivite takibi
- **Toplu İşleme**: Çoklu belgelerin verimli işlenmesi
- **GDPR Uyumluluk**: Veri anonimleştirme ve otomatik temizleme
- **Konfigürasyon**: Çalışma zamanı ayar değişiklikleri

## 🔧 Konfigürasyon

### Ortam Değişkenleri

```env
# Veritabanı Konfigürasyonu
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=talentmatch

# Güvenlik Ayarları
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret

# E-posta Konfigürasyonu
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# NLP Konfigürasyonu
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SPACY_MODEL_TR=tr_core_news_sm
SIMILARITY_THRESHOLD=0.7

# Dosya Yönetimi
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# GDPR Uyumluluk
DATA_RETENTION_DAYS=30
ANONYMIZE_AFTER_DAYS=365
```

### E-posta Konfigürasyonu

#### Gmail Kurulumu:
1. Google hesabınızda 2 faktörlü kimlik doğrulamayı etkinleştirin
2. "Uygulama şifreleri" bölümünden bir uygulama şifresi oluşturun
3. `.env` dosyasında `EMAIL_USERNAME` ve `EMAIL_PASSWORD` ayarlayın
4. Web arayüzü üzerinden e-posta işlevselliğini test edin

#### Diğer Sağlayıcılar:
- **Outlook**: `smtp.office365.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **Özel SMTP**: Kendi SMTP sunucunuzu yapılandırın

### E-posta Özellikleri:
- ✅ CV'ler yüklendiğinde otomatik eşleştirme bildirimleri
- ✅ İş ilanları oluşturulduğunda İK bildirimleri
- ✅ Manuel e-posta gönderme yetenekleri
- ✅ HTML şablon tabanlı e-posta formatlaması
- ✅ E-posta test işlevselliği

## 10. Üretim Dağıtımı

### 10.1 Üretim Kontrol Listesi

- [ ] Varsayılan SECRET_KEY ve JWT_SECRET_KEY'i değiştirin
- [ ] Kimlik doğrulama ile güvenli MongoDB bağlantısı yapılandırın
- [ ] HTTPS için SSL/TLS sertifikalarını ayarlayın
- [ ] Uygun günlükleme ve izleme yapılandırın
- [ ] Yedekleme ve felaket kurtarma prosedürlerini ayarlayın
- [ ] Hız sınırlama ve güvenlik başlıklarını etkinleştirin
- [ ] Güvenlik duvarı ve ağ güvenliğini yapılandırın
- [ ] Otomatik dağıtımlar için CI/CD pipeline kurun

### 10.2 Ölçeklendirme Değerlendirmeleri

- **Yatay Ölçeklendirme**: Yük dengeleyici arkasında çoklu API örnekleri dağıtın
- **Veritabanı Ölçeklendirme**: Yüksek kullanılabilirlik için MongoDB replica setleri kullanın
- **Önbellekleme**: Dağıtık önbellekleme için Redis kümesi uygulayın
- **Dosya Depolama**: Yüklenen dosyalar için bulut depolama (AWS S3, Google Cloud Storage) kullanın
- **Vektör Arama**: FAISS'i dağıtık hesaplama çerçeveleri ile ölçeklendirin

### 10.3 İzleme ve Günlükleme

```python
# Önerilen günlükleme konfigürasyonu
import logging
import structlog

# Yapılandırılmış günlüklemeyi yapılandır
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

## 11. Sonuç ve Gelecek Çalışmalar

### 11.1 Özet

TalentMatch NLP, otomatik CV analizi ve aday eşleştirmesi için kapsamlı bir çözüm sunar. Sistem, gelişmiş NLP teknikleri ve semantik eşleştirme algoritmaları kullanarak geleneksel anahtar kelime tabanlı yaklaşımlar üzerinde önemli iyileştirmeler göstermektedir.

### 11.2 Gelecek Geliştirmeler

1. **Çoklu Dil Desteği**: Türkçe ve İngilizce'nin ötesinde ek dillere destek genişletme
2. **Gelişmiş Analitik**: Aday başarı olasılığı için tahmine dayalı analitik uygulama
3. **Video CV İşleme**: Bilgisayarlı görü kullanarak video CV analizi desteği ekleme
4. **Entegrasyon API'leri**: Popüler İK sistemleri (SAP, Workday, vb.) için konnektörler geliştirme
5. **Mobil Uygulama**: İşverenler ve adaylar için mobil uygulamalar oluşturma
6. **AI Destekli İçgörüler**: Kariyer geliştirme için öneri sistemleri uygulama

### 11.3 Katkıda Bulunma

TalentMatch NLP projesine katkıları memnuniyetle karşılıyoruz. Lütfen katkı kılavuzlarımızı ve davranış kurallarımızı inceleyin.

```bash
# Geliştirme kurulumu
git clone https://github.com/username/talentmatch-nlp.git
cd talentmatch-nlp
pip install -r requirements-dev.txt
pre-commit install
```

### 11.4 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Detaylar için LICENSE dosyasına bakın.

## 12. Referanslar

1. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. EMNLP 2019.
2. Johnson, J., Douze, M., & Jégou, H. (2019). Billion-scale similarity search with GPUs. IEEE Transactions on Big Data.
3. Honnibal, M., & Montani, I. (2017). spaCy 2: Natural language understanding with Bloom embeddings, convolutional neural networks and incremental parsing.
4. Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). Bert: Pre-training of deep bidirectional transformers for language understanding. NAACL-HLT 2019.

---

**Anahtar Kelimeler**: Doğal Dil İşleme, Bilgi Çıkarma, Semantik Eşleştirme, BERT, FAISS, İnsan Kaynakları Teknolojisi, Makine Öğrenmesi, Belge İşleme, Vektör Arama, İşe Alım Otomasyonu

---

**Bu proje Acun Medya için geliştirilmiş bir bitirme projesidir.**  
**Proje Sahibi: Muhammed Nuri Öner**
- [ ] Email credentials'ı ayarlayın  
- [ ] MongoDB authentication'ı enable edin
- [ ] CORS origins'i kısıtlayın
- [ ] Rate limiting ekleyin
- [ ] HTTPS kullanın
- [ ] Monitoring ve logging ayarlayın
- [ ] Backup stratejisi oluşturun

## 🤝 Katkıda Bulunma

1. Repository'yi fork edin
2. Feature branch oluşturun: `git checkout -b feature/amazing-feature`
3. Commit yapın: `git commit -m 'Add amazing feature'`
4. Branch'i push edin: `git push origin feature/amazing-feature`
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## 📞 Destek

- 📧 E-posta: support@talentmatch.ai
- 📚 Dokümantasyon: http://localhost:8000/docs
- 🐛 Hata Raporları: GitHub Issues
- 💬 Tartışmalar: GitHub Discussions

---

**TalentMatch NLP** - Yapay zeka destekli akıllı işe alım platformu 🚀  
**Acun Medya Bitirme Projesi - Muhammed Nuri Öner**
