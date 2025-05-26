# backend/utils/text_to_sql_utils.py

import sys
import os
from typing import Any

# Add parent directory (backend) to sys.path to find logger_config
# This makes the utility runnable standalone for testing if needed,
# and ensures logger is found when imported by other modules.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.logger_config import logger # Assuming logger_config.py is in the backend directory

# Note: This function no longer needs to be async if the LLM's invoke method is synchronous.
# It now takes the llm_instance as an argument.
def generate_sql_from_text_sync(question: str, schema: str, llm_instance: Any) -> str:
    """
    Generates a SQL query from a natural language question using the provided LLM instance.
    This is a synchronous version.

    Args:
        question: The natural language question.
        schema: The database schema string to provide context to the LLM.
        llm_instance: The initialized Langchain LLM instance (e.g., BedrockLLM).

    Returns:
        A string containing the generated SQL query.

    Raises:
        RuntimeError: If the llm_instance is not provided.
        ValueError: If the LLM generates a non-SELECT query (currently logged as warning).
    """
    if not llm_instance:
        logger.error("LLM instance not provided to generate_sql_from_text_sync.")
        raise RuntimeError("LLM for SQL generation not provided.")

    # Prompt for SQL generation
    # This prompt is crucial and might need further tuning based on LLM behavior.
    prompt = f"""You are an expert PostgreSQL data analyst. Your task is to convert a natural language question into a syntactically correct PostgreSQL query.
Only output the SQL query and nothing else. Do not include any explanation, markdown, or any text other than the SQL query itself.
Ensure that table and column names are quoted if they contain spaces or special characters, or if they are PostgreSQL keywords.
PostgreSQL table and column names are case-insensitive if not quoted, and typically stored as lowercase. Use lowercase unless the schema explicitly shows mixed case or special characters requiring quotes.

Database Schema:
---
{schema}
---

User Question: {question}

PostgreSQL Query:
"""
    logger.info(f"Generating SQL for question: '{question}' using synchronous call.")
    logger.debug(f"SQL generation prompt:\n{prompt}")

    try:
        # Use the synchronous invoke method of the LLM
        # Pass model-specific kwargs like max_tokens, temperature if needed and if your LLM wrapper supports them here.
        # The BedrockLLM class in bedrock_utils.py has default model_kwargs in its config,
        # and its _generate method merges runtime kwargs.
        # The .invoke() method on BaseLLM should handle this.
        sql_query_raw = llm_instance.invoke(
            prompt,
            # You can pass LLM-specific parameters here if needed, e.g.:
            # temperature=0.1,
            # max_tokens=300,
            # stop=["\nObservation:"] # If using ReAct style stop sequences for other LLMs
        )
    except Exception as e:
        logger.error(f"Error during LLM invocation for SQL generation: {e}", exc_info=True)
        raise RuntimeError(f"LLM invocation failed during SQL generation: {e}")


    # Clean up the response: remove potential markdown code blocks or "SQL Query:" prefixes
    sql_query = sql_query_raw.strip()
    if sql_query.lower().startswith("sql query:"):
        sql_query = sql_query[len("sql query:") :].strip()
    if sql_query.startswith("```sql"):
        sql_query = sql_query[len("```sql") :].strip()
    if sql_query.startswith("```"):
        sql_query = sql_query[len("```") :].strip()
    if sql_query.endswith("```"):
        sql_query = sql_query[: -len("```")].strip()

    # Basic validation (ensure it's a SELECT query for safety in this basic setup)
    if not sql_query.strip().upper().startswith("SELECT"):
        logger.warning(
            f"Generated query is not a SELECT query: '{sql_query}'. Proceeding with caution."
        )
        # Depending on strictness, you might raise ValueError here:
        # raise ValueError("Generated query is not a SELECT query. Only SELECT queries are allowed for safety.")

    if not sql_query:
        logger.warning(f"LLM returned an empty string for the SQL query. Original question: '{question}'")
        # Handle empty SQL appropriately, perhaps raise an error or return a specific marker
        raise ValueError("LLM generated an empty SQL query.")


    logger.info(f"Generated SQL query: {sql_query}")
    return sql_query

