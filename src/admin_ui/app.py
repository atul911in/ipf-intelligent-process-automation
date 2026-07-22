"""
IPF IPA PoC - Admin Upload Portal (Streamlit)
Allows back-office admins to upload documents for processing.
"""
import streamlit as st
import requests
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ipf-admin-2026")

MARKET_OPTIONS = {
    "Poland (PL)": "PL",
    "Romania (RO)": "RO",
    "Hungary (HU)": "HU",
    "Czech Republic (CZ)": "CZ"
}
SUPPORTING_DOC_TYPES = {
    "PL": ["identity_card", "proof_of_address", "income_proof", "bank_statement"],
    "RO": ["identity_document", "proof_of_address", "income_proof", "bank_statement", "other"],
    "HU": ["identity_card", "address_card", "income_proof", "bank_account_documents"],
    "CZ": ["identity_card", "income_proof", "proof_of_residence", "bank_statement", "evidence_of_expenses", "parameter_r"]
}

st.set_page_config(page_title="IPF Document Upload", page_icon="", layout="wide")

# --- Authentication ---
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.title("IPF Document Upload Portal - Login")
    password = st.text_input("Enter admin password:", type="password")
    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Invalid password")
    st.stop()

# --- Main App ---
st.title("IPF Document Upload Portal")
st.markdown("Upload customer documents for AI-powered extraction and verification.")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio("", ["Upload Documents", "Upload History", "Processing Status"])
    st.divider()
    st.caption("IPF IPA PoC v1.0")
    if st.button("Logout"):
        st.session_state.admin_authenticated = False
        st.rerun()

# --- Upload Page ---
if page == "Upload Documents":
    st.header("Upload New Documents")

    col1, col2 = st.columns(2)
    with col1:
        application_id = st.text_input("Loan Application ID", placeholder="APP-PL-001")
    with col2:
        market_label = st.selectbox("Market", list(MARKET_OPTIONS.keys()))
        market = MARKET_OPTIONS[market_label]

    st.divider()
    st.subheader("Step 1: Loan Application Form")
    st.caption("Upload the customer signed loan application form (single file)")
    loan_app_file = st.file_uploader(
        "Loan Application Form",
        type=["jpg","jpeg","png","pdf","tiff","tif"],
        accept_multiple_files=False,
        key="loan_app_upload"
    )
    if loan_app_file:
        st.success(f"Loan application form selected: {loan_app_file.name}")

    st.divider()
    st.subheader("Step 2: Supporting Documents")
    st.caption("Upload identity, address, income, bank documents")
    uploaded_files = st.file_uploader(
        "Supporting documents",
        type=["jpg","jpeg","png","pdf","tiff","tif"],
        accept_multiple_files=True,
        key="supporting_docs"
    )

    doc_types_selected = []
    if uploaded_files:
        st.write(f"{len(uploaded_files)} supporting file(s) selected")
        for i, file in enumerate(uploaded_files):
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.text(file.name)
            doc_type = c2.selectbox("Type", SUPPORTING_DOC_TYPES.get(market, SUPPORTING_DOC_TYPES["PL"]), key=f"type_{i}")
            doc_types_selected.append(doc_type)
            c3.caption(f"{file.size//1024} KB")

    st.divider()
    if not application_id:
        st.warning("Please enter a Loan Application ID")
    elif st.button("Submit for Processing", type="primary", use_container_width=True):
        with st.spinner("Uploading..."):
            try:
                all_files = []
                all_types = []
                if loan_app_file:
                    all_files.append(loan_app_file)
                    all_types.append("loan_application")
                if uploaded_files:
                    all_files.extend(uploaded_files)
                    all_types.extend(doc_types_selected)
                if not all_files:
                    st.warning("Please select at least one document")
                else:
                    fp = [("files", (f.name, f.getvalue(), f.type or "application/octet-stream")) for f in all_files]
                    data = {"application_id": application_id, "market": market,
                            "document_types": ",".join(all_types), "uploaded_by": "admin"}
                    resp = requests.post(f"{BACKEND_URL}/api/upload", data=data, files=fp, timeout=60)
                    if resp.ok:
                        r = resp.json()
                        st.success(f"{len(all_files)} document(s) uploaded!")
                        if loan_app_file:
                            st.success("Loan application form included - cross-reference enabled")
                        else:
                            st.warning("No loan application form - cross-reference will be limited")
                        st.info(f"Batch ID: {r['batch_id']}")
                        st.info("AI processing started automatically")
                    else:
                        st.error(f"Upload failed: {resp.text}")
            except Exception as e:
                st.error(f"Error: {e}")

elif page == "Upload History":
    st.header(" Upload History")
    try:
        response = requests.get(f"{BACKEND_URL}/api/upload/history", timeout=10)
        if response.ok:
            uploads = response.json().get("uploads", [])
            if uploads:
                for upload in uploads:
                    with st.expander(f" {upload.get('application_id', 'N/A')} | {upload.get('status', '')} | {upload.get('started_at', '')[:10]}"):
                        st.json(upload)
            else:
                st.info("No uploads yet. Go to Upload Documents to get started.")
        else:
            st.warning("Could not fetch history from backend.")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend.")

# --- Processing Status ---
elif page == "Processing Status":
    st.header(" Processing Status")
    app_id = st.text_input("Enter Application ID to check status:")

    if app_id and st.button("Check Status"):
        try:
            response = requests.get(f"{BACKEND_URL}/api/status/{app_id}", timeout=10)
            if response.ok:
                status = response.json()
                st.subheader(f"Application: {status['application_id']}")

                # Workflow status
                wf_status = status.get("workflow_status", "UNKNOWN")
                if wf_status == "DECIDED":
                    st.success(f"Status: {wf_status} ")
                elif wf_status in ("PENDING_REVIEW", "PENDING_DECISION"):
                    st.warning(f"Status: {wf_status} ")
                elif wf_status == "FAILED":
                    st.error(f"Status: {wf_status} ")
                else:
                    st.info(f"Status: {wf_status}")

                # Documents
                st.subheader("Documents")
                for doc in status.get("documents", []):
                    icon = "" if doc["status"] == "VERIFIED" else "" if doc["status"] == "PROCESSING" else ""
                    st.write(f"{icon} {doc['filename']} ({doc['type']})  {doc['status']}")
            else:
                st.warning(f"Application '{app_id}' not found.")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend.")


