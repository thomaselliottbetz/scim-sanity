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

# Schema registry
SCHEMAS = {
    "urn:ietf:params:scim:schemas:core:2.0:User": CORE_USER_SCHEMA,
    "urn:ietf:params:scim:schemas:core:2.0:Group": CORE_GROUP_SCHEMA,
    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": ENTERPRISE_USER_SCHEMA,
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

