"""Supabase Storage helper functions."""

from flask import current_app
from supabase import create_client, Client
import uuid

def get_supabase_client() -> Client:
    """Initialize and return a Supabase client using current app configuration."""
    url = current_app.config.get("SUPABASE_URL")
    key = current_app.config.get("SUPABASE_KEY")
    return create_client(url, key)

def upload_file(bucket_name: str, file_stream, file_name: str, content_type: str) -> str:
    """
    Upload a file to Supabase Storage.
    
    Args:
        bucket_name: Name of the Supabase storage bucket.
        file_stream: The file object (e.g., from request.files).
        file_name: Original file name.
        content_type: MIME type of the file.
        
    Returns:
        The generated object key (path) in the bucket.
    """
    supabase = get_supabase_client()
    
    # Generate unique filename to avoid collisions
    ext = file_name.rsplit('.', 1)[1].lower() if '.' in file_name else ''
    unique_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    
    # Upload to Supabase
    file_bytes = file_stream.read()
    res = supabase.storage.from_(bucket_name).upload(
        file=file_bytes,
        path=unique_filename,
        file_options={"content-type": content_type}
    )
    
    return unique_filename

def get_file_url(bucket_name: str, object_key: str, public: bool = True) -> str:
    """
    Get the URL for a file in Supabase Storage.
    
    Args:
        bucket_name: Name of the storage bucket.
        object_key: The path/key of the object in the bucket.
        public: Whether to get a public URL (True) or a signed URL (False).
        
    Returns:
        The URL string.
    """
    supabase = get_supabase_client()
    
    if public:
        return supabase.storage.from_(bucket_name).get_public_url(object_key)
    else:
        # Default to 1 hour expiration for signed URLs
        res = supabase.storage.from_(bucket_name).create_signed_url(object_key, 3600)
        return res.get('signedURL', '')

def delete_file(bucket_name: str, object_key: str) -> bool:
    """
    Delete a file from Supabase Storage.
    
    Args:
        bucket_name: Name of the storage bucket.
        object_key: The path/key of the object to delete.
        
    Returns:
        True if successful, False otherwise.
    """
    supabase = get_supabase_client()
    try:
        supabase.storage.from_(bucket_name).remove([object_key])
        return True
    except Exception as e:
        current_app.logger.error(f"Error deleting file {object_key} from {bucket_name}: {e}")
        return False
