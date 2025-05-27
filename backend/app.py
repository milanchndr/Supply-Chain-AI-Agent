from flask import Flask, request, jsonify,json
from sqlalchemy import create_engine, text
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token,get_jwt
import os
import bcrypt


from .config import DATABASE_URL, ROLES_PERMISSIONS, JWT_SECRET_KEY
from .utils.langchain_setup import setup_qa_chain
from .logger_config import logger
from .utils.agent_handler import create_supply_chain_agent_executor

app = Flask(__name__)

# Setup JWT
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)

qa_chain = None
db_engine = None
bedrock_llm_instance = None
agent_executor = None

# --- Initialization ---
def initialize_app():
    global qa_chain, db_engine, bedrock_llm_instance, agent_executor
    logger.info("Initializing Flask application...")
    try:
        logger.info("Setting up QA chain (for DocumentQATool)...")
        qa_chain = setup_qa_chain()
        bedrock_llm_instance = qa_chain.combine_documents_chain.llm_chain.llm
        logger.info("QA chain and Bedrock LLM instance for agent tools set up.")
    except Exception as e:
        logger.error(f"Critical Error setting up QA chain/LLM: {e}", exc_info=True)

    try:
        logger.info(f"Setting up database engine: {DATABASE_URL.split('@')[-1]}")
        db_engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
        with db_engine.connect() as connection:
            logger.info("Database connection to Supabase successful.")
    except Exception as e:
        logger.error(f"Critical Error setting up database engine: {e}", exc_info=True)

    if bedrock_llm_instance and qa_chain and db_engine:
        try:
            agent_executor = create_supply_chain_agent_executor(
                llm_instance=bedrock_llm_instance,
                qa_chain_instance=qa_chain,
                db_engine_instance=db_engine
            )
            logger.info("Agent Executor initialized successfully.")
        except Exception as e:
            logger.error(f"Critical Error creating Agent Executor: {e}", exc_info=True)
    else:
        logger.error("Cannot create Agent Executor due to missing dependencies.")

initialize_app()

# --- Audit Logging Function ---
def log_audit(user_id, role, region, query, success, error_message=None):
    try:
        with db_engine.connect() as connection:
            connection.execute(
                text("""
                    INSERT INTO audit_logs (user_id, role, region, query, success, error_message, timestamp)
                    VALUES (:user_id, :role, :region, :query, :success, :error_message, CURRENT_TIMESTAMP)
                """),
                {
                    "user_id": user_id,
                    "role": role,
                    "region": region,
                    "query": query,
                    "success": success,
                    "error_message": error_message
                }
            )
            connection.commit()
    except Exception as e:
        logger.error(f"Failed to log audit: {e}")



# --- Routes ---
@app.route('/')
def home():
    return "AI Supply Chain Agent Backend (Multi-Tool Agent) is running."

@app.route('/health')
def health_check():
    status = {
        "agent_executor_initialized": agent_executor is not None,
        "qa_chain_for_tool_initialized": qa_chain is not None,
        "db_engine_for_tool_initialized": db_engine is not None,
        "llm_for_agent_initialized": bedrock_llm_instance is not None,
    }
    if agent_executor is None:
        status["status"] = "AGENT_NOT_INITIALIZED"
        logger.warning(f"Health check: Agent not initialized. Status: {status}")
        return jsonify(status), 503
    status["status"] = "OK"
    return jsonify(status), 200
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    try:
        with db_engine.connect() as connection: # db_engine is your main Supabase connection
            result = connection.execute(
                text("SELECT user_id, username, password_hash, role, region FROM users WHERE username = :username"),
                {"username": username}
            ).fetchone()

            if not result:
                return jsonify({"error": "Invalid username or password"}), 401

            user_id_from_db, _, password_hash, role_from_db, region_from_db = result

            if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                return jsonify({"error": "Invalid username or password"}), 401


            additional_claims = {
                "role": "authenticated", # Standard Supabase role for authenticated users
                "app_metadata": {
                    "role": role_from_db,       # Your application-specific role
                    "region": region_from_db    # Your application-specific region
                }
            }


            access_token = create_access_token(
                identity=str(user_id_from_db), # This becomes the 'sub' claim
                additional_claims=additional_claims
            )
            logger.info(f"User {username} (user_id: {user_id_from_db}) logged in. JWT created with app_metadata.")
            return jsonify({"access_token": access_token}), 200

    except Exception as e:
        logger.error(f"Error during login for username {username}: {e}", exc_info=True)
        return jsonify({"error": "Login failed due to a server error"}), 500

@app.route('/query', methods=['POST'])
@jwt_required()
def handle_agent_query():
    if not agent_executor:
        logger.error("Agent executor not initialized. Cannot process query.")
        return jsonify({"error": "Agent services not fully initialized. Please check logs."}), 503

    user_identity_sub = get_jwt_identity() # This is the 'sub' claim (user_id_from_db)
    
    jwt_payload = get_jwt() # Get the full JWT payload
    

    app_role = jwt_payload.get("app_metadata", {}).get("role")
    app_region = jwt_payload.get("app_metadata", {}).get("region")

    if not app_role or app_role not in ROLES_PERMISSIONS:
        error_msg = f"Invalid application role: {app_role} or role not configured in backend."
        # Use user_identity_sub for audit logging user ID
        log_audit(user_identity_sub, app_role, app_region, "N/A", False, error_msg)
        return jsonify({"error": error_msg}), 403

    data = request.json
    question = data.get("question", "").strip()

    if not question:
        error_msg = "No question provided"
        log_audit(user_identity_sub, app_role, app_region, question, False, error_msg)
        return jsonify({"error": error_msg}), 400

    logger.info(f"Received agent query from user {user_identity_sub} (app_role: {app_role}, app_region: {app_region}): {question}")

    try:
        response = agent_executor.invoke({
            "input": question,
            "user_role": app_role, # Pass the application role
            "user_region": app_region, # Pass the application region
            "jwt_claims_for_db": json.dumps(jwt_payload) # Pass all claims for DB session
        })
        final_answer = response.get("output", "Agent could not determine a final answer.")
        log_audit(user_identity_sub, app_role, app_region, question, True)
        return jsonify({"answer": final_answer, "type": "agent_multi_tool"})
    
    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        if "Unauthorized access" in str(e) or "permission denied" in str(e).lower(): # Catch DB permission errors
            error_msg = f"You are not authorized to perform this action or access this data. {str(e)}"
            status_code = 403
        else:
            status_code = 500
        log_audit(user_identity_sub, app_role, app_region, question, False, error_msg)
        logger.error(f"Error processing agent query '{question}' for user {user_identity_sub}: {str(e)}", exc_info=True)
        return jsonify({"error": error_msg}), status_code


if __name__ == "__main__":
    logger.info("Starting Flask development server for Multi-Tool Agent...")
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        pass
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=True)