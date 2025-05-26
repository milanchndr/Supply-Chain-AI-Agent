# backend/app.py
# NO sys.path manipulation at the top.

from flask import Flask, request, jsonify
from sqlalchemy import create_engine

# Use relative imports for modules within the 'backend' package when app.py is part of it.
from .config import DATABASE_URL  # Assumes config.py is in backend/
from .utils.langchain_setup import setup_qa_chain
from .logger_config import logger # Assumes logger_config.py is in backend/
from .utils.agent_handler import create_supply_chain_agent_executor # Relative path

app = Flask(__name__)

# --- Global Variables ---
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
        logger.info(f"Setting up database engine (for CustomSQLTool): {DATABASE_URL.split('@')[-1]}")
        db_engine = create_engine(DATABASE_URL)
        with db_engine.connect() as connection:
            logger.info("Database connection successful.")
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

# ... (rest of your Flask routes: /, /health, /query) ...
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


@app.route('/query', methods=['POST'])
def handle_agent_query(): # Main query endpoint now uses the agent
    if not agent_executor:
        logger.error("Agent executor not initialized. Cannot process query.")
        return jsonify({"error": "Agent services not fully initialized. Please check logs."}), 503

    data = request.json
    question = data.get("question", "").strip()

    if not question:
        logger.warning("Query request with no question provided.")
        return jsonify({"error": "No question provided"}), 400

    logger.info(f"Received agent query: {question}")

    try:
        response = agent_executor.invoke({"input": question})
        final_answer = response.get("output", "Agent could not determine a final answer.")
        return jsonify({"answer": final_answer, "type": "agent_multi_tool"})
        
    except Exception as e:
        logger.error(f"Error processing agent query '{question}': {str(e)}", exc_info=True)
        error_message = f"Error processing agent query: {str(e)}"
        if "Could not parse LLM output:" in str(e) and agent_executor.handle_parsing_errors:
             error_message += " This might be due to the LLM not following the expected ReAct format. Check agent prompt and LLM compatibility."
        return jsonify({"error": error_message}), 500

# This __main__ block is primarily for when you run `python backend/app.py` directly
# from the project root (D:\Codes\Hackathon).
# If using `python -m backend.app`, this block isn't strictly necessary for app.run(),
# as the `app` object is found by the WSGI server or Flask CLI.
if __name__ == "__main__":
    logger.info("Starting Flask development server for Multi-Tool Agent...")
    # The debug=True reloader can sometimes cause issues with global state initialization
    # if initialize_app() is not idempotent. Setting use_reloader=False for stability here.
    # When not in debug or with a proper WSGI server, this isn't an issue.
    import os
    # Only run app.run if this script is executed directly, not when imported by reloader
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
         # This condition is to try and prevent initialize_app() from running twice in debug mode
         # but it's tricky. The create_..._executor being a function helps make it more idempotent.
         pass # initialize_app() is already called at module level
    
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=True) # Keep reloader for dev