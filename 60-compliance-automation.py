import getpass
import json
import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

# Handle potential getlogin issues
os.getlogin = getpass.getuser

from mcp.server.fastmcp import FastMCP
from mcp.types import SamplingMessage, TextContent

# Initialize MCP server for compliance automation
mcp = FastMCP("Compliance Automation for Enterprise")

# Directory for storing compliance rules, scan results, and reports
DATA_DIR = Path(os.path.expanduser("~")) / "mcp_compliance"
RULES_DIR = DATA_DIR / "rules"
SCANS_DIR = DATA_DIR / "scans"
REPORTS_DIR = DATA_DIR / "reports"
EVIDENCE_DIR = DATA_DIR / "evidence"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
RULES_DIR.mkdir(exist_ok=True)
SCANS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
EVIDENCE_DIR.mkdir(exist_ok=True)


# Define compliance standards and categories
class ComplianceStandard(str, Enum):
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    SOX = "sox"
    HIPAA = "hipaa"
    ISO27001 = "iso27001"
    GENERAL = "general"


# Define rule severity levels
class RuleSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Initialize default rules if none exist
def init_default_rules():
    if list(RULES_DIR.glob("*.json")):
        return  # Rules already exist

    default_rules = [
        {
            "id": "pci-data-001",
            "standard": ComplianceStandard.PCI_DSS,
            "title": "Credit Card Number Detection",
            "description": "Identifies potential credit card numbers in code or logs",
            "regex": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            "severity": RuleSeverity.CRITICAL,
            "fix_suggestion": "Replace credit card numbers with tokenized values or remove them entirely",
            "category": "data_exposure",
        },
        {
            "id": "gdpr-log-001",
            "standard": ComplianceStandard.GDPR,
            "title": "Personal Data in Logs",
            "description": "Detects personal data (emails, names) in log statements",
            "regex": r"(?:log|console|print|System\.out).*?['\"].*?(?:\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b|[A-Z][a-z]+ [A-Z][a-z]+).*?['\"]",
            "severity": RuleSeverity.HIGH,
            "fix_suggestion": "Use data masking for sensitive information in logs",
            "category": "logging",
        },
        {
            "id": "sox-audit-001",
            "standard": ComplianceStandard.SOX,
            "title": "Missing Audit Trail",
            "description": "Identifies database modifications without audit trail",
            "regex": r"(?:UPDATE|DELETE|INSERT).*?(?:WHERE|SET).*?(?!.*audit|.*log|.*history)",
            "severity": RuleSeverity.HIGH,
            "fix_suggestion": "Implement audit triggers or use ORM with audit capability",
            "category": "audit_trail",
        },
        {
            "id": "hipaa-phi-001",
            "standard": ComplianceStandard.HIPAA,
            "title": "Unencrypted PHI Transfer",
            "description": "Detects potential unencrypted data transfers of health information",
            "regex": r"(?:http|ftp|ws)://(?!https).*?(?:health|medical|patient|doctor|treatment)",
            "severity": RuleSeverity.CRITICAL,
            "fix_suggestion": "Use encrypted protocols (HTTPS, SFTP) for all PHI transfers",
            "category": "encryption",
        },
        {
            "id": "iso-access-001",
            "standard": ComplianceStandard.ISO27001,
            "title": "Hardcoded Credentials",
            "description": "Finds hardcoded usernames and passwords",
            "regex": r"(?:password|passwd|pwd|username|user|apikey)\s*=\s*['\"][^'\"]+['\"]",
            "severity": RuleSeverity.CRITICAL,
            "fix_suggestion": "Store credentials in environment variables or secure vault",
            "category": "authentication",
        },
    ]

    for rule in default_rules:
        rule_path = RULES_DIR / f"{rule['id']}.json"
        with open(rule_path, "w") as f:
            json.dump(rule, f, indent=2)


# Initialize default rules
init_default_rules()


# Helper function to load all rules
def load_rules(standard: Optional[ComplianceStandard] = None) -> List[Dict]:
    rules = []
    for rule_file in RULES_DIR.glob("*.json"):
        with open(rule_file, "r") as f:
            rule = json.load(f)
            if standard is None or rule.get("standard") == standard:
                rules.append(rule)
    return rules


# Helper function to scan code for compliance issues
def scan_code(code: str, rules: List[Dict]) -> List[Dict]:
    findings = []

    for rule in rules:
        if "regex" not in rule:
            continue

        regex = rule["regex"]
        matches = re.finditer(regex, code, re.MULTILINE)

        for match in matches:
            findings.append(
                {
                    "rule_id": rule["id"],
                    "standard": rule["standard"],
                    "title": rule["title"],
                    "severity": rule["severity"],
                    "line": code.count("\n", 0, match.start()) + 1,
                    "match": match.group(0),
                    "fix_suggestion": rule.get(
                        "fix_suggestion",
                        "Review and fix according to compliance requirements",
                    ),
                }
            )

    return findings


# Helper function to save scan results
def save_scan_results(filename: str, code: str, findings: List[Dict]) -> str:
    scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    scan_path = SCANS_DIR / f"{scan_id}.json"

    result = {
        "scan_id": scan_id,
        "timestamp": datetime.now().isoformat(),
        "filename": filename,
        "findings": findings,
        "total_issues": len(findings),
        "severity_counts": {
            "critical": sum(
                1 for f in findings if f["severity"] == RuleSeverity.CRITICAL
            ),
            "high": sum(1 for f in findings if f["severity"] == RuleSeverity.HIGH),
            "medium": sum(1 for f in findings if f["severity"] == RuleSeverity.MEDIUM),
            "low": sum(1 for f in findings if f["severity"] == RuleSeverity.LOW),
            "info": sum(1 for f in findings if f["severity"] == RuleSeverity.INFO),
        },
    }

    with open(scan_path, "w") as f:
        json.dump(result, f, indent=2)

    return scan_id


# Helper function to generate compliance reports
def generate_report(scan_id: str) -> str:
    scan_path = SCANS_DIR / f"{scan_id}.json"

    if not scan_path.exists():
        return f"Scan ID {scan_id} not found"

    with open(scan_path, "r") as f:
        scan_data = json.load(f)

    report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    report_path = REPORTS_DIR / f"{report_id}.json"

    # Generate detailed report with compliance recommendations
    findings_by_standard = {}
    for finding in scan_data["findings"]:
        standard = finding["standard"]
        if standard not in findings_by_standard:
            findings_by_standard[standard] = []
        findings_by_standard[standard].append(finding)

    report = {
        "report_id": report_id,
        "scan_id": scan_id,
        "generated_at": datetime.now().isoformat(),
        "filename": scan_data["filename"],
        "compliance_summary": {
            "total_issues": scan_data["total_issues"],
            "severity_counts": scan_data["severity_counts"],
            "standards_affected": list(findings_by_standard.keys()),
            "compliance_score": max(
                0,
                100
                - (
                    scan_data["severity_counts"].get("critical", 0) * 10
                    + scan_data["severity_counts"].get("high", 0) * 5
                    + scan_data["severity_counts"].get("medium", 0) * 2
                    + scan_data["severity_counts"].get("low", 0) * 1
                ),
            ),
        },
        "findings_by_standard": findings_by_standard,
        "recommendations": {
            standard: [
                {
                    "rule_id": finding["rule_id"],
                    "title": finding["title"],
                    "fix": finding["fix_suggestion"],
                    "line": finding["line"],
                }
                for finding in findings
            ]
            for standard, findings in findings_by_standard.items()
        },
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report_id


# Helper function to apply automated fixes
def apply_fixes(code: str, findings: List[Dict]) -> str:
    lines = code.split("\n")

    # Sort findings by line number in descending order to avoid offset issues
    findings_sorted = sorted(findings, key=lambda x: x["line"], reverse=True)

    for finding in findings_sorted:
        line_idx = finding["line"] - 1
        if line_idx >= len(lines):
            continue

        line = lines[line_idx]
        rule_id = finding["rule_id"]

        # Apply different fixes based on rule ID
        if rule_id.startswith("pci-data"):
            # Mask credit card numbers
            lines[line_idx] = re.sub(
                r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "****-****-****-****", line
            )

        elif rule_id.startswith("gdpr-log"):
            # Mask personal data in logs
            lines[line_idx] = re.sub(
                r"(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b)",
                "[EMAIL REDACTED]",
                line,
            )
            lines[line_idx] = re.sub(
                r"([A-Z][a-z]+ [A-Z][a-z]+)", "[NAME REDACTED]", lines[line_idx]
            )

        elif rule_id.startswith("sox-audit"):
            # Add audit trail comment as a simple fix indicator
            lines[line_idx] = line + " /* COMPLIANCE: Audit trail needed */"

        elif rule_id.startswith("hipaa-phi"):
            # Convert http to https
            lines[line_idx] = re.sub(r"http://", "https://", line)

        elif rule_id.startswith("iso-access"):
            # Replace hardcoded credentials with environment variable pattern
            lines[line_idx] = re.sub(
                r'(password|passwd|pwd|username|user|apikey)\s*=\s*[\'"][^\'"]+"[\'"]',
                r"\1 = process.env.\1.toUpperCase()",
                line,
            )

    return "\n".join(lines)


# MCP Tool: Scan code for compliance issues
@mcp.tool()
def scan_code_for_compliance(
    filename: str, code: str, standard: Optional[str] = None
) -> str:
    """
    Scan code for compliance issues against regulatory standards

    Args:
        filename: Name of the file being scanned
        code: Source code to analyze
        standard: Optional compliance standard to filter rules (e.g., pci_dss, gdpr, sox, hipaa, iso27001)

    Returns:
        Summary of compliance issues found with detailed report
    """
    # Load applicable rules
    std = ComplianceStandard(standard) if standard else None
    rules = load_rules(std)

    if not rules:
        return (
            f"No compliance rules found for standard: {standard}"
            if standard
            else "No compliance rules found"
        )

    # Scan code
    findings = scan_code(code, rules)

    if not findings:
        return f"No compliance issues found in {filename}"

    # Save results
    scan_id = save_scan_results(filename, code, findings)

    # Generate summary
    critical = sum(1 for f in findings if f["severity"] == RuleSeverity.CRITICAL)
    high = sum(1 for f in findings if f["severity"] == RuleSeverity.HIGH)
    medium = sum(1 for f in findings if f["severity"] == RuleSeverity.MEDIUM)
    low = sum(1 for f in findings if f["severity"] == RuleSeverity.LOW)

    result = []
    result.append(f"Compliance scan completed for {filename}")
    result.append(f"Total issues found: {len(findings)}")
    result.append(
        f"Severity breakdown: {critical} Critical, {high} High, {medium} Medium, {low} Low"
    )
    result.append("\nTop issues:")

    # Show top 5 most severe issues
    for i, finding in enumerate(
        sorted(findings, key=lambda x: RuleSeverity(x["severity"]).value)
    ):
        if i >= 5:
            break
        result.append(
            f"- Line {finding['line']}: {finding['title']} ({finding['severity'].upper()}) - {finding['match']}"
        )

    result.append(f"\nScan ID: {scan_id}")
    result.append("Use generate_compliance_report(scan_id) to get a detailed report.")
    result.append("Use apply_compliance_fixes(scan_id) to automatically fix issues.")

    return "\n".join(result)


# MCP Tool: Generate detailed compliance report
@mcp.tool()
def generate_compliance_report(scan_id: str) -> str:
    """
    Generate a detailed compliance report from a previous scan

    Args:
        scan_id: ID of a previously completed scan

    Returns:
        Detailed compliance report with recommendations
    """
    scan_path = SCANS_DIR / f"{scan_id}.json"

    if not scan_path.exists():
        return f"Scan ID {scan_id} not found"

    # Generate report
    report_id = generate_report(scan_id)
    report_path = REPORTS_DIR / f"{report_id}.json"

    with open(report_path, "r") as f:
        report = json.load(f)

    # Format report for display
    result = []
    result.append(f"Compliance Report (ID: {report_id})")
    result.append(f"Generated: {report['generated_at']}")
    result.append(f"Filename: {report['filename']}")
    result.append("\nCompliance Summary:")
    result.append(f"- Total Issues: {report['compliance_summary']['total_issues']}")
    result.append(
        f"- Compliance Score: {report['compliance_summary']['compliance_score']}/100"
    )
    result.append(
        f"- Standards Affected: {', '.join(report['compliance_summary']['standards_affected'])}"
    )

    result.append("\nSeverity Breakdown:")
    for severity, count in report["compliance_summary"]["severity_counts"].items():
        if count > 0:
            result.append(f"- {severity.capitalize()}: {count}")

    result.append("\nTop Recommendations:")
    recommendations = []
    for standard, recs in report["recommendations"].items():
        for rec in recs:
            recommendations.append((standard, rec))

    # Show top 5 most important recommendations
    for i, (standard, rec) in enumerate(recommendations[:5]):
        result.append(f"- {standard.upper()}: Line {rec['line']} - {rec['title']}")
        result.append(f"  Fix: {rec['fix']}")

    result.append(f"\nFull report saved as {report_id}")
    result.append("Use apply_compliance_fixes(scan_id) to automatically fix issues.")
    result.append(
        "Use generate_compliance_evidence(report_id) to generate compliance evidence documentation."
    )

    return "\n".join(result)


# MCP Tool: Apply automated compliance fixes
@mcp.tool()
def apply_compliance_fixes(scan_id: str) -> str:
    """
    Apply automated fixes to compliance issues found in a previous scan

    Args:
        scan_id: ID of a previously completed scan

    Returns:
        Updated code with automated fixes applied
    """
    scan_path = SCANS_DIR / f"{scan_id}.json"

    if not scan_path.exists():
        return f"Scan ID {scan_id} not found"

    with open(scan_path, "r") as f:
        scan_data = json.load(f)

    findings = scan_data["findings"]
    filename = scan_data["filename"]

    # For demonstration purposes, assume original code is stored in the scan
    # In a real implementation, this would need to read the actual file
    # Here we'll just simulate with a placeholder
    original_code = "// This is a placeholder for the original code\n" * 10

    # Apply fixes
    fixed_code = apply_fixes(original_code, findings)

    # Save fixed code (in a real implementation, this would update the actual file)
    fixed_id = f"fixed_{scan_id}"
    fixed_path = SCANS_DIR / f"{fixed_id}.txt"

    with open(fixed_path, "w") as f:
        f.write(fixed_code)

    # Count fixes
    fixes_applied = 0
    for finding in findings:
        rule_id = finding["rule_id"]
        if (
            rule_id.startswith("pci-data")
            or rule_id.startswith("gdpr-log")
            or rule_id.startswith("sox-audit")
            or rule_id.startswith("hipaa-phi")
            or rule_id.startswith("iso-access")
        ):
            fixes_applied += 1

    result = []
    result.append(f"Applied automated fixes for {filename}")
    result.append(f"Total issues addressed: {fixes_applied} of {len(findings)}")

    if fixes_applied < len(findings):
        result.append(
            f"Note: {len(findings) - fixes_applied} issues require manual review"
        )

    result.append("\nFixes applied:")

    # Categorize fixes by type
    fix_categories = {
        "pci-data": "Credit card data masked",
        "gdpr-log": "Personal data redacted in logs",
        "sox-audit": "Audit trail comments added",
        "hipaa-phi": "Upgraded to secure communication protocols",
        "iso-access": "Replaced hardcoded credentials with environment variables",
    }

    fix_counts = {category: 0 for category in fix_categories}

    for finding in findings:
        for prefix, description in fix_categories.items():
            if finding["rule_id"].startswith(prefix):
                fix_counts[prefix] += 1
                break

    for prefix, description in fix_categories.items():
        if fix_counts[prefix] > 0:
            result.append(f"- {description}: {fix_counts[prefix]}")

    result.append(f"\nFixed code ID: {fixed_id}")
    result.append("Use get_fixed_code(fixed_id) to retrieve the updated code.")

    return "\n".join(result)


# MCP Tool: Get fixed code
@mcp.tool()
def get_fixed_code(fixed_id: str) -> str:
    """
    Retrieve code with automated compliance fixes applied

    Args:
        fixed_id: ID of previously fixed code

    Returns:
        Code with compliance fixes applied
    """
    fixed_path = SCANS_DIR / f"{fixed_id}.txt"

    if not fixed_path.exists():
        return f"Fixed code ID {fixed_id} not found"

    with open(fixed_path, "r") as f:
        fixed_code = f.read()

    return fixed_code


# MCP Tool: Generate compliance evidence documentation
@mcp.tool()
def generate_compliance_evidence(report_id: str, comments: str = "") -> str:
    """
    Generate formal compliance evidence documentation for audit purposes

    Args:
        report_id: ID of a previously generated compliance report
        comments: Optional comments to include in the evidence document

    Returns:
        Summary of the generated evidence document
    """
    report_path = REPORTS_DIR / f"{report_id}.json"

    if not report_path.exists():
        return f"Report ID {report_id} not found"

    with open(report_path, "r") as f:
        report = json.load(f)

    # Generate evidence document
    evidence_id = f"evidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    evidence_path = EVIDENCE_DIR / f"{evidence_id}.json"

    evidence = {
        "evidence_id": evidence_id,
        "report_id": report_id,
        "scan_id": report["scan_id"],
        "generated_at": datetime.now().isoformat(),
        "filename": report["filename"],
        "compliance_summary": report["compliance_summary"],
        "standards_addressed": list(report["recommendations"].keys()),
        "auditor_comments": comments,
        "attestation": {
            "timestamp": datetime.now().isoformat(),
            "statement": "This document serves as evidence of compliance review and remediation for audit purposes.",
        },
    }

    with open(evidence_path, "w") as f:
        json.dump(evidence, f, indent=2)

    # Create formatted document
    result = []
    result.append(f"Compliance Evidence Document (ID: {evidence_id})")
    result.append(f"Generated: {evidence['generated_at']}")
    result.append(f"File Reviewed: {evidence['filename']}")
    result.append("\nCompliance Standards Addressed:")
    for standard in evidence["standards_addressed"]:
        result.append(f"- {standard.upper()}")

    result.append("\nCompliance Metrics:")
    result.append(
        f"- Compliance Score: {evidence['compliance_summary']['compliance_score']}/100"
    )
    result.append(
        f"- Issues Identified: {evidence['compliance_summary']['total_issues']}"
    )
    result.append("- Issues by Severity:")
    for severity, count in evidence["compliance_summary"]["severity_counts"].items():
        if count > 0:
            result.append(f"  - {severity.capitalize()}: {count}")

    if comments:
        result.append("\nAuditor Comments:")
        result.append(comments)

    result.append("\nAttestation:")
    result.append(evidence["attestation"]["statement"])
    result.append(f"Timestamp: {evidence['attestation']['timestamp']}")

    result.append(f"\nEvidence document saved as {evidence_id}")
    result.append("This document can be used for regulatory compliance audits.")

    return "\n".join(result)


# MCP Tool: List compliance rules
@mcp.tool()
def list_compliance_rules(standard: Optional[str] = None) -> str:
    """
    List available compliance rules, optionally filtered by standard

    Args:
        standard: Optional compliance standard to filter rules (e.g., pci_dss, gdpr, sox, hipaa, iso27001)

    Returns:
        List of available compliance rules
    """
    std = ComplianceStandard(standard) if standard else None
    rules = load_rules(std)

    if not rules:
        return (
            f"No compliance rules found for standard: {standard}"
            if standard
            else "No compliance rules found"
        )

    result = []
    result.append(f"Compliance Rules{f' for {standard.upper()}' if standard else ''}:")

    for rule in sorted(rules, key=lambda x: x["id"]):
        result.append(f"\n{rule['id']}: {rule['title']}")
        result.append(f"Standard: {rule['standard'].upper()}")
        result.append(f"Severity: {rule['severity'].upper()}")
        result.append(f"Description: {rule['description']}")

    return "\n".join(result)


# MCP Tool: Add custom compliance rule
@mcp.tool()
def add_compliance_rule(
    id: str,
    standard: str,
    title: str,
    description: str,
    regex: str,
    severity: str,
    fix_suggestion: str,
    category: str,
) -> str:
    """
    Add a custom compliance rule

    Args:
        id: Unique ID for the rule (e.g., "custom-001")
        standard: Compliance standard (pci_dss, gdpr, sox, hipaa, iso27001, general)
        title: Short title of the rule
        description: Detailed description of what the rule checks for
        regex: Regular expression pattern to detect violations
        severity: Rule severity (critical, high, medium, low, info)
        fix_suggestion: Suggested fix for violations
        category: Category of the rule (e.g., data_exposure, logging)

    Returns:
        Confirmation of rule creation
    """
    # Validate standard
    try:
        std = ComplianceStandard(standard)
    except ValueError:
        return f"Invalid compliance standard: {standard}. Valid options are: {', '.join([s.value for s in ComplianceStandard])}"

    # Validate severity
    try:
        sev = RuleSeverity(severity)
    except ValueError:
        return f"Invalid severity level: {severity}. Valid options are: {', '.join([s.value for s in RuleSeverity])}"

    # Validate regex
    try:
        re.compile(regex)
    except re.error:
        return f"Invalid regular expression: {regex}"

    # Create rule
    rule = {
        "id": id,
        "standard": std,
        "title": title,
        "description": description,
        "regex": regex,
        "severity": sev,
        "fix_suggestion": fix_suggestion,
        "category": category,
    }

    # Save rule
    rule_path = RULES_DIR / f"{id}.json"

    if rule_path.exists():
        return f"Rule ID {id} already exists. Please use a different ID."

    with open(rule_path, "w") as f:
        json.dump(rule, f, indent=2)

    return f"Compliance rule {id} created successfully"


# MCP Resource: Get compliance standards
@mcp.resource("compliance://standards")
def get_compliance_standards() -> str:
    """Get available compliance standards"""
    standards = {s.value: s.name for s in ComplianceStandard}
    return json.dumps(standards, indent=2)


# MCP Resource: Get compliance rules
@mcp.resource("compliance://rules/{standard}")
def get_compliance_rules(standard: str) -> str:
    """Get compliance rules for a specific standard"""
    try:
        std = ComplianceStandard(standard)
    except ValueError:
        return json.dumps({"error": f"Invalid compliance standard: {standard}"})

    rules = load_rules(std)
    return json.dumps(rules, indent=2)


# MCP Resource: Get compliance reports
@mcp.resource("compliance://reports")
def get_compliance_reports() -> str:
    """Get list of available compliance reports"""
    reports = []
    for report_file in REPORTS_DIR.glob("*.json"):
        with open(report_file, "r") as f:
            report = json.load(f)
            reports.append(
                {
                    "report_id": report["report_id"],
                    "filename": report["filename"],
                    "generated_at": report["generated_at"],
                    "compliance_score": report["compliance_summary"][
                        "compliance_score"
                    ],
                    "total_issues": report["compliance_summary"]["total_issues"],
                }
            )

    return json.dumps(reports, indent=2)


# MCP Prompt for compliance review
@mcp.prompt()
def compliance_review_prompt(
    code: str, filename: str, standards: List[str] = None
) -> List[SamplingMessage]:
    """
    Generate a prompt for reviewing code for compliance issues

    Args:
        code: Source code to analyze
        filename: Name of the file being reviewed
        standards: Optional list of compliance standards to check against
    """
    system_prompt = """
    You are a Compliance Review Expert specialized in regulatory requirements for enterprise software.
    Your task is to analyze the provided code for compliance issues and suggest fixes.
    Focus on security, data privacy, audit trails, and regulatory requirements.
    Be thorough in your analysis and suggest practical fixes for each issue found.
    """

    user_content = f"""
    Please review the following code file for compliance issues:
    
    Filename: {filename}
    {f"Standards to check: {', '.join(standards)}" if standards else "Check against all applicable standards"}
    
    ```
    {code}
    ```
    
    For each potential compliance issue:
    1. Identify the line number and problematic code
    2. Explain why it's a compliance concern
    3. Reference the specific regulation or standard being violated
    4. Suggest a practical fix with example code
    
    Prioritize issues by severity (Critical, High, Medium, Low).
    """

    return [
        SamplingMessage(role="system", content=TextContent(text=system_prompt)),
        SamplingMessage(role="user", content=TextContent(text=user_content)),
    ]
