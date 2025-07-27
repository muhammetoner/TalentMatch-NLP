"""
Enhanced Storage Service with S3 and GridFS support
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime
import hashlib
import mimetypes
from pathlib import Path

# GridFS imports
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

# S3 imports
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Local storage
import aiofiles
import os

logger = logging.getLogger(__name__)

class EnhancedStorageService:
    """Gelişmiş dosya saklama servisi - S3, GridFS ve local storage desteği"""
    
    def __init__(self, storage_config: Dict[str, Any]):
        self.config = storage_config
        self.storage_type = storage_config.get('type', 'local')  # 'local', 'gridfs', 's3', 'hybrid'
        
        # Storage clients
        self.s3_client = None
        self.gridfs_bucket = None
        self.local_path = storage_config.get('local_path', './uploads')
        
        # Initialize based on config
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage backends"""
        if self.storage_type in ['s3', 'hybrid']:
            self._initialize_s3()
        
        if self.storage_type in ['gridfs', 'hybrid']:
            self._initialize_gridfs()
        
        if self.storage_type in ['local', 'hybrid']:
            self._initialize_local()
    
    def _initialize_s3(self):
        """Initialize S3 client"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config.get('s3_access_key'),
                aws_secret_access_key=self.config.get('s3_secret_key'),
                region_name=self.config.get('s3_region', 'us-east-1')
            )
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.config.get('s3_bucket'))
            logger.info("S3 storage initialized successfully")
            
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"S3 initialization failed: {e}")
            if self.storage_type == 's3':
                raise
    
    def _initialize_gridfs(self):
        """Initialize GridFS"""
        try:
            if self.config.get('mongodb_client'):
                db = self.config['mongodb_client'][self.config.get('database_name', 'talentmatch')]
                self.gridfs_bucket = AsyncIOMotorGridFSBucket(db)
                logger.info("GridFS storage initialized successfully")
        except Exception as e:
            logger.error(f"GridFS initialization failed: {e}")
            if self.storage_type == 'gridfs':
                raise
    
    def _initialize_local(self):
        """Initialize local storage"""
        try:
            os.makedirs(self.local_path, exist_ok=True)
            logger.info(f"Local storage initialized: {self.local_path}")
        except Exception as e:
            logger.error(f"Local storage initialization failed: {e}")
            if self.storage_type == 'local':
                raise
    
    async def store_file(
        self, 
        file_content: bytes, 
        filename: str, 
        metadata: Optional[Dict] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store file with automatic backend selection
        Returns storage info including URLs and identifiers
        """
        if not content_type:
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # Generate file hash for deduplication
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Enhanced metadata
        enhanced_metadata = {
            'filename': filename,
            'content_type': content_type,
            'file_size': len(file_content),
            'file_hash': file_hash,
            'upload_timestamp': datetime.utcnow(),
            'original_metadata': metadata or {}
        }
        
        results = {}
        
        try:
            if self.storage_type == 'hybrid':
                # Store in multiple backends for redundancy
                results['s3'] = await self._store_to_s3(file_content, filename, enhanced_metadata)
                results['gridfs'] = await self._store_to_gridfs(file_content, filename, enhanced_metadata)
                results['local'] = await self._store_to_local(file_content, filename, enhanced_metadata)
                results['primary_url'] = results['s3']['url']
                
            elif self.storage_type == 's3':
                results = await self._store_to_s3(file_content, filename, enhanced_metadata)
                
            elif self.storage_type == 'gridfs':
                results = await self._store_to_gridfs(file_content, filename, enhanced_metadata)
                
            else:  # local
                results = await self._store_to_local(file_content, filename, enhanced_metadata)
            
            results['metadata'] = enhanced_metadata
            logger.info(f"File stored successfully: {filename} ({len(file_content)} bytes)")
            return results
            
        except Exception as e:
            logger.error(f"File storage failed: {e}")
            raise
    
    async def _store_to_s3(self, content: bytes, filename: str, metadata: Dict) -> Dict[str, Any]:
        """Store file to S3"""
        if not self.s3_client:
            raise ValueError("S3 client not initialized")
        
        bucket = self.config.get('s3_bucket')
        key = f"cv_files/{datetime.now().year}/{datetime.now().month}/{metadata['file_hash'][:8]}_{filename}"
        
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=content,
                ContentType=metadata['content_type'],
                Metadata={
                    'original_filename': filename,
                    'file_hash': metadata['file_hash'],
                    'upload_timestamp': metadata['upload_timestamp'].isoformat()
                }
            )
            
            # Generate pre-signed URL for access
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=3600  # 1 hour
            )
            
            return {
                'storage_type': 's3',
                'bucket': bucket,
                'key': key,
                'url': url,
                'permanent_url': f"s3://{bucket}/{key}"
            }
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise
    
    async def _store_to_gridfs(self, content: bytes, filename: str, metadata: Dict) -> Dict[str, Any]:
        """Store file to GridFS"""
        if not self.gridfs_bucket:
            raise ValueError("GridFS bucket not initialized")
        
        try:
            # Upload to GridFS
            file_id = await self.gridfs_bucket.upload_from_stream(
                filename,
                content,
                metadata=metadata
            )
            
            return {
                'storage_type': 'gridfs',
                'file_id': str(file_id),
                'url': f"/api/files/gridfs/{file_id}",
                'gridfs_id': file_id
            }
            
        except Exception as e:
            logger.error(f"GridFS upload failed: {e}")
            raise
    
    async def _store_to_local(self, content: bytes, filename: str, metadata: Dict) -> Dict[str, Any]:
        """Store file locally"""
        try:
            # Create subdirectory structure
            year_month = datetime.now().strftime("%Y/%m")
            directory = Path(self.local_path) / year_month
            directory.mkdir(parents=True, exist_ok=True)
            
            # Generate safe filename
            safe_filename = f"{metadata['file_hash'][:8]}_{filename}"
            file_path = directory / safe_filename
            
            # Write file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Store metadata separately
            metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
            async with aiofiles.open(metadata_path, 'w') as f:
                import json
                await f.write(json.dumps(metadata, default=str, indent=2))
            
            return {
                'storage_type': 'local',
                'file_path': str(file_path),
                'url': f"/api/files/local/{year_month}/{safe_filename}",
                'local_path': file_path
            }
            
        except Exception as e:
            logger.error(f"Local storage failed: {e}")
            raise
    
    async def retrieve_file(self, file_identifier: str, storage_type: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve file from storage"""
        try:
            if storage_type == 's3' or (not storage_type and self.s3_client):
                return await self._retrieve_from_s3(file_identifier)
            elif storage_type == 'gridfs' or (not storage_type and self.gridfs_bucket):
                return await self._retrieve_from_gridfs(file_identifier)
            else:
                return await self._retrieve_from_local(file_identifier)
                
        except Exception as e:
            logger.error(f"File retrieval failed: {e}")
            raise
    
    async def delete_file(self, file_identifier: str, storage_type: Optional[str] = None) -> bool:
        """Delete file from storage"""
        try:
            success = True
            
            if self.storage_type == 'hybrid':
                # Delete from all storages
                for st in ['s3', 'gridfs', 'local']:
                    try:
                        if st == 's3' and self.s3_client:
                            await self._delete_from_s3(file_identifier)
                        elif st == 'gridfs' and self.gridfs_bucket:
                            await self._delete_from_gridfs(file_identifier)
                        elif st == 'local':
                            await self._delete_from_local(file_identifier)
                    except Exception as e:
                        logger.warning(f"Failed to delete from {st}: {e}")
                        success = False
            else:
                if storage_type == 's3':
                    await self._delete_from_s3(file_identifier)
                elif storage_type == 'gridfs':
                    await self._delete_from_gridfs(file_identifier)
                else:
                    await self._delete_from_local(file_identifier)
            
            return success
            
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        stats = {
            'storage_type': self.storage_type,
            'timestamp': datetime.utcnow(),
            'backends': {}
        }
        
        try:
            if self.s3_client:
                stats['backends']['s3'] = await self._get_s3_stats()
            
            if self.gridfs_bucket:
                stats['backends']['gridfs'] = await self._get_gridfs_stats()
            
            if self.storage_type in ['local', 'hybrid']:
                stats['backends']['local'] = await self._get_local_stats()
                
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            stats['error'] = str(e)
        
        return stats
    
    async def _get_s3_stats(self) -> Dict[str, Any]:
        """Get S3 storage statistics"""
        try:
            bucket = self.config.get('s3_bucket')
            
            # List objects to get count and size
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket, Prefix='cv_files/')
            
            total_size = 0
            total_count = 0
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_size += obj['Size']
                        total_count += 1
            
            return {
                'total_files': total_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'bucket': bucket
            }
            
        except Exception as e:
            logger.error(f"S3 stats failed: {e}")
            return {'error': str(e)}
    
    async def _get_gridfs_stats(self) -> Dict[str, Any]:
        """Get GridFS storage statistics"""
        try:
            db = self.gridfs_bucket._collection.database
            
            # Get GridFS stats
            stats = await db.command("collStats", "fs.files")
            
            return {
                'total_files': stats.get('count', 0),
                'total_size_bytes': stats.get('size', 0),
                'total_size_mb': round(stats.get('size', 0) / 1024 / 1024, 2),
                'avg_file_size': round(stats.get('avgObjSize', 0), 2)
            }
            
        except Exception as e:
            logger.error(f"GridFS stats failed: {e}")
            return {'error': str(e)}
    
    async def _get_local_stats(self) -> Dict[str, Any]:
        """Get local storage statistics"""
        try:
            total_size = 0
            total_count = 0
            
            for root, dirs, files in os.walk(self.local_path):
                for file in files:
                    if not file.endswith('.meta'):  # Skip metadata files
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                        total_count += 1
            
            return {
                'total_files': total_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'local_path': self.local_path
            }
            
        except Exception as e:
            logger.error(f"Local stats failed: {e}")
            return {'error': str(e)}
