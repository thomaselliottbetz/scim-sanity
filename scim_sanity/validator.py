"""Core SCIM 2.0 validation logic."""

import json
from typing import List, Dict, Any, Optional, Tuple
from .schemas import SCHEMAS, get_schema, get_attribute_def


class ValidationError:
    """Represents a validation error with location and message."""
    
    def __init__(self, message: str, path: str = "", line: Optional[int] = None):
        self.message = message
        self.path = path
        self.line = line
    
    def __str__(self):
        loc = f" at {self.path}" if self.path else ""
        line_info = f" (line {self.line})" if self.line else ""
        return f"{self.message}{loc}{line_info}"


class SCIMValidator:
    """Validates SCIM 2.0 User, Group, Agent, and AgenticApplication resources and PATCH operations."""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.json_lines: List[str] = []
    
    def validate(self, data: Dict[str, Any], operation: str = "full") -> Tuple[bool, List[ValidationError]]:
        """
        Validate SCIM resource or PATCH operation.
        
        Args:
            data: JSON data to validate
            operation: "full" for POST/PUT, "patch" for PATCH operations
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        self.errors = []
        self.json_lines = json.dumps(data, indent=2).split("\n")
        
        if operation == "patch":
            return self._validate_patch(data)
        else:
            return self._validate_full_resource(data)
    
    def _validate_full_resource(self, data: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """Validate a full SCIM resource (POST/PUT)."""
        # Check schemas field
        if "schemas" not in data:
            self.errors.append(ValidationError("Missing required field: 'schemas'"))
            return False, self.errors
        
        schemas = data.get("schemas", [])
        if not isinstance(schemas, list) or not schemas:
            self.errors.append(ValidationError("'schemas' must be a non-empty array"))
            return False, self.errors
        
        # Determine resource type by checking for core schema URNs
        # Auto-detection: Resource type is determined by the presence of schema URNs,
        # so no explicit --agent-mode flag is needed. The validator automatically
        # detects Agent/AgenticApplication resources based on their schema URIs.
        is_user = "urn:ietf:params:scim:schemas:core:2.0:User" in schemas
        is_group = "urn:ietf:params:scim:schemas:core:2.0:Group" in schemas
        is_agent = "urn:ietf:params:scim:schemas:core:2.0:Agent" in schemas
        is_agentic_application = "urn:ietf:params:scim:schemas:core:2.0:AgenticApplication" in schemas
        
        # Validate that at least one known core schema is present
        if not is_user and not is_group and not is_agent and not is_agentic_application:
            self.errors.append(ValidationError(
                "Invalid schema URN. Must include 'urn:ietf:params:scim:schemas:core:2.0:User', "
                "'urn:ietf:params:scim:schemas:core:2.0:Group', "
                "'urn:ietf:params:scim:schemas:core:2.0:Agent', or "
                "'urn:ietf:params:scim:schemas:core:2.0:AgenticApplication'"
            ))
            return False, self.errors
        
        # Validate each schema
        for schema_urn in schemas:
            schema = get_schema(schema_urn)
            if not schema:
                self.errors.append(ValidationError(f"Unknown schema URN: {schema_urn}"))
                continue
            
            self._validate_schema_attributes(data, schema_urn, schema)
        
        # Resource-specific validations
        if is_user:
            self._validate_user_specific(data)
        elif is_group:
            self._validate_group_specific(data)
        elif is_agent:
            self._validate_agent_specific(data)
        elif is_agentic_application:
            self._validate_agentic_application_specific(data)
        
        # Check for immutable attributes being set
        self._check_immutable_attributes(data, schemas)
        
        # Check null vs omitted semantics
        self._check_null_semantics(data, schemas)
        
        return len(self.errors) == 0, self.errors
    
    def _validate_patch(self, data: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """Validate a SCIM PATCH operation."""
        # Check schemas
        if "schemas" not in data:
            self.errors.append(ValidationError("Missing required field: 'schemas'"))
            return False, self.errors
        
        schemas = data.get("schemas", [])
        if "urn:ietf:params:scim:api:messages:2.0:PatchOp" not in schemas:
            self.errors.append(ValidationError(
                "PATCH operation must include schema: 'urn:ietf:params:scim:api:messages:2.0:PatchOp'"
            ))
        
        # Check Operations array
        if "Operations" not in data:
            self.errors.append(ValidationError("Missing required field: 'Operations'"))
            return False, self.errors
        
        operations = data.get("Operations", [])
        if not isinstance(operations, list):
            self.errors.append(ValidationError("'Operations' must be an array"))
            return False, self.errors
        
        if not operations:
            self.errors.append(ValidationError("'Operations' array cannot be empty"))
            return False, self.errors
        
        # Validate each operation
        seen_paths = set()
        for idx, op in enumerate(operations):
            if not isinstance(op, dict):
                self.errors.append(ValidationError(f"Operation {idx} must be an object"))
                continue
            
            op_type = op.get("op")
            if not op_type:
                self.errors.append(ValidationError(f"Operation {idx}: missing required field 'op'"))
                continue
            
            valid_ops = ["add", "remove", "replace"]
            if op_type not in valid_ops:
                self.errors.append(ValidationError(
                    f"Operation {idx}: invalid 'op' value '{op_type}'. Must be one of: {', '.join(valid_ops)}"
                ))
            
            # Check for duplicate paths
            path = op.get("path")
            if path:
                if path in seen_paths:
                    self.errors.append(ValidationError(
                        f"Operation {idx}: duplicate path '{path}' in PATCH operations"
                    ))
                seen_paths.add(path)
            
            # Validate operation structure
            if op_type == "remove":
                if "path" not in op:
                    self.errors.append(ValidationError(f"Operation {idx}: 'remove' operation requires 'path'"))
            elif op_type in ["add", "replace"]:
                if "value" not in op:
                    self.errors.append(ValidationError(f"Operation {idx}: '{op_type}' operation requires 'value'"))
        
        return len(self.errors) == 0, self.errors
    
    def _validate_schema_attributes(self, data: Dict[str, Any], schema_urn: str, schema: Dict[str, Any]):
        """Validate attributes against a schema definition."""
        # Extension schemas store attributes under the schema URN key
        is_extension = schema_urn.startswith("urn:ietf:params:scim:schemas:extension:")
        if is_extension:
            extension_data = data.get(schema_urn, {})
            if not isinstance(extension_data, dict):
                self.errors.append(ValidationError(
                    f"Extension schema '{schema_urn}' must be an object",
                    path=schema_urn
                ))
                return
        else:
            extension_data = data
        
        for attr_def in schema.get("attributes", []):
            attr_name = attr_def["name"]
            required = attr_def.get("required", False)
            mutability = attr_def.get("mutability", "readWrite")
            
            # Check required attributes
            if required and attr_name not in extension_data:
                full_path = f"{schema_urn}.{attr_name}" if is_extension else attr_name
                self.errors.append(ValidationError(
                    f"Missing required attribute: '{attr_name}' (schema: {schema_urn})",
                    path=full_path
                ))
            
            # Validate complex types
            if attr_name in extension_data and attr_def.get("type") == "complex":
                value = extension_data[attr_name]
                full_path = f"{schema_urn}.{attr_name}" if is_extension else attr_name
                if attr_def.get("multiValued"):
                    if not isinstance(value, list):
                        self.errors.append(ValidationError(
                            f"Attribute '{attr_name}' must be an array (multiValued)",
                            path=full_path
                        ))
                    else:
                        for idx, item in enumerate(value):
                            self._validate_complex_attribute(item, attr_def, f"{full_path}[{idx}]")
                else:
                    self._validate_complex_attribute(value, attr_def, full_path)
    
    def _validate_complex_attribute(self, value: Any, attr_def: Dict[str, Any], path: str):
        """Validate a complex attribute value."""
        if not isinstance(value, dict):
            return
        
        sub_attrs = attr_def.get("subAttributes", [])
        for sub_attr_def in sub_attrs:
            sub_name = sub_attr_def["name"]
            required = sub_attr_def.get("required", False)
            
            if required and sub_name not in value:
                self.errors.append(ValidationError(
                    f"Missing required sub-attribute: '{sub_name}' in '{path}'",
                    path=f"{path}.{sub_name}"
                ))
    
    def _validate_user_specific(self, data: Dict[str, Any]):
        """User-specific validations."""
        # userName is required for Users
        if "userName" not in data:
            self.errors.append(ValidationError("User resource missing required attribute: 'userName'"))
    
    def _validate_group_specific(self, data: Dict[str, Any]):
        """Group-specific validations."""
        # displayName is required for Groups
        if "displayName" not in data:
            self.errors.append(ValidationError("Group resource missing required attribute: 'displayName'"))
    
    def _validate_agent_specific(self, data: Dict[str, Any]):
        """
        Agent-specific validations per draft-abbey-scim-agent-extension-00.
        
        Validates that Agent resources conform to the Agent schema requirements:
        - 'name' attribute is REQUIRED (section 5.1.4 of the draft)
        - 'name' must be non-empty (used as unique identifier for authentication)
        
        Note: Only 'name' is required. Other attributes like 'displayName' and 'active'
        are optional per the specification. This minimal validation approach follows
        the draft's principle that "only one attribute is required" for Agents.
        """
        # name is required for Agents (per draft-abbey-scim-agent-extension-00, section 5.1.4)
        if "name" not in data:
            self.errors.append(ValidationError("Agent resource missing required attribute: 'name'"))
        elif data.get("name") == "":
            # The draft specifies that name MUST be non-empty as it's used for authentication
            self.errors.append(ValidationError("Agent resource 'name' attribute must be non-empty"))
    
    def _validate_agentic_application_specific(self, data: Dict[str, Any]):
        """
        AgenticApplication-specific validations per draft-abbey-scim-agent-extension-00.
        
        Validates that AgenticApplication resources conform to the schema requirements:
        - 'name' attribute is REQUIRED (section 5.2.4 of the draft)
        - 'name' must be non-empty (unique identifier for the application)
        
        AgenticApplications represent applications that host or provide access to agents,
        serving as containers and runtime environments for agent management.
        """
        # name is required for AgenticApplications (per draft-abbey-scim-agent-extension-00, section 5.2.4)
        if "name" not in data:
            self.errors.append(ValidationError("AgenticApplication resource missing required attribute: 'name'"))
        elif data.get("name") == "":
            # The draft specifies that name MUST be non-empty as it's the unique identifier
            self.errors.append(ValidationError("AgenticApplication resource 'name' attribute must be non-empty"))
    
    def _check_immutable_attributes(self, data: Dict[str, Any], schemas: List[str]):
        """Check if immutable attributes are being set (should only be set by server)."""
        immutable_attrs = ["id", "meta"]
        
        for schema_urn in schemas:
            schema = get_schema(schema_urn)
            if not schema:
                continue
            
            # Extension schemas store attributes under the schema URN key
            is_extension = schema_urn.startswith("urn:ietf:params:scim:schemas:extension:")
            check_data = data.get(schema_urn, {}) if is_extension else data
            
            for attr_def in schema.get("attributes", []):
                if attr_def.get("mutability") == "readOnly":
                    attr_name = attr_def["name"]
                    if attr_name in check_data:
                        # Allow if it's in a nested path (e.g., meta.created)
                        if "." not in attr_name:
                            full_path = f"{schema_urn}.{attr_name}" if is_extension else attr_name
                            self.errors.append(ValidationError(
                                f"Immutable attribute '{attr_name}' should not be set by client (mutability: readOnly)",
                                path=full_path
                            ))
    
    def _check_null_semantics(self, data: Dict[str, Any], schemas: List[str]):
        """Check for null values (should use omit instead for clearing)."""
        for key, value in data.items():
            if value is None:
                self.errors.append(ValidationError(
                    f"Attribute '{key}' has null value. Use PATCH 'remove' operation to clear attributes instead",
                    path=key
                ))


def validate_file(file_path: str, operation: str = "full") -> Tuple[bool, List[ValidationError]]:
    """Validate a JSON file containing SCIM data."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [ValidationError(f"Invalid JSON: {e}")]
    except Exception as e:
        return False, [ValidationError(f"Error reading file: {e}")]
    
    validator = SCIMValidator()
    return validator.validate(data, operation)


def validate_string(json_str: str, operation: str = "full") -> Tuple[bool, List[ValidationError]]:
    """Validate a JSON string containing SCIM data."""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return False, [ValidationError(f"Invalid JSON: {e}")]
    
    validator = SCIMValidator()
    return validator.validate(data, operation)

