import getpass
import json
import os
from typing import Any, Dict

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# Security vulnerabilities database
SECURITY_VULNERABILITIES = {
    "missing_authentication": {
        "title": "Missing Authentication",
        "severity": "HIGH",
        "description": "Endpoints accessible without proper authentication",
        "remediation": "Implement OAuth, API key, or JWT-based authentication",
        "owasp_reference": "https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/",
    },
    "missing_rate_limiting": {
        "title": "Missing Rate Limiting",
        "severity": "MEDIUM",
        "description": "API does not implement rate limiting, increasing risk of DoS attacks",
        "remediation": "Implement rate limiting headers and enforcement",
        "owasp_reference": "https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/",
    },
    "sensitive_data_exposure": {
        "title": "Sensitive Data Exposure",
        "severity": "HIGH",
        "description": "API may expose sensitive data in responses",
        "remediation": "Implement data minimization, field filtering, and proper data classification",
        "owasp_reference": "https://owasp.org/API-Security/editions/2023/en/0xa3-broken-authentication/",
    },
    "insecure_communication": {
        "title": "Insecure Communication",
        "severity": "CRITICAL",
        "description": "API uses non-HTTPS endpoints",
        "remediation": "Enforce HTTPS for all API endpoints",
        "owasp_reference": "https://owasp.org/API-Security/editions/2023/en/0xa7-security-misconfiguration/",
    },
    "missing_cors": {
        "title": "Missing CORS Headers",
        "severity": "MEDIUM",
        "description": "API does not implement proper CORS headers",
        "remediation": "Implement appropriate CORS headers to restrict cross-origin requests",
        "owasp_reference": "https://owasp.org/API-Security/editions/2023/en/0xa7-security-misconfiguration/",
    },
    "injection_risk": {
        "title": "Injection Risk",
        "severity": "HIGH",
        "description": "Parameters may be vulnerable to injection attacks",
        "remediation": "Implement proper input validation and parameterized queries",
        "owasp_reference": "https://owasp.org/API-Security/editions/2023/en/0xa8-security-logging-monitoring-failures/",
    },
}

# Best practices for securing APIs
SECURITY_BEST_PRACTICES = [
    {
        "category": "Authentication",
        "practices": [
            "Use OAuth 2.0 or JWT for token-based authentication",
            "Implement short-lived tokens with refresh capabilities",
            "Use strong password policies for credential-based auth",
            "Enforce MFA for sensitive operations",
        ],
    },
    {
        "category": "Authorization",
        "practices": [
            "Implement role-based access control (RBAC)",
            "Use principle of least privilege",
            "Check object-level permissions (not just endpoint access)",
            "Validate user permissions on every request",
        ],
    },
    {
        "category": "Input Validation",
        "practices": [
            "Validate all input parameters (type, format, length)",
            "Implement schema validation for request bodies",
            "Use allowlists for acceptable values where possible",
            "Sanitize inputs to prevent injection attacks",
        ],
    },
    {
        "category": "Rate Limiting & Throttling",
        "practices": [
            "Implement per-user/per-client rate limits",
            "Use token bucket or leaky bucket algorithms",
            "Include rate limit headers in responses (X-RateLimit-*)",
            "Implement graduated throttling for suspicious activity",
        ],
    },
    {
        "category": "Sensitive Data",
        "practices": [
            "Encrypt sensitive data in transit and at rest",
            "Implement data minimization principles",
            "Use field-level filtering to limit data exposure",
            "Mask or tokenize PII and sensitive information",
        ],
    },
]

mcp = FastMCP("API Security Audit")


@mcp.tool()
def audit_openapi_security(openapi_json: str) -> str:
    """Perform a security audit on an OpenAPI specification.

    Args:
        openapi_json: OpenAPI specification as JSON string

    Returns:
        Security audit report with findings and recommendations
    """
    try:
        openapi = json.loads(openapi_json)
    except json.JSONDecodeError:
        return "❌ Invalid JSON: The provided OpenAPI specification is not valid JSON."

    # Initialize audit results
    audit_results = {"vulnerabilities": [], "warnings": [], "recommendations": []}

    # Get API info
    api_title = openapi.get("info", {}).get("title", "Unknown API")

    # Check server URLs for HTTPS
    for server in openapi.get("servers", []):
        url = server.get("url", "")
        if url.startswith("http://"):
            audit_results["vulnerabilities"].append(
                {
                    "type": "insecure_communication",
                    "location": f"Server URL: {url}",
                    "details": "Non-HTTPS URL detected",
                }
            )

    # Check security schemes
    security_schemes = openapi.get("components", {}).get("securitySchemes", {})
    if not security_schemes:
        audit_results["vulnerabilities"].append(
            {
                "type": "missing_authentication",
                "location": "securitySchemes",
                "details": "No security schemes defined",
            }
        )

    # Check global security
    if "security" not in openapi:
        audit_results["warnings"].append(
            {
                "type": "missing_authentication",
                "location": "global",
                "details": "No global security requirements defined",
            }
        )

    # Check paths and operations
    for path, path_item in openapi.get("paths", {}).items():
        # Check for path parameters potential injection
        if "{" in path and "}" in path:
            audit_results["warnings"].append(
                {
                    "type": "injection_risk",
                    "location": f"Path: {path}",
                    "details": "Path parameter detected, ensure proper validation",
                }
            )

        # Check each operation
        for method, operation in path_item.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                continue

            operation_id = operation.get("operationId", f"{method} {path}")

            # Check operation security
            if "security" not in operation:
                # Check if this is a public endpoint
                is_public = False
                for tag in operation.get("tags", []):
                    if "public" in tag.lower():
                        is_public = True

                if not is_public:
                    audit_results["vulnerabilities"].append(
                        {
                            "type": "missing_authentication",
                            "location": f"{method.upper()} {path}",
                            "details": "No security requirements defined for non-public endpoint",
                        }
                    )

            # Check for potential sensitive data
            sensitive_fields = [
                "password",
                "token",
                "secret",
                "key",
                "auth",
                "credit",
                "card",
                "ssn",
                "social",
                "passport",
                "license",
                "dob",
                "birth",
            ]

            # Check responses for sensitive data
            for status, response in operation.get("responses", {}).items():
                content = response.get("content", {}).get("application/json", {})
                schema = content.get("schema", {})

                if "properties" in schema:
                    for prop_name in schema["properties"]:
                        if any(
                            sensitive in prop_name.lower()
                            for sensitive in sensitive_fields
                        ):
                            audit_results["warnings"].append(
                                {
                                    "type": "sensitive_data_exposure",
                                    "location": f"{method.upper()} {path} response",
                                    "details": f"Potentially sensitive field in response: {prop_name}",
                                }
                            )

            # Check for rate limiting headers in responses
            has_rate_limit_headers = False
            for status, response in operation.get("responses", {}).items():
                headers = response.get("headers", {})
                if any(
                    "ratelimit" in header.lower() or "rate-limit" in header.lower()
                    for header in headers
                ):
                    has_rate_limit_headers = True
                    break

            if not has_rate_limit_headers:
                audit_results["warnings"].append(
                    {
                        "type": "missing_rate_limiting",
                        "location": f"{method.upper()} {path}",
                        "details": "No rate limiting headers found in responses",
                    }
                )

    # Generate security recommendations
    if not security_schemes:
        audit_results["recommendations"].append(
            {
                "category": "Authentication",
                "details": "Implement OAuth 2.0 or JWT-based authentication",
            }
        )

    has_oauth = any(
        scheme.get("type") == "oauth2" for scheme in security_schemes.values()
    )
    if not has_oauth:
        audit_results["recommendations"].append(
            {
                "category": "Authentication",
                "details": "Consider using OAuth 2.0 for more robust authentication",
            }
        )

    # Generate report
    report = f"# Security Audit Report: {api_title}\n\n"

    # Summary section
    vulnerability_count = len(audit_results["vulnerabilities"])
    warning_count = len(audit_results["warnings"])

    if vulnerability_count == 0 and warning_count == 0:
        report += "✅ **PASSED**: No security issues found.\n\n"
    elif vulnerability_count == 0:
        report += f"⚠️ **PASSED WITH WARNINGS**: {warning_count} potential security concerns.\n\n"
    else:
        report += f"❌ **FAILED**: {vulnerability_count} security vulnerabilities, {warning_count} warnings.\n\n"

    # Vulnerabilities section
    if audit_results["vulnerabilities"]:
        report += "## Critical Security Vulnerabilities\n\n"
        for vuln in audit_results["vulnerabilities"]:
            vuln_info = SECURITY_VULNERABILITIES.get(vuln["type"], {})
            report += f"### {vuln_info.get('title', vuln['type'])}\n\n"
            report += f"**Severity**: {vuln_info.get('severity', 'UNKNOWN')}\n\n"
            report += f"**Location**: {vuln['location']}\n\n"
            report += f"**Details**: {vuln['details']}\n\n"
            report += f"**Remediation**: {vuln_info.get('remediation', 'Contact security team')}\n\n"
            report += f"**Reference**: {vuln_info.get('owasp_reference', '')}\n\n"

    # Warnings section
    if audit_results["warnings"]:
        report += "## Security Warnings\n\n"
        for warning in audit_results["warnings"]:
            vuln_info = SECURITY_VULNERABILITIES.get(warning["type"], {})
            report += f"### {vuln_info.get('title', warning['type'])}\n\n"
            report += f"**Location**: {warning['location']}\n\n"
            report += f"**Details**: {warning['details']}\n\n"
            report += f"**Remediation**: {vuln_info.get('remediation', 'Review implementation')}\n\n"

    # Recommendations section
    if audit_results["recommendations"]:
        report += "## Recommendations\n\n"
        for rec in audit_results["recommendations"]:
            report += f"- [{rec['category']}] {rec['details']}\n"

    return report


@mcp.tool()
def get_security_best_practices() -> str:
    """Get security best practices for API development.

    Returns:
        Comprehensive list of API security best practices
    """
    report = "# API Security Best Practices\n\n"

    for category in SECURITY_BEST_PRACTICES:
        report += f"## {category['category']}\n\n"
        for practice in category["practices"]:
            report += f"- {practice}\n"
        report += "\n"

    report += """## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [OAuth 2.0 Guides](https://oauth.net/2/)
- [JWT Best Practices](https://auth0.com/docs/secure/tokens/json-web-tokens/json-web-token-best-practices)
- [API Security Checklist](https://github.com/shieldfy/API-Security-Checklist)
"""

    return report


@mcp.tool()
def analyze_auth_implementation(
    auth_type: str, implementation_details: Dict[str, Any]
) -> str:
    """Analyze an API authentication implementation for security issues.

    Args:
        auth_type: Type of authentication (oauth2, jwt, api_key, basic)
        implementation_details: Details of the authentication implementation

    Returns:
        Analysis of the authentication implementation with recommendations
    """
    # Initialize analysis results
    analysis = {"strengths": [], "weaknesses": [], "recommendations": []}

    # Analyze based on auth type
    auth_type = auth_type.lower()

    if auth_type == "oauth2":
        # Check OAuth 2.0 implementation
        if implementation_details.get("grant_types", []):
            grant_types = implementation_details["grant_types"]

            # Check for secure grant types
            if "authorization_code" in grant_types:
                analysis["strengths"].append(
                    "Uses Authorization Code grant type, which is recommended for web applications"
                )

            if "password" in grant_types:
                analysis["weaknesses"].append(
                    "Uses Password grant type, which is less secure and not recommended"
                )
                analysis["recommendations"].append(
                    "Replace Password grant with Authorization Code or PKCE flow"
                )

            if "implicit" in grant_types:
                analysis["weaknesses"].append(
                    "Uses Implicit grant type, which has security vulnerabilities"
                )
                analysis["recommendations"].append(
                    "Replace Implicit grant with Authorization Code with PKCE"
                )

        # Check token settings
        token_lifetime = implementation_details.get("token_lifetime_seconds", 0)
        if token_lifetime > 3600:  # 1 hour
            analysis["weaknesses"].append(
                f"Long-lived access tokens ({token_lifetime} seconds) increase security risk if compromised"
            )
            analysis["recommendations"].append(
                "Reduce access token lifetime to 1 hour or less"
            )
        elif token_lifetime > 0:
            analysis["strengths"].append(
                f"Token lifetime ({token_lifetime} seconds) is reasonable"
            )

        # Check refresh token
        if implementation_details.get("uses_refresh_token", False):
            analysis["strengths"].append(
                "Uses refresh tokens, which is good for security and user experience"
            )

            refresh_token_lifetime = implementation_details.get(
                "refresh_token_lifetime_seconds", 0
            )
            if refresh_token_lifetime > 2592000:  # 30 days
                analysis["weaknesses"].append(
                    f"Long-lived refresh tokens ({refresh_token_lifetime} seconds) increase security risk"
                )
                analysis["recommendations"].append(
                    "Reduce refresh token lifetime to 30 days or less"
                )
        else:
            analysis["recommendations"].append(
                "Implement refresh tokens with reasonable expiration time"
            )

        # Check secure storage
        if not implementation_details.get("secure_token_storage", True):
            analysis["weaknesses"].append("Token storage may not be secure")
            analysis["recommendations"].append(
                "Store tokens in secure HTTP-only cookies or secure browser storage"
            )

    elif auth_type == "jwt":
        # Check JWT implementation
        if implementation_details.get("signing_algorithm", "").lower() in [
            "none",
            "hs256",
        ]:
            analysis["weaknesses"].append(
                f"Using weak signing algorithm: {implementation_details.get('signing_algorithm')}"
            )
            analysis["recommendations"].append("Use RS256 or ES256 for JWT signature")
        elif implementation_details.get("signing_algorithm", "").lower() in [
            "rs256",
            "es256",
        ]:
            analysis["strengths"].append(
                f"Using strong signing algorithm: {implementation_details.get('signing_algorithm')}"
            )

        # Check claims
        required_claims = ["iss", "sub", "exp", "iat"]
        included_claims = implementation_details.get("claims", [])

        missing_claims = [
            claim for claim in required_claims if claim not in included_claims
        ]
        if missing_claims:
            analysis["weaknesses"].append(
                f"Missing essential JWT claims: {', '.join(missing_claims)}"
            )
            analysis["recommendations"].append(
                f"Include {', '.join(missing_claims)} claims in your JWTs"
            )

        if "jti" not in included_claims:
            analysis["recommendations"].append(
                "Consider adding 'jti' (JWT ID) claim for token revocation capabilities"
            )

        # Check token expiration
        token_lifetime = implementation_details.get("token_lifetime_seconds", 0)
        if token_lifetime > 3600:  # 1 hour
            analysis["weaknesses"].append(
                f"Long-lived JWTs ({token_lifetime} seconds) increase security risk if compromised"
            )
            analysis["recommendations"].append("Reduce JWT lifetime to 1 hour or less")
        elif token_lifetime > 0:
            analysis["strengths"].append(
                f"Token lifetime ({token_lifetime} seconds) is reasonable"
            )

    elif auth_type == "api_key":
        # Check API key implementation
        key_length = implementation_details.get("key_length", 0)
        if key_length < 32:
            analysis["weaknesses"].append(
                f"API key length ({key_length} characters) is too short"
            )
            analysis["recommendations"].append(
                "Use API keys with at least 32 characters"
            )
        elif key_length >= 32:
            analysis["strengths"].append(
                f"API key length ({key_length} characters) is adequate"
            )

        # Check transmission
        if implementation_details.get("transmit_in", "").lower() == "query":
            analysis["weaknesses"].append(
                "API keys transmitted in query parameters can be leaked in logs and browser history"
            )
            analysis["recommendations"].append(
                "Transmit API keys in authorization header instead"
            )
        elif implementation_details.get("transmit_in", "").lower() == "header":
            analysis["strengths"].append(
                "API keys transmitted in headers is good practice"
            )

        # Check for rate limiting
        if not implementation_details.get("has_rate_limiting", False):
            analysis["weaknesses"].append("API key usage is not rate limited")
            analysis["recommendations"].append(
                "Implement rate limiting for API key usage"
            )

    elif auth_type == "basic":
        # Basic auth is generally not recommended for APIs
        analysis["weaknesses"].append(
            "Basic Authentication transmits credentials with every request"
        )
        analysis["weaknesses"].append(
            "Basic Authentication doesn't support token expiration or refresh"
        )
        analysis["recommendations"].append(
            "Replace Basic Authentication with OAuth 2.0 or JWT"
        )

        # Check for TLS
        if implementation_details.get("requires_tls", True):
            analysis["strengths"].append(
                "Requires TLS, which is mandatory for Basic Authentication"
            )
        else:
            analysis["weaknesses"].append(
                "Basic Authentication without TLS is critically insecure"
            )
            analysis["recommendations"].append("Enable HTTPS/TLS for all API endpoints")

    # Generate report
    report = f"# Authentication Analysis: {auth_type.upper()}\n\n"

    if not analysis["weaknesses"]:
        report += "✅ **STRONG IMPLEMENTATION**: No significant security issues identified.\n\n"
    elif len(analysis["weaknesses"]) <= 2:
        report += (
            "⚠️ **MODERATE IMPLEMENTATION**: Some security improvements recommended.\n\n"
        )
    else:
        report += (
            "❌ **WEAK IMPLEMENTATION**: Significant security issues identified.\n\n"
        )

    # Strengths section
    if analysis["strengths"]:
        report += "## Strengths\n\n"
        for strength in analysis["strengths"]:
            report += f"- ✅ {strength}\n"
        report += "\n"

    # Weaknesses section
    if analysis["weaknesses"]:
        report += "## Weaknesses\n\n"
        for weakness in analysis["weaknesses"]:
            report += f"- ❌ {weakness}\n"
        report += "\n"

    # Recommendations section
    if analysis["recommendations"]:
        report += "## Recommendations\n\n"
        for recommendation in analysis["recommendations"]:
            report += f"- 🛡️ {recommendation}\n"
        report += "\n"

    # Best practices for the specific auth type
    report += f"## {auth_type.upper()} Best Practices\n\n"

    if auth_type == "oauth2":
        report += """- Use Authorization Code flow with PKCE for most applications
- Store tokens securely (HTTP-only cookies or secure storage)
- Keep access token lifetime short (minutes to hours)
- Implement refresh tokens with reasonable expiration
- Validate all tokens on the server side
- Include audience and scopes in tokens
- Implement token revocation endpoints
"""
    elif auth_type == "jwt":
        report += """- Use asymmetric algorithms like RS256 or ES256
- Include standard claims: iss, sub, exp, iat
- Keep tokens short-lived (minutes to hours)
- Don't store sensitive data in JWTs (they're base64 encoded, not encrypted)
- Implement server-side validation of all tokens
- Consider implementing a token blacklist for revocation
- Rotate signing keys periodically
"""
    elif auth_type == "api_key":
        report += """- Generate long, random API keys (≥32 characters)
- Transmit only in authorization headers
- Implement rate limiting and usage monitoring
- Allow customers to generate multiple keys and revoke them
- Don't expose API keys in client-side code
- Implement different keys for different environments
- Consider key rotation policies
"""
    elif auth_type == "basic":
        report += """- Use only over HTTPS/TLS connections
- Combine with IP restrictions where possible
- Implement strong password policies
- Consider rate limiting to prevent brute force attacks
- For production APIs, migrate to token-based authentication
- Implement proper HTTP 401 responses with WWW-Authenticate headers
"""

    return report


@mcp.tool()
def generate_security_checklist(api_name: str) -> str:
    """Generate a security checklist for API implementation.

    Args:
        api_name: Name of the API

    Returns:
        Security implementation checklist
    """
    checklist = f"# Security Implementation Checklist: {api_name}\n\n"

    # Authentication section
    checklist += """## Authentication
- [ ] Implement OAuth 2.0 or JWT-based authentication
- [ ] Use secure token generation and validation
- [ ] Implement proper token expiration and refresh
- [ ] Store credentials securely (hashed and salted)
- [ ] Implement account lockout after failed attempts
- [ ] Require strong passwords (if applicable)
- [ ] Implement MFA for sensitive operations

## Authorization
- [ ] Implement role-based access control (RBAC)
- [ ] Validate permissions for every request
- [ ] Check object-level permissions (not just endpoint access)
- [ ] Use principle of least privilege
- [ ] Implement proper access control for all resources
- [ ] Log authorization failures

## Data Protection
- [ ] Use HTTPS for all endpoints
- [ ] Implement field-level encryption for sensitive data
- [ ] Apply data minimization principle in responses
- [ ] Mask or truncate sensitive values in logs
- [ ] Implement proper data classification 
- [ ] Handle sensitive data according to regulations (GDPR, CCPA, etc.)

## Input Validation
- [ ] Validate all input parameters (type, format, length)
- [ ] Implement schema validation for request bodies
- [ ] Sanitize inputs to prevent injection attacks
- [ ] Validate business logic constraints
- [ ] Implement proper error handling without exposing system details

## API Protection
- [ ] Implement rate limiting
- [ ] Set reasonable timeouts for all operations
- [ ] Include security headers (CORS, Content-Security-Policy, etc.)
- [ ] Monitor for unusual patterns and potential attacks
- [ ] Implement proper logging for security events
- [ ] Set up alerting for potential security incidents

## Development Lifecycle
- [ ] Perform security code reviews
- [ ] Run static code analysis tools
- [ ] Conduct regular security testing
- [ ] Implement proper secret management
- [ ] Document security-related configurations
- [ ] Create an incident response plan
"""

    # Implementation roadmap
    checklist += """
## Security Implementation Roadmap

### Phase 1: Foundation
1. HTTPS implementation
2. Basic authentication and authorization
3. Input validation framework
4. Security headers

### Phase 2: Enhanced Security
1. Comprehensive authentication implementation
2. Fine-grained authorization rules
3. Rate limiting and throttling
4. Enhanced logging and monitoring

### Phase 3: Advanced Protection
1. Advanced threat detection
2. Security analytics
3. Automated security testing
4. Comprehensive security documentation
"""

    return checklist
