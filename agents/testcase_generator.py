import json
from utils.ai_client import call_ai
from utils.json_utils import extract_json

SYSTEM_PROMPT = """
You are the Test Case Generator Agent, a senior Siemens Teamcenter QA engineer.
Generate realistic, executable and requirement-specific test cases. Every case must trace to one or more extracted rules.
Use exact supplied workflow, object, dataset, property, role, group and status names. Never invent client configuration.
Include positive and applicable negative, authorization, workflow rejection/rework, status and audit cases.
Each step must be an actual Teamcenter or Active Workspace tester action and must have a measurable expected result.
Avoid vague actions such as 'validate everything' or 'verify workflow works'. Make IDs unique. Return valid JSON only.
"""


def generate_testcases(requirement_data, analysis, coverage_plan):
    prompt = f"""
Original requirement:
{json.dumps(requirement_data, indent=2)}

Analysis:
{json.dumps(analysis, indent=2)}

Coverage plan:
{json.dumps(coverage_plan, indent=2)}

Return:
{{"test_cases":[{{
 "test_case_id":"TC-001", "requirement_id":"", "title":"", "module":"", "category":"",
 "priority":"High", "objective":"", "user_role":"", "preconditions":[], "test_data":[],
 "steps":[{{"step_number":1,"action":"","expected_result":""}}],
 "final_expected_result":"", "postconditions":[], "automation_candidate":"Yes",
 "traceability":["BR-01"], "assumptions":[], "actual_result":"", "status":"Not Executed"
}}]}}
"""
    return extract_json(call_ai(SYSTEM_PROMPT, prompt))
