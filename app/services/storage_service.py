"""
GridFS File Storage Service
MongoDB GridFS ile dosya yönetimi
"""
import gridfs
from typing import Optional, Dict, Any, List
import logging
from io import BytesIO
from bson import ObjectId
from datetime import datetime

logger = logging.getLogger(__name__)

class GridFSService:
    """GridFS ile dosya yönetimi servisi"""
    
    def __init__(self, database):
        self.db = database
        self.fs = gridfs.GridFS(database)
    
    async def store_file(self, file_content: bytes, filename: str, metadata: Dict[str, Any] = None) -> str:
        """
        Dosyayı GridFS'e kaydet
        """
        try:
            # Metadata hazırla
            file_metadata = {
                'filename': filename,
                'upload_date': datetime.utcnow(),
                'content_type': self._get_content_type(filename),
                **(metadata or {})
            }
            
            # Dosyayı kaydet
            file_id = self.fs.put(
                file_content,
                filename=filename,
                metadata=file_metadata
            )
            
            logger.info(f"Dosya GridFS'e kaydedildi: {filename} -> {file_id}")
            return str(file_id)
            
        except Exception as e:
            logger.error(f"GridFS dosya kaydetme hatası: {e}")
            raise
    
    async def get_file(self, file_id: str) -> Optional[bytes]:
        """
        Dosyayı GridFS'den al
        """
        try:
            grid_out = self.fs.get(ObjectId(file_id))
            return grid_out.read()
            
        except Exception as e:
            logger.error(f"GridFS dosya okuma hatası: {e}")
            return None
    
    async def get_file_metadata(self, file_id: str) -> Optional[Dict]:
        """
        Dosya metadata'sını al
        """
        try:
            grid_out = self.fs.get(ObjectId(file_id))
            return {
                'filename': grid_out.filename,
                'length': grid_out.length,
                'upload_date': grid_out.upload_date,
                'content_type': grid_out.content_type,
                'metadata': grid_out.metadata
            }
            
        except Exception as e:
            logger.error(f"GridFS metadata okuma hatası: {e}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """
        Dosyayı GridFS'den sil
        """
        try:
            self.fs.delete(ObjectId(file_id))
            logger.info(f"Dosya GridFS'den silindi: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"GridFS dosya silme hatası: {e}")
            return False
    
    async def list_files(self, filename_pattern: str = None) -> List[Dict]:
        """
        Dosyaları listele
        """
        try:
            query = {}
            if filename_pattern:
                query['filename'] = {'$regex': filename_pattern}
            
            files = []
            for grid_out in self.fs.find(query):
                files.append({
                    'file_id': str(grid_out._id),
                    'filename': grid_out.filename,
                    'length': grid_out.length,
                    'upload_date': grid_out.upload_date,
                    'content_type': grid_out.content_type
                })
            
            return files
            
        except Exception as e:
            logger.error(f"GridFS dosya listeleme hatası: {e}")
            return []
    
    def _get_content_type(self, filename: str) -> str:
        """
        Dosya uzantısından content type belirle
        """
        ext = filename.lower().split('.')[-1]
        
        content_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword',
            'txt': 'text/plain',
            'rtf': 'application/rtf'
        }
        
        return content_types.get(ext, 'application/octet-stream')

# Global GridFS service instance
gridfs_service = None

async def get_gridfs_service(db):
    """GridFS service instance al"""
    global gridfs_service
    if gridfs_service is None:
        gridfs_service = GridFSService(db)
    return gridfs_service
