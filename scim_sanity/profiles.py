"""Named probe profiles for known SCIM server implementations.

Profiles inject server-specific fields into test payloads to accommodate
non-RFC requirements without polluting the core probe logic.  A profile
is applied before any ``--extra-user-fields`` override, so explicit flags
always win.
"""

import secrets
import string
import uuid
from typing import Any, Dict, List, Optional


# Registry of known profiles: name → human-readable description
PROFILES: Dict[str, str] = {
    "entra": "Microsoft Entra ID SCIM server — adds required password field",
    "fortiauthenticator": "FortiAuthenticator SCIM server — response envelope deviations; no payload injection required",
}


# Structured deviation data for each profile.
# Each entry: {"description": str, "rfc": str, "recommendation": str}
PROFILE_DEVIATIONS: Dict[str, List[Dict[str, str]]] = {
    "entra": [
        {
            "description": "meta.resourceType returned as lowercase 'user'/'group' instead of PascalCase 'User'/'Group'",
            "rfc": "RFC 7643 §3.1 — meta.resourceType values are defined as 'User' and 'Group' (PascalCase)",
            "recommendation": "Clients that route or dispatch on resourceType will silently misroute every resource",
        },
        {
            "description": "ResourceTypes response uses 'resources' (lowercase) instead of RFC-required 'Resources'",
            "rfc": "RFC 7644 §3.4.2 — ListResponse Resources key is case-sensitive",
            "recommendation": "scim-sanity works around this automatically; server should use 'Resources'",
        },
        {
            "description": "DELETE /Users/<id> rejects Accept: application/scim+json header with HTTP 400",
            "rfc": "RFC 7644 §3.6 — DELETE should accept standard SCIM headers",
            "recommendation": "scim-sanity omits Accept/Content-Type on DELETE to work around this",
        },
        {
            "description": "PUT /Users/<id> returns 405 Method Not Allowed — PUT replace is not supported",
            "rfc": "RFC 7644 §3.5.1 — servers SHOULD support PUT for full resource replacement",
            "recommendation": "Use PATCH for all updates against Entra; avoid PUT",
        },
        {
            "description": "PATCH /Users/<id> returns 204 No Content with no body instead of 200 with updated resource",
            "rfc": "RFC 7644 §3.5.2 — server SHOULD return the modified resource on PATCH",
            "recommendation": "Follow PATCH with a GET to retrieve the updated resource state",
        },
        {
            "description": "Created/updated resources missing meta.created and meta.lastModified timestamps",
            "rfc": "RFC 7643 §3.1 — meta.created and meta.lastModified are required",
            "recommendation": "Do not rely on meta timestamps from Entra SCIM responses",
        },
        {
            "description": "GET /Users?count=0 returns HTTP 400 instead of empty ListResponse",
            "rfc": "RFC 7644 §3.4.2.4 — count=0 is a valid pagination parameter (returns count only)",
            "recommendation": "Use count=1 or omit count when querying Entra",
        },
        {
            "description": "GET /Users/<nonexistent-id> returns HTTP 400 instead of 404",
            "rfc": "RFC 7644 §3.4.1 — unknown resource should return 404 Not Found",
            "recommendation": "Treat 400 as 404 when the id format is valid but the resource does not exist",
        },
        {
            "description": "PATCH Group members with a non-existent member id returns 400 (referential integrity enforced)",
            "rfc": "RFC 7644 §3.5.2 — RFC does not require referential integrity validation on member ids",
            "recommendation": "Only use real user ids as group members; Entra validates existence",
        },
        {
            "description": "POST /Users requires non-RFC 'password' field",
            "rfc": "RFC 7643 §4.1 — password is a standard attribute but not required for creation",
            "recommendation": "Always include a password when creating users against Entra; use --profile entra",
        },
        {
            "description": "POST /Users requires Microsoft Entra extension schema and mailNickname",
            "rfc": "RFC 7643 — extension schemas are optional and server-defined",
            "recommendation": "Use --profile entra to inject required extension fields automatically",
        },
        {
            "description": "POST /Groups requires Microsoft Entra Group extension with mailEnabled, mailNickname, securityEnabled",
            "rfc": "RFC 7643 §4.2 — Groups require only displayName; extension fields are optional",
            "recommendation": "Use --profile entra to inject required extension fields automatically",
        },
    ],
    "fortiauthenticator": [
        {
            "description": "Responses use Content-Type 'text/html' instead of 'application/scim+json'",
            "rfc": "RFC 7644 §8.1 — SCIM responses MUST be identified as application/scim+json",
            "recommendation": "Set Content-Type: application/scim+json on all responses served from the SCIM base path (e.g. /scim/v2/)",
        },
        {
            "description": "Created/updated resources missing meta.created and meta.lastModified timestamps",
            "rfc": "RFC 7643 §3.1 — meta.created and meta.lastModified are required",
            "recommendation": "Include meta.created and meta.lastModified in all resource representations",
        },
        {
            "description": "POST create responses (201) missing Location header",
            "rfc": "RFC 7644 §3.3 — Location header should be present on 201 Created",
            "recommendation": "Return Location: <base>/<resource>/<id> on all create (POST) responses",
        },
        {
            "description": "Error response bodies missing required 'status' field",
            "rfc": "RFC 7644 §3.12 — SCIM error responses MUST include 'status' (string)",
            "recommendation": "Include \"status\": \"<http_code>\" in all SCIM error response JSON bodies",
        },
        {
            "description": "Discovery endpoints respond but are not SCIM-compliant due to response envelope issues (notably Content-Type)",
            "rfc": "RFC 7644 §4 — discovery endpoints must return SCIM-compliant responses",
            "recommendation": "Ensure /ServiceProviderConfig, /Schemas, and /ResourceTypes return SCIM responses (starting with Content-Type: application/scim+json)",
        },
    ],
}


# Recommended command template per profile
PROFILE_COMMANDS: Dict[str, str] = {
    "entra": (
        "scim-sanity probe https://graph.microsoft.com/rp/scim \\\n"
        "  --token <bearer-token> \\\n"
        "  --profile entra \\\n"
        "  --user-domain <tenant>.onmicrosoft.com \\\n"
        "  --compat \\\n"
        "  --i-accept-side-effects"
    ),
    "fortiauthenticator": (
        "scim-sanity probe https://<fortiauthenticator-host>/scim/v2 \\\n"
        "  --token <bearer-token> \\\n"
        "  --profile fortiauthenticator \\\n"
        "  --compat \\\n"
        "  --tls-no-verify \\\n"
        "  --i-accept-side-effects"
    ),
}


# External references per profile
PROFILE_REFERENCES: Dict[str, List[str]] = {
    "entra": [
        "Microsoft Entra SCIM server docs: https://learn.microsoft.com/en-us/entra/identity/app-provisioning/use-scim-to-provision-users-and-groups",
        "Get bearer token: Azure portal → Enterprise Apps → Provisioning → Entra SCIM endpoint + token",
        "RFC 7643 (SCIM Core Schema): https://www.rfc-editor.org/rfc/rfc7643",
        "RFC 7644 (SCIM Protocol): https://www.rfc-editor.org/rfc/rfc7644",
    ],
    "fortiauthenticator": [
        "FortiAuthenticator SCIM server profile validated against: v8.0.1 build0033 (GA)",
        "RFC 7643 (SCIM Core Schema): https://www.rfc-editor.org/rfc/rfc7643",
        "RFC 7644 (SCIM Protocol): https://www.rfc-editor.org/rfc/rfc7644",
    ],
}


# Human-readable description of request-side payload injections (documentation only).
# Each entry is a list of bullet strings printed by `scim-sanity profiles <name>`.
PROFILE_INJECTIONS: Dict[str, List[str]] = {
    "entra": [
        "Users: password, mailNickname, enterprise extension schema, Microsoft Entra User extension",
        "Groups: mailEnabled, mailNickname, securityEnabled, Microsoft Entra Group extension",
    ],
    "fortiauthenticator": [
        "None (no payload injection required; use --compat for response-envelope deviations)",
    ],
}


def _random_password() -> str:
    """Generate a random password meeting Azure AD complexity requirements.

    Azure requires: 8+ characters, uppercase, lowercase, digit, and a
    special character.  The password is generated fresh per probe run.
    """
    special = "!@#$%^&*"
    core = (
        secrets.choice(string.ascii_uppercase)
        + secrets.choice(string.ascii_lowercase)
        + secrets.choice(string.digits)
        + secrets.choice(special)
        + "".join(
            secrets.choice(string.ascii_letters + string.digits + special)
            for _ in range(8)
        )
    )
    lst = list(core)
    secrets.SystemRandom().shuffle(lst)
    return "".join(lst)


def get_extra_user_fields(profile: str, user_domain: Optional[str] = None) -> Dict[str, Any]:
    """Return extra fields to merge into user creation payloads for a profile.

    ``user_domain`` overrides the domain portion of ``userName``.  Required
    for profiles like ``entra`` where the server validates the domain against
    its list of verified tenant domains.
    """
    if profile == "entra":
        suffix = uuid.uuid4().hex[:8]
        fields: Dict[str, Any] = {
            "password": _random_password(),
            "schemas": [
                "urn:ietf:params:scim:schemas:core:2.0:User",
                "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                "urn:ietf:params:scim:schemas:extension:Microsoft:Entra:2.0:User",
            ],
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {},
            "urn:ietf:params:scim:schemas:extension:Microsoft:Entra:2.0:User": {
                "mailNickname": f"scim-sanity-test-{suffix}",
            },
        }
        if user_domain:
            fields["userName"] = f"scim-sanity-test-{suffix}@{user_domain}"
        return fields
    return {}


def get_extra_group_fields(profile: str, user_domain: Optional[str] = None) -> Dict[str, Any]:
    """Return extra fields to merge into group creation payloads for a profile."""
    if profile == "entra":
        suffix = uuid.uuid4().hex[:8]
        return {
            "schemas": [
                "urn:ietf:params:scim:schemas:core:2.0:Group",
                "urn:ietf:params:scim:schemas:extension:Microsoft:Entra:2.0:Group",
            ],
            "urn:ietf:params:scim:schemas:extension:Microsoft:Entra:2.0:Group": {
                "mailEnabled": False,
                "mailNickname": f"scim-sanity-test-group-{suffix}",
                "securityEnabled": True,
            },
        }
    return {}
