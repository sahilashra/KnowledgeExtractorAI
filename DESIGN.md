# RAG Pipeline Architecture and JSON Schema Design

## RAG Pipeline Architecture

The RAG (Retrieval-Augmented Generation) pipeline connects the processed documents from Day 1 with the compliance knowledge base from Day 2 to provide grounded responses for test case generation.

The pipeline will have the following steps:

1.  **Requirement Extraction**: The initial requirement is extracted from the input document. This can be done using the Document AI pipeline from Day 1 or the Gemini Pro integration.
2.  **Compliance Search**: The extracted requirement is used to search the Vertex AI Search knowledge base for relevant compliance information.
3.  **Prompt Augmentation**: The original requirement and the retrieved compliance information are combined to create a prompt for the Gemini Pro model.
4.  **Test Case Generation**: The augmented prompt is sent to the Gemini Pro model to generate test cases.
5.  **Output Formatting**: The generated test cases are formatted according to the JSON schema defined below.

## JSON Schema Design

The following JSON schema will be used for healthcare test cases with compliance metadata.

```json
{
  "schema_version": "1.0.0",
  "test_case_id": "string",
  "test_case_title": "string",
  "test_case_description": "string",
  "requirement_id": "string",
  "requirement_title": "string",
  "requirement_description": "string",
  "acceptance_criteria": "string",
  "compliance_metadata": [
    {
      "compliance_id": "string",
      "compliance_title": "string",
      "compliance_description": "string",
      "compliance_source": "string"
    }
  ],
  "test_steps": [
    {
      "step_id": "integer",
      "step_description": "string",
      "expected_result": "string"
    }
  ],
  "created_by": "string",
  "created_at": "string",
  "updated_by": "string",
  "updated_at": "string"
}
```
