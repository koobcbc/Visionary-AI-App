# utils/validators.py
import re
from urllib.parse import urlparse
from typing import Tuple

SAFE_EXT = (".jpg", ".jpeg", ".png")

PRIVATE_IP_RE = re.compile(
    r"(^127\.0\.0\.1)|(^0\.)|(^10\.)|(^169\.254\.)|(^172\.(1[6-9]|2\d|3[0-1])\.)|(^192\.168\.)"
)

UNSAFE_HOST_RE = re.compile(
    r"(localhost|file:|metadata\.googleinternal|169\.254\.169\.254)",
    re.IGNORECASE,
)
    
    

def validate_image_url(url: str) -> Tuple[bool, str]:
    """Validates that the image URL is safe and properly formatted."""
    if not url:
        return False, "image_url is required."

    parsed = urlparse(url)
    
    # Check scheme
    if parsed.scheme not in ("http", "https", "gs"):
        return False, "Invalid URL scheme. Must be http, https, or gs:// (Google Cloud Storage)."
    
    # For gs:// URLs, validate format
    if parsed.scheme == "gs":
        if not parsed.path:
            return False, "Invalid gs:// URL. Path is required."
        # Check extension in path (before any query params)
        path_lower = parsed.path.lower()
        if not any(path_lower.endswith(ext) for ext in SAFE_EXT):
            return False, "Only .jpg, .jpeg, and .png images are allowed."
        return True, ""
    
    # For http/https URLs, check the path for extension (ignore query parameters)
    path_lower = parsed.path.lower()
    if not any(path_lower.endswith(ext) for ext in SAFE_EXT):
        return False, "Only .jpg, .jpeg, and .png images are allowed."

    host = (parsed.hostname or "").lower()
    if not host:
        return False, "Missing hostname in image URL."

    if PRIVATE_IP_RE.search(host):
        return False, "Image URL points to a private or local network address."
    if UNSAFE_HOST_RE.search(url):
        return False, "Unsafe or internal host detected in image URL."

    return True, ""