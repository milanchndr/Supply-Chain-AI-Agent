
# AI Supply Chain Agent

## Project Overview

**Live Frontend Deployment:** [https://supply-chain-ai-agent.netlify.app/](https://supply-chain-ai-agent.netlify.app/)

The AI Supply Chain Agent is a sophisticated backend application designed to provide intelligent insights and perform actions related to supply chain management. It leverages a multi-tool Langchain agent capable of querying structured databases (PostgreSQL, potentially via Supabase or a local instance), searching through unstructured PDF documents (company policies, guidelines), and accessing external information via web search. The agent implements robust Role-Based Access Control (RBAC) combined with geographical data restrictions to ensure users only access data and functionalities appropriate for their roles and specific regions.

The system is built with Flask for the backend API, SQLAlchemy for database interactions, and custom Langchain components interacting with Amazon Bedrock models (via a Lambda proxy) for LLM and embedding capabilities. This backend serves a Vue.js frontend application, providing a complete user experience.

## Features

*   **Multi-Tool Agent:** Utilizes a Langchain ReAct agent with the following tools:
    *   **DocumentPolicySearch:** Answers questions based on a corpus of PDF documents using a RetrievalQA chain (FAISS vector store and Bedrock embeddings).
    *   **SupplyChainDatabaseQuery:** Converts natural language questions into SQL queries to fetch data from a PostgreSQL database, respecting user roles and regions.
    *   **ExternalWebSearch:** Uses DuckDuckGo to find answers to general knowledge or current event questions.
*   **Advanced Access Control (RBAC & Geo-Fencing):**
    *   User authentication via JWT.
    *   **Application-Level Control:** Validates user roles and regions before tool execution.
    *   **Database-Level Security:**
        *   Applies regional filters directly to SQL queries for non-global roles.
        *   Designed for seamless integration with PostgreSQL Row-Level Security (RLS) policies, which can further refine access based on JWT claims (e.g., `app_metadata.role`, `app_metadata.region`). This ensures data segregation at the database layer.
*   **Bedrock Integration (via Lambda):**
    *   Utilizes Amazon Bedrock's Claude models (e.g., Claude 3.5 Sonnet) for LLM tasks (SQL generation, agent reasoning).
    *   Uses Amazon Bedrock's Titan Embeddings models (e.g., `amazon.titan-embed-text-v1` or newer like `cohere.embed-multilingual-v3`) for document embeddings.
    *   Interactions with Bedrock are proxied through a configurable AWS Lambda function for security and abstraction.
*   **Document Processing & Retrieval:**
    *   Extracts text from PDF documents.
    *   Chunks text and generates embeddings using Bedrock.
    *   Stores embeddings in a FAISS vector store for efficient similarity search.
*   **Database Management:**
    *   Script (`load_db.py`) to initialize the PostgreSQL database, create tables (`supply_chain`, `users`, `audit_logs`), create necessary roles (like `authenticated`), grant permissions, and load sample data from a CSV.
*   **API Endpoints:**
    *   `/login`: User authentication, returns JWT.
    *   `/query`: Main endpoint to interact with the AI agent, requires JWT.
    *   `/health`: Health check for the application and its core components.
*   **Audit Logging:** Records user queries, agent actions, and outcomes in an `audit_logs` table for monitoring and compliance.
*   **Vue.js Frontend:** A user-friendly interface (hosted separately, e.g., on Netlify) interacts with these backend APIs to provide a seamless chat experience.

## Project Structure

```
.
├── backend/
│   ├── .env                  # Environment variables (GITIGNORED!)
│   ├── agent_tools.py        # Custom Langchain tools (DocumentQA, SQLQuery)
│   ├── app.py                # Flask application, API endpoints, initialization
│   ├── config.py             # Application configuration, Bedrock IDs, DB URL, ROLES_PERMISSIONS
│   ├── logger_config.py      # Centralized logging setup
│   ├── requirements.txt      # Python dependencies
│   ├── utils/                # Utility modules
│   │   ├── __init__.py
│   │   ├── agent_handler.py  # Agent creation, prompt templating, memory setup
│   │   ├── bedrock_utils.py  # Bedrock LLM and Embedding wrappers (Lambda interaction)
│   │   ├── db_utils.py       # Database schema introspection utilities
│   │   ├── embed_documents.py# Script to process PDFs and create FAISS embeddings
│   │   ├── langchain_setup.py# Initializes QA chain and LLM instances for tools
│   │   ├── load_db.py        # Script to setup database, load data, create users/roles
│   │   └── text_to_sql_utils.py # Text-to-SQL generation logic using LLM
│   ├── documents/            # Store PDF documents here for embedding
│   │   └── DataCoSupplyChainDataset.csv # Sample CSV for database loading
│   ├── embeddings/           # Stores FAISS index (GITIGNORED or managed via artifact store)
├── .gitignore
└── README.md
```

## Setup and Installation

### Prerequisites

*   Python 3.9+
*   PostgreSQL database instance (local, Docker, or cloud-hosted like Supabase)
*   Access to Amazon Bedrock (or a Lambda function proxying Bedrock calls)
*   Git
*   Node.js and npm/yarn (for the Vue.js frontend, if setting it up locally)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-repository-name>
```

### 2. Set Up Backend Environment Variables

Navigate to the `backend` directory and create a `.env` file (you can copy `.env.example` if provided):

```bash
cd backend
# cp .env.example .env # If you have an example file
# Create .env manually if no example exists
```

Edit the `.env` file with your specific configurations:

```env
# Bedrock Configuration
BEDROCK_API_KEY="your_bedrock_or_lambda_api_key" # API Key for your Lambda proxy
LAMBDA_API_URL="your_aws_lambda_url_for_bedrock_proxy"
# BEDROCK_LLM_MODEL_ID and BEDROCK_EMBEDDING_MODEL_ID are usually defined in config.py but can be overridden here.

# Database Configuration
# For local PostgreSQL:
# DB_USER="your_db_user"
# DB_PASSWORD="your_db_password"
# DB_HOST="localhost"
# DB_PORT="5432"
# DB_NAME="your_db_name"
# DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Or for Supabase/Cloud PostgreSQL:
SUPABASE_URL="postgresql://user:password@host:port/database" # Your full DB connection string
DATABASE_URL=${SUPABASE_URL} # Use the same or a specific pooler URL if applicable

# JWT Configuration
JWT_SECRET_KEY="your_very_strong_and_random_jwt_secret_key" # IMPORTANT: Change this!

# Optional: Path to CSV for DB loading (relative to project root if path starts with / or ../)
CSV_PATH_FOR_DB_LOAD="/documents/DataCoSupplyChainDataset.csv" # Default is in config.py

# Optional: Logging Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL="INFO"
```

**Important:** Ensure `.env` is listed in your `.gitignore` file to prevent committing secrets.

### 3. Set Up Python Virtual Environment and Install Dependencies

From the `backend` directory:

```bash
python -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database

*   Ensure your PostgreSQL instance is running.
*   The `load_db.py` script (Step 5) will create tables, roles (like `authenticated`), and grant necessary permissions for local development.
*   **For Supabase or other cloud DBs with RLS:**
    *   Enable RLS on the `supply_chain` table.
        ```sql
        ALTER TABLE supply_chain ENABLE ROW LEVEL SECURITY;
        ALTER TABLE supply_chain FORCE ROW LEVEL SECURITY; -- Recommended for stricter security
        ```
    *   Create helper functions in your DB to extract JWT claims for RLS policies (if you choose to use DB-level RLS in addition to app-level filters). Example:
        ```sql
        -- Helper to get role from JWT (ensure it's SECURITY DEFINER if needed for some setups)
        CREATE OR REPLACE FUNCTION public.get_jwt_claim_app_role()
        RETURNS text LANGUAGE sql STABLE AS $$
          SELECT current_setting('request.jwt.claims', true)::jsonb -> 'app_metadata' ->> 'role';
        $$;
        GRANT EXECUTE ON FUNCTION public.get_jwt_claim_app_role() TO authenticated;

        -- Helper to get region from JWT
        CREATE OR REPLACE FUNCTION public.get_jwt_claim_app_region()
        RETURNS text LANGUAGE sql STABLE AS $$
          SELECT current_setting('request.jwt.claims', true)::jsonb -> 'app_metadata' ->> 'region';
        $$;
        GRANT EXECUTE ON FUNCTION public.get_jwt_claim_app_region() TO authenticated;

        -- Example RLS Policy (applied if DB-level RLS is used)
        CREATE POLICY "User region-based access on supply_chain"
        ON supply_chain FOR SELECT
        TO authenticated -- Apply to the 'authenticated' role
        USING (
            (public.get_jwt_claim_app_role() = 'Global Operations Manager') OR -- GOM has global access
            (LOWER(order_country) = LOWER(public.get_jwt_claim_app_region())) -- Others filtered by region
        );
        ```
    *   Ensure the `authenticated` role (created by `load_db.py` or Supabase) has `SELECT` permissions on tables and `EXECUTE` on helper functions. `load_db.py` handles basic grants for local setups.
*   **Indexes:** `load_db.py` creates some basic indexes. For performance, especially with RLS, ensure relevant columns are indexed (e.g., `LOWER(order_country)` if used in filters/policies).

### 5. Load Initial Data and Create Database Objects

From the project's root directory (where `backend` is a subfolder):

```bash
# Make sure your virtual environment is active
python -m backend.utils.load_db
```

This script will:
*   Connect to your PostgreSQL database using `DATABASE_URL` from `.env`.
*   Create `supply_chain`, `users`, and `audit_logs` tables.
*   Create necessary PostgreSQL roles like `authenticated`.
*   Grant `SELECT` permissions on `supply_chain` to the `authenticated` role.
*   Load data from `DataCoSupplyChainDataset.csv` into `supply_chain`.
*   Create sample users (e.g., `planner_india` with password `mypassword`).

### 6. Generate Document Embeddings

1.  Place your PDF documents (e.g., company policies) into the `backend/documents/` folder.
2.  Run the embedding script from the project's root directory:

    ```bash
    # Make sure your virtual environment is active
    python -m backend.utils.embed_documents
    ```
    This will:
    *   Read PDFs from `backend/documents/`.
    *   Extract text, chunk it, and generate embeddings using Bedrock (via Lambda).
    *   Save the FAISS vector store index to `backend/embeddings/`.

### 7. Running the Backend Application

From the `backend` directory (ensure your virtual environment is active):

```bash
flask run --host=0.0.0.0 --port=5000
# Or, if app.py has app.run(debug=True...):
# python app.py
```

The backend API will be available at `http://localhost:5000`.

### 8. (Optional) Running the Vue.js Frontend Locally

If you have the Vue.js frontend code:
1.  Navigate to the frontend project directory.
2.  Install dependencies: `npm install` or `yarn install`.
3.  Configure the frontend's `.env` file to point to your local backend API URL (e.g., `VITE_API_BASE_URL=http://localhost:5000`).
4.  Run the frontend development server: `npm run dev` or `yarn dev`.

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

## Usage Example (e.g., using `curl`)

1.  **Login:**
    ```bash
    curl -X POST http://localhost:5000/login \
    -H "Content-Type: application/json" \
    -d '{"username": "planner_india", "password": "mypassword"}'
    ```
    (Copy the `access_token` from the response)

2.  **Query the Agent:**
    ```bash
    curl -X POST http://localhost:5000/query \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <PASTE_YOUR_ACCESS_TOKEN_HERE>" \
    -d '{"question": "What is the average sales per customer in India?"}'
    ```

## Key Configuration Points

*   **`backend/config.py`**: Defines Bedrock model IDs, default paths, and crucially, `ROLES_PERMISSIONS` which dictates allowed tables/columns for different application roles and if a role has "global_access" (bypassing app-level regional SQL filters).
*   **`backend/.env`**: Stores all secrets (API keys, DB URLs, JWT secret). **Never commit this file.**
*   **`backend/utils/load_db.py`**: Handles database schema setup, role creation, and initial data loading. Crucial for local development to mimic a Supabase-like environment regarding roles like `authenticated` and basic permissions.
*   **RLS Policies in PostgreSQL/Supabase**: While the app has its own SQL filtering, for defense-in-depth, actual RLS policies in the database are recommended, especially in production. These policies would use `current_setting('request.jwt.claims', true)::jsonb` to access JWT payload.
*   **Lambda Proxy for Bedrock**: The `LAMBDA_API_URL` must point to a working AWS Lambda function that can securely invoke Bedrock models using the provided `BEDROCK_API_KEY`.

## Troubleshooting

*   **"Role 'authenticated' does not exist"**: Ensure `load_db.py` ran successfully and created this role in your local/target PostgreSQL instance.
*   **"Permission denied for table X" for `authenticated` role**: After `SET LOCAL ROLE authenticated;`, the session has permissions of `authenticated`. `load_db.py` should `GRANT SELECT ON supply_chain TO authenticated;`. Verify this grant.
*   **RLS Not Filtering Data (if using DB RLS):**
    *   Verify RLS is `ENABLED` and `FORCED` on the table.
    *   Test your RLS helper functions (e.g., `get_jwt_claim_app_role()`) directly in a SQL client after setting `request.jwt.claims` for a session.
    *   Ensure JWT payload set via `SELECT set_config('request.jwt.claims', '...', true);` is correct *before* queries are run.
*   **SQL Query Errors / "Column does not exist"**: Check the `relevant_tables` and `allowed_columns` in `ROLES_PERMISSIONS` in `config.py`. The LLM generates SQL based on schema derived from these. Also, check for mismatches between CSV column names and database table column names.
*   **Embedding Failures**:
    *   Verify `BEDROCK_API_KEY`, `LAMBDA_API_URL`, and the embedding model ID in `config.py`.
    *   Ensure PDF documents are in `backend/documents/` and are readable.
    *   Check Lambda logs for errors from Bedrock.
*   **Timeouts**: Large queries or inefficient RLS policies can cause timeouts. Optimize SQL and ensure proper indexing on filtered columns (e.g., `order_country`).
*   **CORS Errors (when connecting frontend)**: Ensure `Flask-CORS` is configured correctly in `app.py` to allow requests from your frontend's origin (e.g., `http://localhost:8080` for local Vue dev, or your Netlify URL).

This README provides a comprehensive guide to setting up, running, and understanding the AI Supply Chain Agent.
```
