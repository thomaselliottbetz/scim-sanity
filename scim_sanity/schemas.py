"""SCIM 2.0 core and enterprise extension schemas (RFC 7643, 7644)."""

# Core User schema (RFC 7643)
CORE_USER_SCHEMA = {
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
    "id": "urn:ietf:params:scim:schemas:core:2.0:User",
    "name": "User",
    "description": "User Account",
    "attributes": [
        {"name": "userName", "type": "string", "required": True, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "server"},
        {"name": "name", "type": "complex", "mutability": "readWrite", "returned": "default", "subAttributes": [
            {"name": "formatted", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "familyName", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "givenName", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "middleName", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "honorificPrefix", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "honorificSuffix", "type": "string", "mutability": "readWrite", "returned": "default"},
        ]},
        {"name": "displayName", "type": "string", "mutability": "readWrite", "returned": "default"},
        {"name": "nickName", "type": "string", "mutability": "readWrite", "returned": "default"},
        {"name": "profileUrl", "type": "reference", "mutability": "readWrite", "returned": "default"},
        {"name": "title", "type": "string", "mutability": "readWrite", "returned": "default"},
        {"name": "userType", "type": "string", "mutability": "readWrite", "returned": "default"},
        {"name": "preferredLanguage", "type": "string", "mutability": "readWrite", "returned": "default"},
        {"name": "locale", "type": "string", "mutability": "readWrite", "returned": "default"},
        {"name": "timezone", "type": "string", "mutability": "readWrite", "returned": "default"},
        {"name": "active", "type": "boolean", "mutability": "readWrite", "returned": "default"},
        {"name": "password", "type": "string", "mutability": "writeOnly", "returned": "never"},
        {"name": "emails", "type": "complex", "multiValued": True, "mutability": "readWrite", "returned": "default", "subAttributes": [
            {"name": "value", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "display", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "type", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "primary", "type": "boolean", "mutability": "readWrite", "returned": "default"},
        ]},
        {"name": "phoneNumbers", "type": "complex", "multiValued": True, "mutability": "readWrite", "returned": "default", "subAttributes": [
            {"name": "value", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "display", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "type", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "primary", "type": "boolean", "mutability": "readWrite", "returned": "default"},
        ]},
        {"name": "ims", "type": "complex", "multiValued": True, "mutability": "readWrite", "returned": "default"},
        {"name": "photos", "type": "complex", "multiValued": True, "mutability": "readWrite", "returned": "default"},
        {"name": "addresses", "type": "complex", "multiValued": True, "mutability": "readWrite", "returned": "default", "subAttributes": [
            {"name": "formatted", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "streetAddress", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "locality", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "region", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "postalCode", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "country", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "type", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "primary", "type": "boolean", "mutability": "readWrite", "returned": "default"},
        ]},
        {"name": "groups", "type": "complex", "multiValued": True, "mutability": "readOnly", "returned": "default"},
        {"name": "entitlements", "type": "complex", "multiValued": True, "mutability": "readWrite", "returned": "default"},
        {"name": "roles", "type": "complex", "multiValued": True, "mutability": "readWrite", "returned": "default"},
        {"name": "x509Certificates", "type": "complex", "multiValued": True, "mutability": "readWrite", "returned": "default"},
        {"name": "id", "type": "string", "mutability": "readOnly", "returned": "always"},
        {"name": "externalId", "type": "string", "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
        {"name": "meta", "type": "complex", "mutability": "readOnly", "returned": "default", "subAttributes": [
            {"name": "resourceType", "type": "string", "mutability": "readOnly", "returned": "default"},
            {"name": "created", "type": "dateTime", "mutability": "readOnly", "returned": "default"},
            {"name": "lastModified", "type": "dateTime", "mutability": "readOnly", "returned": "default"},
            {"name": "location", "type": "reference", "mutability": "readOnly", "returned": "default"},
            {"name": "version", "type": "string", "mutability": "readOnly", "returned": "default"},
        ]},
    ]
}

# Core Group schema (RFC 7643)
CORE_GROUP_SCHEMA = {
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
    "id": "urn:ietf:params:scim:schemas:core:2.0:Group",
    "name": "Group",
    "description": "Group",
    "attributes": [
        {"name": "displayName", "type": "string", "required": True, "mutability": "readWrite", "returned": "default"},
        {"name": "members", "type": "complex", "multiValued": True, "mutability": "readWrite", "returned": "default", "subAttributes": [
            {"name": "value", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "$ref", "type": "reference", "mutability": "readOnly", "returned": "default"},
            {"name": "type", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "display", "type": "string", "mutability": "readWrite", "returned": "default"},
        ]},
        {"name": "id", "type": "string", "mutability": "readOnly", "returned": "always"},
        {"name": "externalId", "type": "string", "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
        {"name": "meta", "type": "complex", "mutability": "readOnly", "returned": "default", "subAttributes": [
            {"name": "resourceType", "type": "string", "mutability": "readOnly", "returned": "default"},
            {"name": "created", "type": "dateTime", "mutability": "readOnly", "returned": "default"},
            {"name": "lastModified", "type": "dateTime", "mutability": "readOnly", "returned": "default"},
            {"name": "location", "type": "reference", "mutability": "readOnly", "returned": "default"},
            {"name": "version", "type": "string", "mutability": "readOnly", "returned": "default"},
        ]},
    ]
}

# Enterprise User Extension schema (RFC 7643)
ENTERPRISE_USER_SCHEMA = {
    "schemas": ["urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"],
    "id": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
    "name": "EnterpriseUser",
    "description": "Enterprise User",
    "attributes": [
        {"name": "employeeNumber", "type": "string", "mutability": "readWrite", "returned": "default"},
        {"name": "costCenter", "type": "string", "mutability": "readWrite", "returned": "default"},
        {"name": "organization", "type": "string", "mutability": "readWrite", "returned": "default"},
        {"name": "division", "type": "string", "mutability": "readWrite", "returned": "default"},
        {"name": "department", "type": "string", "mutability": "readWrite", "returned": "default"},
        {"name": "manager", "type": "complex", "mutability": "readWrite", "returned": "default", "subAttributes": [
            {"name": "value", "type": "string", "mutability": "readWrite", "returned": "default"},
            {"name": "$ref", "type": "reference", "mutability": "readOnly", "returned": "default"},
            {"name": "displayName", "type": "string", "mutability": "readWrite", "returned": "default"},
        ]},
    ]
}

# Agent schema (draft-abbey-scim-agent-extension-00)
# 
# Defines the schema for AI Agent resources as specified in the IETF draft
# "SCIM Agents and Agentic Applications Extension" (draft-abbey-scim-agent-extension-00).
# 
# Agents represent AI workloads with their own identifiers, metadata, and privileges,
# independent of runtime environments. Unlike traditional software workloads, agents
# have unpredictable behavior due to AI model delegation.
#
# Key attributes:
# - name (REQUIRED): Unique identifier for the agent, used for authentication
# - displayName: Human-readable display name (optional, name used as fallback)
# - agentType: Classification (e.g., "Assistant", "Researcher", "Chat bot")
# - active: Administrative status (boolean)
# - subject: OIDC subject claim for token federation correlation (read-only)
# - owners: Users/Groups accountable for the agent (multi-valued, read-only)
# - protocols: Communication protocols supported (e.g., A2A, OpenAPI, MCP-Server)
# - applications: References to AgenticApplications this agent belongs to
# - parent: Parent agent in hierarchy (if supported)
# - groups, entitlements, roles: Standard SCIM attributes for access control
#
# Reference: https://datatracker.ietf.org/doc/draft-abbey-scim-agent-extension/
CORE_AGENT_SCHEMA = {
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
    "id": "urn:ietf:params:scim:schemas:core:2.0:Agent",
    "name": "Agent",
    "description": "An AI agent",
    "attributes": [
        {"name": "name", "type": "string", "required": True, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "server"},
        {"name": "displayName", "type": "string", "required": False, "mutability": "readWrite", "returned": "default"},
        {"name": "agentType", "type": "string", "required": False, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
        {"name": "active", "type": "boolean", "required": False, "mutability": "readWrite", "returned": "default"},
        {"name": "description", "type": "string", "required": False, "mutability": "readWrite", "returned": "default"},
        {"name": "subject", "type": "string", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
        {"name": "groups", "type": "complex", "multiValued": True, "required": False, "mutability": "readOnly", "returned": "default", "subAttributes": [
            {"name": "value", "type": "string", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
            {"name": "$ref", "type": "reference", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
            {"name": "display", "type": "string", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
            {"name": "type", "type": "string", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
        ]},
        {"name": "entitlements", "type": "complex", "multiValued": True, "required": False, "mutability": "readWrite", "returned": "default", "subAttributes": [
            {"name": "value", "type": "string", "required": False, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
            {"name": "display", "type": "string", "required": False, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
            {"name": "type", "type": "string", "required": False, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
            {"name": "primary", "type": "boolean", "required": False, "mutability": "readWrite", "returned": "default"},
        ]},
        {"name": "roles", "type": "complex", "multiValued": True, "required": False, "mutability": "readWrite", "returned": "default", "subAttributes": [
            {"name": "value", "type": "string", "required": False, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
            {"name": "display", "type": "string", "required": False, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
            {"name": "type", "type": "string", "required": False, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
            {"name": "primary", "type": "boolean", "required": False, "mutability": "readWrite", "returned": "default"},
        ]},
        {"name": "x509Certificates", "type": "complex", "multiValued": True, "required": False, "caseExact": False, "mutability": "readWrite", "returned": "default", "subAttributes": [
            {"name": "value", "type": "binary", "required": False, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
            {"name": "display", "type": "string", "required": False, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
            {"name": "type", "type": "string", "required": False, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
            {"name": "primary", "type": "boolean", "required": False, "mutability": "readWrite", "returned": "default"},
        ]},
        {"name": "applications", "type": "complex", "multiValued": True, "required": False, "mutability": "readOnly", "returned": "default", "subAttributes": [
            {"name": "value", "type": "string", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
            {"name": "$ref", "type": "reference", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
            {"name": "display", "type": "string", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
        ]},
        {"name": "owners", "type": "complex", "multiValued": True, "required": False, "mutability": "readOnly", "returned": "default", "subAttributes": [
            {"name": "value", "type": "string", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
            {"name": "$ref", "type": "reference", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
            {"name": "display", "type": "string", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
        ]},
        {"name": "protocols", "type": "complex", "multiValued": True, "required": False, "mutability": "readOnly", "returned": "default", "subAttributes": [
            {"name": "type", "type": "string", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
            {"name": "specifiationUrl", "type": "string", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
        ]},
        {"name": "parent", "type": "complex", "multiValued": False, "required": False, "mutability": "readOnly", "returned": "default", "subAttributes": [
            {"name": "value", "type": "string", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
            {"name": "$ref", "type": "reference", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
            {"name": "display", "type": "string", "required": False, "caseExact": False, "mutability": "readOnly", "returned": "default", "uniqueness": "none"},
        ]},
        {"name": "id", "type": "string", "mutability": "readOnly", "returned": "always"},
        {"name": "externalId", "type": "string", "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
        {"name": "meta", "type": "complex", "mutability": "readOnly", "returned": "default", "subAttributes": [
            {"name": "resourceType", "type": "string", "mutability": "readOnly", "returned": "default"},
            {"name": "created", "type": "dateTime", "mutability": "readOnly", "returned": "default"},
            {"name": "lastModified", "type": "dateTime", "mutability": "readOnly", "returned": "default"},
            {"name": "location", "type": "reference", "mutability": "readOnly", "returned": "default"},
            {"name": "version", "type": "string", "mutability": "readOnly", "returned": "default"},
        ]},
    ]
}

# AgenticApplication schema (draft-abbey-scim-agent-extension-00)
#
# Defines the schema for AgenticApplication resources as specified in the IETF draft
# "SCIM Agents and Agentic Applications Extension" (draft-abbey-scim-agent-extension-00).
#
# AgenticApplications are software applications that host or provide access to one or
# more agents. They serve as containers and runtime environments for agents, managing
# authentication, authorization, and resource access.
#
# Key attributes:
# - name (REQUIRED): Unique identifier for the application
# - displayName: Human-readable display name (optional, name used as fallback)
# - description: Description of the application
# - active: Administrative status indicating if application is operational
#
# Note: This schema definition includes core attributes. Additional attributes may be
# added as the draft specification evolves (e.g., applicationUrls, oAuthConfiguration).
#
# Reference: https://datatracker.ietf.org/doc/draft-abbey-scim-agent-extension/
CORE_AGENTIC_APPLICATION_SCHEMA = {
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:AgenticApplication"],
    "id": "urn:ietf:params:scim:schemas:core:2.0:AgenticApplication",
    "name": "AgenticApplication",
    "description": "An agentic application",
    "attributes": [
        {"name": "name", "type": "string", "required": True, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "server"},
        {"name": "displayName", "type": "string", "required": False, "mutability": "readWrite", "returned": "default"},
        {"name": "description", "type": "string", "required": False, "mutability": "readWrite", "returned": "default"},
        {"name": "active", "type": "boolean", "required": False, "mutability": "readWrite", "returned": "default"},
        {"name": "id", "type": "string", "mutability": "readOnly", "returned": "always"},
        {"name": "externalId", "type": "string", "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
        {"name": "meta", "type": "complex", "mutability": "readOnly", "returned": "default", "subAttributes": [
            {"name": "resourceType", "type": "string", "mutability": "readOnly", "returned": "default"},
            {"name": "created", "type": "dateTime", "mutability": "readOnly", "returned": "default"},
            {"name": "lastModified", "type": "dateTime", "mutability": "readOnly", "returned": "default"},
            {"name": "location", "type": "reference", "mutability": "readOnly", "returned": "default"},
            {"name": "version", "type": "string", "mutability": "readOnly", "returned": "default"},
        ]},
    ]
}

# Schema registry
# Maps SCIM schema URNs to their schema definitions for validation lookup.
# Supports:
# - Core SCIM 2.0 schemas (User, Group)
# - Enterprise extension schema
# - Agent extension schemas (Agent, AgenticApplication) from draft-abbey-scim-agent-extension-00
SCHEMAS = {
    "urn:ietf:params:scim:schemas:core:2.0:User": CORE_USER_SCHEMA,
    "urn:ietf:params:scim:schemas:core:2.0:Group": CORE_GROUP_SCHEMA,
    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": ENTERPRISE_USER_SCHEMA,
    "urn:ietf:params:scim:schemas:core:2.0:Agent": CORE_AGENT_SCHEMA,
    "urn:ietf:params:scim:schemas:core:2.0:AgenticApplication": CORE_AGENTIC_APPLICATION_SCHEMA,
}

def get_schema(urn: str):
    """Get schema definition by URN."""
    return SCHEMAS.get(urn)

def get_attribute_def(schema_urn: str, attr_path: str):
    """Get attribute definition by schema URN and dot-separated path."""
    schema = get_schema(schema_urn)
    if not schema:
        return None
    
    parts = attr_path.split(".")
    attrs = schema["attributes"]
    
    for part in parts:
        found = None
        for attr in attrs:
            if attr["name"] == part:
                found = attr
                break
        if not found:
            return None
        if "subAttributes" in found:
            attrs = found["subAttributes"]
        else:
            return found
    
    return found

