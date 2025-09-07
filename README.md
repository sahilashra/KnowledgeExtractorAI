# Knowledge Extractor: A Healthcare QA System

## 1. Project Overview

This project is a comprehensive solution for building a Healthcare Question-Answering (QA) system using Google Cloud's powerful AI services. It's designed for a hackathon setting, providing a clear and easy-to-follow setup for judges to evaluate. The system automates the process of ingesting, understanding, and indexing healthcare compliance documents, making them easily searchable through a user-friendly interface.

### Key Features:

-   **Automated Document Processing:** Uses **Document AI** to parse and extract structured information from PDF forms.
-   **Intelligent Knowledge Base:** Leverages **Vertex AI Search** to create a powerful, searchable knowledge base from compliance documents.
-   **Scalable Infrastructure:** Built on serverless components like **Cloud Storage** and **Cloud Run** for scalability and cost-effectiveness.
-   **User-Friendly Frontend:** A **Next.js** application provides a clean and intuitive interface for interacting with the QA system.

## 2. Architecture Overview

The system is built on a serverless architecture using Google Cloud Platform services.

-   **Frontend:** A Next.js application provides the user interface for uploading documents and asking questions.
-   **Backend:** Python scripts automate the setup and configuration of the GCP services.
    -   **`setup_day1.py`:** Provisions Document AI and Cloud Storage buckets for the document processing pipeline.
    -   **`setup_day2.py`:** Sets up Vertex AI Search to create the knowledge base.
-   **Data Flow:**
    1.  Healthcare compliance documents (PDFs) are uploaded to a **Cloud Storage** bucket.
    2.  **Document AI** processes the documents, extracts structured data, and stores the output in another Cloud Storage bucket.
    3.  **Vertex AI Search** indexes the processed documents, creating a searchable knowledge base.
    4.  The user interacts with the frontend to ask questions, which are then sent to the Vertex AI Search engine to retrieve relevant answers.

### Technology Stack:

-   **Frontend:** Next.js, React, TypeScript
-   **Backend:** Python
-   **Google Cloud Platform:**
    -   Document AI
    -   Vertex AI Search
    -   Cloud Storage
    -   Cloud Run (for deployment)

## 3. Prerequisites

Before you begin, ensure you have the following:

-   **Google Cloud Account:** A GCP account with billing enabled.
-   **gcloud CLI:** The Google Cloud SDK installed and authenticated.
-   **API Keys & Service Accounts:** A GCP project with the following APIs enabled:
    -   Document AI API
    -   Vertex AI Search API
    -   Cloud Storage API
-   **Python 3.9+**
-   **Node.js 18.x+**

## 4. Step-by-Step Setup Guide

### 4.1. Clone the Repository

```bash
git clone https://github.com/your-username/KnowledgeExtractor.git
cd KnowledgeExtractor
```

### 4.2. Configure Environment Variables

1.  **Create a `.env` file:**
    ```bash
    cp .env.example .env
    ```
2.  **Edit the `.env` file:**
    -   `GCP_PROJECT_ID`: Your Google Cloud project ID.
    -   `GCP_REGION`: The GCP region where you want to deploy the services (e.g., `us-central1`).
    -   `GCP_SERVICE_ACCOUNT_KEY_PATH`: The path to your GCP service account key JSON file.
    -   `DOC_AI_PROCESSOR_DISPLAY_NAME`: A display name for your Document AI processor.
    -   `VERTEX_AI_DATA_STORE_DISPLAY_NAME`: A display name for your Vertex AI Search data store.
    -   `VERTEX_AI_SEARCH_ENGINE_DISPLAY_NAME`: A display name for your Vertex AI Search engine.
    -   `SAMPLE_DOC_PATH`: The path to a sample document for testing the Document AI processor.

### 4.3. Backend Setup

1.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```
2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the setup scripts:**
    -   **Day 1: Document Processing Setup**
        ```bash
        python backend/src/setup_day1.py
        ```
    -   **Day 2: Knowledge Base and Search Setup**
        ```bash
        python backend/src/setup_day2.py
        ```

### 4.4. Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```
2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```
3.  **Run the development server:**
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:3000`.

## 5. API Documentation

(This section can be expanded with details about the API endpoints as the project evolves.)

The backend provides a set of scripts for setting up the GCP infrastructure. The frontend communicates with the Vertex AI Search API to perform queries.

## 6. Troubleshooting Guide

-   **Authentication Errors:** Ensure your `gcloud` CLI is authenticated and the service account key has the necessary permissions (e.g., "Document AI Editor", "Vertex AI Search Admin", "Storage Admin").
-   **API Not Enabled:** If you encounter errors related to APIs not being enabled, go to the GCP Console and enable the required APIs for your project.
-   **Python Dependencies:** If you have issues with Python packages, ensure you are using a virtual environment and have installed all the packages from `requirements.txt`.

## 7. Demo Data and Test Files

-   **`compliance-knowledge-base/`:** This directory contains sample compliance documents (PDFs) that will be indexed by Vertex AI Search. You can add your own documents to this directory.
-   **Sample Document:** The `SAMPLE_DOC_PATH` in the `.env` file should point to a sample document for testing the Document AI processor.

## 8. Deployment to Cloud Run

(This section can be added later with instructions on how to deploy the Next.js frontend and a potential backend API to Cloud Run.)

## 9. License

This project is licensed under the MIT License. See the `LICENSE` file for details.
