import json
from utils.ai_client import call_ai
from utils.json_utils import extract_json

SYSTEM_PROMPT = """
You are the Requirement Analyzer Agent, a senior Siemens Teamcenter PLM business analyst and test architect.
Analyze the complete requirement semantically, sentence by sentence. Never rely only on keywords or the selected module.
Identify the business objective, exact actors, Teamcenter objects, datasets, workflow, properties, statuses, dependencies,
preconditions, success behavior, failure behavior, ambiguity, and every independent rule.
Treat must, must not, only, except, when, unless, after, before, if, and then as important constraints.
Assign unique rule IDs: BR for business rules, VR for validations, WF for workflows, AR for access, and DR for data.
Do not invent customer-specific object types, properties, preferences, handlers, workflow templates, roles, or statuses.
Use supplied names exactly. Clearly mark assumptions and missing information. Return valid JSON only.
"""


def analyze_requirement(requirement_data):
    prompt = f"""
Analyze this Teamcenter requirement:
{json.dumps(requirement_data, indent=2)}

Return exactly this top-level structure:
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
  "rules": [{{
    "rule_id": "BR-01",
    "rule_type": "Business Rule",
    "rule": "",
    "positive_condition": "",
    "negative_condition": "",
    "priority": "High"
  }}],
  "expected_outputs": [],
  "failure_conditions": [],
  "dependencies": [],
  "assumptions": [],
  "missing_information": []
}}
"""
    return extract_json(call_ai(SYSTEM_PROMPT, prompt))
