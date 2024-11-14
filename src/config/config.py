import os
from pathlib import Path


class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key-please-change"

    # File Upload
    UPLOAD_FOLDER = Path("uploads")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {
        # Documents
        "pdf", "docx", "doc", "pptx", "ppt", "xlsx", "xls",
        # Text files
        "txt", "md", "rst", "json", "yaml", "yml",
        # Email
        "eml", "msg",
        # Images (with OCR support)
        "png", "jpg", "jpeg", "tiff", "bmp"
    }

    # Google Cloud
    GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")

    # Development
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "1")
