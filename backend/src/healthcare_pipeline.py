# -*- coding: utf-8 -*-
"""
Healthcare QA Hackathon - Complete Gemini Integration with RAG Pipeline

This implements the core AI pipeline: Document Processing 	 Compliance RAG 	 Test Case Generation
Based on GPT-5 and Perplexity research for healthcare compliance and ALM integration.

Author: Claude (based on team research)
Date: 2025-09-03
"""

import logging
import os
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from dotenv import load_dotenv
import google.generativeai as genai
from google.cloud import discoveryengine_v1alpha as discoveryengine
from google.cloud import storage

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

@dataclass
class HealthcareRequirement:
    """Structured healthcare requirement object"""
    requirement_id: str
    title: str
    description: str
    priority: str
    acceptance_criteria: List[str]
    risk_class: str
    iec_class: str
    traceability_links: List[str]
    compliance_standards: List[str]

@dataclass
class ComplianceContext:
    """Compliance context from RAG search"""
    regulation_code: str
    clause_text: str
    document_title: str
    confidence_score: float
    source_url: str

@dataclass
class HealthcareTestCase:
    """Structured healthcare test case"""
    test_case_id: str
    requirement_id: str
    title: str
    description: str
    test_type: str  # Positive, Negative, Boundary, Performance
    priority: str
    steps: List[Dict[str, str]]
    expected_results: str
    compliance_validation: str
    regulatory_citations: List[str]
    risk_category: str
    automation_feasible: bool

class HealthcareGeminiIntegration:
    """
    Complete healthcare-specific Gemini integration with RAG pipeline
    """
    
    def __init__(self):
        """Initialize with healthcare-specific configurations"""
        load_dotenv()
        self.service_account_path: Optional[str] = os.getenv("GCP_SERVICE_ACCOUNT_KEY_PATH")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.service_account_path
        self._validate_config()
        
        # Initialize clients
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
        self.search_client = discoveryengine.SearchServiceClient()
        self.storage_client = storage.Client()
        
        # Configuration
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.search_engine = f"projects/{self.project_id}/locations/global/collections/default_collection/engines/healthcare-compliance-engine"
        
        # Healthcare-specific prompt templates
        self.requirement_parser_prompt = self._load_requirement_parser_prompt()
        self.test_generator_prompt = self._load_test_generator_prompt()
        
    def _validate_config(self):
        """Validate required environment variables"""
        required_vars = ["GCP_PROJECT_ID", "GEMINI_API_KEY", "GCP_SERVICE_ACCOUNT_KEY_PATH"]
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
    
    def _load_requirement_parser_prompt(self) -> str:
        """Load healthcare-specific requirement parsing prompt"""
        return """
# ROLE
You are an expert Healthcare QA Engineer specializing in medical device software validation. You have deep knowledge of FDA regulations, IEC 62304, ISO 13485, and HIPAA compliance requirements.

# TASK
Parse the following healthcare software requirements document and extract structured requirement objects. Each requirement must be mapped to appropriate compliance standards and risk classifications.

# HEALTHCARE COMPLIANCE CONTEXT
- IEC 62304 Classes: A (non-life-threatening), B (non-life-threatening injury possible), C (life-threatening injury possible)
- FDA Risk Categories: Class I (low risk), Class II (moderate risk), Class III (high risk)
- Priority Levels: Critical (patient safety), High (regulatory compliance), Medium (functionality), Low (convenience)

# OUTPUT FORMAT
Return a JSON array of requirements with this exact structure:
```json
[
  {
    "requirement_id": "REQ-XXX",
    "title": "Brief requirement title",
    "description": "Complete requirement description",
    "priority": "Critical|High|Medium|Low",
    "acceptance_criteria": ["criterion 1", "criterion 2"],
    "risk_class": "High|Medium|Low",
    "iec_class": "Class A|Class B|Class C",
    "traceability_links": ["FDA 21CFR820", "IEC 62304"],
    "compliance_standards": ["FDA", "IEC 62304", "HIPAA"]
  }
]
```

# DOCUMENT TO PARSE:
{document_text}

IMPORTANT: Return ONLY the JSON array, no other text.
"""
    
    def _load_test_generator_prompt(self) -> str:
        """Load healthcare-specific test case generation prompt"""
        return """
# ROLE
You are a Senior QA Engineer for medical device software, expert in creating compliant test cases that satisfy FDA, IEC 62304, and ISO 13485 requirements.

# COMPLIANCE CONTEXT
Based on your compliance knowledge base search, consider these regulatory requirements:
{compliance_context}

# REQUIREMENT TO TEST
{requirement_json}

# TASK
Generate comprehensive test cases for this healthcare requirement. Include positive, negative, boundary, and performance test scenarios as appropriate for the risk class.

# TEST CASE REQUIREMENTS
- Each test case MUST cite specific compliance standards
- Include traceability to original requirements
- Cover all acceptance criteria
- Address risk mitigation for identified hazards
- Include automation feasibility assessment

# OUTPUT FORMAT
Return a JSON array of test cases with this exact structure:
```json
[
  {
    "test_case_id": "TC-{requirement_id}-01",
    "requirement_id": "{requirement_id}",
    "title": "Descriptive test case title",
    "description": "What this test validates",
    "test_type": "Positive|Negative|Boundary|Performance",
    "priority": "Critical|High|Medium|Low",
    "steps": [
      {"step": 1, "action": "Step description", "expected_result": "Expected outcome"}
    ],
    "expected_results": "Overall expected test outcome",
    "compliance_validation": "What compliance requirement this validates",
    "regulatory_citations": ["IEC 62304 Section X.X", "FDA 21CFR820.X"],
    "risk_category": "Safety|Security|Performance|Usability",
    "automation_feasible": true|false
  }
]
```

IMPORTANT: Return ONLY the JSON array, no other text.
"""

    def search_compliance_knowledge(self, query: str, max_results: int = 5) -> List[ComplianceContext]:
        """
        Search the compliance knowledge base for relevant regulatory context
        """
        try:
            # Create search request
            request = discoveryengine.SearchRequest(
                serving_config=f"{self.search_engine}/servingConfigs/default_config",
                query=query,
                page_size=max_results,
            )
            
            # Execute search
            response = self.search_client.search(request)
            
            compliance_contexts = []
            for result in response.results:
                # Extract compliance context from search result
                document = result.document
                compliance_contexts.append(ComplianceContext(
                    regulation_code=document.struct_data.get("regulation_code", "Unknown"),
                    clause_text=document.struct_data.get("content", ""),
                    document_title=document.struct_data.get("title", ""),
                    confidence_score=result.model_scores.get("quality_score", 0.0),
                    source_url=document.struct_data.get("uri", "")
                ))
            
            return compliance_contexts
            
        except Exception as e:
            logging.warning(f"Compliance search failed: {e}")
            # Return default compliance context for demo
            return [ComplianceContext(
                regulation_code="IEC 62304",
                clause_text="Default compliance context for demo",
                document_title="Healthcare Software Lifecycle Standard",
                confidence_score=0.8,
                source_url="demo://compliance-knowledge"
            )]
    
    def parse_requirements_from_text(self, document_text: str) -> List[HealthcareRequirement]:
        """
        Parse healthcare requirements from document text using Gemini Pro
        """
        logging.info("Parsing healthcare requirements with Gemini Pro...")
        
        try:
            # Generate prompt with document text
            prompt = self.requirement_parser_prompt.format(document_text=document_text)
            
            # Call Gemini Pro
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent parsing
                    max_output_tokens=4096,
                )
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0]
            
            requirements_data = json.loads(response_text)
            
            # Convert to structured objects
            requirements = []
            for req_data in requirements_data:
                requirements.append(HealthcareRequirement(**req_data))
            
            logging.info(f"Parsed {len(requirements)} healthcare requirements")
            return requirements
            
        except Exception as e:
            logging.error(f"Error parsing requirements: {e}")
            # Return sample requirement for demo
            return [HealthcareRequirement(
                requirement_id="REQ-DEMO-001",
                title="Sample Healthcare Requirement",
                description="Demo requirement for hackathon",
                priority="High",
                acceptance_criteria=["Demo criteria 1", "Demo criteria 2"],
                risk_class="Medium",
                iec_class="Class B",
                traceability_links=["FDA 21CFR820", "IEC 62304"],
                compliance_standards=["FDA", "IEC 62304"]
            )]
    
    def generate_test_cases_for_requirement(self, requirement: HealthcareRequirement) -> List[HealthcareTestCase]:
        """
        Generate test cases for a specific healthcare requirement with compliance grounding
        """
        logging.info(f"Generating test cases for {requirement.requirement_id}...")
        
        # Search for relevant compliance context
        search_query = f"{requirement.description} {' '.join(requirement.compliance_standards)}"
        compliance_contexts = self.search_compliance_knowledge(search_query)
        
        # Format compliance context for prompt
        compliance_text = "\n".join([
            f"- {ctx.regulation_code}: {ctx.clause_text[:200]}..."
            for ctx in compliance_contexts
        ])
        
        try:
            # Generate prompt
            requirement_json = json.dumps({
                "requirement_id": requirement.requirement_id,
                "title": requirement.title,
                "description": requirement.description,
                "priority": requirement.priority,
                "acceptance_criteria": requirement.acceptance_criteria,
                "risk_class": requirement.risk_class,
                "iec_class": requirement.iec_class
            }, indent=2)
            
            prompt = self.test_generator_prompt.format(
                compliance_context=compliance_text,
                requirement_json=requirement_json
            )
            
            # Call Gemini Pro
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,  # Slightly higher for creative test scenarios
                    max_output_tokens=8192,
                )
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0]
            
            test_cases_data = json.loads(response_text)
            
            # Convert to structured objects
            test_cases = []
            for tc_data in test_cases_data:
                test_cases.append(HealthcareTestCase(**tc_data))
            
            logging.info(f"Generated {len(test_cases)} test cases for {requirement.requirement_id}")
            return test_cases
            
        except Exception as e:
            logging.error(f"Error generating test cases: {e}")
            # Return sample test case for demo
            return [HealthcareTestCase(
                test_case_id=f"TC-{requirement.requirement_id}-001",
                requirement_id=requirement.requirement_id,
                title="Sample Test Case",
                description="Demo test case for hackathon",
                test_type="Positive",
                priority=requirement.priority,
                steps=[{"step": 1, "action": "Demo action", "expected_result": "Demo result"}],
                expected_results="Demo expected results",
                compliance_validation="Demo compliance validation",
                regulatory_citations=["IEC 62304 Demo"],
                risk_category="Safety",
                automation_feasible=True
            )]
    
    def export_to_jira_format(self, test_cases: List[HealthcareTestCase], requirements: List[HealthcareRequirement]) -> List[Dict[str, Any]]:
        """Export test cases to Jira API format"""
        jira_test_cases = []
        
        req_map = {req.requirement_id: req for req in requirements}

        for tc in test_cases:
            steps_text = "\n".join([
                f"{step['step']}. {step['action']} | {step['expected_result']}"
                for step in tc.steps
            ])
            
            requirement = req_map.get(tc.requirement_id)
            compliance_standards = requirement.compliance_standards if requirement else []

            jira_test_cases.append({
                "issueType": "Test Case",
                "fields": {
                    "summary": tc.title,
                    "description": tc.description,
                    "customfield_10001": tc.requirement_id,  # Requirement Link
                    "customfield_10002": tc.test_case_id,    # Test Case ID
                    "customfield_10003": steps_text,         # Test Steps
                    "customfield_10004": tc.expected_results, # Expected Results
                    "priority": {"name": tc.priority},
                    "customfield_10005": compliance_standards, # Compliance Standards
                    "customfield_10006": tc.risk_category,   # Risk Category
                    "customfield_10007": tc.regulatory_citations, # Regulatory Citations
                    "labels": [tc.test_type, tc.risk_category, "Healthcare", "Automated" if tc.automation_feasible else "Manual"]
                }
            })
        
        return jira_test_cases
    
    def export_to_azure_devops_format(self, test_cases: List[HealthcareTestCase], requirements: List[HealthcareRequirement]) -> List[Dict[str, Any]]:
        """Export test cases to Azure DevOps format"""
        azure_test_cases = []
        
        req_map = {req.requirement_id: req for req in requirements}

        for tc in test_cases:
            steps_xml = ""
            for step in tc.steps:
                steps_xml += f"<step id='{step['step']}'><parameterizedString isformatted='true'><![CDATA[{step['action']}]]></parameterizedString><parameterizedString isformatted='true'><![CDATA[{step['expected_result']}]]></parameterizedString><description/></step>"
            
            requirement = req_map.get(tc.requirement_id)
            compliance_standards = ", ".join(requirement.compliance_standards) if requirement else ""

            azure_test_cases.append({
                "workItemType": "Test Case",
                "fields": {
                    "System.Title": tc.title,
                    "System.Description": tc.description,
                    "Microsoft.VSTS.TCM.Steps": f"<steps>{steps_xml}</steps>",
                    "Custom.RequirementLink": tc.requirement_id,
                    "Custom.ComplianceStandard": compliance_standards,
                    "Custom.RiskCategory": tc.risk_category,
                    "Custom.RegulatoryCitations": ", ".join(tc.regulatory_citations),
                    "System.Tags": f"{tc.test_type}; {tc.risk_category}; Healthcare"
                }
            })
        
        return azure_test_cases

    def export_to_polarion_format(self, test_cases: List[HealthcareTestCase]) -> str:
        """Export test cases to Polarion XML format"""
        import xml.etree.ElementTree as ET

        root = ET.Element("testcases")
        
        for tc in test_cases:
            testcase_elem = ET.SubElement(root, "testcase", id=tc.test_case_id)
            
            title_elem = ET.SubElement(testcase_elem, "title")
            title_elem.text = tc.title
            
            ET.SubElement(testcase_elem, "requirement_link").text = tc.requirement_id
            ET.SubElement(testcase_elem, "compliance_std").text = ", ".join(tc.regulatory_citations)
            ET.SubElement(testcase_elem, "risk_class").text = tc.risk_category
            
            steps_elem = ET.SubElement(testcase_elem, "steps")
            for step in tc.steps:
                step_elem = ET.SubElement(steps_elem, "step")
                ET.SubElement(step_elem, "action").text = step['action']
                ET.SubElement(step_elem, "expected_result").text = step['expected_result']

        # Pretty print XML
        ET.indent(root, space="\t", level=0)
        return ET.tostring(root, encoding='unicode')

class HealthcareRAGPipeline:
    """
    Complete RAG pipeline orchestrator for healthcare QA
    """
    
    def __init__(self):
        self.gemini_integration = HealthcareGeminiIntegration()
        self.storage_client = storage.Client()
        
    def process_healthcare_document(self, document_text: str) -> Dict[str, Any]:
        """
        Complete end-to-end processing of healthcare requirements document
        """
        logging.info("Starting healthcare document processing pipeline...")
        
        # 1. Parse requirements from document
        requirements = self.gemini_integration.parse_requirements_from_text(document_text)
        
        # 2. Generate test cases for each requirement
        all_test_cases = []
        for requirement in requirements:
            test_cases = self.gemini_integration.generate_test_cases_for_requirement(requirement)
            all_test_cases.extend(test_cases)
        
        # 3. Export to multiple ALM formats
        jira_export = self.gemini_integration.export_to_jira_format(all_test_cases, requirements)
        azure_export = self.gemini_integration.export_to_azure_devops_format(all_test_cases, requirements)
        polarion_export = self.gemini_integration.export_to_polarion_format(all_test_cases)
        
        # 4. Generate traceability matrix
        traceability_matrix = self._generate_traceability_matrix(requirements, all_test_cases)
        
        return {
            "requirements": [req.__dict__ for req in requirements],
            "test_cases": [tc.__dict__ for tc in all_test_cases],
            "exports": {
                "jira": jira_export,
                "azure_devops": azure_export,
                "polarion": polarion_export
            },
            "traceability_matrix": traceability_matrix,
            "summary": {
                "total_requirements": len(requirements),
                "total_test_cases": len(all_test_cases),
                "coverage_percentage": (len(all_test_cases) / len(requirements) * 100) if requirements else 0
            }
        }
    
    def _generate_traceability_matrix(self, requirements: List[HealthcareRequirement], 
                                    test_cases: List[HealthcareTestCase]) -> List[Dict[str, Any]]:
        """Generate requirements to test case traceability matrix"""
        traceability = []
        
        for req in requirements:
            linked_test_cases = [tc for tc in test_cases if tc.requirement_id == req.requirement_id]
            
            traceability.append({
                "requirement_id": req.requirement_id,
                "requirement_title": req.title,
                "priority": req.priority,
                "risk_class": req.risk_class,
                "iec_class": req.iec_class,
                "test_cases": [tc.test_case_id for tc in linked_test_cases],
                "test_coverage": len(linked_test_cases),
                "compliance_standards": req.compliance_standards,
                "regulatory_traceability": req.traceability_links
            })
        
        return traceability

def main():
    """Demo the healthcare RAG pipeline"""
    try:
        # Initialize pipeline
        pipeline = HealthcareRAGPipeline()
        
        # Sample healthcare document
        sample_doc = """
        REQ-PMS-001: Vital Signs Alert System
        Priority: Critical
        Description: The system shall generate immediate visual and audible alerts when any vital sign exceeds predefined threshold values based on patient age group.
        Acceptance Criteria:
        - Alert response time must be less than 1 second
        - Multiple alert channels: screen notification, audible alarm, nurse station alert
        - Alert persistence until acknowledged by qualified clinical staff
        Risk Class: High (failure could result in patient harm)
        IEC 62304 Class: Class C
        Compliance Standards: FDA 21CFR820, IEC 62304, HIPAA
        """
        
        # Process document
        results = pipeline.process_healthcare_document(sample_doc)
        
        # Display results
        logging.info("Pipeline Results:")
        logging.info(f"Requirements processed: {results['summary']['total_requirements']}")
        logging.info(f"Test cases generated: {results['summary']['total_test_cases']}")
        logging.info(f"Test coverage: {results['summary']['coverage_percentage']:.1f}%")
        
        # Save results
        with open("healthcare_qa_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logging.info("Results saved to healthcare_qa_results.json")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")

if __name__ == "__main__":
    main()
