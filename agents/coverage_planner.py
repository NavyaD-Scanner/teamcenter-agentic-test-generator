import json
from utils.ai_client import call_ai
from utils.json_utils import extract_json

SYSTEM_PROMPT = """
You are the Coverage Planning Agent, a Siemens Teamcenter test architect.
Create a requirement-specific coverage plan from the analyzed rules. Select only applicable categories: positive,
negative, mandatory property, property validation, boundary, workflow initiation, task assignment, approval,
rejection, rework, signoff, quorum, release status, access control, role authorization, dataset, revision, BOM,
project assignment, search/visibility, audit, notification, integration, concurrency, recovery, performance, regression.
Every rule must have coverage. Convert each rule into a positive and negative objective when logically applicable.
Do not add unrelated generic coverage. Return valid JSON only.
"""


def plan_coverage(analysis):
    prompt = f"""
Analyzed requirement:
{json.dumps(analysis, indent=2)}

Return:
{{"coverage_items":[{{
  "rule_id":"BR-01",
  "category":"Positive Functional",
  "test_objective":"",
  "priority":"High",
  "required_test_count":1,
  "reason":""
}}]}}
"""
    return extract_json(call_ai(SYSTEM_PROMPT, prompt))
