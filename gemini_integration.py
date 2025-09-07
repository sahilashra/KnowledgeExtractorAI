# -*- coding: utf-8 -*-
"""
Gemini Pro Integration for Healthcare QA Hackathon.

This script provides functionality for requirement parsing and test case generation
using the Gemini Pro model. It includes prompt patterns for both tasks.

Author: Gemini
Date: 2025-09-03
"""

import logging
import os
import json
from typing import List, Dict, Any

from dotenv import load_dotenv
import google.generativeai as genai

# --- Configuration ---

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class GeminiIntegration:
    """
    A class to handle interactions with the Gemini Pro model.
    """

    def __init__(self):
        """
        Initializes the Gemini Pro integration, loading configuration and setting up the model.
        """
        load_dotenv()
        self.gcp_project_id: str = os.getenv("GCP_PROJECT_ID")
        self.gcp_region: str = os.getenv("GCP_REGION")
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY")

        self._validate_config()

        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def _validate_config(self):
        """
        Validates that all required environment variables are set.
        """
        logging.info("Validating configuration...")
        required_vars = ["GCP_PROJECT_ID", "GCP_REGION", "GEMINI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        logging.info("Configuration validated successfully.")

    def _parse_gemini_json_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Cleans and parses a JSON response from the Gemini model.

        Args:
            response_text: The raw text response from the model.

        Returns:
            A list of dictionaries parsed from the JSON.
        """
        logging.info(f"Gemini raw response:\n{response_text}")
        
        # Clean the response to extract only the JSON part.
        # Gemini sometimes includes markdown formatting (```json ... ```)
        cleaned_response = response_text.strip().replace("```json", "").replace("```", "").strip()
        
        # Use a more robust method to remove trailing commas from arrays and objects
        # This handles cases with whitespace or newlines before the closing bracket/brace
        import re
        cleaned_response = re.sub(r",\s*\]", "]", cleaned_response)
        cleaned_response = re.sub(r",\s*\}", "}", cleaned_response)

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from Gemini response: {e}")
            logging.error(f"Problematic cleaned response: {cleaned_response}")
            raise  # Re-raise the exception to be handled by the calling method

    def parse_requirements(self, document_text: str) -> List[Dict[str, Any]]:
        """
        Parses requirements from a document using Gemini Pro.

        Args:
            document_text: The text of the document to parse.

        Returns:
            A list of dictionaries, where each dictionary represents a requirement.
        """
        logging.info("Parsing requirements with Gemini Pro...")
        prompt = f"""
        Please parse the following document and extract the requirements.
        Return the output as a JSON array, where each object in the array represents a requirement.
        Each requirement object should have the following keys:
        - "requirement_id"
        - "title"
        - "description"
        - "acceptance_criteria"

        Document:
        {document_text}
        """
        try:
            response = self.model.generate_content(prompt)
            return self._parse_gemini_json_response(response.text)
        except (json.JSONDecodeError, Exception) as e:
            logging.error(f"Failed to parse requirements, falling back to demo data. Error: {e}")
            # Fallback to demo data in case of parsing failure
            return [{"requirement_id": "REQ-001-DEMO", "title": "Demo Title", "description": "Demo Description", "acceptance_criteria": "Demo Criteria"}]

    def generate_test_cases_with_compliance(self, requirement: Dict[str, Any], compliance_context: str) -> List[Dict[str, Any]]:
        """
        Generates test cases for a single requirement using Gemini Pro, with added compliance context.

        Args:
            requirement: A dictionary representing a single requirement.
            compliance_context: A string containing relevant compliance information.

        Returns:
            A list of dictionaries, where each dictionary represents a test case.
        """
        logging.info(f"Generating test cases for requirement {requirement.get('requirement_id')} with compliance context...")
        
        prompt = f"""
        Please generate detailed test cases for the following requirement, taking into account the provided compliance context from FDA and ISO regulations.
        The test cases should verify that the requirement is met and that it adheres to the relevant compliance standards.

        Return the output as a JSON array of test case objects. Each object should have the following keys:
        - "test_case_id" (must be a unique string in the format TC-<requirement_id>-<three_digit_number>, e.g., TC-REQ-001-001)
        - "title"
        - "description" (include reference to the compliance standard, e.g., "Verify compliance with FDA 21 CFR 820.30")
        - "steps" (provide a detailed, step-by-step procedure for execution)
        - "expected_results" (describe the expected outcome for each step)

        Requirement:
        ID: {requirement.get('requirement_id')}
        Title: {requirement.get('title')}
        Description: {requirement.get('description')}
        Acceptance Criteria: {requirement.get('acceptance_criteria')}

        Compliance Context:
        {compliance_context}
        """
        try:
            response = self.model.generate_content(prompt)
            return self._parse_gemini_json_response(response.text)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON, falling back to demo test case. Error: {e}")
            return [{"test_case_id": "TC-DEMO-JSON-ERROR", "title": "Demo Test Case (JSON Error)", "description": "Demo Description", "steps": "Demo Steps", "expected_results": "Demo Results"}]
        except Exception as e:
            logging.error(f"Error generating test cases with Gemini Pro for requirement {requirement.get('requirement_id')}: {e}")
            return [{"test_case_id": "TC-DEMO-API-ERROR", "title": "Demo Test Case (API Error)", "description": "Demo Description", "steps": "Demo Steps", "expected_results": "Demo Results"}]


def main():
    """
    Main function to demonstrate the Gemini Pro integration.
    """
    try:
        gemini = GeminiIntegration()
        # This is a placeholder for the document text.
        document_text = "This is an example document."
        requirements = gemini.parse_requirements(document_text)
        test_cases = gemini.generate_test_cases(requirements)
        logging.info(f"Generated {len(test_cases)} test cases.")
    except (ValueError, FileNotFoundError) as e:
        logging.error(f"Configuration Error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
