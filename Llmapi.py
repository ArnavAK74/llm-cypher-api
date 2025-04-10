from flask import Flask, request, jsonify
import os
import time 
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# === CONFIGURATION ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-3.5-turbo-16k"
print(OPENAI_API_KEY)

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}


# === Cypher Generation Function ===
def your_groq_llm_conversion_function(text: str) -> str:
    """
    Calls Groq LLM to convert a natural language prompt into a Cypher query.
    """
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
    # response = requests.post(OPENAI_API_URL, headers=HEADERS, json=payload)
    # print(response.status_code)
    # print(response.text)

    try:
        time.sleep(5)
        print(f"[GROQ API] Prompt: {text}")
        response = requests.post(OPENAI_API_URL, headers=HEADERS, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        cypher = result["choices"][0]["message"]["content"].strip()
        

        print(f"[GROQ API] Generated Cypher:\n{cypher}")
        return cypher
    except Exception as e:
        print(f"[ERROR] OPENAI API failed: {e}")
        
        return ""  # Better to return empty string than fallback Cypher


# === REST Endpoint ===
@app.route("/convert", methods=["POST"])
def convert_text():
    data = request.get_json(force=True)
    user_text = data.get("text", "")
    cypher_query = your_groq_llm_conversion_function(user_text)
    print("🧠 Generated Cypher:", cypher_query)
    


    if not cypher_query:
        return jsonify({"error": "Failed to generate Cypher query."}), 500

    return jsonify({"cypher": cypher_query})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)
