from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any
import tempfile
import os
import uuid

from google.cloud import storage
from vertexai.preview import rag
from vertexai.preview.generative_models import GenerativeModel, Tool
import vertexai


@dataclass
class RagConfig:
    project_id: str
    bucket_name: str  # This should be an existing bucket
    location: str = "us-central1"
    display_name: str = "default_corpus"
    embedding_model: str = "textembedding-gecko-multilingual@001"
    chunk_size: int = 512
    chunk_overlap: int = 100


class VertexService:
    def __init__(self, config: RagConfig):
        """Initialize Vertex AI service with configuration."""
        self.config = config
        vertexai.init(project=config.project_id, location=config.location)
        self.storage_client = storage.Client(project=config.project_id)
        self.bucket = self.storage_client.bucket(self.config.bucket_name)

    def _upload_to_gcs(self, content: str) -> str:
        """Upload content to GCS and return the GCS URI."""
        blob_name = f"rag-documents/{uuid.uuid4()}.txt"
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(content)
        return f"gs://{self.config.bucket_name}/{blob_name}"

    def create_corpus(self) -> rag.RagCorpus:
        """Create a new RAG corpus."""
        embedding_model_config = rag.EmbeddingModelConfig(
            publisher_model=f"publishers/google/models/{
                self.config.embedding_model}"
        )

        return rag.create_corpus(
            display_name=self.config.display_name,
            embedding_model_config=embedding_model_config,
        )

    def import_chunks(
        self,
        corpus: rag.RagCorpus,
        chunks: List[str],
        chunk_size: int = None,
    ) -> None:
        """Import text chunks into the RAG corpus."""
        if not chunk_size:
            chunk_size = self.config.chunk_size

        # Upload chunks to GCS
        gcs_uris = []
        for chunk in chunks:
            if chunk.strip():  # Skip empty chunks
                gcs_uri = self._upload_to_gcs(chunk)
                gcs_uris.append(gcs_uri)

        if not gcs_uris:
            raise ValueError("No valid chunks to import")

        try:
            # Import files from GCS
            rag.import_files(
                corpus.name,
                gcs_uris,
                chunk_size=chunk_size,
                chunk_overlap=self.config.chunk_overlap
            )
        except Exception as e:
            # Clean up GCS files on failure
            for uri in gcs_uris:
                try:
                    blob_name = uri.replace(
                        f"gs://{self.config.bucket_name}/", "")
                    self.bucket.blob(blob_name).delete()
                except:
                    pass
            raise e

    def query(
        self,
        corpus: str,
        query: str,
        top_k: int = 5,
        model: str = "gemini-1.0-pro"
    ) -> Dict[str, Any]:
        """Query the RAG corpus using specified model."""
        try:
            rag_retrieval_tool = Tool.from_retrieval(
                retrieval=rag.Retrieval(
                    source=rag.VertexRagStore(
                        rag_resources=[rag.RagResource(rag_corpus=corpus)],
                        similarity_top_k=top_k,
                    )
                )
            )

            model = GenerativeModel(model, tools=[rag_retrieval_tool])
            response = model.generate_content(query)

            return {
                'text': response.text,
                'citations': [
                    {
                        'text': citation.text,
                        'source': citation.source,
                        'score': citation.score,
                    }
                    for citation in getattr(response, 'citations', [])
                ]
            }
        except Exception as e:
            print(f"Error during query: {str(e)}")
            raise

    def list_files(self, corpus: str) -> List[str]:
        """List all files in the corpus."""
        return rag.list_files(corpus)

    def delete_files(self, corpus: str, file_ids: List[str]) -> None:
        """Delete specific files from corpus."""
        for file_id in file_ids:
            rag.delete_file(corpus, file_id)

    def delete_corpus(self, corpus: str) -> None:
        """Delete entire corpus."""
        rag.delete_corpus(corpus)
