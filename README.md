# KnowledgeExtractor AI

**Revolutionizing Healthcare Compliance & QA with Generative AI**

KnowledgeExtractor AI is an intelligent platform that ingests complex healthcare requirements documents and automatically generates a comprehensive, audit-ready suite of QA test cases. Built on Google Cloud AI, it transforms dense regulatory documents (FDA, IEC 62304, ISO 13485) into test suites in minutes, not weeks.

---

## 🚀 Key Features

-   **🤖 AI-Powered Test Generation**: Ingests requirements (PDF, MD) and produces high-quality, relevant test cases using Google's Gemini Pro.
-   **🛡️ Compliance-Aware Knowledge Base**: Ensures tests are aligned with critical industry standards (FDA 21 CFR 820, ISO 13485, etc.) using a RAG architecture with Vertex AI Search.
-   **🔄 Real-time Progress Monitoring**: A dynamic frontend built with Next.js and Server-Sent Events provides a live view of the entire pipeline.
-   **✅ Seamless Jira Integration**: One-click export of approved test cases directly to your Jira project via a robust, asynchronous Google Cloud Task queue.
-   **📦 One-Click Audit-Ready Evidence Bundle**: Instantly download a `.zip` archive containing the original requirements, raw Jira API logs, and a full traceability matrix.
-   **📈 Business Impact Analytics**: A real-time dashboard showing estimated cost savings, risk coverage, and compliance alignment.

---

## 🏛️ Architecture Overview

The system uses a secure and scalable pipeline built on Google Cloud:

1.  **Upload & Parse**: Requirements documents are securely uploaded to Cloud Storage and parsed by Google's Document AI.
2.  **Analyze & Cross-Reference**: Gemini Pro analyzes the text, cross-referencing it with our vector-based Compliance Knowledge Base powered by Vertex AI Search.
3.  **Generate & Review**: Gemini generates detailed test cases, which are presented to the user for review in the web UI.
4.  **Export & Log**: Approved tests are sent to Jira via a Cloud Task queue, and all actions are logged in BigQuery for a complete audit trail.

---

## 🛠️ Getting Started

### Prerequisites

-   Python 3.10+
-   Node.js 18+
-   Access to Google Cloud Platform with a configured project
-   A Service Account key with the required permissions (see below)
-   Jira instance with API access

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd KnowledgeExtractor
```

### 2. Setup the Backend (Python)

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use `.\.venv\Scripts\activate`

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Setup the Frontend (Node.js)

```bash
# Navigate to the frontend directory
cd frontend

# Install Node.js dependencies
npm install
```

### 4. Configure Environment Variables

1.  Make a copy of the example environment file.
    ```bash
    cp .env.example .env
    ```
2.  Open the `.env` file and fill in the required values for your GCP project, Gemini API Key, and Service Account Key path.
3.  **IMPORTANT**: Ensure your Service Account has the following IAM roles:
    -   `Secret Manager Secret Accessor`
    -   `BigQuery User`
    -   `Cloud Tasks Enqueuer`
    -   `Document AI API User`
    -   `Service Account User`
    -   `Storage Object Admin`

---

## 🏃‍♂️ How to Run the Application

### 1. Start the Backend Server

From the project root directory:

```bash
# Ensure your Python virtual environment is activated
node backend/server.js
```

The backend will be running at `http://localhost:3001`.

### 2. Start the Frontend Application

In a separate terminal, from the `frontend` directory:

```bash
npm run dev
```

The frontend will be running at `http://localhost:3000`. Open this URL in your browser to use the application.