import datetime
import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import Message, SystemMessage, UserMessage

# Initialize MCP server for a research assistant application
mcp = FastMCP("Research Assistant")

# Configure data directories
DATA_DIR = Path(os.path.expanduser("~")) / "mcp_research_assistant"
DB_DIR = DATA_DIR / "db"
DOCS_DIR = DATA_DIR / "documents"
EXPORT_DIR = DATA_DIR / "exports"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

# Database setup
DB_PATH = DB_DIR / "research.db"


def init_database():
    """Initialize the SQLite database with necessary tables"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            document_id INTEGER,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            document_id INTEGER,
            content TEXT NOT NULL,
            type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS exports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            filename TEXT NOT NULL,
            format TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)


# Initialize the database
init_database()


# Helper functions for database operations
def get_projects() -> List[Dict]:
    """Get all research projects"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
        return [dict(row) for row in cursor.fetchall()]


def get_project(project_id: int) -> Optional[Dict]:
    """Get a specific project by ID"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_documents(project_id: int) -> List[Dict]:
    """Get all documents for a project"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE project_id = ? ORDER BY added_at DESC",
            (project_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_document(document_id: int) -> Optional[Dict]:
    """Get a specific document by ID"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_document_notes(document_id: int) -> List[Dict]:
    """Get all notes for a document"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM notes WHERE document_id = ? ORDER BY created_at DESC",
            (document_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_document_summaries(document_id: int) -> List[Dict]:
    """Get all summaries for a document"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM summaries WHERE document_id = ? ORDER BY created_at DESC",
            (document_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


# MCP Tools for Project Management
@mcp.tool()
def create_project(name: str, description: str = "") -> str:
    """
    Create a new research project

    Args:
        name: Name of the project
        description: Optional description of the project
    """
    if not name or not name.strip():
        return "Error: Project name cannot be empty."

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO projects (name, description) VALUES (?, ?)",
                (name, description),
            )
            project_id = cursor.lastrowid

            return json.dumps(
                {
                    "message": f"Project '{name}' created successfully.",
                    "project_id": project_id,
                },
                indent=2,
            )
    except Exception as e:
        return f"Error creating project: {str(e)}"


@mcp.tool()
def list_projects() -> str:
    """List all research projects"""
    try:
        projects = get_projects()

        if not projects:
            return "No projects found."

        result = []
        for project in projects:
            result.append(
                {
                    "id": project["id"],
                    "name": project["name"],
                    "description": project["description"],
                    "created_at": project["created_at"],
                }
            )

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing projects: {str(e)}"


@mcp.tool()
def get_project_details(project_id: int) -> str:
    """
    Get detailed information about a specific project

    Args:
        project_id: ID of the project
    """
    try:
        project = get_project(project_id)

        if not project:
            return f"Error: Project with ID {project_id} not found."

        # Get documents for this project
        documents = get_documents(project_id)

        # Get notes count
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM notes WHERE project_id = ?", (project_id,)
            )
            notes_count = cursor.fetchone()[0]

        result = {
            "id": project["id"],
            "name": project["name"],
            "description": project["description"],
            "created_at": project["created_at"],
            "updated_at": project["updated_at"],
            "documents_count": len(documents),
            "notes_count": notes_count,
            "documents": [
                {
                    "id": doc["id"],
                    "title": doc["title"],
                    "source": doc["source"],
                    "added_at": doc["added_at"],
                }
                for doc in documents
            ],
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting project details: {str(e)}"


# MCP Tools for Document Management
@mcp.tool()
def add_document(project_id: int, title: str, content: str, source: str = "") -> str:
    """
    Add a document to a research project

    Args:
        project_id: ID of the project
        title: Title of the document
        content: Content of the document
        source: Optional source information
    """
    if not title or not title.strip():
        return "Error: Document title cannot be empty."

    if not content or not content.strip():
        return "Error: Document content cannot be empty."

    try:
        # Verify project exists
        project = get_project(project_id)
        if not project:
            return f"Error: Project with ID {project_id} not found."

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO documents (project_id, title, content, source) VALUES (?, ?, ?, ?)",
                (project_id, title, content, source),
            )
            document_id = cursor.lastrowid

            # Update project's updated_at timestamp
            cursor.execute(
                "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (project_id,),
            )

            return json.dumps(
                {
                    "message": f"Document '{title}' added to project '{project['name']}'.",
                    "document_id": document_id,
                },
                indent=2,
            )
    except Exception as e:
        return f"Error adding document: {str(e)}"


@mcp.tool()
def get_document_content(document_id: int) -> str:
    """
    Get the content of a specific document

    Args:
        document_id: ID of the document
    """
    try:
        document = get_document(document_id)

        if not document:
            return f"Error: Document with ID {document_id} not found."

        return document["content"]
    except Exception as e:
        return f"Error retrieving document: {str(e)}"


@mcp.tool()
def list_project_documents(project_id: int) -> str:
    """
    List all documents in a project

    Args:
        project_id: ID of the project
    """
    try:
        # Verify project exists
        project = get_project(project_id)
        if not project:
            return f"Error: Project with ID {project_id} not found."

        documents = get_documents(project_id)

        if not documents:
            return f"No documents found in project '{project['name']}'."

        result = []
        for doc in documents:
            # Get the first few characters of content as a preview
            preview = (
                doc["content"][:100] + "..."
                if len(doc["content"]) > 100
                else doc["content"]
            )

            result.append(
                {
                    "id": doc["id"],
                    "title": doc["title"],
                    "source": doc["source"],
                    "added_at": doc["added_at"],
                    "preview": preview,
                }
            )

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing documents: {str(e)}"


# MCP Tools for Analysis using LLM
@mcp.tool()
async def summarize_document(document_id: int, summary_type: str = "brief") -> str:
    """
    Generate a summary of a document using the LLM

    Args:
        document_id: ID of the document to summarize
        summary_type: Type of summary (brief, detailed, bullets, academic)
    """
    valid_types = ["brief", "detailed", "bullets", "academic"]
    if summary_type not in valid_types:
        return f"Error: Invalid summary type. Choose from: {', '.join(valid_types)}"

    try:
        document = get_document(document_id)

        if not document:
            return f"Error: Document with ID {document_id} not found."

        # Prepare prompt for the LLM
        content = document["content"]

        if len(content) < 10:
            return "Error: Document content is too short to summarize."

        # Prepare messages for the LLM
        messages = [
            SystemMessage(
                "You are a research assistant specialized in summarizing academic content."
            ),
            UserMessage(
                f"Please provide a {summary_type} summary of the following document:\nTitle: {document['title']}\n\nContent:\n{content}"
            ),
        ]

        # Request a completion from the LLM
        completion = await mcp.sample(messages=messages)
        summary_content = completion.content

        # Store the summary in the database
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO summaries (project_id, document_id, content, type) VALUES (?, ?, ?, ?)",
                (document["project_id"], document_id, summary_content, summary_type),
            )
            summary_id = cursor.lastrowid

        return json.dumps(
            {
                "message": f"{summary_type.capitalize()} summary created for document '{document['title']}'.",
                "summary_id": summary_id,
                "summary": summary_content,
            },
            indent=2,
        )
    except Exception as e:
        return f"Error creating summary: {str(e)}"


@mcp.tool()
async def extract_key_insights(document_id: int, num_insights: int = 5) -> str:
    """
    Extract key insights from a document using the LLM

    Args:
        document_id: ID of the document
        num_insights: Number of insights to extract (1-10)
    """
    if num_insights < 1 or num_insights > 10:
        return "Error: Number of insights must be between 1 and 10."

    try:
        document = get_document(document_id)

        if not document:
            return f"Error: Document with ID {document_id} not found."

        content = document["content"]

        if len(content) < 10:
            return "Error: Document content is too short to extract insights."

        # Prepare messages for the LLM
        messages = [
            SystemMessage(
                "You are a research assistant specialized in extracting key insights from academic content."
            ),
            UserMessage(
                f"Extract exactly {num_insights} key insights from the following document. Format as a numbered list.\nTitle: {document['title']}\n\nContent:\n{content}"
            ),
        ]

        # Request a completion from the LLM
        completion = await mcp.sample(messages=messages)
        insights = completion.content

        # Store the insights as a note
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notes (project_id, document_id, content) VALUES (?, ?, ?)",
                (document["project_id"], document_id, f"Key Insights:\n\n{insights}"),
            )
            note_id = cursor.lastrowid

        return json.dumps(
            {
                "message": f"Extracted {num_insights} key insights from document '{document['title']}'.",
                "note_id": note_id,
                "insights": insights,
            },
            indent=2,
        )
    except Exception as e:
        return f"Error extracting insights: {str(e)}"


@mcp.tool()
def add_note(document_id: int, note_content: str) -> str:
    """
    Add a note to a document

    Args:
        document_id: ID of the document
        note_content: Content of the note
    """
    if not note_content or not note_content.strip():
        return "Error: Note content cannot be empty."

    try:
        document = get_document(document_id)

        if not document:
            return f"Error: Document with ID {document_id} not found."

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notes (project_id, document_id, content) VALUES (?, ?, ?)",
                (document["project_id"], document_id, note_content),
            )
            note_id = cursor.lastrowid

        return json.dumps(
            {
                "message": f"Note added to document '{document['title']}'.",
                "note_id": note_id,
            },
            indent=2,
        )
    except Exception as e:
        return f"Error adding note: {str(e)}"


@mcp.tool()
def list_document_notes(document_id: int) -> str:
    """
    List all notes for a document

    Args:
        document_id: ID of the document
    """
    try:
        document = get_document(document_id)

        if not document:
            return f"Error: Document with ID {document_id} not found."

        notes = get_document_notes(document_id)

        if not notes:
            return f"No notes found for document '{document['title']}'."

        result = []
        for note in notes:
            # Get the first few characters of content as a preview
            preview = (
                note["content"][:100] + "..."
                if len(note["content"]) > 100
                else note["content"]
            )

            result.append(
                {"id": note["id"], "created_at": note["created_at"], "preview": preview}
            )

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing notes: {str(e)}"


# MCP Tools for Export
@mcp.tool()
async def generate_research_report(project_id: int, format: str = "markdown") -> str:
    """
    Generate a comprehensive research report for a project

    Args:
        project_id: ID of the project
        format: Output format (markdown, text)
    """
    valid_formats = ["markdown", "text"]
    if format not in valid_formats:
        return f"Error: Invalid format. Choose from: {', '.join(valid_formats)}"

    try:
        project = get_project(project_id)

        if not project:
            return f"Error: Project with ID {project_id} not found."

        documents = get_documents(project_id)

        if not documents:
            return f"Error: Project '{project['name']}' has no documents to generate a report from."

        # Collect all document contents and summaries
        project_data = {
            "name": project["name"],
            "description": project["description"],
            "documents": [],
        }

        for doc in documents:
            doc_data = {
                "title": doc["title"],
                "content": doc["content"][:1000] + "..."
                if len(doc["content"]) > 1000
                else doc["content"],
                "source": doc["source"],
                "notes": [note["content"] for note in get_document_notes(doc["id"])],
                "summaries": [
                    summary["content"] for summary in get_document_summaries(doc["id"])
                ],
            }
            project_data["documents"].append(doc_data)

        # Prepare the LLM prompt for generating the report
        project_json = json.dumps(project_data)

        messages = [
            SystemMessage(
                "You are a research assistant specialized in creating comprehensive research reports."
            ),
            UserMessage(
                f"Generate a research report in {format} format based on the following project data. Include an executive summary, key findings, and recommendations.\n\nProject Data:\n{project_json}"
            ),
        ]

        # Request a completion from the LLM
        completion = await mcp.sample(messages=messages)
        report_content = completion.content

        # Save the report to a file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{project['name'].replace(' ', '_')}_{timestamp}.{format}"
        file_path = EXPORT_DIR / filename

        with open(file_path, "w") as f:
            f.write(report_content)

        # Record the export in the database
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO exports (project_id, filename, format) VALUES (?, ?, ?)",
                (project_id, filename, format),
            )

        return json.dumps(
            {
                "message": f"Research report generated for project '{project['name']}'.",
                "filename": filename,
                "file_path": str(file_path),
                "report_preview": report_content[:500] + "..."
                if len(report_content) > 500
                else report_content,
            },
            indent=2,
        )
    except Exception as e:
        return f"Error generating research report: {str(e)}"


@mcp.tool()
def list_exports(project_id: int) -> str:
    """
    List all exports for a project

    Args:
        project_id: ID of the project
    """
    try:
        project = get_project(project_id)

        if not project:
            return f"Error: Project with ID {project_id} not found."

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM exports WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            )
            exports = [dict(row) for row in cursor.fetchall()]

        if not exports:
            return f"No exports found for project '{project['name']}'."

        result = []
        for export in exports:
            file_path = EXPORT_DIR / export["filename"]
            file_exists = file_path.exists()
            file_size = file_path.stat().st_size if file_exists else 0

            result.append(
                {
                    "id": export["id"],
                    "filename": export["filename"],
                    "format": export["format"],
                    "created_at": export["created_at"],
                    "file_exists": file_exists,
                    "file_size_bytes": file_size,
                }
            )

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing exports: {str(e)}"


# MCP Resources
@mcp.resource("research://projects")
def get_projects_resource() -> str:
    """Get a list of all research projects"""
    try:
        projects = get_projects()

        if not projects:
            return json.dumps({"message": "No projects found."})

        return json.dumps(
            [
                {
                    "id": project["id"],
                    "name": project["name"],
                    "description": project["description"],
                    "updated_at": project["updated_at"],
                }
                for project in projects
            ],
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": f"Error retrieving projects: {str(e)}"})


@mcp.resource("research://project/{project_id}")
def get_project_resource(project_id: int) -> str:
    """Get details of a specific project"""
    try:
        project = get_project(project_id)

        if not project:
            return json.dumps({"error": f"Project with ID {project_id} not found."})

        documents = get_documents(project_id)

        result = {
            "id": project["id"],
            "name": project["name"],
            "description": project["description"],
            "created_at": project["created_at"],
            "updated_at": project["updated_at"],
            "document_count": len(documents),
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error retrieving project: {str(e)}"})


@mcp.resource("research://document/{document_id}")
def get_document_resource(document_id: int) -> str:
    """Get content and metadata of a specific document"""
    try:
        document = get_document(document_id)

        if not document:
            return json.dumps({"error": f"Document with ID {document_id} not found."})

        result = {
            "id": document["id"],
            "project_id": document["project_id"],
            "title": document["title"],
            "content": document["content"],
            "source": document["source"],
            "added_at": document["added_at"],
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error retrieving document: {str(e)}"})


# MCP Prompts
@mcp.prompt()
def research_question_prompt(topic: str) -> str:
    """Generate research questions for a given topic"""
    return f"""As a research assistant, please help generate 5 specific research questions related to the topic: {topic}.

The questions should:
- Be specific and focused
- Be answerable through research
- Represent different aspects of the topic
- Include a mix of factual, analytical, and exploratory questions
- Be relevant to academic or professional research

Topic: {topic}

Please format your response as a numbered list."""


@mcp.prompt()
def literature_review_prompt(topic: str, num_sources: int = 3) -> List[Message]:
    """Generate a structured prompt for creating a literature review on a topic"""
    return [
        SystemMessage(
            "You are a research assistant specialized in creating literature reviews."
        ),
        UserMessage(f"""Help me create a literature review on the topic: {topic}.

Please include:
1. A brief overview of the topic
2. Key theories and concepts
3. At least {num_sources} hypothetical sources that would be valuable
4. Gaps in the current research
5. Suggestions for further research

Format this as a structured literature review with appropriate headings."""),
    ]


@mcp.prompt()
def methodology_analysis_prompt(methodology: str) -> List[Message]:
    """Generate a structured prompt for analyzing a research methodology"""
    return [
        SystemMessage("You are a research methodology expert."),
        UserMessage(f"""Analyze the strengths and weaknesses of the following research methodology: {methodology}.

Please include:
1. Overview of the methodology
2. Key assumptions and theoretical foundations
3. Strengths (at least 3)
4. Limitations and weaknesses (at least 3)
5. Scenarios where this methodology is particularly appropriate
6. Scenarios where alternative methodologies might be better
7. Suggestions for mitigating the weaknesses

Format your response with clear headings and bullet points where appropriate."""),
    ]
