from flask import Flask, request, jsonify
import os
import time 
import requests
from dotenv import load_dotenv
import logging

# === Setup Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# === CONFIGURATION ===
Key = os.getenv("OPENAI_API_KEY")
if not Key:
    logger.warning("❌ OPENAI_API_KEY not found in environment!")

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-3.5-turbo-16k"

HEADERS = {
    "Authorization": f"Bearer {Key}",
    "Content-Type": "application/json"
}

@app.route("/check-key")
def check_key():
    Key = os.getenv("OPENAI_API_KEY")
    if Key:
        logger.info("✅ OPENAI_API_KEY is loaded successfully.")
        return f"✅ Key is loaded. Length: {len(Key)}"
    else:
        logger.error("❌ OPENAI_API_KEY is not set!")
        return "❌ OPENAI_API_KEY is not set!", 500

# === Cypher Generation Function ===
def your_groq_llm_conversion_function(text: str) -> str:
    """
    Calls OpenAI LLM to convert a natural language prompt into a Cypher query.
    """
    logger.info(f"🔎 Received user prompt: {text}")

    system_prompt = """
You are an expert Cypher assistant for querying a Neo4j graph.

The graph contains:
- Nodes with a unique 'id' (e.g., Google, Microsoft, France)
- Edges of type CONNECTED_TO, each with a numeric property 'weight'

Your job is to translate natural language questions into valid Cypher queries.
Do NOT explain. Only return a raw Cypher query as output. No markdown.

You must handle queries like:
- Strongest or weakest connection of an entity
- Top N connections of a node
- All connections of a node
- Relationship between two entities
- General exploration of a node (e.g., “Tell me about France”)

Examples:

Q: Who is most connected to OpenAI?
A: MATCH (n {id: 'OpenAI'})-[r:CONNECTED_TO]-(m) RETURN m.id, r.weight ORDER BY r.weight DESC LIMIT 1

Q: What’s the connection between Google and Microsoft?
A: MATCH (a {id: 'Google'})-[r:CONNECTED_TO]-(b {id: 'Microsoft'}) RETURN r.weight

Q: Tell me about France in the graph.
A: MATCH (n {id: 'France'})-[r:CONNECTED_TO]-(m) RETURN m.id, r.weight
"""

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": text}
        ],
        "temperature": 0.3
    }

    try:
        time.sleep(5)  # Rate limit protection
        logger.info("📡 Sending request to OpenAI API...")
        response = requests.post(OPENAI_API_URL, headers=HEADERS, json=payload, timeout=20)
        logger.info(f"🔁 Response status: {response.status_code}")

        response.raise_for_status()

        result = response.json()
        cypher = result["choices"][0]["message"]["content"].strip()

        logger.info(f"✅ Generated Cypher query:\n{cypher}")
        return cypher

    except Exception as e:
        logger.error(f"[ERROR] OPENAI API failed: {e}")
        return ""


# === REST Endpoint ===
@app.route("/convert", methods=["POST"])
def convert_text():
    data = request.get_json(force=True)
    user_text = data.get("text", "")
    logger.info(f"📨 Incoming /convert request: {user_text}")
    
    cypher_query = your_groq_llm_conversion_function(user_text)
    logger.info(f"🧠 Final Cypher output: {cypher_query}")

    if not cypher_query:
        logger.error("❌ No Cypher query generated.")
        return jsonify({"error": "Failed to generate Cypher query."}), 500

    return jsonify({"cypher": cypher_query})


if __name__ == "__main__":
    logger.info("🚀 Flask LLM API is starting on port 5004...")
    app.run(host="0.0.0.0", port=5004)
