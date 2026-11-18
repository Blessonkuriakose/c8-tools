"""Part 1: your first tool call.
Steps 2 to 5: The card, running requests, and the complete loop.
Run:
  python tool_call.py                                  # Asks tool, retrieves data, answers
  python tool_call.py "What is an API?"                # Answers on its own without calling tool
"""
import csv, io, json, os, sys
import requests
from dotenv import load_dotenv

load_dotenv()
if not os.environ.get("GROQ_API_KEY"):
    raise SystemExit("No GROQ_API_KEY found. Make a file called .env next to tool_call.py with one line: GROQ_API_KEY=your key")

# ---------- THE DATA (from instruments.csv) ----------
def search_instruments(query):
    items = []
    with open("instruments.csv", mode="r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = (row.get("Instrument Name / Model") or "").strip()
            if not name or name.upper() == "TOTAL":
                continue
            if query.lower() in name.lower() or query.lower() in (row.get("Instrument Type") or "").lower():
                qty = int(row.get("Quantity") or 0)
                cost = float(row.get("Purchase Cost (INR)") or 0)
                sell = float(row.get("Selling Price (INR)") or 0)
                items.append({
                    "name": name,
                    "type": row.get("Instrument Type"),
                    "purchase_cost": cost,
                    "selling_price": sell,
                    "quantity": qty,
                    "profit": (sell - cost) * qty
                })
    return items or {"error": f"No instrument found matching '{query}'"}

# ---------- THE MODEL (given) ----------
def ask_model(messages, tools=None):
    body = {"model": "openai/gpt-oss-120b", "messages": messages}
    if tools:
        body["tools"] = tools
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers={"Authorization": "Bearer " + os.environ["GROQ_API_KEY"]}, json=body)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]

# ---------- YOUR SERVER ----------
question = " ".join(sys.argv[1:]) or "What is the selling price and profit of the Yamaha F310 Acoustic Guitar?"
messages = [{"role": "user", "content": question}]

# Step 2. The card
card = {"type": "function", "function": {
    "name": "search_instruments",
    "description": "Look up an instrument in the purchase & profit register by model name or category to find its cost, selling price, quantity, and profit",
    "parameters": {"type": "object",
                   "properties": {"query": {"type": "string",
                                             "description": "The instrument name, model, or category to look up"}},
                   "required": ["query"]},
}}

# Send question and card to model
reply = ask_model(messages, [card])

# Step 5: Loop while the model asks for tool calls.
# If the question doesn't need a tool (e.g. "What is an API?"), reply has no tool_calls and the loop is skipped.
while reply.get("tool_calls"):
    messages.append(reply)
    for call in reply["tool_calls"]:
        args = json.loads(call["function"]["arguments"])
        result = search_instruments(**args)
        # Step 4: Hand the result back to messages with role "tool"
        messages.append({
            "role": "tool",
            "tool_call_id": call["id"],
            "content": json.dumps(result)
        })
    reply = ask_model(messages, [card])

# Print final answer
print(reply["content"])
