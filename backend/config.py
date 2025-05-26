# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

BEDROCK_API_KEY = os.getenv("BEDROCK_API_KEY")

# Use the short model IDs as expected by the Lambda API
BEDROCK_LLM_MODEL_ID = "claude-3.5-sonnet"  # Or "claude-3-haiku"
BEDROCK_EMBEDDING_MODEL_ID = "amazon-embedding-v2"

# Unified Lambda URL from .env
LAMBDA_API_URL = os.getenv("LAMBDA_API_URL")

# These will now point to the same unified URL
BEDROCK_LLM_LAMBDA_URL = LAMBDA_API_URL
BEDROCK_EMBEDDING_LAMBDA_URL = LAMBDA_API_URL

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hackathon_db")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# Validations
if not BEDROCK_API_KEY:
    raise ValueError("BEDROCK_API_KEY not found. Please set it in .env file.")
if not LAMBDA_API_URL: # Check the unified URL
    raise ValueError("LAMBDA_API_URL not found. Please set it in .env file.")

TESSERACT_CMD_PATH = os.getenv("TESSERACT_CMD_PATH") # Optional
CSV_PATH_FOR_DB_LOAD = os.getenv("CSV_PATH", "documents/DataCoSupplyChainDataset.csv")