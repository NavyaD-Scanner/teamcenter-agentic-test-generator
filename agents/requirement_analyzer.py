import json

from utils.ai_client import call_ai


SYSTEM_PROMPT = """
You are a senior Siemens Teamcenter business analyst and test architect.

Analyze the complete requirement semantically. Do not perform simple
keyword matching.

You must identify:
- Business objective
- Teamcenter module
- Feature
- Actors
- Business objects
- Dataset types
- Workflow
- Properties
- Business rules
- Validation rules
- Workflow rules
- Access rules
- Expected results
- Failure conditions
- Dependencies
- Assumptions
- Missing information

Extract every independent rule and give it a unique rule ID.

Use:
- BR for business rules
- VR for validation rules
- WF for workflow rules
- AR for access rules
- DR for data rules

Return valid JSON only. Do not include markdown or an explanation.
"""


def build_analysis_request(requirement_data):
    return f"""
Analyze the following Teamcenter requirement.

Requirement ID:
{requirement_data.get("requirement_id")}

Requirement Title:
{requirement_data.get("requirement_title")}

Requirement Description:
{requirement_data.get("requirement_description")}

Selected Module:
{requirement_data.get("module")}

Business Object Type:
{requirement_data.get("business_object_type")}

Dataset Type:
{requirement_data.get("dataset_type")}

Workflow:
{requirement_data.get("workflow")}

Selected Performers:
{requirement_data.get("performers")}

User Roles:
{requirement_data.get("user_roles")}

Properties:
{requirement_data.get("properties")}

Business Rules:
{requirement_data.get("business_rules")}

Expected Status:
{requirement_data.get("expected_status")}

Additional Instructions:
{requirement_data.get("additional_instructions")}

Return this JSON structure:

{{
  "requirement_id": "",
  "interpreted_requirement": "",
  "business_objective": "",
  "module": "",
  "feature": "",
  "actors": [],
  "objects": [],
  "datasets": [],
  "workflow": "",
  "properties": [],
  "rules": [
    {{
      "rule_id": "BR-01",
      "rule_type": "Business Rule",
      "rule": "",
      "positive_condition": "",
      "negative_condition": "",
      "priority": "High"
    }}
  ],
  "expected_outputs": [],
  "failure_conditions": [],
  "dependencies": [],
  "assumptions": [],
  "missing_information": []
}}
"""


def analyze_requirement(requirement_data):
    request = build_analysis_request(requirement_data)

    response = call_ai(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=request
    )

    return json.loads(response)
