import getpass
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

# Fix os.getlogin for environments that might have issues
os.getlogin = getpass.getuser

from mcp.sampling import SamplingMessage, TextContent
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolError

# Create an MCP server
mcp = FastMCP("Document Analysis")


# Sample documents library
class DocumentLibrary:
    def __init__(self):
        self.documents = {
            "financial_report_2024.pdf": {
                "title": "Annual Financial Report 2024",
                "type": "pdf",
                "content": """
                ANNUAL FINANCIAL REPORT 2024
                
                Executive Summary
                
                The fiscal year 2024 showed strong performance across all business segments. 
                Revenue increased by 15% year-over-year to $245 million, while operating 
                expenses were reduced by 3% through strategic cost-cutting initiatives.
                
                Key Financial Metrics:
                - Revenue: $245 million (15% YoY increase)
                - Operating Income: $78 million (23% YoY increase)
                - Net Profit Margin: 18.5% (up from 16.2% in 2023)
                - Return on Assets: 12.3%
                - Debt-to-Equity Ratio: 0.45
                
                Regional Performance:
                - North America: $120 million in revenue (49% of total)
                - Europe: $75 million (31% of total)
                - Asia-Pacific: $35 million (14% of total)
                - Rest of World: $15 million (6% of total)
                
                Product Line Performance:
                - Product A: $90 million (37% of total)
                - Product B: $70 million (29% of total)
                - Product C: $55 million (22% of total)
                - Other Products: $30 million (12% of total)
                
                Outlook for 2025:
                We expect continued growth in the range of 10-12% for the upcoming fiscal year,
                with particularly strong performance in the Asia-Pacific region.
                """,
                "metadata": {
                    "author": "Finance Department",
                    "date": "2024-03-15",
                    "keywords": ["financial", "annual report", "2024", "revenue"],
                    "pages": 12,
                },
            },
            "market_research.pdf": {
                "title": "Market Research Report: Emerging Technology Trends",
                "type": "pdf",
                "content": """
                MARKET RESEARCH REPORT: EMERGING TECHNOLOGY TRENDS
                
                Executive Summary
                
                This report analyzes five key technology trends expected to have significant 
                market impact over the next 3-5 years.
                
                1. Artificial Intelligence
                   The AI market is projected to grow from $95 billion in 2024 to $240 billion
                   by 2028, representing a CAGR of 26%. Key growth areas include:
                   - Generative AI applications
                   - AI-powered cybersecurity solutions
                   - Healthcare diagnostics and drug discovery
                   
                2. Quantum Computing
                   While still in early commercial stages, the quantum computing market is
                   expected to reach $3.5 billion by 2028, up from $780 million in 2024.
                   Early adoption is concentrated in:
                   - Financial modeling
                   - Material science research
                   - Logistics optimization
                   
                3. Augmented Reality/Virtual Reality
                   The AR/VR market is projected to grow at 35% CAGR, reaching $95 billion
                   by 2028. Key growth sectors include:
                   - Industrial training and maintenance
                   - Healthcare education
                   - Retail customer experiences
                   
                4. Clean Energy Technology
                   Clean energy tech investments are expected to exceed $550 billion by 2027,
                   with particular growth in:
                   - Next-generation battery storage
                   - Green hydrogen production
                   - Smart grid technologies
                   
                5. Biotechnology
                   The biotech market is projected to grow from $1.2 trillion in 2024 to
                   $2.1 trillion by 2028, driven by:
                   - Personalized medicine
                   - CRISPR and gene editing technologies
                   - Synthetic biology applications
                """,
                "metadata": {
                    "author": "Research Department",
                    "date": "2024-05-22",
                    "keywords": ["market research", "technology", "trends", "forecast"],
                    "pages": 45,
                },
            },
            "strategic_plan.pdf": {
                "title": "Strategic Plan 2025-2027",
                "type": "pdf",
                "content": """
                STRATEGIC PLAN 2025-2027
                
                Executive Summary
                
                This document outlines our company's strategic priorities and initiatives
                for the three-year period from 2025 to 2027.
                
                Strategic Pillars:
                
                1. Market Expansion
                   - Enter 3 new international markets in Southeast Asia
                   - Increase market share in existing territories by 5-7%
                   - Develop partnership network with 15+ local distributors
                   
                2. Product Innovation
                   - Launch next-generation platform by Q2 2025
                   - Allocate 18% of revenue to R&D (up from 15%)
                   - File at least 25 new patents by end of 2026
                   - Reduce time-to-market for new features by 30%
                   
                3. Operational Excellence
                   - Implement AI-driven process automation across 80% of eligible workflows
                   - Reduce operational costs by 12% through efficiency initiatives
                   - Achieve carbon neutrality in all operations by end of 2026
                   - Optimize supply chain for 99.5% fulfillment rate
                   
                4. Customer Experience Enhancement
                   - Increase Net Promoter Score from 42 to 60+
                   - Deploy unified customer data platform by Q3 2025
                   - Reduce customer support response time by 65%
                   - Launch premium service tier with personalized support
                   
                5. Talent Development
                   - Implement comprehensive upskilling program for 100% of employees
                   - Reduce voluntary turnover rate from 12% to below 8%
                   - Increase diversity in leadership positions by 40%
                   - Establish 5 new university partnerships for talent pipeline
                """,
                "metadata": {
                    "author": "Executive Team",
                    "date": "2024-06-10",
                    "keywords": [
                        "strategic plan",
                        "business strategy",
                        "roadmap",
                        "growth",
                    ],
                    "pages": 28,
                },
            },
        }

        # Keep track of analysis results
        self.analysis_results = {}
        self.analysis_counter = 0

        # Track document uploads
        self.uploads = {}
        self.upload_counter = 0

    def get_document_list(self) -> List[Dict]:
        """Get a list of all available documents with metadata"""
        return [
            {
                "filename": filename,
                "title": doc["title"],
                "type": doc["type"],
                "metadata": doc["metadata"],
            }
            for filename, doc in self.documents.items()
        ]

    def get_document(self, filename: str) -> Dict:
        """Get a document by filename"""
        if filename not in self.documents:
            return {"error": f"Document '{filename}' not found"}

        return {
            "filename": filename,
            "title": self.documents[filename]["title"],
            "content": self.documents[filename]["content"],
            "metadata": self.documents[filename]["metadata"],
        }

    def search_documents(self, query: str) -> List[Dict]:
        """Search documents for matching content"""
        results = []

        for filename, doc in self.documents.items():
            content = doc["content"].lower()
            title = doc["title"].lower()
            query_lower = query.lower()

            if query_lower in content or query_lower in title:
                # Find context around matches in content
                matches = []
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if query_lower in line.lower():
                        context_start = max(0, i - 1)
                        context_end = min(len(lines), i + 2)
                        context = "\n".join(lines[context_start:context_end])
                        matches.append(context)

                results.append(
                    {
                        "filename": filename,
                        "title": doc["title"],
                        "metadata": doc["metadata"],
                        "matches": matches[:3],  # Limit to first 3 matches
                    }
                )

        return results

    def extract_key_information(self, filename: str) -> Dict:
        """Extract key information from a document"""
        if filename not in self.documents:
            return {"error": f"Document '{filename}' not found"}

        doc = self.documents[filename]
        content = doc["content"]

        # Extract metrics and numbers
        metrics = {}
        number_pattern = r"[\$£€]?\d+(?:[.,]\d+)?(?:\s*[bmk%]\b|\s*million|\s*billion)?"
        metric_pattern = r"([A-Za-z\s-]+):\s*(" + number_pattern + ")"

        for match in re.finditer(metric_pattern, content):
            metric_name = match.group(1).strip()
            metric_value = match.group(2).strip()
            metrics[metric_name] = metric_value

        # Extract dates
        dates = []
        date_pattern = (
            r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b"
        )

        for match in re.finditer(date_pattern, content):
            dates.append(match.group(0))

        # Extract entities (simplistic approach)
        entities = {"organizations": [], "locations": [], "products": []}

        org_keywords = ["Company", "Corporation", "Inc", "Ltd", "LLC", "GmbH"]
        for keyword in org_keywords:
            pattern = r"\b[A-Z][A-Za-z]*\s*" + keyword + r"\b"
            for match in re.finditer(pattern, content):
                if match.group(0) not in entities["organizations"]:
                    entities["organizations"].append(match.group(0))

        # Extract sections
        sections = []
        section_pattern = r"^\s*([A-Z][A-Za-z\s]+):\s*$"

        for line in content.split("\n"):
            match = re.match(section_pattern, line)
            if match:
                sections.append(match.group(1).strip())

        return {
            "filename": filename,
            "title": doc["title"],
            "metrics": metrics,
            "dates": dates,
            "entities": entities,
            "sections": sections,
        }

    def upload_document(self, title: str, content: str, metadata: Dict) -> Dict:
        """Upload a new document to the library"""
        self.upload_counter += 1
        filename = f"uploaded_doc_{self.upload_counter}.pdf"

        self.documents[filename] = {
            "title": title,
            "type": "pdf",
            "content": content,
            "metadata": metadata,
        }

        self.uploads[filename] = {
            "timestamp": datetime.now().isoformat(),
            "title": title,
        }

        return {
            "filename": filename,
            "title": title,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_document(self, filename: str) -> str:
        """Generate an analysis ID for a document"""
        if filename not in self.documents:
            return None

        self.analysis_counter += 1
        analysis_id = f"analysis_{self.analysis_counter}"

        self.analysis_results[analysis_id] = {
            "filename": filename,
            "title": self.documents[filename]["title"],
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
        }

        return analysis_id

    def get_analysis_result(self, analysis_id: str) -> Dict:
        """Get the result of a document analysis"""
        if analysis_id not in self.analysis_results:
            return {"error": f"Analysis ID '{analysis_id}' not found"}

        analysis = self.analysis_results[analysis_id]
        if analysis["status"] == "pending":
            analysis["status"] = "completed"
            analysis["result"] = {
                "summary": f"Analysis of {analysis['title']} completed successfully.",
                "key_points": [
                    "The document contains important financial information.",
                    "Several strategic initiatives are outlined.",
                    "Performance metrics indicate positive growth trends.",
                ],
                "recommendations": [
                    "Consider further analysis of financial projections.",
                    "Compare with industry benchmarks for context.",
                ],
            }
            self.analysis_results[analysis_id] = analysis

        return analysis


# Initialize document library
doc_lib = DocumentLibrary()


# Define MCP tools for document analysis
@mcp.tool()
def list_documents() -> List[Dict]:
    """
    Get a list of all available documents with metadata

    Returns:
        List of document information
    """
    return doc_lib.get_document_list()


@mcp.tool()
def get_document_content(filename: str) -> Dict:
    """
    Get the content of a document by filename

    Args:
        filename: Name of the document file

    Returns:
        Dictionary with document content and metadata
    """
    return doc_lib.get_document(filename)


@mcp.tool()
def search_documents(query: str) -> List[Dict]:
    """
    Search all documents for content matching the query

    Args:
        query: Search terms to look for in documents

    Returns:
        List of matching documents with context
    """
    return doc_lib.search_documents(query)


@mcp.tool()
def extract_document_information(filename: str) -> Dict:
    """
    Extract key information from a document

    Args:
        filename: Name of the document file

    Returns:
        Dictionary with extracted information
    """
    return doc_lib.extract_key_information(filename)


@mcp.tool()
def upload_document(title: str, content: str, metadata: Optional[Dict] = None) -> Dict:
    """
    Upload a new document to the library

    Args:
        title: Title of the document
        content: Document content text
        metadata: Optional metadata for the document

    Returns:
        Dictionary with upload result information
    """
    if metadata is None:
        metadata = {
            "author": "User",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "keywords": [],
            "pages": 1,
        }

    return doc_lib.upload_document(title, content, metadata)


@mcp.tool()
def analyze_document_with_ai(filename: str) -> Dict:
    """
    Analyze a document with AI and generate insights

    Args:
        filename: Name of the document file

    Returns:
        Dictionary with analysis information and ID
    """
    if filename not in doc_lib.documents:
        raise ToolError(f"Document '{filename}' not found")

    analysis_id = doc_lib.analyze_document(filename)
    if not analysis_id:
        raise ToolError("Failed to initiate document analysis")

    # Get the document content
    doc = doc_lib.get_document(filename)

    # Create a prompt for the LLM
    prompt = f"""
    Analyze the following document:
    
    Title: {doc["title"]}
    
    Content:
    {doc["content"]}
    
    Please provide:
    1. A concise summary of the document
    2. Key insights and important information
    3. Notable metrics, figures, or statistics
    4. Potential action items or recommendations based on the content
    """

    # Sample from LLM
    messages = [
        SamplingMessage(
            role="system",
            content=[
                TextContent(
                    "You are a document analysis expert specializing in extracting insights from business documents."
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

    # Update the analysis result
    doc_lib.analysis_results[analysis_id] = {
        "filename": filename,
        "title": doc["title"],
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "result": {"ai_analysis": analysis},
    }

    return {
        "analysis_id": analysis_id,
        "status": "completed",
        "document": filename,
        "timestamp": datetime.now().isoformat(),
    }


@mcp.tool()
def get_analysis_result(analysis_id: str) -> Dict:
    """
    Get the result of a document analysis by ID

    Args:
        analysis_id: ID of the analysis to retrieve

    Returns:
        Dictionary with analysis results
    """
    result = doc_lib.get_analysis_result(analysis_id)
    if "error" in result:
        raise ToolError(result["error"])
    return result


# Resources for accessing document information
@mcp.resource("documents://list")
def resource_list_documents() -> str:
    """Get a list of all available documents"""
    return json.dumps(doc_lib.get_document_list())


@mcp.resource("documents://{filename}")
def resource_get_document(filename: str) -> str:
    """Get a document by filename"""
    doc = doc_lib.get_document(filename)
    return json.dumps(doc)


@mcp.resource("documents://analysis/{analysis_id}")
def resource_get_analysis(analysis_id: str) -> str:
    """Get analysis results by ID"""
    analysis = doc_lib.get_analysis_result(analysis_id)
    return json.dumps(analysis)


# Prompt templates for document analysis
document_analysis_prompt = """
You're now connected to a Document Analysis tool that lets you analyze business documents:

Available tools:
- list_documents(): Get a list of all available documents
- get_document_content(filename): Get the full content of a document
- search_documents(query): Search all documents for matching content
- extract_document_information(filename): Extract key information from a document
- upload_document(title, content, metadata): Upload a new document
- analyze_document_with_ai(filename): Analyze a document with AI
- get_analysis_result(analysis_id): Get analysis results by ID

Start by listing the available documents, then you can retrieve and analyze specific documents.

Sample workflow:
1. List available documents
2. Get content of a specific document
3. Extract key information like metrics, dates, and entities
4. Search across documents for specific terms
5. Run AI analysis to get insights and recommendations

The tool provides access to business documents like financial reports, market research, and strategic plans.
"""

mcp.add_prompt_template("document_analysis", document_analysis_prompt)
