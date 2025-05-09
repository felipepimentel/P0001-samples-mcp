import getpass
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Fix os.getlogin for environments that might have issues
os.getlogin = getpass.getuser

from mcp.sampling import SamplingMessage, TextContent
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolError

mcp = FastMCP("Browser Automation")


# Simulated browser state
class BrowserSimulator:
    def __init__(self):
        self.current_url = ""
        self.page_content = {}
        self.screenshots = {}
        self.form_data = {}

        # Initialize with a sample website
        self.websites = {
            "https://example.com": {
                "title": "Example Domain",
                "content": "This domain is for use in illustrative examples in documents.",
                "elements": [
                    {"type": "heading", "text": "Example Domain", "id": "main-heading"},
                    {
                        "type": "paragraph",
                        "text": "This domain is for use in illustrative examples in documents.",
                        "id": "description",
                    },
                    {
                        "type": "link",
                        "text": "More information",
                        "href": "https://www.iana.org/domains/example",
                        "id": "info-link",
                    },
                    {
                        "type": "form",
                        "id": "contact-form",
                        "fields": [
                            {
                                "name": "name",
                                "type": "text",
                                "placeholder": "Your name",
                            },
                            {
                                "name": "email",
                                "type": "email",
                                "placeholder": "Your email",
                            },
                            {
                                "name": "message",
                                "type": "textarea",
                                "placeholder": "Your message",
                            },
                        ],
                    },
                ],
            },
            "https://www.iana.org/domains/example": {
                "title": "IANA — Example domains",
                "content": "Example domains are registered domains that are reserved for use in example situations.",
                "elements": [
                    {
                        "type": "heading",
                        "text": "Example Domains",
                        "id": "main-heading",
                    },
                    {
                        "type": "paragraph",
                        "text": "Example domains are reserved for documentation purposes.",
                        "id": "info-text",
                    },
                    {
                        "type": "list",
                        "items": ["example.com", "example.net", "example.org"],
                        "id": "examples-list",
                    },
                ],
            },
            "https://weather.example.com": {
                "title": "Weather Forecast",
                "content": "Current weather conditions and forecasts.",
                "elements": [
                    {
                        "type": "heading",
                        "text": "Weather Forecast",
                        "id": "main-heading",
                    },
                    {
                        "type": "widget",
                        "id": "weather-widget",
                        "data": {
                            "location": "New York",
                            "temperature": 72,
                            "condition": "Partly Cloudy",
                            "forecast": [
                                {
                                    "day": "Monday",
                                    "high": 75,
                                    "low": 62,
                                    "condition": "Sunny",
                                },
                                {
                                    "day": "Tuesday",
                                    "high": 70,
                                    "low": 60,
                                    "condition": "Rain",
                                },
                                {
                                    "day": "Wednesday",
                                    "high": 68,
                                    "low": 58,
                                    "condition": "Cloudy",
                                },
                            ],
                        },
                    },
                ],
            },
        }

    def navigate(self, url: str) -> Dict:
        """Navigate to a URL and return page information"""
        if url in self.websites:
            self.current_url = url
            self.page_content = self.websites[url]
            return {
                "url": url,
                "title": self.page_content["title"],
                "status": "success",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "url": url,
                "status": "error",
                "message": "Page not found",
                "timestamp": datetime.now().isoformat(),
            }

    def get_page_content(self) -> Dict:
        """Get content of the current page"""
        if not self.current_url:
            return {"error": "No page loaded"}
        return {
            "url": self.current_url,
            "title": self.page_content["title"],
            "content": self.page_content["content"],
            "timestamp": datetime.now().isoformat(),
        }

    def get_elements(self, selector: str = None) -> List[Dict]:
        """Get elements from the current page, optionally filtered by selector"""
        if not self.current_url:
            return [{"error": "No page loaded"}]

        elements = self.page_content.get("elements", [])

        if selector:
            # Simple selector implementation (id only)
            if selector.startswith("#"):
                element_id = selector[1:]
                return [elem for elem in elements if elem.get("id") == element_id]
            # Type selector
            else:
                return [elem for elem in elements if elem.get("type") == selector]

        return elements

    def take_screenshot(self) -> Dict:
        """Take a screenshot of the current page"""
        if not self.current_url:
            return {"error": "No page loaded"}

        screenshot_id = f"screenshot_{len(self.screenshots) + 1}"
        self.screenshots[screenshot_id] = {
            "url": self.current_url,
            "timestamp": datetime.now().isoformat(),
            "data": f"[Simulated screenshot of {self.page_content['title']}]",
        }

        return {
            "id": screenshot_id,
            "url": self.current_url,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
        }

    def fill_form(self, form_id: str, data: Dict[str, str]) -> Dict:
        """Fill a form with the provided data"""
        if not self.current_url:
            return {"error": "No page loaded"}

        # Find the form
        form = None
        for element in self.page_content.get("elements", []):
            if element.get("type") == "form" and element.get("id") == form_id:
                form = element
                break

        if not form:
            return {"error": f"Form with ID '{form_id}' not found"}

        # Validate the form data
        valid_fields = [field["name"] for field in form.get("fields", [])]
        invalid_fields = [field for field in data if field not in valid_fields]

        if invalid_fields:
            return {"error": f"Invalid fields: {', '.join(invalid_fields)}"}

        # Store the form data
        if self.current_url not in self.form_data:
            self.form_data[self.current_url] = {}

        self.form_data[self.current_url][form_id] = data

        return {
            "status": "success",
            "form_id": form_id,
            "fields_filled": list(data.keys()),
            "timestamp": datetime.now().isoformat(),
        }

    def submit_form(self, form_id: str) -> Dict:
        """Submit a form with previously filled data"""
        if not self.current_url:
            return {"error": "No page loaded"}

        if self.current_url not in self.form_data or form_id not in self.form_data.get(
            self.current_url, {}
        ):
            return {"error": f"Form with ID '{form_id}' not filled out yet"}

        form_data = self.form_data[self.current_url][form_id]

        return {
            "status": "success",
            "form_id": form_id,
            "data_submitted": form_data,
            "timestamp": datetime.now().isoformat(),
            "result": "Thank you for your submission!",
        }

    def extract_data(self, element_id: str) -> Dict:
        """Extract data from a specific element"""
        if not self.current_url:
            return {"error": "No page loaded"}

        for element in self.page_content.get("elements", []):
            if element.get("id") == element_id:
                return {
                    "element_id": element_id,
                    "type": element.get("type"),
                    "data": element.get("data") if "data" in element else element,
                    "timestamp": datetime.now().isoformat(),
                }

        return {"error": f"Element with ID '{element_id}' not found"}


# Initialize browser simulator
browser = BrowserSimulator()


# Browser automation tools
@mcp.tool()
def navigate_to_url(url: str) -> Dict:
    """
    Navigate to a specified URL in the browser

    Args:
        url: The URL to navigate to

    Returns:
        Dictionary with navigation result
    """
    return browser.navigate(url)


@mcp.tool()
def get_page_content() -> Dict:
    """
    Get the content of the currently loaded page

    Returns:
        Dictionary with page content information
    """
    return browser.get_page_content()


@mcp.tool()
def get_elements(selector: Optional[str] = None) -> List[Dict]:
    """
    Get elements from the current page, optionally filtered by selector

    Args:
        selector: Optional CSS-like selector (e.g., "#element-id" or "paragraph")

    Returns:
        List of elements matching the selector
    """
    return browser.get_elements(selector)


@mcp.tool()
def take_screenshot() -> Dict:
    """
    Take a screenshot of the current page

    Returns:
        Dictionary with screenshot information
    """
    return browser.take_screenshot()


@mcp.tool()
def fill_form(form_id: str, data: Dict[str, str]) -> Dict:
    """
    Fill a form with the provided data

    Args:
        form_id: ID of the form to fill
        data: Dictionary of form field names and values

    Returns:
        Dictionary with form filling result
    """
    return browser.fill_form(form_id, data)


@mcp.tool()
def submit_form(form_id: str) -> Dict:
    """
    Submit a previously filled form

    Args:
        form_id: ID of the form to submit

    Returns:
        Dictionary with form submission result
    """
    return browser.submit_form(form_id)


@mcp.tool()
def extract_data(element_id: str) -> Dict:
    """
    Extract data from a specific element

    Args:
        element_id: ID of the element to extract data from

    Returns:
        Dictionary with extracted data
    """
    return browser.extract_data(element_id)


# Resources
@mcp.resource("browser://current_url")
def get_current_url() -> str:
    """Get the currently loaded URL"""
    return browser.current_url or "No page loaded"


@mcp.resource("browser://page_title")
def get_page_title() -> str:
    """Get the title of the currently loaded page"""
    if not browser.current_url:
        return "No page loaded"
    return browser.page_content.get("title", "Untitled Page")


@mcp.resource("browser://screenshots/{id}")
def get_screenshot(id: str) -> str:
    """Get a specific screenshot by ID"""
    if id not in browser.screenshots:
        return f"Screenshot with ID '{id}' not found"
    return json.dumps(browser.screenshots[id])


# Advanced sampling tool for web scraping analysis
@mcp.tool()
def analyze_webpage_content() -> Dict:
    """
    Analyze the current webpage content and extract key information using LLM

    Returns:
        Dictionary with analyzed information
    """
    if not browser.current_url:
        raise ToolError("No page loaded")

    # Create a prompt for the LLM
    prompt = f"""
    Analyze the following webpage content and extract key information:
    
    URL: {browser.current_url}
    Title: {browser.page_content.get("title", "Untitled")}
    Content: {browser.page_content.get("content", "No content")}
    
    Elements:
    {json.dumps(browser.page_content.get("elements", []), indent=2)}
    
    Please provide:
    1. A brief summary of the webpage
    2. Key topics or themes
    3. Important data points
    4. Recommended actions based on the content
    """

    # Sample from LLM
    messages = [
        SamplingMessage(
            role="system",
            content=[
                TextContent(
                    "You are a web content analyzer that extracts key information from webpages."
                )
            ],
        ),
        SamplingMessage(role="user", content=[TextContent(prompt)]),
    ]

    sampling = mcp.get_sampling()
    response = sampling.sample(messages=messages)

    # Extract the content from the response
    analysis = (
        response.message.content[0].text
        if response and response.message and response.message.content
        else "Analysis failed"
    )

    return {
        "url": browser.current_url,
        "title": browser.page_content.get("title", "Untitled"),
        "analysis": analysis,
        "timestamp": datetime.now().isoformat(),
    }


# Prompt templates for browser automation
browser_automation_prompt = """
You're now connected to a Browser Automation tool that lets you interact with web pages:

Available tools:
- navigate_to_url(url): Navigate to a specific URL
- get_page_content(): Get content of the current page
- get_elements(selector): Get elements matching a selector
- take_screenshot(): Take a screenshot of the current page
- fill_form(form_id, data): Fill a form with data
- submit_form(form_id): Submit a previously filled form
- extract_data(element_id): Extract data from a specific element
- analyze_webpage_content(): Analyze the current webpage using AI

Start by navigating to a URL like "https://example.com" or "https://weather.example.com"

Sample websites available:
- https://example.com
- https://www.iana.org/domains/example
- https://weather.example.com

You can extract data, fill forms, take screenshots, and even analyze page content.
"""

mcp.add_prompt_template("browser_automation", browser_automation_prompt)
