# AI Supply Chain Agent

## Project Overview

The AI Supply Chain Agent is a sophisticated backend application designed to provide intelligent insights and perform actions related to supply chain management. It leverages a multi-tool Langchain agent capable of querying structured databases (PostgreSQL via Supabase), searching through unstructured PDF documents (company policies, guidelines), and accessing external information via web search. The agent implements Role-Based Access Control (RBAC) to ensure users only access data and functionalities appropriate for their roles and regions.

The system is built with Flask for the backend API, SQLAlchemy for database interactions, and custom Langchain components interacting with Amazon Bedrock models (via a Lambda proxy) for LLM and embedding capabilities.

## Features

*   **Multi-Tool Agent:** Utilizes a Langchain ReAct agent with the following tools:
    *   **DocumentPolicySearch:** Answers questions based on a corpus of PDF documents using a RetrievalQA chain (FAISS vector store and Bedrock embeddings).
    *   **SupplyChainDatabaseQuery:** Converts natural language questions into SQL queries to fetch data from a PostgreSQL database, respecting user roles and regions.
    *   **ExternalWebSearch:** Uses DuckDuckGo to find answers to general knowledge or current event questions.
*   **Role-Based Access Control (RBAC):**
    *   User authentication via JWT.
    *   Application-level role and region checks.
    *   Database-level Row-Level Security (RLS) to filter data based on user's region and role (requires RLS policies to be set up in Supabase).
*   **Bedrock Integration (via Lambda):**
    *   Utilizes Amazon Bedrock's Claude (e.g., Sonnet 3.5) for LLM tasks (SQL generation, agent reasoning).
    *   Uses Amazon Bedrock's Titan Multimodal Embeddings (e.g., `amazon-embedding-v2`) for document embeddings.
    *   Interactions with Bedrock are proxied through a configurable AWS Lambda function.
*   **Document Processing:**
    *   Extracts text from PDF documents.
    *   Chunks text and generates embeddings.
    *   Stores embeddings in a FAISS vector store for efficient similarity search.
*   **Database Management:**
    *   Script (`load_db.py`) to initialize the PostgreSQL database, create tables (`supply_chain`, `users`, `audit_logs`), and load sample data from a CSV.
*   **API Endpoints:**
    *   `/login`: User authentication.
    *   `/query`: Main endpoint to interact with the AI agent.
    *   `/health`: Health check for the application.
*   **Audit Logging:** Records user queries and agent interactions in an `audit_logs` table.

## Project Structure

```
.
├── backend/
│   ├── .env                  # Environment variables (GITIGNORED!)
│   ├── agent_tools.py        # Custom Langchain tools
│   ├── app.py                # Flask application, API endpoints
│   ├── config.py             # Application configuration, Bedrock IDs, DATABASE_URL
│   ├── logger_config.py      # Logging setup
│   ├── requirements.txt      # Python dependencies
│   ├── utils/                # Utility modules
│   │   ├── __init__.py
│   │   ├── agent_handler.py  # Agent creation and prompt logic
│   │   ├── bedrock_utils.py  # Bedrock LLM and Embedding wrappers (Lambda interaction)
│   │   ├── db_utils.py       # Database schema introspection
│   │   ├── embed_documents.py# Script to process PDFs and create embeddings
│   │   ├── langchain_setup.py# Initializes QA chain and LLM instances
│   │   ├── load_db.py        # Script to load data into the database
│   │   └── text_to_sql_utils.py # Text-to-SQL generation logic
│   ├── documents/            # Store PDF documents here for embedding
│   │   └── DataCoSupplyChainDataset.csv # Sample CSV for database loading
│   ├── embeddings/           # Stores FAISS index (GITIGNORED or managed via artifact store)
│   └── (other_python_files...)
├── .gitignore
└── README.md
```

## Setup and Installation

### Prerequisites

*   Python 3.9+
*   PostgreSQL database (Supabase project recommended)
*   Access to Amazon Bedrock (or a Lambda function proxying Bedrock)
*   Git

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-repository-name>
```

### 2. Set Up Environment Variables

Navigate to the `backend` directory and create a `.env` file:
```bash
cd backend
cp .env.example .env # If you have an example file, otherwise create .env manually
```
Edit the `.env` file with your specific configurations:

```env
# Bedrock Configuration
BEDROCK_API_KEY="your_bedrock_or_lambda_api_key"
LAMBDA_API_URL="your_aws_lambda_url_for_bedrock_proxy"
# BEDROCK_LLM_MODEL_ID="claude-3.5-sonnet" # Defined in config.py, can be overridden here if needed
# BEDROCK_EMBEDDING_MODEL_ID="amazon-embedding-v2" # Defined in config.py

# Database Configuration
SUPABASE_URL="postgresql://user:password@host:port/database" # Your Supabase DB connection string
DATABASE_URL=${SUPABASE_URL} # Can be the same or a different pooler URL

# JWT Configuration
JWT_SECRET_KEY="your_super_secret_jwt_key" # Change this to a strong random string

# Optional: Path to CSV for DB loading (relative to backend directory)
# CSV_PATH_FOR_DB_LOAD="../documents/DataCoSupplyChainDataset.csv" # Default is in config.py

# Optional: Logging Level
# LOG_LEVEL="INFO" # (DEBUG, INFO, WARNING, ERROR)
```
**Important:** Ensure `.env` is listed in your `.gitignore` file to prevent committing secrets.

### 3. Set Up Python Virtual Environment and Install Dependencies

From the `backend` directory:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Set Up Supabase Database

*   Ensure your Supabase project is running and you have the connection string.
*   **RLS Policies (Crucial for RBAC on Database):**
    You need to set up Row-Level Security policies on your `supply_chain` table in Supabase. Example policies are discussed in the project and usually involve checking `current_setting('request.jwt.claims.app_metadata.role', true)` and `current_setting('request.jwt.claims.app_metadata.region', true)`.
    Refer to the [Supabase RLS documentation](https.supabase.com/docs/guides/auth/row-level-security) and the RLS policy examples developed during this project. This typically involves:
    ```sql
    -- Enable RLS on the table
    ALTER TABLE supply_chain ENABLE ROW LEVEL SECURITY;
    ALTER TABLE supply_chain FORCE ROW LEVEL SECURITY; -- Recommended

    -- Helper functions for RLS (create these in your DB)
    CREATE OR REPLACE FUNCTION public.get_jwt_claim_role() RETURNS TEXT ... STABLE SECURITY DEFINER;
    CREATE OR REPLACE FUNCTION public.get_jwt_claim_region() RETURNS TEXT ... STABLE SECURITY DEFINER;
    GRANT EXECUTE ON FUNCTION public.get_jwt_claim_role() TO authenticated;
    GRANT EXECUTE ON FUNCTION public.get_jwt_claim_region() TO authenticated;


    -- Example RLS Policy
    CREATE POLICY "User region-based access on supply_chain"
    ON supply_chain FOR SELECT USING (
        (public.get_jwt_claim_role() = LOWER('Global Operations Manager')) OR
        (LOWER(order_country) = public.get_jwt_claim_region())
    );
    ```
    *Ensure the helper functions and the policy are correctly implemented in your Supabase SQL editor.*
*   **Indexes:** Create necessary indexes for performance. Some are created by `load_db.py`, but you can add more via the SQL editor.
    ```sql
    CREATE INDEX IF NOT EXISTS idx_supply_chain_lower_order_country ON supply_chain (LOWER(order_country));
    -- Add other relevant indexes on frequently queried columns
    ```

### 5. Load Initial Data and Create Users

From the `backend/utils` directory (or adjust path if running from `backend`):
```bash
# Make sure your virtual environment is active
# Navigate to the directory containing load_db.py if not already in backend/utils/
# cd backend/utils  (if load_db.py is there)
# python load_db.py

# Or if load_db.py is in backend/ and you run from project root:
# python backend/load_db.py
```
This script will:
*   Create the `supply_chain`, `users`, and `audit_logs` tables.
*   Load data from `DataCoSupplyChainDataset.csv` into `supply_chain`.
*   Create a sample user (e.g., `planner_india` / `mypassword`). You can add more users directly in your Supabase `users` table or modify the script.

### 6. Generate Document Embeddings

Place your PDF documents into the `backend/documents/` folder.
Then, run the embedding script from the `backend/utils` directory (or adjust path):
```bash
# Make sure your virtual environment is active
# Navigate to the directory containing embed_documents.py
# cd backend/utils
# python embed_documents.py

# Or if embed_documents.py is in backend/ and you run from project root:
# python backend/embed_documents.py
```
This will create a `backend/embeddings/` folder containing the FAISS index. Ensure this path aligns with what `langchain_setup.py` expects.

## Running the Application

From the `backend` directory (ensure your virtual environment is active):

```bash
flask run --host=0.0.0.0 --port=5000
# Or, if app.py has app.run(debug=True...):
# python app.py
```
The application will be available at `http://localhost:5000`.

## API Endpoints

*   **`POST /login`**:
    *   Authenticates a user.
    *   Request Body: `{"username": "your_username", "password": "your_password"}`
    *   Response: `{"access_token": "your_jwt_token"}`
*   **`POST /query`**:
    *   Sends a question to the AI agent.
    *   Headers: `Authorization: Bearer <your_jwt_token>`
    *   Request Body: `{"question": "Your natural language question here"}`
    *   Response: `{"answer": "Agent's answer", "type": "agent_multi_tool"}`
*   **`GET /health`**:
    *   Checks the health and initialization status of backend components.

## Usage Example (e.g., using curl or Postman)

1.  **Login:**
    ```bash
    curl -X POST http://localhost:5000/login \
    -H "Content-Type: application/json" \
    -d '{"username": "planner_india", "password": "mypassword"}'
    ```
    *(Save the returned `access_token`)*

2.  **Query the Agent:**
    ```bash
    curl -X POST http://localhost:5000/query \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <PASTE_YOUR_ACCESS_TOKEN_HERE>" \
    -d '{"question": "What is the average sales per customer in India?"}'
    ```

## Key Configuration Points

*   **`backend/config.py`**: Defines Bedrock model IDs, role permissions (`ROLES_PERMISSIONS`), and default paths.
*   **`backend/.env`**: Stores all secrets and environment-specific URLs.
*   **RLS Policies in Supabase**: Essential for database security and multi-tenancy/regional access.
*   **Lambda Proxy for Bedrock**: The `LAMBDA_API_URL` must point to a working Lambda function that can invoke Bedrock models using the provided `BEDROCK_API_KEY`.

## Troubleshooting

*   **"Function does not exist" errors (PostgreSQL):** Ensure helper functions for RLS (`get_jwt_claim_role`, `get_jwt_claim_region`) are created in the correct schema (usually `public`) and that the `authenticated` role (or other relevant roles) have `EXECUTE` permissions on them. RLS policies should use schema-qualified function names (e.g., `public.get_jwt_claim_role()`).
*   **RLS Not Filtering Data:**
    *   Verify RLS is enabled on the table (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`).
    *   Consider `ALTER TABLE ... FORCE ROW LEVEL SECURITY;`.
    *   Double-check the logic in your RLS policy and the values returned by helper functions within a simulated user session.
    *   Ensure data consistency between `users.region` and `supply_chain.order_country` (or a similar column).
*   **Timeouts ("Gateway Timeout", "Upstream Timeout"):**
    *   Often due to RLS policies being inefficient on large tables. Optimize RLS using `STABLE` helper functions and appropriate indexes (e.g., on `LOWER(order_country)`).
    *   Consider increasing statement timeouts in Supabase connection pooler settings for debugging, but aim to optimize queries/RLS for production.
*   **`current_setting('request.jwt.claims...', true)` returning NULL:** This was a major debug point. Ensure the JWT is correctly set in the session *before* RLS policies try to read it. The order of `SET ROLE` and `set_config` in your application's database interaction matters. Using explicit JSONB functions (`::jsonb -> 'path' ->> 'key'`) in RLS policies on `current_setting('request.jwt.claims', true)` is more robust than relying on `current_setting('request.jwt.claims.path.key', true)`.
*   **Embedding Failures:** Check `BEDROCK_EMBEDDING_MODEL_ID`, `LAMBDA_API_URL`, and `BEDROCK_API_KEY`. Ensure PDF documents are in the `backend/documents` folder.
