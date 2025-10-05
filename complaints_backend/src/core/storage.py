import os
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from werkzeug.utils import secure_filename
import uuid

class StorageBackend(ABC):
    
    @abstractmethod
    def save(self, file: BinaryIO, filename: str, folder: str = '') -> str:
        pass
    
    @abstractmethod
    def delete(self, filepath: str) -> bool:
        pass
    
    @abstractmethod
    def get_url(self, filepath: str) -> str:
        pass
    
    @abstractmethod
    def exists(self, filepath: str) -> bool:
        pass

class LocalStorage(StorageBackend):
    
    def __init__(self, base_path: str = 'src/uploads'):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    def save(self, file: BinaryIO, filename: str, folder: str = '') -> str:
        secure_name = secure_filename(filename)
        name, ext = os.path.splitext(secure_name)
        unique_name = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        folder_path = os.path.join(self.base_path, folder)
        os.makedirs(folder_path, exist_ok=True)
        
        filepath = os.path.join(folder_path, unique_name)
        
        with open(filepath, 'wb') as f:
            f.write(file.read())
        
        relative_path = os.path.join(folder, unique_name) if folder else unique_name
        return relative_path
    
    def delete(self, filepath: str) -> bool:
        try:
            full_path = os.path.join(self.base_path, filepath)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception:
            return False
    
    def get_url(self, filepath: str) -> str:
        return f"/uploads/{filepath}"
    
    def exists(self, filepath: str) -> bool:
        full_path = os.path.join(self.base_path, filepath)
        return os.path.exists(full_path)

class S3Storage(StorageBackend):
    
    def __init__(
        self,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = 'us-east-1'
    ):
        import boto3
        
        self.bucket_name = bucket_name
        
        session_config = {}
        if access_key and secret_key:
            session_config['aws_access_key_id'] = access_key
            session_config['aws_secret_access_key'] = secret_key
        if region:
            session_config['region_name'] = region
        
        client_config = {}
        if endpoint_url:
            client_config['endpoint_url'] = endpoint_url
        
        self.s3_client = boto3.client('s3', **session_config, **client_config)
    
    def save(self, file: BinaryIO, filename: str, folder: str = '') -> str:
        secure_name = secure_filename(filename)
        name, ext = os.path.splitext(secure_name)
        unique_name = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        s3_key = f"{folder}/{unique_name}" if folder else unique_name
        
        self.s3_client.upload_fileobj(file, self.bucket_name, s3_key)
        
        return s3_key
    
    def delete(self, filepath: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=filepath)
            return True
        except Exception:
            return False
    
    def get_url(self, filepath: str) -> str:
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': filepath},
            ExpiresIn=3600
        )
    
    def exists(self, filepath: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=filepath)
            return True
        except Exception:
            return False

def get_storage_backend() -> StorageBackend:
    storage_type = os.getenv('STORAGE_BACKEND', 'local').lower()
    
    if storage_type == 's3' or storage_type == 'minio':
        return S3Storage(
            bucket_name=os.getenv('S3_BUCKET_NAME', 'complaints-uploads'),
            endpoint_url=os.getenv('S3_ENDPOINT'),
            access_key=os.getenv('S3_ACCESS_KEY'),
            secret_key=os.getenv('S3_SECRET_KEY'),
            region=os.getenv('S3_REGION', 'us-east-1')
        )
    else:
        return LocalStorage(base_path=os.getenv('LOCAL_STORAGE_PATH', 'complaints_backend/src/uploads'))
