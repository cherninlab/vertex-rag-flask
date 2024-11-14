from pathlib import Path
from typing import List

from unstructured.partition.auto import partition
from unstructured.cleaners.core import clean, replace_unicode_quotes
from unstructured.staging.base import elements_to_json

class DocumentService:
    def process_document(self, file_path: Path) -> List[str]:
        """Process document using unstructured library."""
        # Partition the document
        elements = partition(
            str(file_path),
            include_page_breaks=True,
            strategy="auto",
        )
        
        # Clean and normalize text
        cleaned_elements = []
        for element in elements:
            if hasattr(element, 'text') and element.text.strip():
                # Apply text cleaning
                text = clean(
                    element.text,
                    bullets=True,
                    extra_whitespace=True,
                    dashes=True,
                    trailing_punctuation=True,
                )
                text = replace_unicode_quotes(text)
                
                if text.strip():  # Only keep non-empty chunks
                    cleaned_elements.append(text.strip())
        
        return cleaned_elements

    def get_document_metadata(self, file_path: Path) -> dict:
        """Extract metadata from document."""
        elements = partition(str(file_path))
        return elements_to_json(elements, metadata_only=True)