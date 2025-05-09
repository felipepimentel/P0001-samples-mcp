import getpass
import os
from datetime import datetime
from typing import Optional

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# Sample API versions and compatibility data
API_VERSIONS = [
    {
        "version": "v1",
        "released_date": "2022-01-15",
        "status": "deprecated",
        "sunset_date": "2023-12-31",
        "breaking_changes": [],
        "major_features": [
            "Basic CRUD operations for users and products",
            "Authentication via API keys",
        ],
    },
    {
        "version": "v2",
        "released_date": "2022-08-22",
        "status": "stable",
        "sunset_date": None,
        "breaking_changes": [
            {
                "endpoint": "/users",
                "change": "Response format changed: 'name' field split into 'firstName' and 'lastName'",
                "migration_guide": "Update clients to handle the new name fields",
            },
            {
                "endpoint": "/products",
                "change": "Required fields added: 'category' and 'sku'",
                "migration_guide": "Ensure all product creation includes the new required fields",
            },
        ],
        "major_features": [
            "Enhanced query capabilities",
            "OAuth 2.0 authentication support",
            "Pagination and sorting for collection endpoints",
        ],
    },
    {
        "version": "v3",
        "released_date": "2023-04-10",
        "status": "stable",
        "sunset_date": None,
        "breaking_changes": [
            {
                "endpoint": "/orders",
                "change": "New required field 'shippingDetails' with address validation",
                "migration_guide": "Update order creation to include shipping details object",
            },
            {
                "endpoint": "/auth",
                "change": "Removed API key authentication, now requires OAuth 2.0",
                "migration_guide": "Migrate all clients to use OAuth 2.0 authentication flow",
            },
        ],
        "major_features": [
            "GraphQL support for complex queries",
            "Webhook notifications for resource changes",
            "Enhanced error responses with more details",
        ],
    },
    {
        "version": "v4-beta",
        "released_date": "2023-10-05",
        "status": "beta",
        "sunset_date": None,
        "breaking_changes": [
            {
                "endpoint": "all endpoints",
                "change": "Response envelope structure changed to include metadata",
                "migration_guide": "Update clients to extract data from the 'data' field in responses",
            }
        ],
        "major_features": [
            "Real-time updates via Server-Sent Events",
            "Enhanced analytics endpoints",
            "Bulk operations for all resources",
        ],
    },
]

# Compatibility matrix between versions
COMPATIBILITY_MATRIX = {
    "client_v1": {
        "server_v1": "full",
        "server_v2": "partial",
        "server_v3": "none",
        "server_v4-beta": "none",
    },
    "client_v2": {
        "server_v1": "none",
        "server_v2": "full",
        "server_v3": "partial",
        "server_v4-beta": "partial",
    },
    "client_v3": {
        "server_v1": "none",
        "server_v2": "none",
        "server_v3": "full",
        "server_v4-beta": "partial",
    },
}

# Best practices for API versioning
VERSIONING_BEST_PRACTICES = [
    {
        "category": "Version Strategy",
        "practices": [
            "Use semantic versioning (major.minor.patch) for internal version tracking",
            "Expose simplified version identifiers to clients (v1, v2, v3)",
            "Include version in URL path for clearest compatibility (/v1/resource)",
            "Avoid using query parameters or headers for versioning as they're less visible",
        ],
    },
    {
        "category": "Change Management",
        "practices": [
            "Clearly define what constitutes a breaking vs. non-breaking change",
            "Document all changes, breaking or not, in a changelog",
            "Provide migration guides for breaking changes",
            "Never make breaking changes within the same version",
        ],
    },
    {
        "category": "Deprecation Policy",
        "practices": [
            "Announce deprecation at least 6-12 months before sunset",
            "Add Deprecated headers to responses when using deprecated features",
            "Provide clear documentation of sunset dates for deprecated versions",
            "Keep deprecated versions running at least until announced sunset date",
            "Monitor usage of deprecated features to identify clients needing to migrate",
        ],
    },
    {
        "category": "Documentation",
        "practices": [
            "Maintain separate documentation for each API version",
            "Highlight differences between versions",
            "Include version information in all API references and examples",
            "Provide SDKs or client libraries that match your API versions",
        ],
    },
]

mcp = FastMCP("API Versioning Manager")


@mcp.tool()
def get_api_version_status() -> str:
    """Get status report for all API versions.

    Returns:
        Status report for all API versions
    """
    # Build the report
    report = "# API Version Status Report\n\n"

    # Current date for calculations
    current_date = datetime.now().date()

    # Group versions by status
    stable_versions = []
    beta_versions = []
    deprecated_versions = []

    for version in API_VERSIONS:
        if version["status"] == "stable":
            stable_versions.append(version)
        elif version["status"] == "beta":
            beta_versions.append(version)
        elif version["status"] == "deprecated":
            deprecated_versions.append(version)

    # Stable versions
    report += "## ✅ Stable Versions\n\n"
    if stable_versions:
        for version in stable_versions:
            released_date = datetime.strptime(
                version["released_date"], "%Y-%m-%d"
            ).date()
            days_since_release = (current_date - released_date).days

            report += f"### {version['version']}\n\n"
            report += f"- **Released**: {version['released_date']} ({days_since_release} days ago)\n"
            report += f"- **Status**: {version['status'].upper()}\n"

            # Breaking changes
            if version["breaking_changes"]:
                report += (
                    f"- **Breaking Changes**: {len(version['breaking_changes'])}\n"
                )
            else:
                report += "- **Breaking Changes**: None\n"

            # Features
            report += "\n**Major Features**:\n"
            for feature in version["major_features"]:
                report += f"- {feature}\n"

            report += "\n"
    else:
        report += "No stable versions available.\n\n"

    # Beta versions
    report += "## 🧪 Beta Versions\n\n"
    if beta_versions:
        for version in beta_versions:
            released_date = datetime.strptime(
                version["released_date"], "%Y-%m-%d"
            ).date()
            days_since_release = (current_date - released_date).days

            report += f"### {version['version']}\n\n"
            report += f"- **Released**: {version['released_date']} ({days_since_release} days ago)\n"
            report += f"- **Status**: {version['status'].upper()}\n"
            report += "- **Warning**: Beta versions may change without notice\n"

            # Breaking changes
            if version["breaking_changes"]:
                report += "\n**Planned Breaking Changes**:\n"
                for change in version["breaking_changes"]:
                    report += f"- {change['endpoint']}: {change['change']}\n"

            # Features
            report += "\n**New Features**:\n"
            for feature in version["major_features"]:
                report += f"- {feature}\n"

            report += "\n"
    else:
        report += "No beta versions available.\n\n"

    # Deprecated versions
    report += "## ⚠️ Deprecated Versions\n\n"
    if deprecated_versions:
        for version in deprecated_versions:
            released_date = datetime.strptime(
                version["released_date"], "%Y-%m-%d"
            ).date()
            days_since_release = (current_date - released_date).days

            sunset_date = None
            days_until_sunset = None
            if version["sunset_date"]:
                sunset_date = datetime.strptime(
                    version["sunset_date"], "%Y-%m-%d"
                ).date()
                days_until_sunset = (sunset_date - current_date).days

            report += f"### {version['version']}\n\n"
            report += f"- **Released**: {version['released_date']} ({days_since_release} days ago)\n"
            report += f"- **Status**: {version['status'].upper()}\n"

            if sunset_date:
                if days_until_sunset > 0:
                    report += f"- **Sunset Date**: {version['sunset_date']} ({days_until_sunset} days remaining) 🔴\n"
                else:
                    report += (
                        f"- **Sunset Date**: {version['sunset_date']} (PAST DUE) 🔴\n"
                    )

            report += "\n**Migration Path**: Upgrade to the latest stable version.\n\n"
    else:
        report += "No deprecated versions.\n\n"

    # Recommendations
    report += "## Recommendations\n\n"

    # Check for very old stable versions that should be deprecated
    old_stable_versions = [
        v
        for v in stable_versions
        if (
            current_date - datetime.strptime(v["released_date"], "%Y-%m-%d").date()
        ).days
        > 365
    ]
    if old_stable_versions:
        report += "- 🟠 Consider deprecating these older stable versions:\n"
        for version in old_stable_versions:
            report += f"  - {version['version']} (released {version['released_date']}, over a year old)\n"

    # Check for beta versions that have been in beta too long
    long_beta_versions = [
        v
        for v in beta_versions
        if (
            current_date - datetime.strptime(v["released_date"], "%Y-%m-%d").date()
        ).days
        > 180
    ]
    if long_beta_versions:
        report += "- 🟠 These beta versions have been in beta for over 6 months, consider promoting to stable or reassessing:\n"
        for version in long_beta_versions:
            days = (
                current_date
                - datetime.strptime(version["released_date"], "%Y-%m-%d").date()
            ).days
            report += f"  - {version['version']} (in beta for {days} days)\n"

    # Check for deprecated versions without sunset dates
    no_sunset_deprecated = [v for v in deprecated_versions if not v["sunset_date"]]
    if no_sunset_deprecated:
        report += "- 🔴 Set sunset dates for these deprecated versions:\n"
        for version in no_sunset_deprecated:
            report += f"  - {version['version']}\n"

    return report


@mcp.tool()
def check_version_compatibility(
    client_version: str, server_version: Optional[str] = None
) -> str:
    """Check compatibility between client and server API versions.

    Args:
        client_version: Client API version (e.g., v1, v2)
        server_version: Server API version (optional, defaults to latest stable)

    Returns:
        Compatibility analysis between client and server versions
    """
    # Normalize input versions (remove 'v' prefix if present)
    if client_version.startswith("v"):
        client_key = f"client_{client_version}"
    else:
        client_key = f"client_v{client_version}"

    # If server version not specified, use latest stable
    if not server_version:
        stable_versions = [v for v in API_VERSIONS if v["status"] == "stable"]
        stable_versions.sort(key=lambda x: x["version"], reverse=True)
        if stable_versions:
            server_version = stable_versions[0]["version"]
        else:
            return "❌ Error: No stable server versions found."

    # Normalize server version
    if server_version.startswith("v"):
        server_key = f"server_{server_version}"
    else:
        server_key = f"server_v{server_version}"

    # Check compatibility
    if client_key not in COMPATIBILITY_MATRIX:
        return f"❌ Unknown client version: {client_version}"

    if server_key.replace("server_", "") not in [v["version"] for v in API_VERSIONS]:
        return f"❌ Unknown server version: {server_version}"

    compatibility = COMPATIBILITY_MATRIX.get(client_key, {}).get(server_key, "unknown")

    # Get version details
    client_version_clean = client_key.replace("client_", "")
    server_version_clean = server_key.replace("server_", "")

    client_version_info = next(
        (v for v in API_VERSIONS if v["version"] == client_version_clean), None
    )
    server_version_info = next(
        (v for v in API_VERSIONS if v["version"] == server_version_clean), None
    )

    # Build the report
    report = (
        f"# Version Compatibility: {client_version_clean} → {server_version_clean}\n\n"
    )

    # Compatibility status
    if compatibility == "full":
        report += "## ✅ FULL COMPATIBILITY\n\n"
        report += "The client version is fully compatible with the server version.\n\n"
    elif compatibility == "partial":
        report += "## ⚠️ PARTIAL COMPATIBILITY\n\n"
        report += "The client version is partially compatible with the server version. Some features may not work correctly.\n\n"
    elif compatibility == "none":
        report += "## ❌ NOT COMPATIBLE\n\n"
        report += "The client version is not compatible with the server version.\n\n"
    else:
        report += "## ❓ UNKNOWN COMPATIBILITY\n\n"
        report += "The compatibility between these versions is unknown.\n\n"

    # Breaking changes
    if server_version_info and compatibility != "full":
        breaking_changes = []
        for version in API_VERSIONS:
            if version["version"] == server_version_clean:
                breaking_changes.extend(version["breaking_changes"])
            elif (
                version["version"] > client_version_clean
                and version["version"] <= server_version_clean
            ):
                breaking_changes.extend(version["breaking_changes"])

        if breaking_changes:
            report += "## Breaking Changes\n\n"
            for change in breaking_changes:
                report += f"### {change['endpoint']}\n\n"
                report += f"**Change**: {change['change']}\n\n"
                if "migration_guide" in change:
                    report += f"**Migration**: {change['migration_guide']}\n\n"

    # Version status
    report += "## Version Status\n\n"

    if client_version_info:
        client_status = client_version_info["status"].upper()
        report += f"**Client Version ({client_version_clean})**: {client_status}\n"
        if client_version_info["status"] == "deprecated":
            if client_version_info["sunset_date"]:
                report += f"⚠️ This version will be sunset on {client_version_info['sunset_date']}\n"
            else:
                report += "⚠️ This version is deprecated with no sunset date specified\n"

    if server_version_info:
        server_status = server_version_info["status"].upper()
        report += f"**Server Version ({server_version_clean})**: {server_status}\n"
        if server_version_info["status"] == "deprecated":
            if server_version_info["sunset_date"]:
                report += f"⚠️ This version will be sunset on {server_version_info['sunset_date']}\n"
            else:
                report += "⚠️ This version is deprecated with no sunset date specified\n"
        elif server_version_info["status"] == "beta":
            report += "⚠️ This version is in beta and may change without notice\n"

    # Recommendations
    report += "\n## Recommendations\n\n"

    if compatibility == "none":
        # Find the latest compatible server version
        compatible_server_versions = []
        for version_key, compat in COMPATIBILITY_MATRIX.get(client_key, {}).items():
            if compat in ["full", "partial"]:
                version = version_key.replace("server_", "")
                version_info = next(
                    (v for v in API_VERSIONS if v["version"] == version), None
                )
                if version_info:
                    compatible_server_versions.append(version_info)

        if compatible_server_versions:
            compatible_server_versions.sort(key=lambda x: x["version"], reverse=True)
            best_version = compatible_server_versions[0]["version"]
            report += f"- 🔄 Consider using server version {best_version} which is compatible with your client\n"

        report += f"- 🔄 Upgrade client to latest stable version to work with server {server_version_clean}\n"

    elif compatibility == "partial":
        report += "- ⚠️ Test thoroughly with this combination of versions\n"
        report += f"- 🔄 Consider upgrading client to match server version {server_version_clean}\n"

    if client_version_info and client_version_info["status"] == "deprecated":
        # Find the latest stable version to recommend
        stable_versions = [v for v in API_VERSIONS if v["status"] == "stable"]
        if stable_versions:
            stable_versions.sort(key=lambda x: x["version"], reverse=True)
            latest_stable = stable_versions[0]["version"]
            report += f"- 🔄 Upgrade client from deprecated {client_version_clean} to latest stable version {latest_stable}\n"

    return report


@mcp.tool()
def plan_api_version_migration(current_version: str, target_version: str) -> str:
    """Plan a migration path between API versions.

    Args:
        current_version: Current API version (e.g., v1, v2)
        target_version: Target API version to migrate to

    Returns:
        Migration plan with steps and considerations
    """
    # Normalize version inputs
    if not current_version.startswith("v"):
        current_version = f"v{current_version}"

    if not target_version.startswith("v"):
        target_version = f"v{target_version}"

    # Get version info
    current_version_info = next(
        (v for v in API_VERSIONS if v["version"] == current_version), None
    )
    target_version_info = next(
        (v for v in API_VERSIONS if v["version"] == target_version), None
    )

    if not current_version_info:
        return f"❌ Unknown current version: {current_version}"

    if not target_version_info:
        return f"❌ Unknown target version: {target_version}"

    # Check if this is an upgrade or downgrade
    is_upgrade = current_version < target_version

    if not is_upgrade:
        return f"❌ Migration plan only supports upgrades, not downgrades ({current_version} → {target_version})"

    # Find intermediate versions
    all_versions = [
        v
        for v in API_VERSIONS
        if v["version"] > current_version and v["version"] <= target_version
    ]
    all_versions.sort(key=lambda x: x["version"])

    # Collect all breaking changes that affect this migration
    breaking_changes = []
    for version in all_versions:
        breaking_changes.extend(
            [(version["version"], change) for change in version["breaking_changes"]]
        )

    # Build the report
    report = f"# API Migration Plan: {current_version} → {target_version}\n\n"

    # Version summary
    report += "## Version Summary\n\n"
    report += f"- **Current Version**: {current_version} ({current_version_info['status'].upper()})\n"
    report += f"- **Target Version**: {target_version} ({target_version_info['status'].upper()})\n"

    if current_version_info["status"] == "deprecated":
        if current_version_info["sunset_date"]:
            report += f"- ⚠️ Current version will be sunset on {current_version_info['sunset_date']}\n"
        else:
            report += "- ⚠️ Current version is deprecated (no sunset date specified)\n"

    if target_version_info["status"] == "beta":
        report += "- ⚠️ Target version is in beta and may change without notice\n"

    # Migration complexity
    complexity = "Low"
    if len(breaking_changes) > 5:
        complexity = "High"
    elif len(breaking_changes) > 2:
        complexity = "Medium"

    report += f"- **Migration Complexity**: {complexity}\n"

    # Breaking changes
    if breaking_changes:
        report += "\n## Breaking Changes\n\n"
        for version, change in breaking_changes:
            report += f"### {version}: {change['endpoint']}\n\n"
            report += f"**Change**: {change['change']}\n\n"
            if "migration_guide" in change:
                report += f"**Migration**: {change['migration_guide']}\n\n"
    else:
        report += "\n## Breaking Changes\n\nNo breaking changes identified for this migration.\n\n"

    # New features
    report += "## New Features Available\n\n"
    for version in all_versions:
        report += f"### {version['version']}\n\n"
        for feature in version["major_features"]:
            report += f"- {feature}\n"
        report += "\n"

    # Migration strategy
    report += "## Migration Strategy\n\n"

    if (
        current_version_info["status"] == "deprecated"
        and current_version_info["sunset_date"]
    ):
        sunset_date = datetime.strptime(
            current_version_info["sunset_date"], "%Y-%m-%d"
        ).date()
        current_date = datetime.now().date()
        days_until_sunset = (sunset_date - current_date).days

        if days_until_sunset <= 30:
            report += "### Urgent Migration Required\n\n"
            report += f"⚠️ **CRITICAL**: The current version will be sunset in {days_until_sunset} days. Immediate migration is required.\n\n"

    # Consider the steps based on the number of versions to jump
    if len(all_versions) > 1:
        # Multi-step migration
        report += "### Multi-Step Migration Approach\n\n"
        report += (
            "Given the multiple versions involved, consider a phased approach:\n\n"
        )

        for i, version in enumerate(all_versions):
            phase_num = i + 1
            report += f"**Phase {phase_num}: Migrate to {version['version']}**\n\n"

            if i < len(all_versions) - 1:
                report += "1. Address breaking changes\n"
                report += "2. Update client code\n"
                report += "3. Test thoroughly\n"
                report += "4. Deploy and monitor\n\n"
            else:
                report += "1. Address breaking changes\n"
                report += "2. Update client code to leverage new features\n"
                report += "3. Test thoroughly\n"
                report += "4. Deploy and monitor\n"
                report += "5. Retire old version client code\n\n"
    else:
        # Direct migration
        report += "### Direct Migration Approach\n\n"
        report += "Since this is a single version upgrade, a direct migration approach is recommended:\n\n"
        report += "1. Address all breaking changes\n"
        report += "2. Update client code to leverage new features\n"
        report += "3. Run comprehensive tests\n"
        report += "4. Deploy and monitor\n"
        report += "5. Retire old version client code\n\n"

    # Implementation checklist
    report += "## Implementation Checklist\n\n"
    report += "- [ ] Create dedicated branch for API migration\n"
    report += "- [ ] Update API client code to handle breaking changes\n"
    report += "- [ ] Update API endpoints to use new version paths\n"

    for version, change in breaking_changes:
        report += f"- [ ] Address {version} change: {change['endpoint']}\n"

    report += "- [ ] Update documentation to reflect new API usage\n"
    report += "- [ ] Run comprehensive integration tests\n"
    report += "- [ ] Deploy changes to staging environment\n"
    report += "- [ ] Validate in staging environment\n"
    report += "- [ ] Deploy to production\n"
    report += "- [ ] Monitor for errors post-migration\n"

    return report


@mcp.tool()
def get_versioning_best_practices() -> str:
    """Get best practices for API versioning.

    Returns:
        Comprehensive guide to API versioning best practices
    """
    # Build the report
    report = "# API Versioning Best Practices\n\n"

    # Introduction
    report += """## Introduction

Effective API versioning is critical for maintaining compatibility while evolving your API.
These best practices will help you create a versioning strategy that balances innovation
with stability for your API consumers.
"""

    # Versioning approaches
    report += """
## Versioning Approaches

There are several common approaches to API versioning:

1. **URI Path Versioning**: `/v1/users`, `/v2/users`
   - **Pros**: Explicit, clear, easy to test
   - **Cons**: Not truly RESTful (resource shouldn't change based on version)

2. **Query Parameter Versioning**: `/users?version=1`
   - **Pros**: More RESTful
   - **Cons**: Less visible, easier to miss

3. **Header-Based Versioning**: `Accept: application/vnd.company.api+json;version=1`
   - **Pros**: Most RESTful, doesn't pollute URI
   - **Cons**: Harder to test, less discoverable

4. **Content Negotiation**: `Accept: application/vnd.company.v1+json`
   - **Pros**: Follows HTTP standards
   - **Cons**: Complex, harder to debug

The most common and recommended approach is **URI Path Versioning** due to its clarity and ease of use.
"""

    # Best practices by category
    for category in VERSIONING_BEST_PRACTICES:
        report += f"\n## {category['category']}\n\n"
        for practice in category["practices"]:
            report += f"- {practice}\n"

    # Additional recommendations
    report += """
## Additional Recommendations

### Backward Compatibility
- Aim to maintain backward compatibility whenever possible
- Add new fields without removing old ones
- Support old field names alongside new ones
- Accept both old and new request formats

### Testing
- Maintain automated tests for each supported API version
- Test migrations between versions
- Monitor version usage to identify clients using outdated versions

### Client Communication
- Announce new versions via multiple channels (email, blog, API dashboard)
- Provide detailed changelogs
- Create migration guides for breaking changes
- Consider a developer preview program for major version changes
"""

    return report
