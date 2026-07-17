"""Supabase Storage helper functions."""

from flask import current_app
from supabase import create_client, Client
import uuid

# Cache satu Supabase client per (url, key). Membuat client baru tiap panggilan
# sangat mahal: setiap create_client memuat sertifikat SSL dari disk
# (load_verify_locations ~300ms) dan membangun beberapa sub-client HTTP.
# Dulu ini dipanggil per-file saat render daftar -> render bisa 2-6 detik.
_client_cache: dict[tuple[str, str], Client] = {}

def get_supabase_client() -> Client:
    """Return a cached Supabase client for the current app configuration."""
    url = current_app.config.get("SUPABASE_URL")
    key = current_app.config.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Supabase belum dikonfigurasi. Isi SUPABASE_URL dan SUPABASE_KEY di file .env.")
    cache_key = (url, key)
    client = _client_cache.get(cache_key)
    if client is None:
        client = create_client(url, key)
        _client_cache[cache_key] = client
    return client

BUCKET_MAPPING = {
    'profile_photo': 'photos',
    'company_logo': 'logos',
    'resume': 'cvs',
    'certificate': 'certificates',
    'report': 'reports'
}

def get_bucket_for_purpose(purpose: str) -> str:
    """Get the appropriate Supabase bucket name based on file purpose."""
    return BUCKET_MAPPING.get(purpose, 'internlink')

def validate_file(file_stream, allowed_extensions: list, max_size_mb: int = 2) -> tuple[bool, str]:
    """
    Validate file extension and size.
    Returns (is_valid, error_message).
    """
    if not file_stream or file_stream.filename == '':
        return False, "Tidak ada file yang dipilih."
        
    filename = file_stream.filename
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext not in allowed_extensions:
        return False, f"Format file tidak valid. Format yang diizinkan: {', '.join(allowed_extensions).upper()}."
        
    file_stream.seek(0, 2)
    size = file_stream.tell()
    file_stream.seek(0)
    
    if size > max_size_mb * 1024 * 1024:
        return False, f"Ukuran file terlalu besar. Maksimal {max_size_mb}MB."
        
    return True, ""

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
    try:
        res = supabase.storage.from_(bucket_name).upload(
            file=file_bytes,
            path=unique_filename,
            file_options={"content-type": content_type}
        )
    except Exception as e:
        if "Bucket not found" in str(e) or "bucket not found" in str(e).lower():
            # Create the bucket automatically and make it public
            supabase.storage.create_bucket(bucket_name, options={"public": True})
            # Retry upload
            res = supabase.storage.from_(bucket_name).upload(
                file=file_bytes,
                path=unique_filename,
                file_options={"content-type": content_type}
            )
        else:
            raise e
    
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
    if public:
        # URL publik Supabase bersifat deterministik, jadi rakit sebagai string.
        # Tidak perlu membuat/memakai client (hindari overhead SSL + HTTP) — ini
        # dipanggil per-file saat render daftar, jadi harus semurah mungkin.
        base = (current_app.config.get("SUPABASE_URL") or "").rstrip('/')
        return f"{base}/storage/v1/object/public/{bucket_name}/{object_key}"

    # Signed URL tetap butuh client (butuh penandatanganan di sisi server).
    supabase = get_supabase_client()
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
