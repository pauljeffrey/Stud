"""
S3 Storage Service for Stud
Handles file uploads to S3 for persistent storage
Allows re-ingestion of expired documents from vector DB
"""
import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """
    Service for storing and retrieving files from S3
    """
    
    def __init__(self):
        """Initialize S3 service"""
        self.enabled = os.getenv("S3_ENABLED", "false").lower() == "true"
        
        if not self.enabled:
            logger.info("S3 storage is disabled")
            return
        
        # Get S3 configuration from environment
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.region = os.getenv("S3_REGION", "us-east-1")
        self.access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if not all([self.bucket_name, self.access_key_id, self.secret_access_key]):
            logger.warning("S3 enabled but missing required environment variables. Disabling S3.")
            self.enabled = False
            return
        
        try:
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key
            )
            
            # Verify bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 service initialized successfully. Bucket: {self.bucket_name}")
        except ClientError as e:
            logger.error(f"Failed to initialize S3 service: {e}")
            self.enabled = False
        except Exception as e:
            logger.error(f"Unexpected error initializing S3: {e}")
            self.enabled = False
    
    def _get_object_key(self, user_id: str, document_id: str, file_name: str) -> str:
        """Generate S3 object key for a document"""
        # Sanitize file name
        safe_filename = file_name.replace(" ", "_").replace("/", "_")
        return f"documents/{user_id}/{document_id}/{safe_filename}"
    
    async def upload_file(
        self,
        file_content: bytes,
        user_id: str,
        document_id: str,
        file_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Upload file to S3
        
        Args:
            file_content: File content as bytes
            user_id: User ID
            document_id: Document ID
            file_name: Original file name
            content_type: MIME type
            metadata: Additional metadata
            
        Returns:
            S3 object key if successful, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            object_key = self._get_object_key(user_id, document_id, file_name)
            
            # Prepare metadata
            s3_metadata = {
                "user_id": user_id,
                "document_id": document_id,
                "uploaded_at": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_content,
                ContentType=content_type or "application/octet-stream",
                Metadata={k: str(v) for k, v in s3_metadata.items()}
            )
            
            logger.info(f"File uploaded to S3: {object_key}")
            return object_key
        
        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")
            return None
    
    async def download_file(self, user_id: str, document_id: str, file_name: str) -> Optional[bytes]:
        """
        Download file from S3
        
        Args:
            user_id: User ID
            document_id: Document ID
            file_name: File name
            
        Returns:
            File content as bytes if successful, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            object_key = self._get_object_key(user_id, document_id, file_name)
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            file_content = response['Body'].read()
            logger.info(f"File downloaded from S3: {object_key}")
            return file_content
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found in S3: {object_key}")
            else:
                logger.error(f"Error downloading file from S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading from S3: {e}")
            return None
    
    async def delete_file(self, user_id: str, document_id: str, file_name: str) -> bool:
        """
        Delete file from S3
        
        Args:
            user_id: User ID
            document_id: Document ID
            file_name: File name
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            object_key = self._get_object_key(user_id, document_id, file_name)
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            logger.info(f"File deleted from S3: {object_key}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False
    
    async def file_exists(self, user_id: str, document_id: str, file_name: str) -> bool:
        """
        Check if file exists in S3
        
        Args:
            user_id: User ID
            document_id: Document ID
            file_name: File name
            
        Returns:
            True if file exists, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            object_key = self._get_object_key(user_id, document_id, file_name)
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError:
            return False
        except Exception as e:
            logger.error(f"Error checking file existence in S3: {e}")
            return False
    
    def get_file_url(self, user_id: str, document_id: str, file_name: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for file access
        
        Args:
            user_id: User ID
            document_id: Document ID
            file_name: File name
            expires_in: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL if successful, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            object_key = self._get_object_key(user_id, document_id, file_name)
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expires_in
            )
            
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None


# Global instance
_s3_service: Optional[S3Service] = None


def get_s3_service() -> S3Service:
    """Get or create global S3 service instance"""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
