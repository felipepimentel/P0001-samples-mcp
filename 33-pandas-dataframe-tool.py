import base64
import io

import matplotlib.pyplot as plt
import pandas as pd
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Pandas DataFrame Tool Example")


@mcp.tool()
def csv_stats(csv_content: str) -> str:
    """Return basic statistics for a CSV (as string)"""
    df = pd.read_csv(io.StringIO(csv_content))
    return df.describe().to_csv()


@mcp.tool()
def csv_histogram(csv_content: str, column: str) -> str:
    """Return histogram of a column as base64 PNG"""
    df = pd.read_csv(io.StringIO(csv_content))
    plt.figure()
    df[column].hist()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()
