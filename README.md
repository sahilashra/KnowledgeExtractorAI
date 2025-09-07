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
-   **Backend:** Python scripts automate the setup and execution of the QA pipeline.
    -   **`setup_day1.py`:** Provisions Document AI and Cloud Storage buckets.
    -   **`setup_day2.py`:** Sets up Vertex AI Search.
    -   **`populate_kb.py`:** Uploads compliance documents to Cloud Storage.
    -   **`main_pipeline.py`:** Orchestrates the end-to-end RAG pipeline.
    -   **`healthcare_pipeline.py`:** Contains the core logic for parsing documents and generating test cases.
-   **Data Flow:**
    1.  Compliance documents are uploaded to **Cloud Storage** using `populate_kb.py`.
    2.  The `main_pipeline.py` script is run, which uses `healthcare_pipeline.py` to:
        a.  Parse requirements from the documents.
        b.  Search the **Vertex AI Search** knowledge base for compliance context.
        c.  Generate test cases using Gemini, grounded in the compliance context.
    3.  The generated test cases are saved to a JSON file and can be exported to various ALM formats.

### Technology Stack:

-   **Frontend:** Next.js, React, TypeScript
-   **Backend:** Python, Gemini Pro, Vertex AI Search
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
git clone https://github.com/sahilashra/KnowledgeExtractorAI.git
cd KnowledgeExtractorAI
```

### 4.2. Configure Environment Variables

1.  **Create a `.env` file:**
    ```bash
    cp .env.example .env
    ```
2.  **Edit the `.env` file** with your GCP project details, service account key path, and a prefix for your GCS buckets.

### 4.3. Backend Setup and Execution

1.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```
2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the setup scripts in order:**
    ```bash
    python backend/src/setup_day1.py
    python backend/src/setup_day2.py
    python backend/src/populate_kb.py
    ```
4.  **Execute the main pipeline:**
    ```bash
    python backend/src/main_pipeline.py
    ```
    This will generate a `healthcare_qa_results.json` file in the root directory.

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

The backend provides a set of scripts for setting up the GCP infrastructure and running the QA pipeline. The core logic is in `healthcare_pipeline.py`, which uses Gemini and Vertex AI Search.

## 6. Troubleshooting Guide

-   **Authentication Errors:**
    -   Ensure your `gcloud` CLI is authenticated. Run `gcloud auth login` and `gcloud auth application-default login`.
    -   Verify that the service account key specified in `GCP_SERVICE_ACCOUNT_KEY_PATH` is correct and has the necessary IAM roles: "Document AI Editor", "Vertex AI Search Admin", and "Storage Admin".
    -   Make sure you have enabled the required APIs in your GCP project.

-   **API Not Enabled:**
    -   If you see errors like `API has not been used in project...`, go to the Google Cloud Console, navigate to "APIs & Services" > "Enabled APIs & Services", and enable the "Document AI API", "Vertex AI Search API", and "Cloud Storage API".

-   **Python Dependencies:**
    -   Always use a virtual environment to avoid conflicts.
    -   If `pip install` fails, check your Python version and ensure it's compatible with the packages in `requirements.txt`.

-   **Frontend Issues:**
    -   If `npm install` fails, try deleting the `node_modules` directory and `package-lock.json` file in the `frontend` directory, then run `npm install` again.
    -   Ensure you have a `.env.local` file in the `frontend` directory with the necessary environment variables for the frontend application.

## 7. Demo Data and Test Files

-   **`compliance-knowledge-base/`:** This directory should be populated with the PDF documents you want to be indexed. Sample documents are provided.
-   **Sample Document:** Ensure the `SAMPLE_DOC_PATH` in your `.env` file points to a valid document for testing the Document AI pipeline.

## 8. Submission Materials

You can find supplementary materials for this hackathon submission in the `/docs` directory:

-   **/docs/presentation:** Contains the presentation slides.
-   **/docs/screenshots:** Contains screenshots of the application.
-   **/docs/samples:** Contains sample output files, such as `healthcare_qa_results.json`.

## 9. Deployment to Cloud Run

To deploy the Next.js frontend to Cloud Run, you can use a Dockerfile.

### 8.1. Create a `Dockerfile` in the `frontend` directory:

```Dockerfile
# Use the official Node.js 18 image.
FROM node:18-alpine

# Set the working directory.
WORKDIR /app

# Copy package.json and package-lock.json.
COPY package*.json ./

# Install dependencies.
RUN npm install

# Copy the rest of the application files.
COPY . .

# Build the Next.js application.
RUN npm run build

# Expose the port the app runs on.
EXPOSE 3000

# Run the application.
CMD ["npm", "start"]
```

### 8.2. Build and Push the Docker Image to Google Artifact Registry:

```bash
# Navigate to the frontend directory
cd frontend

# Configure Docker to use the gcloud CLI
gcloud auth configure-docker

# Build the Docker image
docker build -t us-central1-docker.pkg.dev/YOUR_GCP_PROJECT_ID/knowledge-extractor/frontend:latest .

# Push the image to Artifact Registry
docker push us-central1-docker.pkg.dev/YOUR_GCP_PROJECT_ID/knowledge-extractor/frontend:latest
```

### 8.3. Deploy to Cloud Run:

```bash
gcloud run deploy frontend \
    --image us-central1-docker.pkg.dev/YOUR_GCP_PROJECT_ID/knowledge-extractor/frontend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

Replace `YOUR_GCP_PROJECT_ID` with your actual GCP project ID.

## 9. License

This project is licensed under the MIT License. See the `LICENSE` file for details.
