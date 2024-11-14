from flask import Blueprint, jsonify, request
from pydantic import BaseModel

from app.services.vertex_service import RagConfig, VertexService

bp = Blueprint("api", __name__, url_prefix="/api")


class QueryRequest(BaseModel):
    query: str
    project_id: str
    corpus_name: str
    top_k: int = 5


@bp.route("/query", methods=["POST"])
def query():
    try:
        data = QueryRequest(**request.get_json())
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    try:
        config = RagConfig(project_id=data.project_id)
        service = VertexService(config)
        
        response = service.query(
            corpus=data.corpus_name,
            query=data.query,
            top_k=data.top_k
        )
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/files/<corpus_name>", methods=["GET"])
def list_files(corpus_name: str):
    project_id = request.args.get("project_id")
    if not project_id:
        return jsonify({"error": "project_id is required"}), 400

    try:
        config = RagConfig(project_id=project_id)
        service = VertexService(config)
        files = service.list_files(corpus_name)
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/corpus/<corpus_name>/document", methods=["DELETE"])
def delete_document(corpus_name: str):
    project_id = request.args.get("project_id")
    document_id = request.args.get("document_id")
    
    if not all([project_id, document_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        config = RagConfig(project_id=project_id)
        service = VertexService(config)
        service.delete_files(corpus_name, [document_id])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500