import json
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types
 
st.set_page_config(page_title="Teamcenter Test Case Generator", layout="wide")
 
st.title("Teamcenter Test Case Generator")
st.write(
    "Enter the requirement and the document location within Teamcenter to generate structured validation test steps."
)
 
api_key = st.sidebar.text_input("Gemini API Key", type="password")
 
SYSTEM_PROMPT = """
You are a Quality Assurance Automation Engineer specializing in Siemens Teamcenter PLM.
Take the user requirement and document location, and output a structured list of test steps for validation in Teamcenter.
 
Respond ONLY with a valid JSON array of objects with the following schema:
[
  {
    "step_number": 1,
    "document_location": "...",
    "action": "...",
    "preconditions": "...",
    "expected_result": "...",
    "pass_fail_criteria": "..."
  }
]
Do not wrap the JSON in markdown formatting or include preamble text.
"""
 
col1, col2 = st.columns([2, 1])
 
with col1:
    requirement = st.text_area(
        "Requirement Description",
        placeholder="Example: When submitting an Item Revision to the Release Workflow, ensure attached specification documents are converted and locked.",
        height=120,
    )
 
with col2:
    doc_location = st.text_input(
        "Document / Dataset Location",
        placeholder="e.g., Home > Project_A > ItemRev_00123/A > Attachments",
        help="Specify the folder path, Item Revision container, or Active Workspace tab where the document is located.",
    )
 
if st.button("Generate Test Case", type="primary"):
    if not api_key:
        st.error("Please provide a valid Gemini API Key in the sidebar.")
    elif not requirement.strip():
        st.warning("Please enter a requirement first.")
    else:
        with st.spinner("Generating test case with document location..."):
            try:
                client = genai.Client(api_key=api_key)
 
                # Combine requirement and location for the prompt
                full_input = (
                    f"Requirement: {requirement}\n"
                    f"Document/Dataset Location: {doc_location if doc_location.strip() else 'N/A'}"
                )
 
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_input,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
 
                test_steps = json.loads(response.text)
                df = pd.DataFrame(test_steps)
 
                # Reorder and rename columns for table presentation
                df = df.rename(
                    columns={
                        "step_number": "Step #",
                        "document_location": "Document / Path Location",
                        "action": "Action / Procedure",
                        "preconditions": "Preconditions",
                        "expected_result": "Expected Result",
                        "pass_fail_criteria": "Pass/Fail Criteria",
                    }
                )
 
                st.subheader("Generated Test Case Table")
                st.dataframe(df, use_container_width=True, hide_index=True)
 
                # CSV Export
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download Test Case as CSV",
                    data=csv,
                    file_name="teamcenter_test_case.csv",
                    mime="text/csv",
                )
 
            except Exception as e:
                st.error(f"Error generating test case: {e}")
