import json

from utils.ai_client import call_ai


SYSTEM_PROMPT = """
You are an independent Siemens Teamcenter test-case reviewer.

Review and improve the generated test cases.

Verify:
- Every requirement rule is covered
- Test cases are requirement-specific
- Positive paths are covered
- Relevant negative paths are covered
- Workflow approval, rejection and rework are covered when applicable
- Role and access validation is covered when applicable
- Every action has an expected result
- Preconditions are executable
- Test data is clear
- Test case IDs are unique
- Traceability is accurate
- Duplicate cases are removed
- Customer-specific values are not invented

Correct the test cases directly.

Return valid JSON only.
"""


def review_testcases(
    requirement_data,
    analysis,
    coverage_plan,
    generated_testcases
):
    request = f"""
Original requirement:

{json.dumps(requirement_data, indent=2)}

Requirement analysis:

{json.dumps(analysis, indent=2)}

Coverage plan:

{json.dumps(coverage_plan, indent=2)}

Generated test cases:

{json.dumps(generated_testcases, indent=2)}

Return:

{{
  "review_summary": {{
    "quality_score": 0,
    "issues_found": [],
    "corrections_made": [],
    "uncovered_rules": [],
    "clarification_questions": []
  }},
  "test_cases": [],
  "traceability_matrix": [
    {{
      "rule_id": "",
      "rule": "",
      "test_case_ids": [],
      "coverage_type": "",
      "coverage_status": "Covered"
    }}
  ],
  "coverage_summary": {{
    "total_rules": 0,
    "total_test_cases": 0,
    "positive_test_cases": 0,
    "negative_test_cases": 0,
    "workflow_test_cases": 0,
    "access_test_cases": 0,
    "automation_candidates": 0,
    "covered_rules": 0,
    "partially_covered_rules": 0,
    "blocked_rules": 0
  }}
}}
"""

    response = call_ai(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=request
    )

    return json.loads(response)
