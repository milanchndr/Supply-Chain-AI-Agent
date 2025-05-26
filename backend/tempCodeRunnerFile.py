# backend/app.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from flask import Flask, request, jsonify
from utils.langchain_setup import setup_qa_chain
from sqlalchemy import create_engine, text
from config import BEDROCK_API_KEY

app = Flask(__name__)

# Initialize QA chain for document queries
try:
    qa_chain = setup_qa_chain()
except Exception as e:
    print(f"Error setting up QA chain: {e}")
    qa_chain = None

# Initialize database connection
try:
    engine = create_engine('postgresql://postgres:123@localhost:5432/hackathon_db')
except Exception as e:
    print(f"Error setting up database: {e}")
    engine = None

def is_document_query(question):
    """Simple heuristic to classify query type."""
    doc_keywords = ["policy", "guidelines", "procedure", "write-off", "ethical"]
    return any(keyword in question.lower() for keyword in doc_keywords)

@app.route('/')
def home():
    return "AI Supply Chain Agent Backend"

@app.route('/query', methods=['POST'])
def query():
    """Handle document or database queries."""
    if not qa_chain or not engine:
        return jsonify({"error": "Backend not initialized"}), 500

    data = request.json
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        if is_document_query(question):
            # Document-based query
            result = qa_chain.invoke({"query": question})
            answer = result["result"]
            sources = [{"content": doc.page_content, "source": doc.metadata["source"]} for doc in result["source_documents"]]
            return jsonify({"answer": answer, "sources": sources, "type": "document"})
        else:
            # Database query (adjusted for DataCo dataset)
            with engine.connect() as connection:
                query = text('SELECT SUM("Order Item Quantity") as total_inventory FROM supply_chain WHERE "Region" = :region')
                result = connection.execute(query, {"region": "Southwest"}).fetchone()
                answer = f"Total inventory in Southwest region: {result[0] if result else 0} units"
                return jsonify({"answer": answer, "sources": [], "type": "database"})
    except Exception as e:
        return jsonify({"error": f"Error processing query: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)