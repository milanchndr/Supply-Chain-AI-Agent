# backend/utils/embed_documents.py
import os
import sys
import pdfplumber
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Add parent directory (backend) to sys.path to find config, logger_config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.bedrock_utils import AmazonEmbeddings
from backend.config import BEDROCK_API_KEY, BEDROCK_EMBEDDING_MODEL_ID, BEDROCK_EMBEDDING_LAMBDA_URL
from backend.logger_config import logger

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file using pdfplumber."""
    logger.info(f"Extracting text from: {pdf_path}")
    text_content = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
            if text_content.strip():
                logger.info(f"Successfully extracted text from {pdf_path} using pdfplumber.")
                return text_content.strip()
    except Exception as e:
        logger.warning(f"pdfplumber failed for {pdf_path}: {e}.")

    if not text_content.strip():
        logger.warning(f"No text extracted from {pdf_path} after all attempts.")
    return ""

def create_document_embeddings():
    """Generate and save embeddings for PDF documents with metadata, splitting text into chunks."""
    script_dir = os.path.dirname(__file__)  # .../backend/utils
    base_dir = os.path.abspath(os.path.join(script_dir, '..'))  # .../backend

    document_dir = os.path.join(base_dir, "documents")
    embeddings_dir = os.path.join(base_dir, "embeddings")
    os.makedirs(embeddings_dir, exist_ok=True)

    logger.info(f"Looking for documents in: {document_dir}")
    logger.info(f"Embeddings will be saved to: {embeddings_dir}")

    try:
        embeddings_util = AmazonEmbeddings(
            api_key=BEDROCK_API_KEY,
            model_id=BEDROCK_EMBEDDING_MODEL_ID,
            embedding_lambda_url=BEDROCK_EMBEDDING_LAMBDA_URL
        )
        logger.info(f"AmazonEmbeddings initialized for embedding creation with model {BEDROCK_EMBEDDING_MODEL_ID}.")
    except Exception as e:
        logger.error(f"Failed to initialize AmazonEmbeddings: {e}")
        return

    # Initialize text splitter for chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Roughly a few paragraphs; adjust based on your needs
        chunk_overlap=200  # Overlap to maintain context between chunks
    )

    langchain_documents = []
    if not os.path.isdir(document_dir):
        logger.error(f"Document directory not found: {document_dir}")
        return

    for filename in os.listdir(document_dir):
        if filename.lower().endswith(".pdf"):
            file_path = os.path.join(document_dir, filename)
            text = extract_text_from_pdf(file_path)
            if text:
                # Split the text into chunks
                chunks = text_splitter.split_text(text)
                for i, chunk in enumerate(chunks):
                    langchain_documents.append(Document(
                        page_content=chunk,
                        metadata={"source": filename, "chunk_id": i}
                    ))
            else:
                logger.warning(f"Skipping {filename}: No text extracted.")

    if not langchain_documents:
        logger.warning("No valid documents found or text extracted. No embeddings to create.")
        return

    logger.info(f"Found {len(langchain_documents)} document chunks to process for embeddings.")

    try:
        vectorstore = FAISS.from_documents(langchain_documents, embeddings_util)
        vectorstore.save_local(folder_path=embeddings_dir, index_name="index")  # Default index_name="index"
        logger.info(f"FAISS vector store with embeddings saved to: {embeddings_dir}")
    except ValueError as ve:  # Catch specific errors from _get_embedding like empty embedding
        logger.error(f"ValueError during embedding or FAISS creation: {ve}. This might be due to an issue with a specific document or the embedding model.")
    except RuntimeError as re:  # Catch issues from Bedrock/Lambda calls
        logger.error(f"RuntimeError during embedding or FAISS creation: {re}")
    except Exception as e:
        logger.error(f"An unexpected error occurred creating or saving FAISS vector store: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting document embedding process...")
    create_document_embeddings()
    logger.info("Document embedding process finished.")