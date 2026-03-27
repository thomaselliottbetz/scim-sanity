"""Validates the example payload catalog against the SCIM validator.

Every example marked valid=True must pass validation.
Every example marked valid=False must fail, and each expected_error substring
must appear in at least one returned error message.
"""

import pytest
from scim_sanity.examples import EXAMPLES
from scim_sanity.validator import SCIMValidator


@pytest.mark.parametrize("example", EXAMPLES, ids=[e["id"] for e in EXAMPLES])
def test_example_validates_correctly(example):
    validator = SCIMValidator()
    is_valid, errors = validator.validate(example["payload"], example["operation"])

    if example["valid"]:
        assert is_valid, (
            f"Example '{example['id']}' is marked valid=True but failed validation:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
    else:
        assert not is_valid, (
            f"Example '{example['id']}' is marked valid=False but passed validation"
        )
        error_messages = " | ".join(str(e) for e in errors)
        for expected in example.get("expected_errors", []):
            assert expected.lower() in error_messages.lower(), (
                f"Example '{example['id']}': expected error substring '{expected}' "
                f"not found in: {error_messages}"
            )
