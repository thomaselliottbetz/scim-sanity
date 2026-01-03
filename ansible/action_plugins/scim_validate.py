#!/usr/bin/env python
"""
Ansible Action Plugin for SCIM Validation

This plugin validates SCIM 2.0 payloads using scim-sanity before they're sent
to identity providers like Entra ID or Google Workspace.

Example usage:
  - name: Validate SCIM user payload
    scim_validate:
      payload: "{{ user_payload }}"
      operation: full
    register: validation_result
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import sys
from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError

try:
    from scim_sanity.validator import SCIMValidator, ValidationError
    HAS_SCIM_SANITY = True
except ImportError:
    HAS_SCIM_SANITY = False


class ActionModule(ActionBase):
    """Ansible action plugin for SCIM validation."""

    def run(self, tmp=None, task_vars=None):
        """Execute the SCIM validation action."""
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # Check if scim-sanity is available
        if not HAS_SCIM_SANITY:
            result['failed'] = True
            result['msg'] = (
                "scim-sanity is not installed. "
                "Install it with: pip install scim-sanity"
            )
            return result

        # Get parameters
        payload = self._task.args.get('payload', None)
        operation = self._task.args.get('operation', 'full')
        file_path = self._task.args.get('file', None)

        # Validate parameters
        if payload is None and file_path is None:
            result['failed'] = True
            result['msg'] = "Either 'payload' or 'file' parameter must be provided"
            return result

        if payload is not None and file_path is not None:
            result['failed'] = True
            result['msg'] = "Cannot specify both 'payload' and 'file' parameters"
            return result

        # Load payload
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    payload = json.load(f)
            except FileNotFoundError:
                result['failed'] = True
                result['msg'] = f"File not found: {file_path}"
                return result
            except json.JSONDecodeError as e:
                result['failed'] = True
                result['msg'] = f"Invalid JSON in file {file_path}: {e}"
                return result
        else:
            # payload is provided directly
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError as e:
                    result['failed'] = True
                    result['msg'] = f"Invalid JSON in payload: {e}"
                    return result
            elif not isinstance(payload, dict):
                result['failed'] = True
                result['msg'] = "Payload must be a dictionary or valid JSON string"
                return result

        # Validate operation parameter
        if operation not in ['full', 'patch']:
            result['failed'] = True
            result['msg'] = f"Operation must be 'full' or 'patch', got: {operation}"
            return result

        # Perform validation
        try:
            validator = SCIMValidator()
            is_valid, errors = validator.validate(payload, operation)
            
            result['valid'] = is_valid
            result['changed'] = False
            
            if is_valid:
                result['msg'] = "SCIM validation passed"
                result['errors'] = []
            else:
                # Convert ValidationError objects to dictionaries
                error_list = []
                for error in errors:
                    error_dict = {
                        'message': error.message,
                        'path': error.path,
                        'line': error.line
                    }
                    error_list.append(error_dict)
                
                result['errors'] = error_list
                result['msg'] = f"SCIM validation failed with {len(errors)} error(s)"
                
                # Optionally fail the task if validation fails
                fail_on_error = self._task.args.get('fail_on_error', True)
                if fail_on_error:
                    result['failed'] = True
                    error_messages = [e['message'] for e in error_list]
                    result['msg'] = f"SCIM validation failed:\n" + "\n".join(f"  - {msg}" for msg in error_messages)
            
        except Exception as e:
            result['failed'] = True
            result['msg'] = f"Error during SCIM validation: {str(e)}"
            return result

        return result

