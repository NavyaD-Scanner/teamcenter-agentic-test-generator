
import json

from utils.ai_client import call_ai


SYSTEM_PROMPT = """
You are a Siemens Teamcenter test architect.

Create a test coverage plan from the analyzed requirement.

Select only categories relevant to the identified rules.

Possible categories include:
- Positive functional
- Negative
- Mandatory property
- Property validation
- Boundary value
- Workflow initiation
- Task assignment
- Approval
- Rejection
- Rework
- Signoff
- Quorum
- Release status
- Access control
- Role authorization
- Dataset
- Revision
- BOM structure
- Project assignment
- Search and visibility
- Audit history
- Notification
- Integration
- Regression
- Performance

Each requirement rule must be covered.

Return valid JSON only.
"""


def plan_coverage(analysis):
    request = f"""
Create a Teamcenter test coverage plan for this analyzed requirement:

{json.dumps(analysis, indent=2)}

Return:

{{
  "coverage_items": [
    {{
      "rule_id": "BR-01",
      "category": "Positive Functional",
      "test_objective": "",
      "priority": "High",
      "required_test_count": 1,
      "reason": ""
    }}
  ]
}}
"""

    response = call_ai(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=request
    )

    return json.loads(response)
