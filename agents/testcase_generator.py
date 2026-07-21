import json

from utils.ai_client import call_ai


SYSTEM_PROMPT = """
You are a senior Siemens Teamcenter QA engineer.

Generate realistic and executable Teamcenter test cases from the analyzed
requirement and coverage plan.

Important rules:

1. Do not generate generic test cases.
2. Every test case must map to at least one requirement rule.
3. Use the exact workflow, property, object, dataset, role and status names
   supplied in the requirement.
4. Do not invent customer-specific Teamcenter configuration.
5. Add assumptions when necessary.
6. Create positive and negative cases where logically applicable.
7. Each test step must contain a measurable expected result.
8. Use actual Teamcenter or Active Workspace tester actions.
9. Do not use vague steps such as "verify everything".
10. Ensure that test case IDs are unique.
11. Return valid JSON only.
"""


def generate_testcases(requirement_data, analysis, coverage_plan):
    request = f"""
Original requirement:

{json.dumps(requirement_data, indent=2)}

Requirement analysis:

{json.dumps(analysis, indent=2)}

Coverage plan:

{json.dumps(coverage_plan, indent=2)}

Generate test cases in this JSON structure:

{{
  "test_cases": [
    {{
      "test_case_id": "TC-001",
      "requirement_id": "",
      "title": "",
      "module": "",
      "category": "",
      "priority": "High",
      "objective": "",
      "user_role": "",
      "preconditions": [],
      "test_data": [],
      "steps": [
        {{
          "step_number": 1,
          "action": "",
          "expected_result": ""
        }}
      ],
      "final_expected_result": "",
      "postconditions": [],
      "automation_candidate": "Yes",
      "traceability": ["BR-01"],
      "assumptions": []
    }}
  ]
}}
"""

    response = call_ai(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=request
    )

    return json.loads(response)

