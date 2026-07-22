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

MARKETS = ["PL", "RO", "HU", "CZ"]
DOC_TYPES = {
    "PL": ["identity_card", "proof_of_address", "income_proof"],
    "RO": ["identity_document", "proof_of_address", "income_proof", "other"],
    "HU": ["identity_card", "address_card", "income_proof", "bank_account_documents"],
    "CZ": ["identity_card", "income_proof", "proof_of_residence", "evidence_of_expenses", "parameter_r"]
}

st.set_page_config(page_title="IPF Document Upload", page_icon="📄", layout="wide")

# --- Authentication ---
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.title("🔐 IPF Admin Portal - Login")
    password = st.text_input("Enter admin password:", type="password")
    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Invalid password")
    st.stop()

# --- Main App ---
st.title("📄 IPF Document Upload Portal")
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
        market = st.selectbox("Market", MARKETS)

    st.divider()

    uploaded_files = st.file_uploader(
        "Upload documents (drag and drop or browse)",
        type=["jpg", "jpeg", "png", "pdf", "tiff", "tif"],
        accept_multiple_files=True,
        help="Max 20 files, 25MB each. Supported: JPEG, PNG, PDF, TIFF"
    )

    if uploaded_files:
        st.subheader(f"📎 {len(uploaded_files)} file(s) selected")

        doc_types_selected = []
        for i, file in enumerate(uploaded_files):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.text(f"{file.name}")
            with col2:
                doc_type = st.selectbox(
                    "Type",
                    DOC_TYPES.get(market, DOC_TYPES["PL"]),
                    key=f"type_{i}"
                )
                doc_types_selected.append(doc_type)
            with col3:
                size_kb = file.size / 1024
                st.caption(f"{size_kb:.0f} KB")

        st.divider()

        if not application_id:
            st.warning("Please enter a Loan Application ID")
        elif st.button("🚀 Submit for Processing", type="primary", use_container_width=True):
            with st.spinner("Uploading documents and starting AI processing..."):
                try:
                    files_payload = [("files", (f.name, f.getvalue(), f.type or "application/octet-stream")) for f in uploaded_files]
                    data = {
                        "application_id": application_id,
                        "market": market,
                        "document_types": ",".join(doc_types_selected),
                        "uploaded_by": "admin"
                    }
                    response = requests.post(f"{BACKEND_URL}/api/upload", data=data, files=files_payload, timeout=60)

                    if response.ok:
                        result = response.json()
                        st.success(f"✅ {len(uploaded_files)} documents uploaded successfully!")
                        st.info(f"Batch ID: {result['batch_id']}")
                        st.info("🤖 AI processing started automatically. Check Processing Status for results.")
                    else:
                        st.error(f"❌ Upload failed: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Is the server running?")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# --- Upload History ---
elif page == "Upload History":
    st.header("📋 Upload History")
    try:
        response = requests.get(f"{BACKEND_URL}/api/upload/history", timeout=10)
        if response.ok:
            uploads = response.json().get("uploads", [])
            if uploads:
                for upload in uploads:
                    with st.expander(f"📦 {upload.get('application_id', 'N/A')} | {upload.get('status', '')} | {upload.get('started_at', '')[:10]}"):
                        st.json(upload)
            else:
                st.info("No uploads yet. Go to Upload Documents to get started.")
        else:
            st.warning("Could not fetch history from backend.")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend.")

# --- Processing Status ---
elif page == "Processing Status":
    st.header("📊 Processing Status")
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
                    st.success(f"Status: {wf_status} ✅")
                elif wf_status in ("PENDING_REVIEW", "PENDING_DECISION"):
                    st.warning(f"Status: {wf_status} ⏳")
                elif wf_status == "FAILED":
                    st.error(f"Status: {wf_status} ❌")
                else:
                    st.info(f"Status: {wf_status}")

                # Documents
                st.subheader("Documents")
                for doc in status.get("documents", []):
                    icon = "✅" if doc["status"] == "VERIFIED" else "⏳" if doc["status"] == "PROCESSING" else "🔴"
                    st.write(f"{icon} {doc['filename']} ({doc['type']}) — {doc['status']}")
            else:
                st.warning(f"Application '{app_id}' not found.")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend.")
