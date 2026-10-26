# =============================================================
# Agri LMS — Security Utilities
# =============================================================
# File    : app/utils/security.py
# Purpose : Platform-wide security helper functions including
#           input sanitization, file security validation,
#           rate limiting helpers, and security logging.
# =============================================================

import re
import os
import hashlib
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import request, abort, current_app
from flask_login import current_user


logger = logging.getLogger(__name__)


# =============================================================
# INPUT SANITIZATION
# =============================================================

def sanitize_string(value, max_length=500, allow_html=False):
    """
    Sanitize a string input by stripping whitespace,
    removing dangerous HTML if not allowed, and
    enforcing a maximum length.

    Args:
        value (str): Raw input string.
        max_length (int): Maximum allowed length.
        allow_html (bool): If False, strips all HTML tags.

    Returns:
        str: Cleaned and safe string.
    """
    if not value:
        return ''

    # Convert to string and strip whitespace
    value = str(value).strip()

    # Strip HTML tags if not allowed
    if not allow_html:
        value = re.sub(r'<[^>]+>', '', value)

    # Remove null bytes and other dangerous characters
    value = value.replace('\x00', '')
    value = value.replace('\r', '')

    # Enforce maximum length
    if len(value) > max_length:
        value = value[:max_length]

    return value


def sanitize_email(email):
    """
    Sanitize and normalize an email address.

    Args:
        email (str): Raw email input.

    Returns:
        str: Lowercased and stripped email, or empty string.
    """
    if not email:
        return ''
    return sanitize_string(email, max_length=150).lower()


def sanitize_filename(filename):
    """
    Sanitize an uploaded filename to prevent
    directory traversal and other file-based attacks.

    Args:
        filename (str): Original filename from upload.

    Returns:
        str: Safe filename with dangerous characters removed.
    """
    if not filename:
        return 'upload'

    # Remove directory separators and null bytes
    filename = filename.replace('/', '_').replace('\\', '_')
    filename = filename.replace('\x00', '')

    # Remove leading dots to prevent hidden file creation
    filename = filename.lstrip('.')

    # Allow only safe characters
    filename = re.sub(r'[^\w\-. ]', '_', filename)

    # Collapse multiple underscores
    filename = re.sub(r'_+', '_', filename)

    # Enforce maximum filename length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename  = name[:195] + ext

    return filename or 'upload'


def sanitize_integer(value, min_val=None, max_val=None, default=0):
    """
    Safely convert a value to an integer with optional
    range clamping.

    Args:
        value: Value to convert.
        min_val (int): Minimum allowed value.
        max_val (int): Maximum allowed value.
        default (int): Value returned on conversion failure.

    Returns:
        int: Safe integer value.
    """
    try:
        result = int(value)
        if min_val is not None:
            result = max(result, min_val)
        if max_val is not None:
            result = min(result, max_val)
        return result
    except (ValueError, TypeError):
        return default


def sanitize_float(value, min_val=None, max_val=None, default=0.0):
    """
    Safely convert a value to a float with optional
    range clamping.

    Args:
        value: Value to convert.
        min_val (float): Minimum allowed value.
        max_val (float): Maximum allowed value.
        default (float): Value returned on conversion failure.

    Returns:
        float: Safe float value.
    """
    try:
        result = float(value)
        if min_val is not None:
            result = max(result, min_val)
        if max_val is not None:
            result = min(result, max_val)
        return result
    except (ValueError, TypeError):
        return default


# =============================================================
# FILE SECURITY
# =============================================================

SAFE_MATERIAL_EXTENSIONS = {
    'mp4', 'webm', 'mkv', 'avi', 'mov',
    'pdf',
    'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt',
    'png', 'jpg', 'jpeg', 'gif', 'webp',
    'zip', 'rar',
}

SAFE_SUBMISSION_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
    'png', 'jpg', 'jpeg', 'gif',
    'zip', 'rar', 'txt', 'py', 'ipynb', 'csv',
}

SAFE_IMAGE_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'webp'
}

# File signatures (magic bytes) for type verification
FILE_SIGNATURES = {
    b'\x25\x50\x44\x46':         'pdf',       # %PDF
    b'\x50\x4B\x03\x04':         'zip',       # PK
    b'\xFF\xD8\xFF':              'jpg',       # JPEG
    b'\x89\x50\x4E\x47':         'png',       # PNG
    b'\x47\x49\x46\x38':         'gif',       # GIF
    b'\x00\x00\x00\x18ftypmp42': 'mp4',       # MP4
    b'\x1A\x45\xDF\xA3':         'webm',      # WebM/MKV
}


def is_safe_file_extension(filename, allowed_set):
    """
    Check whether a filename has an extension in the
    allowed set.

    Args:
        filename (str): Filename to check.
        allowed_set (set): Set of allowed lowercase extensions.

    Returns:
        bool: True if the extension is allowed.
    """
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[-1].lower().strip()
    return ext in allowed_set


def is_safe_file_size(file_obj, max_mb):
    """
    Check whether an uploaded file does not exceed
    the maximum size limit.

    Args:
        file_obj: Werkzeug FileStorage object.
        max_mb (int): Maximum allowed size in megabytes.

    Returns:
        bool: True if the file is within the size limit.
    """
    try:
        file_obj.seek(0, 2)       # Seek to end
        size_bytes = file_obj.tell()
        file_obj.seek(0)          # Reset position
        return size_bytes <= (max_mb * 1024 * 1024)
    except Exception:
        return False


def get_file_size_bytes(file_obj):
    """
    Get the size of an uploaded file in bytes.

    Args:
        file_obj: Werkzeug FileStorage object.

    Returns:
        int: File size in bytes, or 0 on error.
    """
    try:
        file_obj.seek(0, 2)
        size = file_obj.tell()
        file_obj.seek(0)
        return size
    except Exception:
        return 0


def verify_file_signature(file_obj):
    """
    Read the first 16 bytes of an uploaded file and
    attempt to identify its true type from its magic
    bytes signature, independent of the filename extension.

    This prevents extension spoofing attacks where a
    dangerous file is renamed with a safe extension.

    Args:
        file_obj: Werkzeug FileStorage object.

    Returns:
        str or None: Detected file type string, or None
                     if the signature is not recognized.
    """
    try:
        header = file_obj.read(16)
        file_obj.seek(0)

        for signature, file_type in FILE_SIGNATURES.items():
            if header.startswith(signature):
                return file_type

        return None

    except Exception:
        return None


def generate_secure_filename(original_filename):
    """
    Generate a cryptographically safe stored filename
    by prepending a UUID-based unique prefix to a
    sanitized version of the original filename.

    This prevents:
        - Filename collisions between uploads
        - Directory traversal via crafted filenames
        - Information leakage via predictable names

    Args:
        original_filename (str): Original filename from upload.

    Returns:
        str: UUID-prefixed safe stored filename.
    """
    import uuid
    safe_name     = sanitize_filename(original_filename)
    unique_prefix = uuid.uuid4().hex[:10]
    return f'{unique_prefix}_{safe_name}'


# =============================================================
# URL AND REDIRECT SECURITY
# =============================================================

def is_safe_redirect_url(url):
    """
    Validate that a redirect URL is safe — that it points
    to the same host and does not redirect to an external
    domain, preventing open redirect vulnerabilities.

    Args:
        url (str): URL string to validate.

    Returns:
        bool: True if the URL is safe to redirect to.
    """
    if not url:
        return False

    # Must start with a single forward slash
    # Double slash // is a protocol-relative URL (unsafe)
    if not url.startswith('/') or url.startswith('//'):
        return False

    # Must not contain protocol indicators
    if '://' in url:
        return False

    # Must not contain backslashes (Windows path bypass)
    if '\\' in url:
        return False

    return True


def get_safe_next_url(default_url):
    """
    Extract and validate the 'next' URL parameter from the
    request, falling back to a safe default if the provided
    next URL is invalid or potentially malicious.

    Args:
        default_url (str): Safe fallback URL.

    Returns:
        str: Validated safe redirect URL.
    """
    next_url = request.args.get('next', '').strip()

    if next_url and is_safe_redirect_url(next_url):
        return next_url

    return default_url


# =============================================================
# SECURITY LOGGING
# =============================================================

def log_security_event(event_type, details=None, user_id=None):
    """
    Log a security-relevant event to the application logger.

    Security events include:
        - Failed login attempts
        - Access denied to restricted resources
        - Suspicious file upload attempts
        - CSRF validation failures
        - Password change attempts

    Args:
        event_type (str): Type of security event.
        details (str): Additional event details.
        user_id (int): ID of the user involved.
    """
    uid     = user_id or (current_user.id
                          if current_user.is_authenticated else 'anonymous')
    ip_addr = request.remote_addr if request else 'unknown'
    ua      = request.user_agent.string[:100] \
              if request and request.user_agent else 'unknown'

    log_msg = (
        f'[SECURITY] event={event_type} '
        f'user_id={uid} '
        f'ip={ip_addr} '
        f'path={request.path if request else "N/A"} '
        f'ua={ua}'
    )

    if details:
        log_msg += f' details={details}'

    logger.warning(log_msg)


def log_failed_login(email):
    """
    Log a failed login attempt with the attempted email.

    Args:
        email (str): Email address used in the failed attempt.
    """
    log_security_event(
        event_type='FAILED_LOGIN',
        details=f'email={sanitize_email(email)}'
    )


def log_access_denied(resource):
    """
    Log an unauthorized access attempt to a protected resource.

    Args:
        resource (str): The resource that was denied.
    """
    log_security_event(
        event_type='ACCESS_DENIED',
        details=f'resource={resource}'
    )


# =============================================================
# CONTENT SECURITY POLICY
# =============================================================

def get_csp_header():
    """
    Generate a Content Security Policy header value.

    Returns:
        str: CSP header string for use in response headers.
    """
    return (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' "
        "https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "media-src 'self'; "
        "frame-src 'self' https://www.youtube.com "
        "https://drive.google.com; "
        "connect-src 'self'; "
        "object-src 'none';"
    )