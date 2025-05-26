# Supply-Chain-AI-Agent

**Supply-Chain-AI-Agent** is an intelligent assistant designed to streamline supply chain operations by providing quick and accurate answers from both policy documents and structured operational data. This project leverages Large Language Models (LLMs) through a custom Bedrock Lambda interface and a RAG (Retrieval Augmented Generation) pipeline for document querying, alongside direct PostgreSQL database querying for real-time data insights.

## Features

*   **Dual Query Capability:**
    *   **Document Intelligence:** Ask questions about company policies, procedures, guidelines, and ethical standards. OCA uses a RAG pipeline with FAISS vector stores and LLMs to find relevant information from PDF documents.
    *   **Database Insights:** Query structured supply chain data (e.g., inventory levels, order statuses) directly from a PostgreSQL database.
*   **Flask API Backend:** Exposes a simple and clean API for querying.
*   **Custom Bedrock Integration:** Utilizes a custom AWS Lambda function to interact with Amazon Bedrock models for LLM and embedding generation, managed via an API key.
*   **Modular Design:** Separated concerns for data loading, embedding generation, Langchain setup, and API logic.

## Project Structure

```
AI Agent/
├── backend/                    # Core backend application
│   ├── app.py                  # Main Flask application
│   ├── config.py               # Configuration (API keys, DB URL from .env)
│   ├── embed_documents.py      # Script to process PDFs and create embeddings
│   ├── documents/              # Source PDF documents & DataCoSupplyChainDataset.csv
│   │   ├── DataCoSupplyChainDataset.csv
│   │   └── example_policy.pdf
│   ├── embeddings/             # Stores FAISS index (generated, gitignored)
│   ├── utils/                  # Utility modules
│   │   ├── __init__.py
│   │   ├── bedrock_utils.py    # Custom Bedrock LLM/Embeddings via Lambda
│   │   ├── langchain_setup.py  # Langchain RAG pipeline setup
│   │   └── load_db.py          # Script to load CSV data into PostgreSQL
│   ├── .env.example            # Example environment file for backend
│   ├── requirements.txt        # Python dependencies for backend
│   └── README.md               # Detailed README for the backend component
├── .gitignore                  # Specifies intentionally untracked files for the whole project
└── README.md                   # This main project README file
```

## Technology Stack

*   **Backend:** Python, Flask
*   **LLM & Embeddings:** Amazon Bedrock (via custom Lambda), Langchain, FAISS
*   **Database:** PostgreSQL
*   **Document Processing:** pdfplumber, PyMuPDF (fitz), Pytesseract OCR
*   **Data Handling:** Pandas, SQLAlchemy

## Prerequisites

Before you begin, ensure you have the following installed:

*   Python (3.9+ recommended)
*   Git
*   PostgreSQL (running and accessible)
*   Tesseract OCR
    *   Installation: [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
    *   Ensure Tesseract is added to your system's PATH, or update the path in `backend/embed_documents.py`.
*   Access to an AWS Lambda function that interfaces with Amazon Bedrock and an API Key for it.

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
    cd YOUR_REPOSITORY_NAME # e.g., cd OmniChain-AI-Agent
    ```

2.  **Navigate to the Backend Directory:**
    ```bash
    cd backend
    ```

3.  **Create and Activate a Python Virtual Environment:**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure PostgreSQL:**
    *   Ensure your PostgreSQL server is running.
    *   Create a database (e.g., `hackathon_db`).
    *   Note your database user, password, host, and port.

6.  **Set Up Environment Variables:**
    *   In the `backend/` directory, copy `.env.example` to a new file named `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit `backend/.env` with your actual credentials and API key:
        ```
        BEDROCK_API_KEY="your_bedrock_lambda_api_key_here"
        BEDROCK_LLM_MODEL_ID="claude-3.5-sonnet" # Or your preferred LLM for the Lambda
        BEDROCK_EMBEDDING_MODEL_ID="amazon.titan-embed-text-v1" # Or your preferred embedding model for the Lambda

        DB_USER="your_db_user"
        DB_PASSWORD="your_db_password"
        DB_HOST="localhost"
        DB_PORT="5432"
        DB_NAME="hackathon_db"
        ```

7.  **Prepare Data and Documents:**
    *   Place your PDF policy documents into the `backend/documents/` folder.
    *   Ensure the `DataCoSupplyChainDataset.csv` file is present in the `backend/documents/` folder. (If this file is very large and not committed, provide download instructions here).

## Data Loading and Embedding Generation

Execute these scripts from the `backend/` directory (while your virtual environment is active).

1.  **Load CSV Data into PostgreSQL:**
    This script will create/replace the `supply_chain` table in your database.
    ```bash
    python utils/load_db.py
    ```

2.  **Generate Document Embeddings:**
    This script will process PDFs in `backend/documents/`, generate embeddings, and save them to the `backend/embeddings/` folder. This can take some time depending on the number and size of your documents.
    ```bash
    python embed_documents.py
    ```

## Running the Backend Application

Once setup, data loading, and embedding generation are complete:

1.  Ensure you are in the `backend/` directory and your virtual environment is active.
2.  Start the Flask application:
    ```bash
    python app.py
    ```
    The API server will start, typically on `http://localhost:5000`. You will see logs in the console, including initialization messages for the database and QA chain (either at startup or on the first query, depending on lazy loading).

## API Usage

The primary endpoint for interacting with the agent is `/query`.

*   **Endpoint:** `POST /query`
*   **URL:** `http://localhost:5000/query`
*   **Headers:** `Content-Type: application/json`
*   **Body (JSON):**
    ```json
    {
        "question": "Your question about documents or database information?"
    }
    ```

**Example Requests (using a tool like Postman or curl):**

1.  **Document Query:**
    ```json
    {
        "question": "What is the company policy on ethical sourcing?"
    }
    ```
    *Expected Response Type: `document`*

2.  **Database Query (heuristic-based):**
    (The current implementation uses a simple heuristic and a fixed SQL query for non-document questions. This query targets a specific region, e.g., "West of USA", for inventory sum.)
    ```json
    {
        "question": "What is the total inventory for West of USA?"
    }
    ```
    *Expected Response Type: `database`*

*   **Status Check:**
    *   **Endpoint:** `GET /`
    *   **URL:** `http://localhost:5000/`
    *   Provides a JSON response with the status of backend components.

## Troubleshooting

*   **`ModuleNotFoundError`:** Ensure your virtual environment is active and all dependencies in `requirements.txt` are installed. If running scripts directly, ensure your Python path is set up correctly or that scripts handle relative imports appropriately (as done in `utils/load_db.py`).
*   **Database Connection Errors:** Verify `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` in `backend/.env` are correct and your PostgreSQL server is running and accessible.
*   **`UndefinedColumn` SQL errors:** The column names used in SQL queries within `app.py` must exactly match the cleaned column names generated by `utils/load_db.py`. Check the console output of `load_db.py` for `New columns: [...]`.
*   **Bedrock/Lambda Errors (e.g., 401 Unauthorized, timeouts, KeyError):**
    *   Ensure `BEDROCK_API_KEY` is correct in `backend/.env`.
    *   Verify your Lambda function is deployed, healthy, and configured correctly for the specified Bedrock models.
    *   Check Lambda logs in AWS CloudWatch.
    *   If `KeyError` occurs in `bedrock_utils.py` when parsing Lambda responses, the JSON structure returned by your Lambda does not match what the utility expects. You'll need to debug by printing the raw Lambda response in `bedrock_utils.py` and adjusting the parsing logic.
*   **Embedding Errors:** Ensure `embed_documents.py` ran successfully and created `index.faiss` and `index.pkl` in `backend/embeddings/`. Check Tesseract OCR installation.

## Future Enhancements

*   **Natural Language to SQL (NL2SQL):** Implement a more sophisticated mechanism to convert natural language database queries into SQL.
*   **Advanced Heuristics/Classifier:** Improve the `is_document_query` function or replace it with a more robust query classification model.
*   **User Authentication & Authorization.**
*   **Support for More Document Types.**
*   **Streaming Responses** for long LLM generations.
*   **Frontend Interface.**
*   **Containerization** with Docker.
