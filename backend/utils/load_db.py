import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
import bcrypt
from time import sleep

# Add parent directory (backend) to sys.path to find config, logger_config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.config import DATABASE_URL, CSV_PATH_FOR_DB_LOAD
from backend.logger_config import logger

def load_data_to_db():
    """Load data from CSV into the Supabase PostgreSQL database and set up the users table."""
    logger.info("Starting database loading process...")

    # Retry logic for connecting to Supabase
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Create database engine for Supabase with connection pooling options
            engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
            with engine.connect() as connection:
                logger.info(f"Connected to Supabase database: {DATABASE_URL.split('@')[-1]}")
            break
        except Exception as e:
            logger.error(f"Failed to connect to Supabase database (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                logger.error("Max retries reached. Exiting.")
                return
            sleep(2)  # Wait before retrying

    try:
        # Construct the absolute path to the CSV file
        current_dir = os.path.dirname(__file__)  # backend directory
        csv_file_path = os.path.join(current_dir, '..', 'documents', 'DataCoSupplyChainDataset.csv')
        csv_file_path = os.path.abspath(csv_file_path)

        logger.info(f"Attempting to load CSV data from: {csv_file_path} with encoding: latin1")
        df = pd.read_csv(csv_file_path, encoding='latin1')

        # Clean column names (SQLAlchemy doesn't like spaces or special characters in column names)
        df.columns = [c.replace(' ', '_').replace('(', '').replace(')', '').lower() for c in df.columns]
        logger.info(f"Cleaned column names: {df.columns.tolist()}")

        # Rename the date column to 'order_date' if it exists under a different name
        possible_date_columns = ['order_date_dateorders', 'orderdate', 'order_date', 'date']
        date_column = None
        for col in possible_date_columns:
            if col in df.columns:
                date_column = col
                break

        if date_column and date_column != 'order_date':
            logger.info(f"Renaming column '{date_column}' to 'order_date'")
            df = df.rename(columns={date_column: 'order_date'})
        elif not date_column:
            logger.error("No order date column found in CSV. Expected one of: " + ", ".join(possible_date_columns))
            return

        # Convert date columns to datetime before loading
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
        df['shipping_date_dateorders'] = pd.to_datetime(df['shipping_date_dateorders'], errors='coerce')

        # Handle any data type issues
        numeric_columns = ['benefit_per_order', 'sales_per_customer', 'customer_zipcode', 'latitude', 'longitude', 
                          'order_item_discount', 'order_item_discount_rate', 'order_item_product_price', 
                          'order_item_profit_ratio', 'sales', 'order_item_total', 'order_profit_per_order', 
                          'order_zipcode', 'product_price']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"DataFrame columns: {list(df.columns)}")

        # Create and load data with proper transaction handling
        with engine.connect() as connection:
            # Start a transaction
            trans = connection.begin()
            try:
                # Set longer timeout for this session
                connection.execute(text("SET statement_timeout = '1200s';"))
                logger.info("Set statement_timeout to 1200 seconds (20 minutes) for this session.")

                # Drop table if exists to avoid conflicts
                connection.execute(text("DROP TABLE IF EXISTS supply_chain CASCADE"))
                logger.info("Dropped supply_chain table if it existed.")

                # Create the table manually with proper schema
                create_table_query = """
                CREATE TABLE supply_chain (
                    type VARCHAR(20),
                    days_for_shipping_real INTEGER,
                    days_for_shipment_scheduled INTEGER,
                    benefit_per_order FLOAT,
                    sales_per_customer FLOAT,
                    delivery_status VARCHAR(50),
                    late_delivery_risk INTEGER,
                    category_id INTEGER,
                    category_name VARCHAR(100),
                    customer_city VARCHAR(100),
                    customer_country VARCHAR(100),
                    customer_email VARCHAR(100),
                    customer_fname VARCHAR(50),
                    customer_id INTEGER,
                    customer_lname VARCHAR(50),
                    customer_password VARCHAR(50),
                    customer_segment VARCHAR(50),
                    customer_state VARCHAR(50),
                    customer_street VARCHAR(200),
                    customer_zipcode FLOAT,
                    department_id INTEGER,
                    department_name VARCHAR(100),
                    latitude FLOAT,
                    longitude FLOAT,
                    market VARCHAR(50),
                    order_city VARCHAR(100),
                    order_country VARCHAR(100),
                    order_customer_id INTEGER,
                    order_date TIMESTAMP,
                    order_id INTEGER,
                    order_item_cardprod_id INTEGER,
                    order_item_discount FLOAT,
                    order_item_discount_rate FLOAT,
                    order_item_id INTEGER,
                    order_item_product_price FLOAT,
                    order_item_profit_ratio FLOAT,
                    order_item_quantity INTEGER,
                    sales FLOAT,
                    order_item_total FLOAT,
                    order_profit_per_order FLOAT,
                    order_region VARCHAR(100),
                    order_state VARCHAR(100),
                    order_status VARCHAR(50),
                    order_zipcode FLOAT,
                    product_card_id INTEGER,
                    product_category_id INTEGER,
                    product_description TEXT,
                    product_image VARCHAR(200),
                    product_name VARCHAR(200),
                    product_price FLOAT,
                    product_status INTEGER,
                    shipping_date_dateorders TIMESTAMP,
                    shipping_mode VARCHAR(50)
                );
                """
                
                connection.execute(text(create_table_query))
                logger.info("Created supply_chain table successfully.")

                # Load data in smaller chunks to avoid timeout
                chunk_size = 1000
                total_rows = len(df)
                logger.info(f"Loading {total_rows} rows in chunks of {chunk_size}")
                
                for i in range(0, total_rows, chunk_size):
                    chunk = df.iloc[i:i+chunk_size]
                    chunk.to_sql('supply_chain', connection, if_exists='append', index=False, method='multi')
                    logger.info(f"Loaded chunk {i//chunk_size + 1}/{(total_rows-1)//chunk_size + 1} ({len(chunk)} rows)")

                # Create indexes for performance
                logger.info("Creating initial indexes...")
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_order_date ON supply_chain (order_date)"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_sales ON supply_chain (sales)"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_customer_id ON supply_chain (customer_id)"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_order_id ON supply_chain (order_id)"))
                # Index for RLS (if you keep it)
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_lower_order_country ON supply_chain (LOWER(order_country))"))
                logger.info("Initial indexes created successfully.")

                logger.info("Creating additional performance indexes...")
                # Financial & Key Metrics
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_sales_per_customer ON supply_chain (sales_per_customer)"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_benefit_per_order ON supply_chain (benefit_per_order)"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_order_profit_per_order ON supply_chain (order_profit_per_order)"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_product_price ON supply_chain (product_price)"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_order_item_pprice ON supply_chain (order_item_product_price)"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_order_item_qty ON supply_chain (order_item_quantity)"))

                # Categorical / IDs
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_category_id ON supply_chain (category_id)"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_department_id ON supply_chain (department_id)"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_market ON supply_chain (market)")) # Text column
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_order_region ON supply_chain (order_region)")) # Text column
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_order_status ON supply_chain (order_status)")) # Text column
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_shipping_mode ON supply_chain (shipping_mode)")) # Text column
                connection.execute(text("CREATE INDEX IF NOT EXISTS idx_supply_chain_product_card_id ON supply_chain (product_card_id)"))

                # Commit the transaction
                trans.commit()
                logger.info("Successfully loaded all data into supply_chain table.")

                # Reset statement timeout to default
                connection.execute(text("SET statement_timeout = '120s';"))
                logger.info("Reset statement_timeout to default (120 seconds).")

            except Exception as e:
                trans.rollback()
                logger.error(f"Error during data loading, rolling back: {e}")
                raise

    except FileNotFoundError as e:
        logger.error(f"Failed to load supply chain data: CSV file not found at '{e.filename}'. Please check the file path and ensure it exists.", exc_info=True)
        return
    except Exception as e:
        logger.error(f"Failed to load supply chain data: {e}", exc_info=True)
        return

    # Step 3: Create the users table
    try:
        with engine.connect() as connection:
            # Drop table if it exists (for idempotency)
            connection.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            logger.info("Dropped users table if it existed.")

            # Create users table
            create_users_table_query = """
            CREATE TABLE users (
                user_id VARCHAR(50) PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                region VARCHAR(50) NOT NULL
            );
            """
            connection.execute(text(create_users_table_query))
            connection.commit()
            logger.info("Created users table successfully.")

    except Exception as e:
        logger.error(f"Failed to create users table: {e}", exc_info=True)
        return

    # Step 4: Insert a sample user with a hashed password
    try:
        # Generate a hashed password for the sample user
        password = "mypassword"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        logger.info(f"Generated hashed password for sample user")

        with engine.connect() as connection:
            insert_user_query = """
            INSERT INTO users (user_id, username, password_hash, role, region) VALUES
            ('user123', 'planner_india', :password_hash, 'Planning', 'India');
            """
            connection.execute(
                text(insert_user_query),
                {"password_hash": hashed_password}
            )
            connection.commit()
            logger.info("Inserted sample user 'planner_india' into users table.")

    except Exception as e:
        logger.error(f"Failed to insert sample user: {e}", exc_info=True)
        return

    # Step 5: Create the audit_logs table
    try:
        with engine.connect() as connection:
            # Drop table if it exists (for idempotency)
            connection.execute(text("DROP TABLE IF EXISTS audit_logs CASCADE"))
            logger.info("Dropped audit_logs table if it existed.")

            # Create audit_logs table
            create_audit_logs_query = """
            CREATE TABLE audit_logs (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50),
                role VARCHAR(50),
                region VARCHAR(50),
                query TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN,
                error_message TEXT
            );
            """
            connection.execute(text(create_audit_logs_query))
            connection.commit()
            logger.info("Created audit_logs table successfully.")

    except Exception as e:
        logger.error(f"Failed to create audit_logs table: {e}", exc_info=True)
        return

    logger.info("Database loading process completed successfully.")

if __name__ == "__main__":
    load_data_to_db()