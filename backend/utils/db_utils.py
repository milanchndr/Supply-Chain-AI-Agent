# backend/utils/db_utils.py
from sqlalchemy import create_engine, inspect as sqlalchemy_inspect
from sqlalchemy.engine import Engine

# If running this file directly for testing, adjust path
import sys
import os
if __name__ == '__main__': # Allow running this file standalone for testing schema utility
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

from backend.logger_config import logger
from backend.config import DATABASE_URL # Using the full URL from config

def get_db_schema_string(engine: Engine, table_name: str) -> str:
    """
    Retrieves the schema for a specific table and formats it as a string.
    """
    inspector = sqlalchemy_inspect(engine)
    schema_parts = []
    
    if not inspector.has_table(table_name):
        logger.warning(f"Table '{table_name}' not found in the database.")
        return f"-- Table '{table_name}' not found."

    schema_parts.append(f"Table: {table_name}")
    schema_parts.append("Columns:")
    try:
        columns = inspector.get_columns(table_name)
        for column in columns:
            col_name = column['name']
            col_type = str(column['type'])
            # Ensure column names with spaces or special characters are quoted for LLM clarity
            schema_parts.append(f'  "{col_name}": {col_type}')
    except Exception as e:
        logger.error(f"Error inspecting columns for table {table_name}: {e}")
        return f"-- Error retrieving schema for table '{table_name}'."
        
    return "\n".join(schema_parts)

def get_limited_db_schema_string(engine: Engine, relevant_tables: list = None) -> str:
    """
    Retrieves schema for a list of relevant tables or a few sample tables.
    """
    inspector = sqlalchemy_inspect(engine)
    all_tables = inspector.get_table_names()
    
    if relevant_tables is None:
        # If no specific tables, pick a few or common ones (e.g. supply_chain)
        relevant_tables = [t for t in ['supply_chain'] if t in all_tables]
        if not relevant_tables and all_tables: # Fallback to first few tables
            relevant_tables = all_tables[:2] 
            
    full_schema_string = []
    for table_name in relevant_tables:
        if table_name in all_tables:
            full_schema_string.append(get_db_schema_string(engine, table_name))
        else:
            logger.warning(f"Requested table '{table_name}' for schema not found.")
            
    return "\n\n".join(full_schema_string)


if __name__ == '__main__':
    # Example usage (for testing this utility directly)
    # Ensure your .env file is in the `backend` directory or accessible
    # and your PostgreSQL server is running with the hackathon_db.
    try:
        test_engine = create_engine(DATABASE_URL)
        logger.info(f"Connected to {DATABASE_URL} for schema test.")
        
        # Test with 'supply_chain' table
        schema_str_single = get_db_schema_string(test_engine, "supply_chain")
        logger.info(f"\nSchema for 'supply_chain':\n{schema_str_single}")

        # Test with relevant tables
        schema_str_multi = get_limited_db_schema_string(test_engine, relevant_tables=["supply_chain"]) # Add other tables if exist
        logger.info(f"\nSchema for relevant tables:\n{schema_str_multi}")

    except Exception as e:
        logger.error(f"Error during schema utility test: {e}")