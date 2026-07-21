import re
from copy import deepcopy


MODULE_COVERAGE = {
    "Item and Revision Management": [
        "object creation",
        "mandatory properties",
        "duplicate ID",
        "save behavior",
        "revision creation",
        "ownership",
        "search visibility",
        "release status",
    ],
    "Dataset Management": [
        "dataset creation",
        "named reference",
        "file upload",
        "file download",
        "check-in",
        "check-out",
        "dataset version",
        "unsupported file type",
        "access permissions",
    ],
    "Workflow": [
        "workflow initiation",
        "target attachment",
        "performer assignment",
        "approval",
        "rejection",
        "rework",
        "release status",
        "audit history",
    ],
    "BOM and Structure Management": [
        "child addition",
        "child removal",
        "quantity",
        "find number",
        "occurrence properties",
        "duplicate component",
        "revision rule",
        "save behavior",
    ],
    "Change Management": [
        "change creation",
        "affected item",
        "solution item",
        "workflow",
        "approval",
        "status transition",
        "audit history",
    ],
    "Project Management": [
        "project creation",
        "project team",
        "project assignment",
        "member access",
        "non-member access",
        "project visibility",
    ],
    "Access Manager": [
        "read access",
        "write access",
        "delete access",
        "download access",
        "ownership",
        "role authorization",
    ],
    "Active Workspace": [
        "command visibility",
        "create panel",
        "edit panel",
        "property display",
        "summary view",
        "search",
        "messages",
        "refresh behavior",
    ],
}


def clean_value(value, default="Not specified"):
    if value is None:
        return default

    if isinstance(value, list):
        cleaned = [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

        return ", ".join(cleaned) if cleaned else default

    value = str(value).strip()

    if not value:
        return default

    return value


def normalize_lines(value):
    if not value:
        return []

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    return [
        line.strip(" -•\t")
        for line in str(value).splitlines()
        if line.strip(" -•\t")
    ]


def sentence_split(text):
    if not text:
        return []

    sentences = re.split(
        r"(?<=[.!?])\s+|\n+",
        str(text)
    )

    return [
        sentence.strip(" -•\t")
        for sentence in sentences
        if sentence.strip(" -•\t")
    ]


def contains_any(text, keywords):
    normalized = text.lower()

    return any(
        keyword.lower() in normalized
        for keyword in keywords
    )


def append_unique(values, new_value):
    if new_value and new_value not in values:
        values.append(new_value)


def detect_rule_type(sentence):
    text = sentence.lower()

    if contains_any(
        text,
        [
            "workflow",
            "review",
            "approve",
            "reject",
            "rework",
            "signoff",
            "task",
            "performer",
        ],
    ):
        return "WF", "Workflow Rule"

    if contains_any(
        text,
        [
            "role",
            "access",
            "permission",
            "authorized",
            "unauthorized",
            "only",
            "member",
            "non-member",
        ],
    ):
        return "AR", "Access Rule"

    if contains_any(
        text,
        [
            "mandatory",
            "required",
            "invalid",
            "validation",
            "must not be empty",
            "maximum",
            "minimum",
            "format",
        ],
    ):
        return "VR", "Validation Rule"

    if contains_any(
        text,
        [
            "dataset",
            "file",
            "named reference",
            "attachment",
            "property",
            "attribute",
            "item id",
            "revision id",
        ],
    ):
        return "DR", "Data Rule"

    return "BR", "Business Rule"


def extract_rules(requirement_data):
    description = clean_value(
        requirement_data.get(
            "requirement_description"
        ),
        "",
    )

    business_rules = normalize_lines(
        requirement_data.get("business_rules")
    )

    properties = normalize_lines(
        requirement_data.get("properties")
    )

    candidate_rules = sentence_split(description)
    candidate_rules.extend(business_rules)

    for property_definition in properties:
        property_text = property_definition.lower()

        if contains_any(
            property_text,
            [
                "mandatory",
                "required",
                "validation",
                "maximum",
                "minimum",
                "format",
            ],
        ):
            candidate_rules.append(
                "Validate property: "
                + property_definition
            )

    significant_words = [
        "must",
        "should",
        "only",
        "cannot",
        "must not",
        "required",
        "mandatory",
        "when",
        "after",
        "before",
        "if",
        "workflow",
        "approve",
        "reject",
        "status",
        "access",
        "assign",
        "create",
        "update",
        "delete",
        "upload",
        "download",
        "release",
    ]

    filtered_rules = [
        rule
        for rule in candidate_rules
        if contains_any(rule, significant_words)
    ]

    if not filtered_rules:
        filtered_rules = candidate_rules

    counters = {
        "BR": 0,
        "VR": 0,
        "WF": 0,
        "AR": 0,
        "DR": 0,
    }

    extracted_rules = []
    seen_rules = set()

    for candidate in filtered_rules:
        normalized_candidate = (
            candidate.strip().lower()
        )

        if normalized_candidate in seen_rules:
            continue

        seen_rules.add(normalized_candidate)

        prefix, rule_type = detect_rule_type(
            candidate
        )

        counters[prefix] += 1

        rule_id = (
            f"{prefix}-"
            f"{counters02d}"
        )

        extracted_rules.append(
            {
                "rule_id": rule_id,
                "rule_type": rule_type,
                "rule": candidate,
                "positive_condition": (
                    "The configured behavior is completed "
                    "using valid data and an authorized user."
                ),
                "negative_condition": (
                    "The behavior is attempted with invalid "
                    "data, missing information, or an "
                    "unauthorized user when applicable."
                ),
                "priority": (
                    "High"
                    if contains_any(
                        candidate,
                        [
                            "must",
                            "mandatory",
                            "only",
                            "release",
                            "approve",
                            "reject",
                        ],
                    )
                    else "Medium"
                ),
            }
        )

    if not extracted_rules:
        extracted_rules.append(
            {
                "rule_id": "BR-01",
                "rule_type": "Business Rule",
                "rule": (
                    "The functionality described by the "
                    "requirement must operate successfully."
                ),
                "positive_condition": (
                    "Complete the requested operation using "
                    "valid data."
                ),
                "negative_condition": (
                    "Attempt the requested operation using "
                    "invalid or incomplete data."
                ),
                "priority": "High",
            }
        )

    return extracted_rules


def build_analysis(requirement_data):
    module = clean_value(
        requirement_data.get("module")
    )

    object_type = clean_value(
        requirement_data.get(
            "business_object_type"
        )
    )

    workflow = clean_value(
        requirement_data.get("workflow"),
        "Not applicable",
    )

    roles = requirement_data.get(
        "user_roles",
        [],
    )

    performers = requirement_data.get(
        "performers",
        {},
    )

    actors = []

    for role in roles:
        append_unique(actors, role)

    for performer_role in performers.values():
        if performer_role != "Not selected":
            append_unique(actors, performer_role)

    rules = extract_rules(requirement_data)

    properties = normalize_lines(
        requirement_data.get("properties")
    )

    datasets = []

    dataset_type = clean_value(
        requirement_data.get("dataset_type"),
        "Not applicable",
    )

    if dataset_type != "Not applicable":
        datasets.append(dataset_type)

    missing_information = []

    if object_type == "Not specified":
        missing_information.append(
            "Business object type is not specified."
        )

    if not actors:
        missing_information.append(
            "User roles are not specified."
        )

    return {
        "requirement_id": clean_value(
            requirement_data.get(
                "requirement_id"
            ),
            "REQ-001",
        ),
        "interpreted_requirement": clean_value(
            requirement_data.get(
                "requirement_description"
            )
        ),
        "business_objective": clean_value(
            requirement_data.get(
                "requirement_title"
            )
        ),
        "module": module,
        "feature": (
            MODULE_COVERAGE.get(
                module,
                ["functional validation"],
            )[0]
        ),
        "actors": actors,
        "objects": [object_type],
        "datasets": datasets,
        "workflow": workflow,
        "properties": properties,
        "rules": rules,
        "expected_outputs": [
            clean_value(
                requirement_data.get(
                    "expected_status"
                ),
                "Expected business result",
            )
        ],
        "failure_conditions": [
            rule["negative_condition"]
            for rule in rules
        ],
        "dependencies": [
            "Required users, roles, test objects and "
            "Teamcenter configuration must exist."
        ],
        "assumptions": [
            "The target test environment is available.",
            "The selected users have the configured "
            "Teamcenter group and role assignments.",
        ],
        "missing_information": missing_information,
    }


def get_category(rule):
    rule_type = rule["rule_type"]

    mapping = {
        "Workflow Rule": "Workflow",
        "Access Rule": "Access Control",
        "Validation Rule": "Validation",
        "Data Rule": "Data Validation",
        "Business Rule": "Positive Functional",
    }

    return mapping.get(
        rule_type,
        "Positive Functional",
    )


def build_coverage_plan(analysis):
    coverage_items = []

    for rule in analysis["rules"]:
        category = get_category(rule)

        coverage_items.append(
            {
                "rule_id": rule["rule_id"],
                "category": category,
                "test_objective": (
                    "Verify successful behavior for: "
                    + rule["rule"]
                ),
                "priority": rule["priority"],
                "required_test_count": 1,
                "reason": (
                    "Positive validation of the "
                    "extracted requirement rule."
                ),
            }
        )

        coverage_items.append(
            {
                "rule_id": rule["rule_id"],
                "category": "Negative",
                "test_objective": (
                    "Verify controlled failure or "
                    "prevention for: "
                    + rule["rule"]
                ),
                "priority": rule["priority"],
                "required_test_count": 1,
                "reason": (
                    "Negative validation is required "
                    "for the extracted requirement rule."
                ),
            }
        )

    return {
        "coverage_items": coverage_items
    }


def build_standard_steps(
    requirement_data,
    rule,
    negative=False,
):
    module = clean_value(
        requirement_data.get("module")
    )

    object_type = clean_value(
        requirement_data.get(
            "business_object_type"
        )
    )

    workflow = clean_value(
        requirement_data.get("workflow"),
        "Not applicable",
    )

    expected_status = clean_value(
        requirement_data.get(
            "expected_status"
        ),
        "Not specified",
    )

    roles = requirement_data.
