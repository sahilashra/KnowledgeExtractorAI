# -*- coding: utf-8 -*-
"""
Populate Vertex AI Search Knowledge Base for Healthcare QA Hackathon.

This script uploads compliance documents from a local directory structure
to Google Cloud Storage, along with structured metadata JSON files,
to populate the Vertex AI Search data store.

Author: Gemini
Date: 2025-09-03
"""

import logging
import os
import json
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage
from google.api_core import exceptions

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class KnowledgeBasePopulator:
    """
    Handles the structured upload of compliance documents and metadata.
    """

    def __init__(self):
        load_dotenv()
        self.service_account_path: Optional[str] = os.getenv("GCP_SERVICE_ACCOUNT_KEY_PATH")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.service_account_path
        
        self.storage_client = storage.Client()
        self.bucket_prefix = os.getenv("BUCKET_PREFIX")
        if not self.bucket_prefix:
            raise ValueError("BUCKET_PREFIX not set in .env file.")
        
        # The bucket containing structured data that feeds Vertex AI Search
        self.target_bucket_name = f"{self.bucket_prefix}-structured-data"
        self.local_kb_path = Path("compliance-knowledge-base")

    def setup_local_directory(self):
        """
        Creates a sample local directory structure and placeholder files
        based on the Day 2 implementation plan.
        """
        logging.info(f"Setting up local knowledge base structure at: ./{self.local_kb_path}")
        
        # Define structure and placeholder content
        structure = {
            "FDA_21CFR": {"820_quality_system.pdf": "Content for FDA 820 Quality System."},
            "IEC_62304": {"software_lifecycle.pdf": "Content for IEC 62304 Software Lifecycle."},
            "ISO_13485": {"quality_management.pdf": "Content for ISO 13485 Quality Management."}
        }

        for dirname, files in structure.items():
            dirpath = self.local_kb_path / dirname
            dirpath.mkdir(parents=True, exist_ok=True)
            for filename, content in files.items():
                filepath = dirpath / filename
                if not filepath.exists():
                    filepath.write_text(content, encoding="utf-8")
                    logging.info(f"Created placeholder file: {filepath}")

    def generate_metadata_files(self):
        """
        Generates corresponding .json metadata files for each .pdf file.
        """
        logging.info("Generating placeholder metadata files...")
        
        for pdf_path in self.local_kb_path.rglob("*.pdf"):
            metadata_path = pdf_path.with_suffix(".json")
            
            # Create placeholder metadata based on the plan's schema
            # In a real scenario, this data would be accurate.
            metadata = {
              "document_title": pdf_path.stem.replace("_", " ").title(),
              "regulation_code": pdf_path.parent.name.replace("_", " "),
              "risk_class": "Class C",
              "clause_summary": f"Summary for {pdf_path.stem}",
              "effective_date": "2025-01-01",
              "document_type": "standard",
              "keywords": [pdf_path.stem.split("_")[0], "compliance", "healthcare"]
            }
            
            if not metadata_path.exists():
                metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
                logging.info(f"Created metadata file: {metadata_path}")

    def upload_to_gcs(self):
        """
        Uploads all PDF and JSON files to the target GCS bucket.
        """
        logging.info(f"Uploading knowledge base to gs://{self.target_bucket_name}...")
        
        try:
            bucket = self.storage_client.get_bucket(self.target_bucket_name)
        except exceptions.NotFound:
            logging.error(f"Error: Bucket '{self.target_bucket_name}' not found.")
            logging.error("Please ensure you have run setup_day1.py successfully.")
            return

        for file_path in self.local_kb_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.pdf', '.json']:
                destination_blob_name = file_path.relative_to(self.local_kb_path).as_posix()
                blob = bucket.blob(destination_blob_name)
                
                logging.info(f"Uploading {file_path} to gs://{self.target_bucket_name}/{destination_blob_name}...")
                blob.upload_from_filename(str(file_path))
        
        logging.info("All knowledge base files uploaded successfully.")
        logging.info("Vertex AI Search will now begin indexing these documents.")

def main():
    """
    Runs the full knowledge base population process.
    """
    populator = KnowledgeBasePopulator()
    populator.setup_local_directory()
    populator.generate_metadata_files()
    populator.upload_to_gcs()

if __name__ == "__main__":
    main()
