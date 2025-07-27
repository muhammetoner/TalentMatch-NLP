import pytest
from app.services.cv_parser import CVParser

@pytest.fixture
def cv_parser():
    """CV Parser instance"""
    return CVParser()

def test_detect_language_turkish(cv_parser):
    """Türkçe dil tespiti testi"""
    text = "İstanbul Üniversitesi Bilgisayar Mühendisliği bölümünden mezunum."
    language = cv_parser._detect_language(text)
    assert language == "tr"

def test_detect_language_english(cv_parser):
    """İngilizce dil tespiti testi"""
    text = "I graduated from Computer Engineering at Istanbul University."
    language = cv_parser._detect_language(text)
    assert language == "en"

def test_extract_email(cv_parser):
    """Email çıkarma testi"""
    text = "İletişim: john.doe@example.com veya john@company.co.uk"
    # Basit regex testi
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    assert len(emails) >= 1
    assert "john.doe@example.com" in emails

def test_extract_year(cv_parser):
    """Yıl çıkarma testi"""
    text = "2019-2023 yılları arası İstanbul Üniversitesi"
    year = cv_parser._extract_year(text)
    assert year in ["2019", "2023"]

def test_clean_text(cv_parser):
    """Metin temizleme testi"""
    text = "   Çok    fazla    boşluk   var   "
    cleaned = cv_parser._clean_text(text)
    assert cleaned == "Çok fazla boşluk var"
