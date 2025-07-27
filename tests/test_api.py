import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.fixture
def event_loop():
    """Async test için event loop"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client():
    """Test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Ana endpoint testi"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "TalentMatch NLP API"
    assert data["version"] == "1.0.0"

@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Sağlık kontrolü endpoint testi"""
    response = await client.get("/health")
    # Database bağlantısı olmayabilir test ortamında
    assert response.status_code in [200, 503]

@pytest.mark.asyncio
async def test_cv_list_empty(client):
    """Boş CV listesi testi"""
    response = await client.get("/api/cv/list")
    assert response.status_code == 200
    data = response.json()
    assert "cvs" in data
    assert "total" in data

@pytest.mark.asyncio
async def test_job_list_empty(client):
    """Boş iş ilanı listesi testi"""
    response = await client.get("/api/jobs/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_invalid_cv_id(client):
    """Geçersiz CV ID testi"""
    response = await client.get("/api/cv/nonexistent-id")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_invalid_job_id(client):
    """Geçersiz Job ID testi"""
    response = await client.get("/api/jobs/nonexistent-id")
    assert response.status_code == 404
