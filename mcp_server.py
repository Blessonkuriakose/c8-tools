import csv
import io
import os
import socket
from typing import Annotated
from dotenv import load_dotenv
from fastmcp import FastMCP
import requests

load_dotenv()

COURSE_SHEET_ENDPOINT = "https://docs.google.com/spreadsheets/d/1Kg6T-dJWaYx_JCPiRk3u0nBuAQcsCVRDPj1NFKP4WzM/gviz/tq?tqx=out:csv&headers=0&gid=368290478"

mcp = FastMCP("Cohort8 Curriculum Service")


def is_port_open(target_port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex((host, target_port)) == 0


@mcp.tool
def get_lecture(
    number: Annotated[int, "The 100x Cohort lecture number between 1 and 19."]
) -> dict:
    """Fetch details for 100x Cohort sessions, including date, topic, format, and tools covered."""
    resp = requests.get(COURSE_SHEET_ENDPOINT, timeout=15)
    resp.raise_for_status()

    prefix = f"{number}. "
    for date_val, title_val, type_val, tools_val, *_ in csv.reader(io.StringIO(resp.text)):
        if title_val.strip().startswith(prefix):
            return {
                "date": date_val.strip(),
                "title": title_val.strip(),
                "type": type_val.strip(),
                "tools": tools_val.strip(),
            }

    return {"error": f"Lecture {number} was not found. Valid numbers are 1 through 19."}


if __name__ == "__main__":
    app_port = int(os.getenv("PORT", "8000"))

    if is_port_open(app_port):
        raise SystemExit(
            f"Port {app_port} is currently occupied. Terminate any existing server process before restarting."
        )

    mcp.run(transport="http", host="0.0.0.0", port=app_port)
