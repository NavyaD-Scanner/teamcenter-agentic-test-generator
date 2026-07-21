import re
from copy import deepcopy

MODULE_COVERAGE = {
    "Item and Revision Management": "Object creation and revision management",
    "Dataset Management": "Dataset and named-reference management",
    "Workflow": "Workflow routing, signoff, approval, rejection, and rework",
    "BOM and Structure Management": "BOM structure and occurrence management",
    "Change Management": "Change object and lifecycle management",
    "Project Management": "Project assignment, membership, and visibility",
    "Access Manager": "Role-based authorization and object access",
    "Active Workspace": "Commands, panels, properties, and UI behavior",
}


def clean(value, default="Not specified"):
    if value is None:
        return default
    if isinstance(value, list):
        values = [str(x).strip() for x in value if str(x).strip()]
        return ", ".join(values) if values else default
    text = str(value).strip()
    return text or default


def lines(value):
    if not value:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip(" -•\t") for x in str(value).splitlines() if x.strip(" -•\t")]


def sentences(text):
    return [x.strip(" -•\t") for x in re.split(r"(?<=[.!?])\s+|\n+", str(text or "")) if x.strip(" -•\t")]


def has(text, words):
    low = text.lower()
    return any(word.lower() in low for word in words)


def rule_type(text):
    if has(text, ["workflow", "review", "approve", "reject", "rework", "signoff", "task", "performer"]):
        return "WF", "Workflow Rule"
    if has(text, ["role", "access", "permission", "authorized", "unauthorized", "only", "member", "non-member"]):
        return "AR", "Access Rule"
    if has(text, ["mandatory", "required", "invalid", "validation", "must not be empty", "maximum", "minimum", "format"]):
        return "VR", "Validation Rule"
    if has(text, ["dataset", "file", "named reference", "attachment", "property", "attribute", "item id", "revision id"]):
        return "DR", "Data Rule"
    return "BR", "Business Rule"


def extract_rules(data):
    candidates = sentences(data.get("requirement_description"))
    candidates += lines(data.get("business_rules"))
    for prop in lines(data.get("properties")):
        if has(prop, ["mandatory", "required", "validation", "maximum", "minimum", "format"]):
            candidates.append("Validate property: " + prop)
    markers = ["must", "should", "only", "cannot", "required", "mandatory", "when", "after", "before", "if", "workflow", "approve", "reject", "status", "access", "assign", "create", "update", "delete", "upload", "download", "release"]
    selected = [x for x in candidates if has(x, markers)] or candidates
    counts = {"BR": 0, "VR": 0, "WF": 0, "AR": 0, "DR": 0}
    result, seen = [], set()
    for candidate in selected:
        key = candidate.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        prefix, kind = rule_type(candidate)
        counts[prefix] += 1
        result.append({
            "rule_id": f"{prefix}-{counts[prefix]:02d}",
            "rule_type": kind,
            "rule": candidate,
            "positive_condition": "Complete the configured behavior with valid data and an authorized user.",
            "negative_condition": "Attempt the behavior with invalid, incomplete, or unauthorized input where applicable.",
            "priority": "High" if has(candidate, ["must", "mandatory", "only", "release", "approve", "reject"]) else "Medium",
        })
    if not result:
        result.append({"rule_id": "BR-01", "rule_type": "Business Rule", "rule": "The described functionality must operate successfully.", "positive_condition": "Complete with valid data.", "negative_condition": "Attempt with invalid or incomplete data.", "priority": "High"})
    return result


def build_analysis(data):
    module = clean(data.get("module"))
    object_type = clean(data.get("business_object_type"))
    workflow = clean(data.get("workflow"), "Not applicable")
    actors = []
    for actor in data.get("user_roles", []):
        if actor not in actors: actors.append(actor)
    for actor in data.get("performers", {}).values():
        if actor and actor != "Not selected" and actor not in actors: actors.append(actor)
    missing = []
    if object_type == "Not specified": missing.append("Business object type is not specified.")
    if not actors: missing.append("User roles are not specified.")
    dataset = clean(data.get("dataset_type"), "Not applicable")
    return {
        "requirement_id": clean(data.get("requirement_id"), "REQ-001"),
        "interpreted_requirement": clean(data.get("requirement_description")),
        "business_objective": clean(data.get("requirement_title")),
        "module": module,
        "feature": MODULE_COVERAGE.get(module, "Functional validation"),
        "actors": actors,
        "objects": [object_type],
        "datasets": [] if dataset == "Not applicable" else [dataset],
        "workflow": workflow,
        "properties": lines(data.get("properties")),
        "rules": extract_rules(data),
        "expected_outputs": [clean(data.get("expected_status"), "Expected business result")],
        "failure_conditions": ["Invalid or unauthorized operations are prevented without corrupting data."],
        "dependencies": ["The required Teamcenter configuration, users, roles, and test data exist."],
        "assumptions": ["The test environment is available.", "Selected users have the intended group and role assignments."],
        "missing_information": missing,
    }


def category(rule):
    return {"Workflow Rule": "Workflow", "Access Rule": "Access Control", "Validation Rule": "Validation", "Data Rule": "Data Validation"}.get(rule["rule_type"], "Positive Functional")


def build_steps(data, rule, negative=False):
    module = clean(data.get("module")); obj = clean(data.get("business_object_type")); workflow = clean(data.get("workflow"), "Not applicable")
    roles = data.get("user_roles", []); role = roles[0] if roles else "Authorized Teamcenter User"
    expected_status = clean(data.get("expected_status"), "Not specified")
    steps = [
        {"step_number": 1, "action": f"Log in to Teamcenter or Active Workspace as {role}.", "expected_result": "Login succeeds and commands allowed for the selected role are displayed."},
        {"step_number": 2, "action": f"Navigate to the {module} functionality.", "expected_result": f"The {module} interface opens without an application error."},
        {"step_number": 3, "action": f"Create, locate, or open the required {obj} test object.", "expected_result": f"The required {obj} is available for testing."},
        {"step_number": 4, "action": f"Use {'invalid, incomplete, or unauthorized' if negative else 'valid'} test data and execute {rule['rule_id']}: {rule['rule']}", "expected_result": "The operation is prevented with an appropriate validation or authorization message." if negative else "The configured action is accepted without an unexpected error."},
    ]
    if workflow != "Not applicable" and has(rule["rule"], ["workflow", "approve", "reject", "review", "rework", "task", "status"]):
        steps.append({"step_number": len(steps)+1, "action": f"Open the {workflow} process, related tasks, and audit information.", "expected_result": "Task assignment, decision, process state, and audit information match the expected negative behavior." if negative else "Task assignment, decision, process state, and audit information match the requirement."})
    if expected_status != "Not specified":
        steps.append({"step_number": len(steps)+1, "action": "Refresh and reopen the target object, then inspect its release status.", "expected_result": f"The {expected_status} status is not incorrectly applied." if negative else f"The object has {expected_status} status only when all required conditions are satisfied."})
    return steps


def generate_cases(data, analysis):
    cases, number = [], 1
    roles = data.get("user_roles", []); role = roles[0] if roles else "Authorized Teamcenter User"
    for rule in analysis["rules"]:
        for negative in (False, True):
            test_id = f"TC-{number:03d}"; number += 1
            cases.append({
                "test_case_id": test_id,
                "requirement_id": analysis["requirement_id"],
                "title": ("Negative validation for " if negative else "Verify ") + f"{rule['rule_id']} - {rule['rule'][:90]}",
                "module": analysis["module"],
                "category": "Negative" if negative else category(rule),
                "priority": rule["priority"],
                "objective": ("Verify invalid, incomplete, or unauthorized execution is controlled for " if negative else "Verify successful implementation of ") + rule["rule"],
                "user_role": role,
                "preconditions": ["The Teamcenter test environment is available.", "Required configuration and test data exist.", "The test user has the intended role or intentionally lacks it for an access-negative test."],
                "test_data": [("Invalid/incomplete/unauthorized" if negative else "Valid") + " test object and property values.", "Requirement rule: " + rule["rule"]],
                "steps": build_steps(data, rule, negative),
                "final_expected_result": "The invalid operation is prevented and no incorrect data, status, or workflow result occurs." if negative else f"The behavior completes successfully and satisfies {rule['rule_id']}.",
                "postconditions": ["Record created or modified test data and restore reusable data when required."],
                "automation_candidate": "Yes",
                "traceability": [rule["rule_id"]],
                "assumptions": deepcopy(analysis["assumptions"]),
                "actual_result": "",
                "status": "Not Executed",
            })
    return cases


def generate_offline(data):
    analysis = build_analysis(data)
    coverage = {"coverage_items": []}
    for rule in analysis["rules"]:
        for cat, objective in ((category(rule), "Verify successful behavior for: "), ("Negative", "Verify controlled failure or prevention for: ")):
            coverage["coverage_items"].append({"rule_id": rule["rule_id"], "category": cat, "test_objective": objective + rule["rule"], "priority": rule["priority"], "required_test_count": 1, "reason": "Requirement-derived offline coverage."})
    cases = generate_cases(data, analysis)
    matrix = []
    for rule in analysis["rules"]:
        ids = [x["test_case_id"] for x in cases if rule["rule_id"] in x["traceability"]]
        matrix.append({"rule_id": rule["rule_id"], "rule": rule["rule"], "test_case_ids": ids, "coverage_type": "Positive and Negative", "coverage_status": "Covered" if ids else "Not Covered"})
    def count(text): return sum(1 for x in cases if text.lower() in x["category"].lower())
    reviewed = {
        "review_summary": {"quality_score": 75, "issues_found": ["Offline mode uses deterministic rules rather than an LLM; manually review complex requirements."], "corrections_made": ["Generated positive and negative coverage and rule traceability."], "uncovered_rules": [], "clarification_questions": analysis["missing_information"]},
        "test_cases": cases,
        "traceability_matrix": matrix,
        "coverage_summary": {"generation_mode": "Offline", "total_rules": len(analysis["rules"]), "total_test_cases": len(cases), "positive_test_cases": len(cases)-count("Negative"), "negative_test_cases": count("Negative"), "workflow_test_cases": count("Workflow"), "access_test_cases": count("Access"), "high_priority_test_cases": sum(1 for x in cases if x["priority"] == "High"), "automation_candidates": sum(1 for x in cases if x["automation_candidate"] == "Yes"), "covered_rules": len(matrix), "partially_covered_rules": 0, "blocked_rules": 0},
    }
    return {"analysis": analysis, "coverage_plan": coverage, "reviewed_result": reviewed}
