import getpass
import json
import os
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List

# Handle potential getlogin issues
os.getlogin = getpass.getuser

from mcp.server.fastmcp import FastMCP

# Initialize MCP server for legacy system migration
mcp = FastMCP("Legacy System Migration")

# Directory for storing legacy code samples and migration templates
DATA_DIR = Path(os.path.expanduser("~")) / "mcp_legacy_migration"
LEGACY_DIR = DATA_DIR / "legacy_code"
MODERN_DIR = DATA_DIR / "modern_code"
TEMPLATES_DIR = DATA_DIR / "templates"
MIGRATION_DIR = DATA_DIR / "migrations"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
LEGACY_DIR.mkdir(exist_ok=True)
MODERN_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
MIGRATION_DIR.mkdir(exist_ok=True)


# Define supported legacy and target languages
class LegacyLanguage(str, Enum):
    COBOL = "cobol"
    VB6 = "vb6"
    FORTRAN = "fortran"
    CPP = "cpp"
    JAVA = "java"
    PERL = "perl"
    PHP = "php"


class ModernLanguage(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    KOTLIN = "kotlin"
    RUST = "rust"
    GO = "go"
    CSHARP = "csharp"
    SCALA = "scala"


@dataclass
class MigrationProject:
    """Represents a migration project from legacy to modern code"""

    id: str
    name: str
    description: str
    legacy_language: LegacyLanguage
    modern_language: ModernLanguage
    legacy_files: List[str] = field(default_factory=list)
    modern_files: List[str] = field(default_factory=list)
    status: str = "pending"
    created_at: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "legacy_language": self.legacy_language,
            "modern_language": self.modern_language,
            "legacy_files": self.legacy_files,
            "modern_files": self.modern_files,
            "status": self.status,
            "created_at": self.created_at,
        }


# Store active migration projects
MIGRATION_PROJECTS: Dict[str, MigrationProject] = {}

# Sample legacy code snippets
LEGACY_CODE_SAMPLES = {
    LegacyLanguage.COBOL: {
        "account_processing.cbl": """
      * ACCOUNT PROCESSING MODULE
       IDENTIFICATION DIVISION.
       PROGRAM-ID. ACCTPROC.
       ENVIRONMENT DIVISION.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-ACCOUNT-FILE      PIC X(50) VALUE 'ACCOUNT.DAT'.
       01 WS-ACCOUNT-RECORD.
          05 WS-ACCOUNT-NUMBER  PIC 9(10).
          05 WS-ACCOUNT-NAME    PIC X(30).
          05 WS-ACCOUNT-BALANCE PIC 9(10)V99.
          05 WS-LAST-ACCESS-DATE.
             10 WS-YEAR         PIC 9(4).
             10 WS-MONTH        PIC 9(2).
             10 WS-DAY          PIC 9(2).
       01 WS-FLAGS.
          05 WS-EOF-FLAG        PIC X VALUE 'N'.
             88 WS-EOF          VALUE 'Y'.
             88 WS-NOT-EOF      VALUE 'N'.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT ACCOUNT-FILE.
           PERFORM READ-PROCESS-RECORD UNTIL WS-EOF.
           CLOSE ACCOUNT-FILE.
           STOP RUN.
       READ-PROCESS-RECORD.
           READ ACCOUNT-FILE INTO WS-ACCOUNT-RECORD
               AT END SET WS-EOF TO TRUE
               NOT AT END PERFORM PROCESS-RECORD
           END-READ.
       PROCESS-RECORD.
           IF WS-ACCOUNT-BALANCE > 100000
               DISPLAY 'HIGH VALUE ACCOUNT: ' WS-ACCOUNT-NUMBER
               DISPLAY 'CUSTOMER: ' WS-ACCOUNT-NAME
               DISPLAY 'BALANCE: ' WS-ACCOUNT-BALANCE
           END-IF.
        """
    },
    LegacyLanguage.VB6: {
        "customer_form.frm": """
VERSION 5.00
Begin VB.Form frmCustomer
   Caption         =   "Customer Management"
   ClientHeight    =   5175
   ClientLeft      =   60
   ClientTop       =   345
   ClientWidth     =   7080
   LinkTopic       =   "Form1"
   ScaleHeight     =   5175
   ScaleWidth      =   7080
   StartUpPosition =   3  'Windows Default
   Begin VB.TextBox txtLastName
      Height          =   375
      Left            =   1800
      TabIndex        =   5
      Top             =   960
      Width           =   3135
   End
   Begin VB.TextBox txtFirstName
      Height          =   375
      Left            =   1800
      TabIndex        =   3
      Top             =   480
      Width           =   3135
   End
   Begin VB.CommandButton cmdSave
      Caption         =   "Save"
      Height          =   495
      Left            =   1920
      TabIndex        =   1
      Top             =   4320
      Width           =   1215
   End
   Begin VB.CommandButton cmdCancel
      Caption         =   "Cancel"
      Height          =   495
      Left            =   3480
      TabIndex        =   0
      Top             =   4320
      Width           =   1215
   End
   Begin VB.Label lblLastName 
      Caption         =   "Last Name:"
      Height          =   255
      Left            =   360
      TabIndex        =   4
      Top             =   960
      Width           =   1215
   End
   Begin VB.Label lblFirstName
      Caption         =   "First Name:"
      Height          =   255
      Left            =   360
      TabIndex        =   2
      Top             =   480
      Width           =   1215
   End
End
Attribute VB_Name = "frmCustomer"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private m_customerID As Long
Private m_db As Database
Private m_rs As Recordset

Private Sub Form_Load()
    ' Connect to database
    Set m_db = OpenDatabase("CUSTOMER.MDB")
    Set m_rs = m_db.OpenRecordset("Customers", dbOpenDynaset)
    
    ' Check if we have a customer ID to load
    If m_customerID > 0 Then
        LoadCustomer
    End If
End Sub

Private Sub cmdSave_Click()
    On Error GoTo ErrorHandler
    
    ' Input validation
    If Trim(txtFirstName.Text) = "" Then
        MsgBox "First name is required", vbExclamation
        txtFirstName.SetFocus
        Exit Sub
    End If
    
    If Trim(txtLastName.Text) = "" Then
        MsgBox "Last name is required", vbExclamation
        txtLastName.SetFocus
        Exit Sub
    End If
    
    ' Save customer information
    If m_customerID > 0 Then
        ' Update existing record
        m_rs.FindFirst "CustomerID = " & m_customerID
        If Not m_rs.NoMatch Then
            m_rs.Edit
        End If
    Else
        ' Add new record
        m_rs.AddNew
    End If
    
    ' Save the fields
    m_rs("FirstName") = txtFirstName.Text
    m_rs("LastName") = txtLastName.Text
    m_rs.Update
    
    MsgBox "Customer saved successfully", vbInformation
    Unload Me
    Exit Sub
    
ErrorHandler:
    MsgBox "Error saving customer: " & Err.Description, vbCritical
End Sub

Private Sub cmdCancel_Click()
    Unload Me
End Sub

Private Sub LoadCustomer()
    ' Find the customer record
    m_rs.FindFirst "CustomerID = " & m_customerID
    
    If Not m_rs.NoMatch Then
        ' Populate the form fields
        txtFirstName.Text = m_rs("FirstName")
        txtLastName.Text = m_rs("LastName")
    Else
        MsgBox "Customer not found", vbExclamation
        Unload Me
    End If
End Sub

Public Property Let CustomerID(ByVal lngID As Long)
    m_customerID = lngID
End Property
        """
    },
    LegacyLanguage.CPP: {
        "account_manager.cpp": """
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <ctime>

// Account record structure
struct AccountRecord {
    int accountId;
    char firstName[50];
    char lastName[50];
    double balance;
    char status[10];
    time_t lastUpdated;
};

class AccountManager {
private:
    std::string m_fileName;
    std::vector<AccountRecord> m_accounts;
    
    // Load accounts from file
    bool LoadAccounts() {
        std::ifstream file(m_fileName.c_str(), std::ios::binary);
        if (!file.is_open()) {
            std::cerr << "Error: Cannot open file " << m_fileName << std::endl;
            return false;
        }
        
        AccountRecord record;
        while (file.read(reinterpret_cast<char*>(&record), sizeof(AccountRecord))) {
            m_accounts.push_back(record);
        }
        
        file.close();
        return true;
    }
    
    // Save accounts to file
    bool SaveAccounts() {
        std::ofstream file(m_fileName.c_str(), std::ios::binary);
        if (!file.is_open()) {
            std::cerr << "Error: Cannot open file " << m_fileName << " for writing" << std::endl;
            return false;
        }
        
        for (size_t i = 0; i < m_accounts.size(); ++i) {
            file.write(reinterpret_cast<const char*>(&m_accounts[i]), sizeof(AccountRecord));
        }
        
        file.close();
        return true;
    }
    
public:
    AccountManager(const std::string& fileName) : m_fileName(fileName) {
        LoadAccounts();
    }
    
    ~AccountManager() {
        SaveAccounts();
    }
    
    // Add new account
    bool AddAccount(const std::string& firstName, const std::string& lastName, double initialBalance) {
        AccountRecord record;
        
        // Generate account ID
        record.accountId = m_accounts.size() + 1000;
        
        // Copy name with bounds checking
        strncpy(record.firstName, firstName.c_str(), sizeof(record.firstName) - 1);
        record.firstName[sizeof(record.firstName) - 1] = '\\0';
        
        strncpy(record.lastName, lastName.c_str(), sizeof(record.lastName) - 1);
        record.lastName[sizeof(record.lastName) - 1] = '\\0';
        
        record.balance = initialBalance;
        strcpy(record.status, "ACTIVE");
        record.lastUpdated = time(NULL);
        
        m_accounts.push_back(record);
        return true;
    }
    
    // Find account by ID
    AccountRecord* FindAccount(int accountId) {
        for (size_t i = 0; i < m_accounts.size(); ++i) {
            if (m_accounts[i].accountId == accountId) {
                return &m_accounts[i];
            }
        }
        return NULL;
    }
    
    // Update account balance
    bool UpdateBalance(int accountId, double newBalance) {
        AccountRecord* account = FindAccount(accountId);
        if (account == NULL) {
            std::cerr << "Error: Account not found" << std::endl;
            return false;
        }
        
        account->balance = newBalance;
        account->lastUpdated = time(NULL);
        return true;
    }
    
    // Close account
    bool CloseAccount(int accountId) {
        AccountRecord* account = FindAccount(accountId);
        if (account == NULL) {
            std::cerr << "Error: Account not found" << std::endl;
            return false;
        }
        
        strcpy(account->status, "CLOSED");
        account->lastUpdated = time(NULL);
        return true;
    }
    
    // Print all accounts
    void PrintAccounts() {
        std::cout << "=== Account List ===" << std::endl;
        for (size_t i = 0; i < m_accounts.size(); ++i) {
            std::cout << "Account ID: " << m_accounts[i].accountId << std::endl;
            std::cout << "Name: " << m_accounts[i].firstName << " " << m_accounts[i].lastName << std::endl;
            std::cout << "Balance: $" << m_accounts[i].balance << std::endl;
            std::cout << "Status: " << m_accounts[i].status << std::endl;
            std::cout << "Last Updated: " << ctime(&m_accounts[i].lastUpdated);
            std::cout << "-------------------" << std::endl;
        }
    }
};

int main() {
    AccountManager manager("accounts.dat");
    
    int choice;
    do {
        std::cout << "\\n1. Add Account\\n2. Update Balance\\n3. Close Account\\n4. List Accounts\\n0. Exit\\nChoice: ";
        std::cin >> choice;
        
        switch (choice) {
            case 1: {
                std::string firstName, lastName;
                double balance;
                
                std::cout << "First Name: ";
                std::cin >> firstName;
                
                std::cout << "Last Name: ";
                std::cin >> lastName;
                
                std::cout << "Initial Balance: ";
                std::cin >> balance;
                
                if (manager.AddAccount(firstName, lastName, balance)) {
                    std::cout << "Account added successfully" << std::endl;
                }
                break;
            }
            case 2: {
                int accountId;
                double newBalance;
                
                std::cout << "Account ID: ";
                std::cin >> accountId;
                
                std::cout << "New Balance: ";
                std::cin >> newBalance;
                
                if (manager.UpdateBalance(accountId, newBalance)) {
                    std::cout << "Balance updated successfully" << std::endl;
                }
                break;
            }
            case 3: {
                int accountId;
                
                std::cout << "Account ID: ";
                std::cin >> accountId;
                
                if (manager.CloseAccount(accountId)) {
                    std::cout << "Account closed successfully" << std::endl;
                }
                break;
            }
            case 4:
                manager.PrintAccounts();
                break;
            case 0:
                std::cout << "Exiting program" << std::endl;
                break;
            default:
                std::cout << "Invalid choice" << std::endl;
        }
    } while (choice != 0);
    
    return 0;
}
        """
    },
}


# Initialize legacy code samples
def initialize_legacy_code():
    """Initialize legacy code samples in the legacy directory"""
    for language, samples in LEGACY_CODE_SAMPLES.items():
        language_dir = LEGACY_DIR / language
        language_dir.mkdir(exist_ok=True)

        for filename, content in samples.items():
            file_path = language_dir / filename
            with open(file_path, "w") as f:
                f.write(content.strip())


# Initialize the data
initialize_legacy_code()


# Define MCP Tools for legacy code migration
@mcp.tool
def list_legacy_languages() -> List[str]:
    """
    Lists all supported legacy languages for migration.

    Returns:
        List of supported legacy languages
    """
    return [lang.value for lang in LegacyLanguage]


@mcp.tool
def list_modern_languages() -> List[str]:
    """
    Lists all supported modern languages as migration targets.

    Returns:
        List of supported modern languages
    """
    return [lang.value for lang in ModernLanguage]


@mcp.tool
def list_legacy_code_files(language: str) -> List[str]:
    """
    Lists all available legacy code files for a specific language.

    Args:
        language: The legacy language to list files for

    Returns:
        List of available code files for the specified language
    """
    try:
        language_dir = LEGACY_DIR / language
        if not language_dir.exists():
            return []

        return [f.name for f in language_dir.iterdir() if f.is_file()]
    except Exception as e:
        return [f"Error listing files: {str(e)}"]


@mcp.tool
def get_legacy_code_content(language: str, filename: str) -> str:
    """
    Retrieves the content of a specific legacy code file.

    Args:
        language: The legacy language
        filename: The name of the file to retrieve

    Returns:
        Content of the specified file
    """
    try:
        file_path = LEGACY_DIR / language / filename
        if not file_path.exists():
            return f"File not found: {filename}"

        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool
def create_migration_project(
    name: str,
    description: str,
    legacy_language: str,
    modern_language: str,
    legacy_files: List[str],
) -> Dict:
    """
    Creates a new migration project.

    Args:
        name: Name of the migration project
        description: Description of the project
        legacy_language: The legacy language to migrate from
        modern_language: The modern language to migrate to
        legacy_files: List of legacy code files to include in the project

    Returns:
        The created migration project
    """
    # Validate languages
    if legacy_language not in [lang.value for lang in LegacyLanguage]:
        return {"error": f"Unsupported legacy language: {legacy_language}"}

    if modern_language not in [lang.value for lang in ModernLanguage]:
        return {"error": f"Unsupported modern language: {modern_language}"}

    # Validate files
    available_files = list_legacy_code_files(legacy_language)
    for file in legacy_files:
        if file not in available_files:
            return {"error": f"File not found: {file}"}

    # Create project
    project_id = str(uuid.uuid4())
    project = MigrationProject(
        id=project_id,
        name=name,
        description=description,
        legacy_language=legacy_language,
        modern_language=modern_language,
        legacy_files=legacy_files,
    )

    MIGRATION_PROJECTS[project_id] = project

    # Create project directory
    project_dir = MIGRATION_DIR / project_id
    project_dir.mkdir(exist_ok=True)

    # Save project metadata
    with open(project_dir / "metadata.json", "w") as f:
        json.dump(project.to_dict(), f, indent=2)

    return project.to_dict()


@mcp.tool
def list_migration_projects() -> List[Dict]:
    """
    Lists all migration projects.

    Returns:
        List of migration projects
    """
    return [project.to_dict() for project in MIGRATION_PROJECTS.values()]


@mcp.tool
def get_migration_project(project_id: str) -> Dict:
    """
    Gets details of a specific migration project.

    Args:
        project_id: ID of the project to retrieve

    Returns:
        Details of the specified migration project
    """
    if project_id not in MIGRATION_PROJECTS:
        return {"error": "Project not found"}

    return MIGRATION_PROJECTS[project_id].to_dict()


@mcp.tool
def migrate_code(project_id: str, legacy_file: str) -> Dict:
    """
    Migrates a specific legacy code file to the target modern language.

    Args:
        project_id: ID of the migration project
        legacy_file: Name of the legacy file to migrate

    Returns:
        Migration result with the generated modern code
    """
    if project_id not in MIGRATION_PROJECTS:
        return {"error": "Project not found"}

    project = MIGRATION_PROJECTS[project_id]

    if legacy_file not in project.legacy_files:
        return {"error": f"File not part of project: {legacy_file}"}

    # Get legacy code content
    legacy_code = get_legacy_code_content(project.legacy_language, legacy_file)

    # This is where you would apply migration logic based on the source and target languages
    # For this example, we'll create a placeholder migrated file

    # Determine output filename based on target language extension
    extension_map = {
        ModernLanguage.PYTHON: ".py",
        ModernLanguage.TYPESCRIPT: ".ts",
        ModernLanguage.KOTLIN: ".kt",
        ModernLanguage.RUST: ".rs",
        ModernLanguage.GO: ".go",
        ModernLanguage.CSHARP: ".cs",
        ModernLanguage.SCALA: ".scala",
    }

    # Create output filename
    output_filename = (
        os.path.splitext(legacy_file)[0] + extension_map[project.modern_language]
    )

    # Add to project's modern files
    if output_filename not in project.modern_files:
        project.modern_files.append(output_filename)

    # Update project status
    project.status = "in_progress"

    # Return a placeholder result
    return {
        "legacy_file": legacy_file,
        "modern_file": output_filename,
        "status": "pending",
        "message": f"Migration of {legacy_file} to {project.modern_language} is in progress.",
    }


@mcp.tool
def analyze_legacy_code(project_id: str, legacy_file: str) -> Dict:
    """
    Analyzes legacy code to identify patterns, dependencies, and complexity.

    Args:
        project_id: ID of the migration project
        legacy_file: Name of the legacy file to analyze

    Returns:
        Analysis of the legacy code
    """
    if project_id not in MIGRATION_PROJECTS:
        return {"error": "Project not found"}

    project = MIGRATION_PROJECTS[project_id]

    if legacy_file not in project.legacy_files:
        return {"error": f"File not part of project: {legacy_file}"}

    # Get legacy code content
    legacy_code = get_legacy_code_content(project.legacy_language, legacy_file)

    # Here you would implement static code analysis
    # For this example, we'll return a placeholder analysis

    return {
        "filename": legacy_file,
        "language": project.legacy_language,
        "metrics": {
            "lines_of_code": len(legacy_code.split("\n")),
            "complexity": "medium",
            "dependencies": ["stdlib"],
            "risk_areas": ["data format conversion", "error handling"],
        },
        "summary": "Legacy code appears to implement a basic account management system with file I/O.",
    }


# Define the prompt for legacy code migration
migration_prompt = """
# Legacy System Migration Assistant

You are an expert in migrating legacy systems to modern technology stacks. Your role is to help developers analyze, convert, and migrate legacy code to modern programming languages while preserving business logic and improving maintainability.

Your capabilities include:
- Analyzing legacy code written in languages like COBOL, VB6, and C++
- Converting legacy code to modern languages such as Python, TypeScript, and Rust
- Creating migration projects that track the transformation process
- Identifying patterns and dependencies in legacy systems
- Providing modernization recommendations

## Available Tools

- `list_legacy_languages()` - Lists all supported legacy languages
- `list_modern_languages()` - Lists all supported modern languages as migration targets
- `list_legacy_code_files(language)` - Lists all available legacy code files for a specific language
- `get_legacy_code_content(language, filename)` - Retrieves the content of a specific legacy code file
- `create_migration_project(name, description, legacy_language, modern_language, legacy_files)` - Creates a new migration project
- `list_migration_projects()` - Lists all migration projects
- `get_migration_project(project_id)` - Gets details of a specific migration project
- `migrate_code(project_id, legacy_file)` - Migrates a specific legacy code file to the target modern language
- `analyze_legacy_code(project_id, legacy_file)` - Analyzes legacy code to identify patterns, dependencies, and complexity

## Migration Approach

When migrating legacy systems, follow these steps:
1. Analyze the legacy code to understand its structure and functionality
2. Identify business rules and critical logic that must be preserved
3. Design a modern architecture that maintains the essential functionality
4. Convert code file by file, focusing on core business logic first
5. Modernize APIs, data access, and user interfaces
6. Test thoroughly to ensure functional equivalence
7. Deploy the migrated system with appropriate monitoring

Remember that successful migration preserves business value while enabling future growth and maintenance.
"""

# Register the migration prompt
mcp.add_prompt("migration", migration_prompt)

# Start the MCP server
if __name__ == "__main__":
    mcp.start()
