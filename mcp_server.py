"""Part 2: the same tool on the sheet's side, as an MCP server.
Run: python mcp_server.py
"""
import csv, io, os, socket
from typing import Annotated
import requests
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Instrument Register")

LOCAL_CSV_PATH = os.path.join(os.path.dirname(__file__), "instruments.csv")

# Step 1. Move function here and put @mcp.tool on the line above def
# Step 2. Write the card into the function:
#   - Tool Name: function name (search_instruments)
#   - "Use it when": the docstring ("""...""")
#   - "It needs": the type hint: query: Annotated[str, "..."]
@mcp.tool
def search_instruments(
    query: Annotated[str, "The instrument name, model, or category to look up (e.g. 'Yamaha', 'Guitar', 'Keyboard', or 'all')"]
) -> list | dict:
    """Look up an instrument in the purchase & profit register by model name or category to find its cost, selling price, quantity, and profit."""
    items = []
    with open(LOCAL_CSV_PATH, mode="r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = (row.get("Instrument Name / Model") or "").strip()
            if not name or name.upper() == "TOTAL":
                continue
            if (not query or query.lower() == "all"
                    or query.lower() in name.lower()
                    or query.lower() in (row.get("Instrument Type") or "").lower()):
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


# Any app can now reach it at http://localhost:8000/mcp
if __name__ == "__main__":
    if socket.socket().connect_ex(("127.0.0.1", 8000)) == 0:
        raise SystemExit("Port 8000 is already in use, probably by a server you started earlier. "
                         "Stop it with Ctrl+C in its terminal, or run: kill $(lsof -t -i:8000)")
    mcp.run(transport="http", port=8000)
