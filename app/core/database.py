from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """MongoDB bağlantı yöneticisi"""
    
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.database: AsyncIOMotorDatabase = None
    
    async def connect(self):
        """Veritabanına bağlan"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.database = self.client[settings.database_name]
            
            # Bağlantıyı test et
            await self.client.admin.command('ping')
            logger.info("MongoDB'ye başarıyla bağlanıldı")
            
            # İndexleri oluştur
            await self._create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"MongoDB bağlantı hatası: {e}")
            raise
    
    async def disconnect(self):
        """Veritabanı bağlantısını kapat"""
        if self.client:
            self.client.close()
            logger.info("MongoDB bağlantısı kapatıldı")
    
    async def _create_indexes(self):
        """Gerekli indeksleri oluştur"""
        try:
            # CV koleksiyonu indeksleri
            await self.database.cvs.create_index("email")
            await self.database.cvs.create_index("uploaded_at")
            
            # Job koleksiyonu indeksleri
            await self.database.jobs.create_index("title")
            await self.database.jobs.create_index("company")
            await self.database.jobs.create_index("created_at")
            
            # Match koleksiyonu indeksleri
            await self.database.matches.create_index([("job_id", 1), ("cv_id", 1)])
            await self.database.matches.create_index("similarity_score")
            
            logger.info("Veritabanı indeksleri oluşturuldu")
            
        except Exception as e:
            logger.error(f"İndeks oluşturma hatası: {e}")

# Global database manager
db_manager = DatabaseManager()

async def get_database() -> AsyncIOMotorDatabase:
    """Veritabanı instance'ını döndür"""
    if not db_manager.database:
        await db_manager.connect()
    return db_manager.database

async def close_database():
    """Veritabanı bağlantısını kapat"""
    await db_manager.disconnect()
