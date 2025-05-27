import os
from dotenv import load_dotenv

load_dotenv()

BEDROCK_API_KEY = os.getenv("BEDROCK_API_KEY")
BEDROCK_LLM_MODEL_ID = "claude-3.5-sonnet"  
BEDROCK_EMBEDDING_MODEL_ID = "amazon-embedding-v2"
LAMBDA_API_URL = os.getenv("LAMBDA_API_URL")
BEDROCK_LLM_LAMBDA_URL = LAMBDA_API_URL
BEDROCK_EMBEDDING_LAMBDA_URL = LAMBDA_API_URL
SUPABASE_URL = os.getenv("SUPABASE_URL", "postgresql://postgres.bwhbyokbracredavgzgl:milan7004165372@aws-0-ap-south-1.pooler.supabase.com:6543/postgres")
DATABASE_URL = SUPABASE_URL


# Validations
if not BEDROCK_API_KEY:
    raise ValueError("BEDROCK_API_KEY not found. Please set it in .env file.")
if not LAMBDA_API_URL: # Check the unified URL
    raise ValueError("LAMBDA_API_URL not found. Please set it in .env file.")
CSV_PATH_FOR_DB_LOAD = os.getenv("CSV_PATH", "/documents/DataCoSupplyChainDataset.csv")


ROLES_PERMISSIONS = {
    "Planning": {
        "allowed_data": ["inventory", "logistics", "forecasting"],
        "allowed_tables": ["supply_chain"],
        "allowed_columns": [
            "days_for_shipping_real", "days_for_shipment_scheduled", "delivery_status", "late_delivery_risk",
            "order_date", "order_id", "order_status", "shipping_date_dateorders", "shipping_mode",
            "market", "order_city", "order_country", "order_region", "order_state", "latitude", "longitude",
            "order_item_quantity", "product_card_id", "product_name", "category_id", "category_name",
            "department_id", "department_name", "product_status", "order_item_cardprod_id",
            "sales", "order_item_product_price", "product_price",
            "customer_city", "customer_country", "customer_state", "customer_segment", "order_customer_id"
        ],
    },
    "Finance": {
        "allowed_data": ["margin_reports", "cost_breakdowns", "p_and_l"],
        "allowed_tables": ["supply_chain"],
        "allowed_columns": [
            "type", "benefit_per_order", "sales_per_customer", "order_item_discount", "order_item_discount_rate",
            "order_item_product_price", "order_item_profit_ratio", "sales", "order_item_total", "order_profit_per_order",
            "order_date", "order_id", "market", "order_region", "category_name", "product_name", "department_name",
            "order_item_quantity", "customer_segment", "order_customer_id"
        ],
    },
    "Global Operations Manager": {
        "allowed_data": ["all"],
        "allowed_tables": ["supply_chain"],
        "allowed_columns": [ 
            "type", "days_for_shipping_real", "days_for_shipment_scheduled", "benefit_per_order",
            "sales_per_customer", "delivery_status", "late_delivery_risk", "category_id", "category_name",
            "customer_city", "customer_country", "customer_id", "customer_segment", "customer_state", "customer_street", 
            "customer_fname", "customer_lname", 
            "department_id", "department_name", "latitude", "longitude", "market",
            "order_city", "order_country", "order_customer_id", "order_date", "order_id",
            "order_item_cardprod_id", "order_item_discount", "order_item_discount_rate",
            "order_item_id", "order_item_product_price", "order_item_profit_ratio",
            "order_item_quantity", "sales", "order_item_total", "order_profit_per_order",
            "order_region", "order_state", "order_status", "order_zipcode",
            "product_card_id", "product_category_id", "product_description", "product_name",
            "product_price", "product_status", "shipping_date_dateorders", "shipping_mode"

        ],
        "global_access": True
    }
}


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")