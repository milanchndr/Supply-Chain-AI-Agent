# backend/agent_tools.py
from langchain_core.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field, ConfigDict # Import ConfigDict

# ... other imports (text_to_sql_utils, db_utils, logger, sqlalchemy.text) ...
from .utils.text_to_sql_utils import generate_sql_from_text_sync
from .utils.db_utils import get_limited_db_schema_string
from .logger_config import logger
from sqlalchemy import text


# --- Document QA Tool Input Schema ---
class DocumentSearchInput(BaseModel):
    query: str = Field(description="A natural language question to search in the documents.")

# --- Document QA Tool ---
class DocumentQATool(BaseTool):
    # Allow arbitrary types for Pydantic v2 if needed for complex objects like chains/engines
    model_config = ConfigDict(arbitrary_types_allowed=True) # Add this

    name: str = "DocumentPolicySearch"
    description: str = (
        "Useful for when you need to answer questions about company policies, "
        "guidelines, procedures, supplier codes of conduct, or other information "
        "likely found in PDF documents. Input should be a specific question."
    )
    args_schema: Type[BaseModel] = DocumentSearchInput
    
    qa_chain: Any # This is now a Pydantic field

    # REMOVE custom __init__ if it only set qa_chain. Pydantic handles it.
    # def __init__(self, qa_chain_instance: Any, **kwargs: Any):
    #     super().__init__(**kwargs)
    #     self.qa_chain = qa_chain_instance

    def _run(self, query: str) -> str:
        # ... (implementation as before, self.qa_chain will be set by Pydantic) ...
        logger.debug(f"DocumentQATool executing with query: {query}")
        if not self.qa_chain: # Should be set if instantiation was correct
            logger.error("DocumentQATool: QA chain not available on self.")
            return "Error: Document QA chain not properly initialized on tool."
        # ... rest of _run ...
        try:
            result = self.qa_chain.invoke({"query": query})
            answer = result.get("result", "No answer found in documents.")
            sources = result.get("source_documents", [])
            source_names = list(set([doc.metadata.get("source", "Unknown") for doc in sources]))
            if source_names:
                return f"Answer from documents: {answer}\nSources: {', '.join(source_names)}"
            return f"Answer from documents: {answer}"
        except Exception as e:
            logger.error(f"Error during document search: {e}", exc_info=True)
            return f"Error during document search: {str(e)}"


    async def _arun(self, query: str) -> str:
        # ... (implementation as before, self.qa_chain will be set by Pydantic) ...
        logger.debug(f"DocumentQATool (async) executing with query: {query}")
        if not self.qa_chain:
            logger.error("DocumentQATool (async): QA chain not available on self.")
            return "Error: Document QA chain not properly initialized on tool."
        # ... rest of _arun ...
        try:
            result = await self.qa_chain.ainvoke({"query": query})
            answer = result.get("result", "No answer found in documents.")
            sources = result.get("source_documents", [])
            source_names = list(set([doc.metadata.get("source", "Unknown") for doc in sources]))
            if source_names:
                return f"Answer from documents: {answer}\nSources: {', '.join(source_names)}"
            return f"Answer from documents: {answer}"
        except Exception as e:
            logger.error(f"Error during async document search: {e}", exc_info=True)
            return f"Error during async document search: {str(e)}"


# --- SQL Database Query Tool Input Schema ---
class DatabaseQueryInput(BaseModel):
    natural_language_query: str = Field(description="A question in natural language to be converted into a SQL query and executed against the supply chain database.")

# --- SQL Database Query Tool ---
class CustomSQLTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True) # Add this

    name: str = "SupplyChainDatabaseQuery"
    description: str = (
        "Useful for when you need to answer questions about specific supply chain data, "
        # ... (rest of description)
    )
    args_schema: Type[BaseModel] = DatabaseQueryInput
    
    db_engine: Any # Pydantic field
    llm: Any       # Pydantic field

    # REMOVE custom __init__ if it only set db_engine and llm
    # def __init__(self, db_engine_instance: Any, llm_instance: Any, **kwargs: Any):
    #     super().__init__(**kwargs)
    #     self.db_engine = db_engine_instance
    #     self.llm = llm_instance

    def _run(self, natural_language_query: str) -> str:
        # ... (implementation as before, self.db_engine and self.llm will be set) ...
        logger.debug(f"CustomSQLTool executing with query: {natural_language_query}")
        if not self.db_engine or not self.llm:
            logger.error("CustomSQLTool: Database engine or LLM not available on self.")
            return "Error: Database engine or LLM for SQL tool not properly initialized."
        # ... rest of _run ...
        sql_query_generated = "N/A (SQL generation not attempted or failed)"
        try:
            schema = get_limited_db_schema_string(self.db_engine, relevant_tables=['supply_chain'])
            if not schema or "not found" in schema.lower(): 
                logger.error(f"CustomSQLTool: Failed to retrieve a valid schema for 'supply_chain'. Schema: {schema}")
                return "Error: Could not retrieve a valid database schema to construct the SQL query."

            sql_query_generated = generate_sql_from_text_sync(natural_language_query, schema, self.llm)
            logger.info(f"CustomSQLTool generated SQL: {sql_query_generated}")

            with self.db_engine.connect() as connection:
                result_proxy = connection.execute(text(sql_query_generated))
                if result_proxy.returns_rows:
                    results = result_proxy.fetchall()
                    column_names = list(result_proxy.keys())
                    answer_data = [dict(zip(column_names, map(str, row_obj))) for row_obj in results] 
                    if not answer_data:
                        return f"Query '{sql_query_generated}' executed successfully, but returned no results."
                    return f"SQL Query Executed: {sql_query_generated}\nResults (up to 5 rows): {str(answer_data[:5])}"
                else:
                    return f"SQL Query '{sql_query_generated}' executed successfully, but it did not return data (e.g., an UPDATE or INSERT, or a SELECT that found no rows)."
        except ValueError as ve: 
            logger.error(f"ValueError in CustomSQLTool: {ve}. NLQ: '{natural_language_query}', Generated SQL: '{sql_query_generated}'", exc_info=True)
            return f"Error processing database query: {str(ve)}. NLQ: '{natural_language_query}'. Generated SQL (if attempted): '{sql_query_generated}'"
        except Exception as e:
            logger.error(f"Unexpected error in CustomSQLTool: {e}. NLQ: '{natural_language_query}', Generated SQL: '{sql_query_generated}'", exc_info=True)
            return f"Error executing database query: {str(e)}. NLQ: '{natural_language_query}'. Generated SQL (if attempted): '{sql_query_generated}'"

    async def _arun(self, natural_language_query: str) -> str:
        # ... (implementation as before) ...
        logger.warning("CustomSQLTool._arun called, but using synchronous _run as fallback.")
        try:
            return self._run(natural_language_query)
        except Exception as e: 
            return f"Error in async fallback for CustomSQLTool: {str(e)}"