import json
import streamlit as st
from dotenv import load_dotenv
from agents.requirement_analyzer import analyze_requirement
from agents.coverage_planner import plan_coverage
from agents.testcase_generator import generate_testcases
from agents.testcase_reviewer import review_testcases
from agents.offline_generator import generate_offline
from utils.export_utils import create_excel
from utils.ai_client import get_provider_configuration, test_connection

load_dotenv()
st.set_page_config(page_title="Teamcenter Test Generator", page_icon="🧪", layout="wide")

@st.cache_data
def load_config():
    with open("config/teamcenter_config.json", "r", encoding="utf-8") as file:
        return json.load(file)

config = load_config()
st.title("Teamcenter Test Case Generator")
st.caption("Offline rule-based generation or optional connected AI generation")

with st.sidebar:
    st.header("Application Mode")
    generation_mode = st.radio("Generation Mode", ["Offline Generator", "AI Generator"], index=0, help="Offline mode needs no API key. AI mode requires OpenAI or Azure OpenAI.")
    st.header("Teamcenter Configuration")
    module = st.selectbox("Module", config["modules"])
    object_type = st.selectbox("Business Object Type", ["Not specified"] + config["business_object_types"])
    dataset_type = st.selectbox("Dataset Type", ["Not applicable"] + config["dataset_types"])
    workflow = st.selectbox("Workflow", ["Not applicable"] + list(config["workflows"].keys()))
    expected_status = st.selectbox("Expected Status", ["Not specified"] + config["release_statuses"])
    st.divider()
    if generation_mode == "AI Generator":
        st.subheader("AI Connection")
        try:
            provider = get_provider_configuration()
            st.success(f"Configured provider: {provider['provider'].upper()}")
            st.caption(f"Deployment: {provider['deployment']}" if provider["provider"] == "azure" else f"Model: {provider['model']}")
            if st.button("Test AI Connection", use_container_width=True):
                result = test_connection()
                st.success(result["message"]) if result["success"] else st.error(result["message"])
        except Exception as error:
            st.error(str(error))
    else:
        st.info("Offline mode is active. No API key is required.")

c1, c2 = st.columns(2)
with c1: requirement_id = st.text_input("Requirement ID", "REQ-001")
with c2: requirement_title = st.text_input("Requirement Title")
requirement_description = st.text_area("Requirement Description", height=220)
selected_roles = st.multiselect("User Roles", config["roles"])
performers = {}
if workflow != "Not applicable":
    st.subheader("Workflow Performers")
    cols = st.columns(2)
    for i, name in enumerate(config["workflows"].get(workflow, [])):
        with cols[i % 2]: performers[name] = st.selectbox(name, ["Not selected"] + config["roles"], key=f"performer_{name}")
properties = st.text_area("Properties and Attributes", placeholder="One property per line, including mandatory/optional and validation details.")
business_rules = st.text_area("Business Rules", placeholder="Enter exact business, access, workflow, and validation rules.")
additional = st.text_area("Additional Instructions")
button_label = "Generate Offline Test Cases" if generation_mode == "Offline Generator" else "Generate AI Test Cases"

if st.button(button_label, type="primary", use_container_width=True):
    if not requirement_title.strip() or not requirement_description.strip():
        st.error("Requirement title and description are required."); st.stop()
    data = {"requirement_id": requirement_id, "requirement_title": requirement_title, "requirement_description": requirement_description, "module": module, "business_object_type": object_type, "dataset_type": dataset_type, "workflow": workflow, "performers": performers, "user_roles": selected_roles, "properties": properties, "business_rules": business_rules, "expected_status": expected_status, "additional_instructions": additional}
    try:
        progress = st.progress(0)
        if generation_mode == "Offline Generator":
            with st.status("Running offline Teamcenter generator...", expanded=True) as status:
                st.write("Extracting rules and generating test coverage")
                result = generate_offline(data); progress.progress(100)
                analysis, coverage, reviewed = result["analysis"], result["coverage_plan"], result["reviewed_result"]
                status.update(label="Offline generation completed", state="complete")
        else:
            with st.status("Running four-agent AI workflow...", expanded=True) as status:
                st.write("1/4 Analyzing requirement"); analysis = analyze_requirement(data); progress.progress(25)
                st.write("2/4 Planning coverage"); coverage = plan_coverage(analysis); progress.progress(50)
                st.write("3/4 Generating cases"); generated = generate_testcases(data, analysis, coverage); progress.progress(75)
                st.write("4/4 Reviewing cases"); reviewed = review_testcases(data, analysis, coverage, generated); progress.progress(100)
                status.update(label="AI generation completed", state="complete")
        st.session_state.update(data=data, analysis=analysis, coverage=coverage, reviewed=reviewed, mode=generation_mode)
    except Exception as error:
        st.error(str(error)); st.exception(error)

if "reviewed" in st.session_state:
    analysis, coverage, reviewed = st.session_state.analysis, st.session_state.coverage, st.session_state.reviewed
    st.info(f"Result generated using: {st.session_state.mode}")
    tabs = st.tabs(["Requirement Analysis", "Coverage Plan", "Test Cases", "Traceability", "Review"])
    with tabs[0]: st.json(analysis)
    with tabs[1]: st.json(coverage)
    with tabs[2]:
        cases = reviewed.get("test_cases", []); st.metric("Total Test Cases", len(cases))
        for case in cases:
            with st.expander(f'{case.get("test_case_id", "")} - {case.get("title", "")}'):
                st.write(f'**Category:** {case.get("category", "")} | **Priority:** {case.get("priority", "")} | **Role:** {case.get("user_role", "")}')
                st.write("**Objective:**", case.get("objective", ""))
                st.write("**Preconditions:**")
                for item in case.get("preconditions", []): st.write("-", item)
                st.write("**Steps:**")
                for step in case.get("steps", []):
                    st.markdown(f'**{step.get("step_number")}. Action:** {step.get("action", "")}')
                    st.success(f'Expected: {step.get("expected_result", "")}')
                st.write("**Traceability:**", ", ".join(case.get("traceability", [])))
    with tabs[3]: st.dataframe(reviewed.get("traceability_matrix", []), use_container_width=True); st.json(reviewed.get("coverage_summary", {}))
    with tabs[4]: st.json(reviewed.get("review_summary", {}))
    excel = create_excel(reviewed)
    st.download_button("Download Excel", excel, f'{st.session_state.data.get("requirement_id", "REQ")}_teamcenter_test_cases.xlsx', "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
