# backend/utils/langchain_setup.py
import os

from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS

# Adjust path for direct execution vs. import from app.py
import sys
# This adds the 'backend' directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import (
    BEDROCK_API_KEY, BEDROCK_LLM_MODEL_ID, BEDROCK_EMBEDDING_MODEL_ID,
    BEDROCK_LLM_LAMBDA_URL, BEDROCK_EMBEDDING_LAMBDA_URL
)
from utils.bedrock_utils import BedrockLLM, BedrockLLMConfig, AmazonEmbeddings
from backend.logger_config import logger


def setup_qa_chain():
    """
    Initializes and returns a RetrievalQA chain using Bedrock LLM (via Lambda) and FAISS.
    """
    logger.info("Setting up QA chain...")

    # --- 1. Configure the Bedrock LLM ---
    if not BEDROCK_LLM_MODEL_ID or not BEDROCK_API_KEY or not BEDROCK_LLM_LAMBDA_URL:
        error_msg = "Bedrock LLM config (MODEL_ID, API_KEY, LAMBDA_URL) missing in environment."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    bedrock_config = BedrockLLMConfig(
        model_id=BEDROCK_LLM_MODEL_ID,
        api_key=BEDROCK_API_KEY,
        llm_lambda_url=BEDROCK_LLM_LAMBDA_URL,
        model_kwargs={"temperature": 0.5, "max_tokens": 2000} # Example kwargs
    )
    llm = BedrockLLM(config=bedrock_config)
    logger.info(f"BedrockLLM initialized with model: {BEDROCK_LLM_MODEL_ID}")

    # --- 2. Initialize embeddings and vector store ---
    if not BEDROCK_EMBEDDING_MODEL_ID or not BEDROCK_EMBEDDING_LAMBDA_URL:
        error_msg = "Bedrock Embeddings config (MODEL_ID, LAMBDA_URL) missing."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    embeddings = AmazonEmbeddings(
        api_key=BEDROCK_API_KEY,
        model_id=BEDROCK_EMBEDDING_MODEL_ID,
        embedding_lambda_url=BEDROCK_EMBEDDING_LAMBDA_URL
    )
    logger.info(f"AmazonEmbeddings initialized with model: {BEDROCK_EMBEDDING_MODEL_ID}")

    # Resolve the embeddings folder relative to this file's parent (backend dir)
    here = os.path.dirname(__file__) # .../backend/utils
    embeddings_base_path = os.path.abspath(os.path.join(here, "..", "embeddings")) # .../backend/embeddings

    # FAISS expects "index.faiss" and "index.pkl" in the folder.
    # Our embed_documents.py saves it this way using FAISS.save_local()
    # with default index_name="index"

    if not os.path.isdir(embeddings_base_path):
        error_msg = f"Embeddings directory not found: {embeddings_base_path}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    index_file = os.path.join(embeddings_base_path, "index.faiss")
    pkl_file = os.path.join(embeddings_base_path, "index.pkl")

    if not os.path.isfile(index_file) or not os.path.isfile(pkl_file):
        error_msg = f"FAISS index files (index.faiss, index.pkl) not found in: {embeddings_base_path}. Run embed_documents.py first."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        vectorstore = FAISS.load_local(
            embeddings_base_path,
            embeddings,
            allow_dangerous_deserialization=True, # Ensure you trust the source of index.pkl
            index_name="index" # Default, but explicit
        )
        logger.info(f"FAISS vector store loaded successfully from {embeddings_base_path}")
    except Exception as e:
        logger.error(f"Failed to load FAISS vector store: {e}")
        raise RuntimeError(f"Failed to load FAISS vector store: {e}") from e


    # --- 3. Build RetrievalQA chain ---
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # "stuff" is simple, consider "map_reduce" or "refine" for large docs
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}), # Retrieve top 3 docs
        return_source_documents=True
    )
    logger.info("RetrievalQA chain created successfully.")
    return qa_chain

if __name__ == '__main__':
    # For testing setup_qa_chain directly
    # Ensure .env is correctly set up in the `backend` directory
    # and embeddings are generated.
    try:
        logger.info("Testing langchain_setup.py...")
        chain = setup_qa_chain()
        if chain:
            logger.info("QA Chain setup successful (test).")
            # Example query
            # test_query = "What is the policy on data privacy?"
            # result = chain.invoke({"query": test_query})
            # logger.info(f"Test query result: {result}")
        else:
            logger.error("QA Chain setup failed (test).")
    except Exception as e:
        logger.error(f"Error during langchain_setup.py test: {e}", exc_info=True)