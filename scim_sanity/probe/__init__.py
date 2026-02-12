"""SCIM server conformance probe — test a live SCIM endpoint for RFC 7643/7644 compliance.

This package runs a 7-phase CRUD lifecycle test sequence against a live
SCIM server, validating discovery endpoints, resource CRUD for User/Group/
Agent/AgenticApplication, search and pagination, and error handling.

Entry point: ``scim_sanity.probe.runner.run_probe()``
"""
