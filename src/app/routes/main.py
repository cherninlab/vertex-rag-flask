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
        try:
            upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
            upload_dir.mkdir(mode=0o755, parents=True, exist_ok=True)

            # Check if file was submitted
            if "file" not in request.files:
                current_app.logger.error("No file part in request")
                flash("No file part", "error")
                return redirect(request.url)

            # Validate bucket name
            project_id = get_project_id()
            bucket_name = request.form.get("bucket_name")
            if not bucket_name:
                current_app.logger.error("Missing bucket name")
                flash("Bucket name is required", "error")
                return redirect(request.url)

            file = request.files["file"]
            if file.filename == "":
                current_app.logger.error("No selected file")
                flash("No selected file", "error")
                return redirect(request.url)

            if file and allowed_file(file.filename):
                try:
                    current_app.config["LAST_BUCKET_NAME"] = bucket_name
                    filename = secure_filename(file.filename)
                    filepath = upload_dir / filename

                    # Log file details
                    current_app.logger.info(f"Processing file: {filename}")
                    current_app.logger.info(
                        f"File size: {len(file.read())} bytes")
                    file.seek(0)  # Reset file pointer

                    file.save(filepath)

                    # Process document
                    doc_service = DocumentService()
                    chunks = doc_service.process_document(filepath)

                    if not chunks:
                        current_app.logger.error(
                            f"No content extracted from {filename}")
                        flash("No text content found in document", "error")
                        return redirect(request.url)

                    # Create corpus and import chunks
                    config = RagConfig(
                        project_id=project_id,
                        bucket_name=bucket_name,
                        display_name=f"corpus_{filename}"
                    )
                    service = VertexService(config)
                    corpus = service.create_corpus()
                    service.import_chunks(corpus, chunks)

                    flash(f"Successfully processed document: {
                          filename}", "success")
                    return redirect(url_for("main.chat", corpus_name=corpus.name, project_id=project_id))

                except Exception as e:
                    current_app.logger.error(
                        f"Upload processing error: {str(e)}")
                    flash(f"Error processing upload: {str(e)}", "error")
                    return redirect(request.url)
                finally:
                    # Clean up uploaded file
                    if filepath.exists():
                        filepath.unlink()
            else:
                current_app.logger.error(f"Invalid file type: {file.filename}")
                flash("Invalid file type", "error")
                return redirect(request.url)

        except Exception as e:
            current_app.logger.error(f"Unexpected error: {str(e)}")
            flash("An unexpected error occurred", "error")
            return redirect(request.url)

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
