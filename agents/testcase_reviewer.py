import json
from utils.ai_client import call_ai
from utils.json_utils import extract_json

SYSTEM_PROMPT = """
You are the independent Review and Correction Agent for Siemens Teamcenter test cases.
Check semantic alignment, complete rule coverage, executable steps, measurable expected results, positive/negative paths,
workflow approve/reject/rework, role/access validation, status behavior, unique IDs, exact traceability and duplicates.
Remove generic or unrelated cases. Correct defects directly without inventing configuration.
If essential information is missing, retain safe cases and list focused clarification questions.
Calculate all summary counts from the final corrected test cases. Return valid JSON only.
"""


def review_testcases(requirement_data, analysis, coverage_plan, generated_testcases):
    prompt = f"""
Original requirement:
{json.dumps(requirement_data, indent=2)}
Analysis:
{json.dumps(analysis, indent=2)}
Coverage plan:
{json.dumps(coverage_plan, indent=2)}
Generated test cases:
{json.dumps(generated_testcases, indent=2)}

Return:
{{
 "review_summary":{{"quality_score":0,"issues_found":[],"corrections_made":[],"uncovered_rules":[],"clarification_questions":[]}},
 "test_cases":[],
 "traceability_matrix":[{{"rule_id":"","rule":"","test_case_ids":[],"coverage_type":"","coverage_status":"Covered"}}],
 "coverage_summary":{{
   "total_rules":0,"total_test_cases":0,"positive_test_cases":0,"negative_test_cases":0,
   "workflow_test_cases":0,"access_test_cases":0,"high_priority_test_cases":0,
   "automation_candidates":0,"covered_rules":0,"partially_covered_rules":0,"blocked_rules":0
 }}
}}
"""
    return extract_json(call_ai(SYSTEM_PROMPT, prompt))
