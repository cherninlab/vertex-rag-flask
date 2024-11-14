import uuid
import os
from pathlib import Path
from flask import (
    Blueprint, current_app, flash, redirect,
    render_template, request, url_for, jsonify
)
from werkzeug.utils import secure_filename

from app.services.document_service import DocumentService
from app.services.vertex_service import RagConfig, VertexService
from app.utils.helpers import allowed_file
from app.utils.gcp import get_project_id, list_buckets, create_bucket

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Render the index page."""
    return render_template("index.html")


@bp.route("/buckets")
def get_buckets():
    """API endpoint to get list of buckets."""
    project_id = get_project_id()
    buckets = list_buckets(project_id)
    return jsonify(buckets)


@bp.route("/bucket/create", methods=["POST"])
def create_new_bucket():
    """API endpoint to create a new bucket."""
    project_id = get_project_id()
    bucket_name = request.json.get("bucket_name")

    if not bucket_name:
        return jsonify({"error": "Bucket name is required"}), 400

    success = create_bucket(project_id, bucket_name)
    if success:
        return jsonify({"message": f"Bucket {bucket_name} created successfully"})
    else:
        return jsonify({"error": "Failed to create bucket"}), 400


@bp.route("/upload", methods=["GET", "POST"])
def upload():
    """Handle document uploads and processing."""
    if request.method == "POST":
        upload_id = str(uuid.uuid4())
        temp_file = None

        try:
            current_app.logger.info(
                f"Upload request received - ID: {upload_id}")
            current_app.logger.debug(
                f"Request headers: {dict(request.headers)}")

            if "file" not in request.files:
                raise ValueError("No file uploaded")

            file = request.files["file"]
            if not file.filename:
                raise ValueError("Empty filename")

            # Create temporary file
            filename = secure_filename(file.filename)
            upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
            upload_dir.mkdir(exist_ok=True)
            temp_file = upload_dir / f"{upload_id}_{filename}"

            # Save uploaded file temporarily
            file.save(temp_file)
            current_app.logger.info(f"Saved temp file: {temp_file}")

            # Update status
            current_app.config[f"upload_status_{upload_id}"] = {
                "status": "processing",
                "step": "validating",
                "progress": 10
            }

            # Process document
            doc_service = DocumentService()
            chunks = doc_service.process_document(str(temp_file))

            if not chunks:
                raise ValueError("No content could be extracted from document")

            # Return success response
            return jsonify({
                "status": "success",
                "message": "Document processed successfully",
                "redirect": url_for("main.chat")
            })

        except Exception as e:
            current_app.logger.error(
                f"Upload failed - ID: {upload_id}", exc_info=True)
            error_msg = str(
                e) if current_app.debug else "Document processing failed"
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 400

        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)

    # GET request handling
    project_id = get_project_id()
    buckets = list_buckets(project_id)
    last_bucket_name = current_app.config.get("LAST_BUCKET_NAME", "")
    return render_template("upload.html", buckets=buckets, last_bucket_name=last_bucket_name)


@bp.route("/chat")
def chat():
    """Render the chat interface."""
    corpus_name = request.args.get("corpus_name")
    if not corpus_name:
        return redirect(url_for("main.index"))

    project_id = get_project_id()
    bucket_name = current_app.config.get("LAST_BUCKET_NAME", "")

    return render_template(
        "chat.html",
        corpus_name=corpus_name,
        project_id=project_id,
        bucket_name=bucket_name
    )
