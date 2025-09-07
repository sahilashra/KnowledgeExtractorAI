# -*- coding: utf-8 -*-
"""
Day 2 Setup Script for the Healthcare QA Hackathon.

This script provisions Vertex AI Search resources, including a data store
and a search engine, to create a compliance knowledge base.

Author: Gemini
Date: 2025-09-03
"""

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from google.api_core import exceptions
from google.cloud import discoveryengine_v1alpha as discoveryengine
from google.cloud import storage

# --- Configuration ---

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class VertexAISearchSetup:
    """
    A class to automate the setup of Day 2 resources for the Healthcare QA Hackathon.
    """

    def __init__(self):
        """
        Initializes the setup class, loading configuration and setting up clients.
        """
        load_dotenv()
        self.gcp_project_id: Optional[str] = os.getenv("GCP_PROJECT_ID")
        self.gcp_region: Optional[str] = os.getenv("GCP_REGION")
        self.service_account_path: Optional[str] = os.getenv("GCP_SERVICE_ACCOUNT_KEY_PATH")
        self.data_store_display_name: Optional[str] = os.getenv("DATA_STORE_DISPLAY_NAME")
        self.engine_display_name: Optional[str] = os.getenv("ENGINE_DISPLAY_NAME")
        self.data_store_display_name: Optional[str] = os.getenv("DATA_STORE_DISPLAY_NAME")
        self.engine_display_name: Optional[str] = os.getenv("ENGINE_DISPLAY_NAME")
        self.bucket_prefix: Optional[str] = os.getenv("BUCKET_PREFIX")

        self._validate_config()

        # Set up Google Cloud clients
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.service_account_path
        self.discoveryengine_client = discoveryengine.DataStoreServiceClient()
        self.engine_client = discoveryengine.EngineServiceClient()
        self.document_client = discoveryengine.DocumentServiceClient()
        self.search_client = discoveryengine.SearchServiceClient()
        self.storage_client = storage.Client()

        self.data_store_name: str = ""
        self.engine_name: str = ""
        self.structured_data_bucket: str = f"{self.bucket_prefix}-structured-data"

    def _validate_config(self):
        """
        Validates that all required environment variables are set.
        """
        logging.info("Validating configuration...")
        required_vars = [
            "GCP_PROJECT_ID", "GCP_REGION", "GCP_SERVICE_ACCOUNT_KEY_PATH",
            "DATA_STORE_DISPLAY_NAME", "ENGINE_DISPLAY_NAME", "BUCKET_PREFIX"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        if not os.path.exists(self.service_account_path):
            raise FileNotFoundError(f"Service account key file not found at: {self.service_account_path}")

        logging.info("Configuration validated successfully.")

    def get_or_create_data_store(self) -> str:
        """
        Checks for an existing Vertex AI Search data store or creates a new one.

        Returns:
            The full resource name of the data store.
        """
        parent = f"projects/{self.gcp_project_id}/locations/global"
        logging.info(f"Checking for Vertex AI Search data store in {parent}...")

        try:
            # Check if data store already exists
            for data_store in self.discoveryengine_client.list_data_stores(parent=parent):
                if data_store.display_name == self.data_store_display_name:
                    logging.info(f"Found existing data store: {data_store.name}")
                    self.data_store_name = data_store.name
                    return self.data_store_name

            # Create a new data store if not found
            logging.info(f"No existing data store found. Creating a new one...")
            
            create_data_store_request = discoveryengine.CreateDataStoreRequest(
                parent=parent,
                data_store=discoveryengine.DataStore(
                    display_name=self.data_store_display_name,
                    industry_vertical="GENERIC",
                    solution_types=["SOLUTION_TYPE_SEARCH"],
                    content_config=discoveryengine.DataStore.ContentConfig.CONTENT_CONFIG_UNSPECIFIED,
                ),
                data_store_id=self.data_store_display_name.lower().replace("_", "-")
            )
            
            operation = self.discoveryengine_client.create_data_store(request=create_data_store_request)
            data_store = operation.result()

            logging.info(f"Successfully created data store: {data_store.name}")
            self.data_store_name = data_store.name
            return self.data_store_name

        except exceptions.GoogleAPICallError as e:
            logging.error(f"API error during data store setup: {e}")
            raise

    def get_or_create_engine(self) -> str:
        """
        Checks for an existing Vertex AI Search engine or creates a new one.

        Returns:
            The full resource name of the engine.
        """
        parent = f"projects/{self.gcp_project_id}/locations/global"
        logging.info(f"Checking for Vertex AI Search engine in {parent}...")

        try:
            # Check if engine already exists
            for engine in self.engine_client.list_engines(parent=parent):
                if engine.display_name == self.engine_display_name:
                    logging.info(f"Found existing engine: {engine.name}")
                    self.engine_name = engine.name
                    return self.engine_name

            # Create a new engine if not found
            logging.info(f"No existing engine found. Creating a new one...")

            create_engine_request = discoveryengine.CreateEngineRequest(
                parent=parent,
                engine=discoveryengine.Engine(
                    display_name=self.engine_display_name,
                    data_store_ids=[self.data_store_name.split("/")[-1]],
                    solution_type="SOLUTION_TYPE_SEARCH",
                ),
                engine_id=self.engine_display_name.lower().replace("_", "-")
            )

            operation = self.engine_client.create_engine(request=create_engine_request)
            engine = operation.result()

            logging.info(f"Successfully created engine: {engine.name}")
            self.engine_name = engine.name
            return self.engine_name

        except exceptions.GoogleAPICallError as e:
            logging.error(f"API error during engine setup: {e}")
            raise

    def import_compliance_documents(self):
        """
        Imports compliance documents from the local 'compliance-knowledge-base' directory
        into the Vertex AI Search data store.
        """
        if not self.data_store_name:
            raise ValueError("Data store name is not set. Please run get_or_create_data_store() first.")

        logging.info("--- Starting Compliance Document Import ---")
        
        # 1. Get the GCS bucket for unstructured data
        unstructured_bucket_name = f"{self.bucket_prefix}-unstructured-data"
        try:
            unstructured_bucket = self.storage_client.get_bucket(unstructured_bucket_name)
            logging.info(f"Using existing GCS bucket: {unstructured_bucket_name}")
        except exceptions.NotFound:
            logging.error(f"Bucket {unstructured_bucket_name} not found. Please run setup_day1.py to create it.")
            raise

        # 2. Upload local PDFs to the GCS bucket
        local_compliance_dir = "compliance-knowledge-base"
        pdf_files_to_import = []

        for root, _, files in os.walk(local_compliance_dir):
            for file in files:
                if file.endswith(".pdf"):
                    local_path = os.path.join(root, file)
                    blob_name = f"{os.path.basename(root)}/{file}"
                    blob = unstructured_bucket.blob(blob_name)
                    
                    logging.info(f"Uploading {local_path} to gs://{unstructured_bucket_name}/{blob_name}")
                    blob.upload_from_filename(local_path)
                    
                    gcs_uri = f"gs://{unstructured_bucket_name}/{blob_name}"
                    pdf_files_to_import.append(gcs_uri)

        if not pdf_files_to_import:
            logging.warning("No PDF documents found in 'compliance-knowledge-base' directory. Skipping import.")
            return

        # 3. Import the documents from GCS into the Vertex AI data store
        logging.info(f"Importing {len(pdf_files_to_import)} documents into data store: {self.data_store_name}")
        
        parent_resource = f"{self.data_store_name}/branches/default_branch"

        gcs_source = discoveryengine.GcsSource(input_uris=pdf_files_to_import)
        import_request = discoveryengine.ImportDocumentsRequest(
            parent=parent_resource,
            gcs_source=gcs_source,
            reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
        )

        try:
            operation = self.document_client.import_documents(request=import_request)
            logging.info("Waiting for document import to complete... This may take a few minutes.")
            operation.result()
            logging.info("Document import completed successfully.")

        except exceptions.GoogleAPICallError as e:
            logging.error(f"API error during document import: {e}")
            raise

    def search_compliance_knowledge_base(self, search_query: str) -> str:
        """
        Performs a search in the compliance knowledge base.

        Args:
            search_query: The query to search for.

        Returns:
            A formatted string of search results.
        """
        if not self.engine_name:
            # Ensure engine is identified before searching
            self.get_or_create_engine()

        serving_config_name = f"{self.engine_name}/servingConfigs/default_serving_config"

        request = discoveryengine.SearchRequest(
            serving_config=serving_config_name,
            query=search_query,
            page_size=3,
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                    return_snippet=True
                ),
                summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                    summary_result_count=3,
                    include_citations=True,
                ),
            ),
        )

        try:
            response = self.search_client.search(request)
            logging.info(f"Successfully performed search for query: '{search_query}'")
            
            # Format the results into a string for the prompt
            results_str = "Compliance Search Results:\n"
            for i, result in enumerate(response.results):
                doc = result.document
                results_str += f"\n--- Result {i+1} ---\n"
                results_str += f"Title: {doc.derived_struct_data['title']}\n"
                results_str += f"Source: {doc.name.split('/')[-1]}\n"
                results_str += f"Snippet: {doc.derived_struct_data['snippets'][0]['snippet']}\n"
            
            return results_str

        except exceptions.GoogleAPICallError as e:
            logging.error(f"API error during search: {e}")
            return "Error: Could not perform compliance search."

    def run_setup(self):
        """
        Executes the full Day 2 setup process step-by-step.
        """
        logging.info("--- Starting Healthcare QA Hackathon Day 2 Setup ---")
        try:
            self.get_or_create_data_store()
            self.get_or_create_engine()
            self.import_compliance_documents()
            logging.info("--- Day 2 Setup Completed Successfully! ---")
            logging.info("Your Vertex AI Search environment is ready.")
        except Exception as e:
            logging.error(f"--- Day 2 Setup Failed: {e} ---")
            logging.error("Please check the logs and your configuration, then try again.")


def main():
    """
    Main function to run the setup script.
    """
    try:
        setup = VertexAISearchSetup()
        setup.run_setup()
    except (ValueError, FileNotFoundError) as e:
        logging.error(f"Configuration Error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
