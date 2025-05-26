# backend/load_db.py
import pandas as pd
from sqlalchemy import create_engine
import os
import sys

# Add backend directory to sys.path to find config and logger
sys.path.append(os.path.dirname(__file__)) # Assumes load_db.py is in backend/
# If load_db.py is outside backend/, adjust path to find backend.config, backend.logger_config

from config import DATABASE_URL, CSV_PATH_FOR_DB_LOAD
from logger_config import logger


def load_data_to_db():
    logger.info(f"Attempting to load data from CSV: {CSV_PATH_FOR_DB_LOAD}")
    logger.info(f"Target database: {DATABASE_URL.split('@')[-1]}") # Avoid logging password

    if not CSV_PATH_FOR_DB_LOAD or not os.path.exists(CSV_PATH_FOR_DB_LOAD):
        logger.error(f"CSV file not found at path: {CSV_PATH_FOR_DB_LOAD}. Please check CSV_PATH in .env or config.py.")
        return

    try:
        engine = create_engine(DATABASE_URL)
        logger.info("Database engine created.")
    except Exception as e:
        logger.error(f"Error creating database engine: {e}")
        return

    try:
        # Try common encodings if default (utf-8) fails
        encodings_to_try = ['latin1', 'iso-8859-1', 'cp1252', 'utf-8']
        df = None
        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(CSV_PATH_FOR_DB_LOAD, encoding=encoding)
                logger.info(f"CSV file loaded successfully using encoding: {encoding}")
                break
            except UnicodeDecodeError:
                logger.warning(f"Failed to load CSV with encoding {encoding}. Trying next...")
            except FileNotFoundError:
                logger.error(f"File not found: {CSV_PATH_FOR_DB_LOAD}") # Should be caught by os.path.exists earlier
                return
        
        if df is None:
            logger.error(f"Could not load CSV with any of the attempted encodings: {encodings_to_try}")
            return

        # Basic data cleaning: Sanitize column names for SQL compatibility
        # Pandas to_sql handles most, but good practice to make them more standard
        original_columns = df.columns.tolist()
        df.columns = [col.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('-', '_').lower() for col in df.columns]
        renamed_columns = dict(zip(original_columns, df.columns))
        if original_columns != df.columns.tolist():
             logger.info(f"Column names sanitized. Mapping: {renamed_columns}")


        # Load data into a table named 'supply_chain'
        # Consider chunksize for very large CSVs
        df.to_sql('supply_chain', engine, if_exists='replace', index=False, chunksize=10000)
        logger.info("Data loaded successfully into 'supply_chain' table!")

    except Exception as e:
        logger.error(f"Error during CSV loading or database operation: {e}", exc_info=True)


if __name__ == "__main__":
    load_data_to_db()