import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("LLM Multimodal Tool Example")

OPENAI_VISION_URL = "https://api.openai.com/v1/chat/completions"


@mcp.tool()
def analyze_image_with_openai(
    image_url: str, api_key: str, prompt: str = "Describe this image"
) -> str:
    """Send image URL to OpenAI Vision (GPT-4o) and return analysis"""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        "max_tokens": 512,
    }
    resp = httpx.post(OPENAI_VISION_URL, json=data, headers=headers)
    if resp.status_code != 200:
        return f"Error: {resp.text}"
    return resp.json()["choices"][0]["message"]["content"]
