from langchain_core.tools import BaseTool, ToolException
from typing import Type, Any, Dict, Union # Added Dict, Union, ToolException
from pydantic import BaseModel, Field, ConfigDict, ValidationError # Added ValidationError
from sqlalchemy import text
import json 

from .utils.text_to_sql_utils import generate_sql_from_text_sync
from .utils.db_utils import get_limited_db_schema_string
from .logger_config import logger
from .config import ROLES_PERMISSIONS 

# --- Document QA Tool Input Schema ---
class DocumentSearchInput(BaseModel):
    query: str = Field(description="A natural language question to search in the documents.")
    user_role: str = Field(description="The role of the user making the query.")
    user_region: str = Field(description="The region the user is authorized to access.")

# --- Document QA Tool ---
class DocumentQATool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "DocumentPolicySearch"
    description: str = (
        "Useful for when you need to answer questions about company policies, "
        "guidelines, procedures, supplier codes of conduct, or other information "
        "likely found in PDF documents. Input should be a specific question."
    )
    args_schema: Type[BaseModel] = DocumentSearchInput
    
    qa_chain: Any

    def _parse_input(self, tool_input: Union[str, Dict]) -> Dict[str, Any]:
        """Override to ensure JSON string is parsed correctly for multi-argument schema."""
        if isinstance(tool_input, str):
            try:
                parsed_input = json.loads(tool_input)
                if not isinstance(parsed_input, dict):
                    raise ToolException(
                        f"Tool {self.name} received a JSON string that did not decode to a dictionary: {tool_input}"
                    )
                return parsed_input 
            except json.JSONDecodeError as e:
                raise ToolException(
                    f"Tool {self.name} received input '{tool_input}' which is not valid JSON "
                    f"for a multi-argument schema. Error: {e}"
                )
        elif isinstance(tool_input, dict):
            return tool_input
        
        raise ToolException(
            f"Tool {self.name} received tool input of type {type(tool_input)} "
            f"but expects a JSON string or a dict."
        )

    def _run(self, query: str, user_role: str, user_region: str) -> str:
        logger.debug(f"DocumentQATool executing with query: {query}, role: {user_role}, region: {user_region}")
        if not self.qa_chain:
            logger.error("DocumentQATool: QA chain not available on self.")
            return "Error: Document QA chain not properly initialized on tool."

        if user_role not in ROLES_PERMISSIONS:
            return f"Error: Unauthorized access due to invalid role '{user_role}' for DocumentPolicySearch."

        role_permissions_config = ROLES_PERMISSIONS[user_role]
        try:
            effective_query = query
            if user_region != "Global" and not role_permissions_config.get("global_access", False):
                effective_query = f"{query} (related to {user_region})"
                logger.info(f"DocumentQATool: Query augmented for region: {user_region}")

            logger.info(f"DocumentQATool effective query: {effective_query}")
            result = self.qa_chain.invoke({"query": effective_query}) # QA chain expects a dict
            answer = result.get("result", "No answer found in documents.")
            sources = result.get("source_documents", [])
            
            # Simplified source filtering for brevity
            source_names = sorted(list(set([doc.metadata.get("source", "Unknown") for doc in sources])))

            if not answer or answer == "No answer found in documents.":
                 if source_names:
                     return f"I found relevant information in the following documents: {', '.join(source_names)}, but could not extract a direct answer. Please review them."
                 return "I searched the available documents but could not find an answer."

            if source_names:
                return f"Answer from documents: {answer}\nSources: {', '.join(source_names)}"
            return f"Answer from documents: {answer}"
        except Exception as e:
            logger.error(f"Error during document search: {e}", exc_info=True)
            return f"Error: An issue occurred during document search: {str(e)}"

    async def _arun(self, query: str, user_role: str, user_region: str) -> str:
        logger.debug(f"DocumentQATool (async) executing with query: {query}, role: {user_role}, region: {user_region}")
        return self._run(query, user_role, user_region)


# --- SQL Database Query Tool Input Schema ---
class DatabaseQueryInput(BaseModel):
    natural_language_query: str = Field(description="A question in natural language to be converted into a SQL query.")
    user_role: str = Field(description="The role of the user making the query. This helps in context but RLS enforces permissions.")
    user_region: str = Field(description="The region the user is authorized to access. This helps in context but RLS enforces permissions.")
    jwt_claims_for_db: str = Field(description="The JSON string of JWT claims for setting DB session context for RLS.")

# --- SQL Database Query Tool ---
class CustomSQLTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "SupplyChainDatabaseQuery"
    description: str = (
        "Useful for when you need to answer questions about specific supply chain data directly from the database, "
        "such as inventory levels, sales figures, order statuses, or logistics information. Use this when the question implies "
        "retrieving structured data, numbers, lists, or performing calculations on database records. "
        "Do not use this for general policy questions."
    )
    args_schema: Type[BaseModel] = DatabaseQueryInput
    
    db_engine: Any
    llm: Any 

    def _parse_input(self, tool_input: Union[str, Dict]) -> Dict[str, Any]:
        """Override to ensure JSON string is parsed correctly for multi-argument schema."""
        if isinstance(tool_input, str):
            try:
                parsed_input = json.loads(tool_input)
                if not isinstance(parsed_input, dict):
                     raise ToolException(
                        f"Tool {self.name} received a JSON string that did not decode to a dictionary: {tool_input}"
                    )
                return parsed_input
            except json.JSONDecodeError as e:
                raise ToolException(
                    f"Tool {self.name} received input '{tool_input}' which is not valid JSON "
                    f"for a multi-argument schema. Error: {e}"
                )
        elif isinstance(tool_input, dict):
            return tool_input
        raise ToolException(
            f"Tool {self.name} received tool input of type {type(tool_input)} "
            f"but expects a JSON string or a dict."
        )

    def _run(self, natural_language_query: str, user_role: str, user_region: str, jwt_claims_for_db: str) -> str:
        logger.debug(f"CustomSQLTool executing with NLQ: '{natural_language_query}', role: {user_role}, region: {user_region}")
        
        if not self.db_engine or not self.llm:
            logger.error("CustomSQLTool: Database engine or LLM not available on self.")
            return "Error: Database engine or LLM for SQL tool not properly initialized."

        if user_role not in ROLES_PERMISSIONS:
            logger.warning(f"CustomSQLTool: Role '{user_role}' not found in ROLES_PERMISSIONS.")
            return f"Error: Unauthorized. Role '{user_role}' not configured for database access."

        sql_query_generated = "N/A"
        try:
            relevant_tables = ROLES_PERMISSIONS[user_role].get("allowed_tables", ["supply_chain"])
            schema_str = get_limited_db_schema_string(self.db_engine, relevant_tables=relevant_tables)
            
            if not schema_str or "not found" in schema_str.lower():
                logger.error(f"CustomSQLTool: Failed to get schema for {relevant_tables}. Schema: {schema_str}")
                return "Error: Could not get database schema to construct SQL query."

            # Generate initial SQL from LLM
            sql_query_generated_by_llm = generate_sql_from_text_sync(natural_language_query, schema_str, self.llm)
            logger.info(f"CustomSQLTool initial LLM SQL: {sql_query_generated_by_llm}")
            
            final_sql_to_execute = sql_query_generated_by_llm
            params = {}  # For parameterized queries
            
            # Check if user is Global Operations Manager
            is_gom = (user_role.lower() == "global operations manager")
            
            if not sql_query_generated_by_llm.strip().upper().startswith("SELECT"):
                logger.warning(f"Generated query is not SELECT: '{sql_query_generated_by_llm}'. Blocking.")
                return "Error: Generated query was not SELECT. Only data retrieval is supported."

            # Apply regional filtering for non-GOM users
            if not is_gom and user_region:
                logger.info(f"Applying regional filter for role '{user_role}' and region '{user_region}'")
                
                # Define the regional filter clause using parameterized query
                region_filter_clause = "LOWER(order_country) = LOWER(:user_region_param)"
                params['user_region_param'] = user_region
                
                # Process the SQL to inject WHERE clause
                processed_query = final_sql_to_execute.rstrip().removesuffix(';')
                
                if " where " in processed_query.lower():
                    # WHERE clause already exists, add AND condition
                    final_sql_to_execute = f"{processed_query} AND ({region_filter_clause})"
                else:
                    # No WHERE clause exists, need to add one
                    # Find the position to insert WHERE (before GROUP BY, ORDER BY, LIMIT, etc.)
                    end_of_select_from = len(processed_query)
                    clause_keywords = [" group by", " order by", " limit", " having", " union", " intersect", " except"]
                    
                    for clause_keyword in clause_keywords:
                        idx = processed_query.lower().find(clause_keyword)
                        if idx != -1:
                            end_of_select_from = min(end_of_select_from, idx)
                    
                    if end_of_select_from < len(processed_query):
                        # Found a subsequent clause, insert WHERE before it
                        final_sql_to_execute = f"{processed_query[:end_of_select_from]} WHERE ({region_filter_clause}) {processed_query[end_of_select_from:]}"
                    else:
                        # No other major clauses found after FROM, append WHERE at the end
                        final_sql_to_execute = f"{processed_query} WHERE ({region_filter_clause})"
                
                # Add semicolon back if needed
                final_sql_to_execute += ";"
                logger.info(f"SQL after app-level regional filter: {final_sql_to_execute} with params: {params}")
            else:
                logger.info(f"GOM or no region specified, executing LLM SQL directly: {final_sql_to_execute}")

            # Store the final SQL for error reporting
            sql_query_generated = final_sql_to_execute

            with self.db_engine.connect() as connection:
                try:
                    # Set up database context (keeping original RLS setup for compatibility)
                    connection.execute(text("SET LOCAL ROLE authenticated;"))
                    escaped_jwt_claims = jwt_claims_for_db.replace("'", "''")
                    
                    connection.execute(text(f"SELECT set_config('request.jwt.claims', '{escaped_jwt_claims}', true);"))
                    connection.execute(text("SET LOCAL ROLE authenticated;"))
                    
                    logger.info(f"Set JWT claims, then RLS context set for user_role: {user_role}, region: {user_region}. Claims content: {escaped_jwt_claims[:100]}...")
                except Exception as e_rls:
                    logger.error(f"CRITICAL: Failed to set RLS context: {e_rls}", exc_info=True)
                    return f"Error: Security context for DB query failed: {e_rls}"

                # Execute query with parameters if any were added
                if params:
                    result_proxy = connection.execute(text(final_sql_to_execute), params)
                else:
                    result_proxy = connection.execute(text(final_sql_to_execute))
                
                if result_proxy.returns_rows:
                    results = result_proxy.fetchall()
                    if not results:
                        return "Query executed, but no data found matching your question and permissions."

                    column_names = list(result_proxy.keys())
                    answer_data = [dict(zip(column_names, map(str, row))) for row in results]
                    
                    num_rows = len(answer_data)
                    display_limit = 5 
                    displayed_data = answer_data[:display_limit]
                    
                    summary = f"Query found {num_rows} record(s). "
                    summary += f"Showing first {display_limit if num_rows > display_limit else num_rows}: "
                    
                    return f"Database query result: {summary}{json.dumps(displayed_data, indent=2)}"
                else:
                    # DML statements
                    return f"Database modification query executed. Rows affected: {result_proxy.rowcount}"

        except ValueError as ve: 
            logger.error(f"ValueError in CustomSQLTool: {ve}. NLQ: '{natural_language_query}', SQL: '{sql_query_generated}'")
            return f"Error processing database query: {ve}."
        except Exception as e: 
            msg = str(e).lower()
            logger.error(f"Error in CustomSQLTool: {e}. NLQ: '{natural_language_query}', SQL: '{sql_query_generated}'", exc_info=True)
            if "permission denied" in msg or "policy" in msg:
                return f"Error: Access denied for this database operation or data. ({e})"
            if "syntax error" in msg or "does not exist" in msg:
                 return f"Error: Generated SQL had an issue. Rephrase or contact support. (SQL Error: {e})"
            return f"Error executing database query: {e}"

    async def _arun(self, natural_language_query: str, user_role: str, user_region: str, jwt_claims_for_db: str) -> str:
        logger.warning("CustomSQLTool._arun called, using synchronous _run fallback.")
        return self._run(natural_language_query, user_role, user_region, jwt_claims_for_db)