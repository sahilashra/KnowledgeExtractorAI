# -*- coding: utf-8 -*-
"""
Main RAG Pipeline for the Healthcare QA Hackathon.

This script orchestrates the end-to-end RAG pipeline, connecting
document processing, compliance search, and test case generation.

Author: Gemini
Date: 2025-09-03
"""

import logging
import os
import json
from typing import List, Dict, Any

from dotenv import load_dotenv

from setup_day1 import HealthcareQASetup
from setup_day2 import VertexAISearchSetup
from gemini_integration import GeminiIntegration

# --- Configuration ---

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class RAGPipeline:
    """
    A class to orchestrate the RAG pipeline.
    """

    def __init__(self):
        """
        Initializes the RAG pipeline, loading configuration and setting up clients.
        """
        load_dotenv(override=True)
        self.day1_setup = HealthcareQASetup()
        self.day2_setup = VertexAISearchSetup()
        self.gemini = GeminiIntegration()

    def run_pipeline(self, document_path: str) -> List[Dict[str, Any]]:
        """
        Runs the end-to-end RAG pipeline.

        Args:
            document_path: The path to the document to process.

        Returns:
            A list of dictionaries, where each dictionary represents a test case.
        """
        logging.info("--- Starting RAG Pipeline ---")

        # 1. Read the document text
        logging.info(f"Reading document from: {document_path}")
        try:
            with open(document_path, 'r', encoding='utf-8') as f:
                document_text = f.read()
        except FileNotFoundError:
            logging.error(f"Document not found at path: {document_path}")
            raise

        # 2. Parse the requirements from the document text
        requirements = self.gemini.parse_requirements(document_text)

        # 3. For each requirement, find relevant compliance information
        all_test_cases = []
        for req in requirements:
            logging.info(f"Processing requirement: {req.get('requirement_id')}")
            query = f"{req.get('title')} {req.get('description')}"
            compliance_context = self.day2_setup.search_compliance_knowledge_base(query)
            
            # 4. Generate test cases with compliance context
            test_cases = self.gemini.generate_test_cases_with_compliance(req, compliance_context)
            all_test_cases.extend(test_cases)

        logging.info("--- RAG Pipeline Completed Successfully! ---")
        return all_test_cases


def main():
    """
    Main function to run the RAG pipeline.
    """
    try:
        pipeline = RAGPipeline()
        document_path = os.getenv("SAMPLE_DOC_PATH")
        test_cases = pipeline.run_pipeline(document_path)
        
        output_filename = "healthcare_qa_results.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(test_cases, f, indent=2)
            
        logging.info(f"Generated {len(test_cases)} test cases and saved them to '{output_filename}'.")

    except (ValueError, FileNotFoundError) as e:
        logging.error(f"Configuration Error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
