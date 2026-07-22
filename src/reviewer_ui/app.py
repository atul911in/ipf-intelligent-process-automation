"""
IPF IPA PoC - Document Review Portal (Streamlit)
Allows document reviewers and credit assessors to:
- View AI extraction results with confidence scores
- Correct field values
- Approve or decline loan applications
"""
import streamlit as st
import requests
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
REVIEWER_PASSWORD = os.getenv("REVIEWER_PASSWORD", "ipf-reviewer-2026")
ASSESSOR_PASSWORD = os.getenv("ASSESSOR_PASSWORD", "ipf-assessor-2026")

st.set_page_config(page_title="IPF Document Review", page_icon="🔍", layout="wide")


# --- Authentication ---
def check_auth():
    if "reviewer_authenticated" not in st.session_state:
        st.session_state.reviewer_authenticated = False
        st.session_state.reviewer_role = None

    if not st.session_state.reviewer_authenticated:
        st.title("🔐 IPF Document Review Portal - Login")
        role = st.selectbox("Login as:", ["Document Reviewer", "Credit Assessor"])
        password = st.text_input("Password:", type="password")
        if st.button("Login"):
            expected = ASSESSOR_PASSWORD if role == "Credit Assessor" else REVIEWER_PASSWORD
            if password == expected:
                st.session_state.reviewer_authenticated = True
                st.session_state.reviewer_role = role
                st.session_state.reviewer_id = role.lower().replace(" ", "_")
                st.rerun()
            else:
                st.error("Invalid password")
        st.stop()


check_auth()

role = st.session_state.reviewer_role
reviewer_id = st.session_state.reviewer_id


# --- Confidence colour helper ---
def confidence_colour(score: int) -> str:
    if score >= 85:
        return "🟢"
    elif score >= 70:
        return "🟡"
    else:
        return "🔴"


def validation_icon(status: str) -> str:
    return {"PASS": "✅", "FAIL": "❌", "WARNING": "⚠️", "PENDING": "⏳"}.get(status, "❓")


# --- Main App ---
st.title("🔍 IPF Document Review Portal")
st.caption(f"Logged in as: **{role}**")

with st.sidebar:
    st.header("Navigation")
    page = st.radio("", ["Work Queue", "Review Document", "Loan Decision", "Audit Trail"])
    st.divider()
    st.caption("IPF IPA PoC v1.0")
    if st.button("Logout"):
        st.session_state.reviewer_authenticated = False
        st.rerun()


# ─────────────────────────────────────────────
# WORK QUEUE
# ─────────────────────────────────────────────
if page == "Work Queue":
    st.header("📋 Work Queue")

    col1, col2 = st.columns([2, 1])
    with col2:
        status_filter = st.selectbox("Filter by status:", ["All", "PENDING_REVIEW", "EXTRACTED", "VERIFIED"])

    try:
        params = {} if status_filter == "All" else {"status": status_filter}
        response = requests.get(f"{BACKEND_URL}/api/queue", params=params, timeout=10)

        if response.ok:
            items = response.json().get("items", [])
            if items:
                st.markdown(f"**{len(items)} item(s) in queue**")
                for item in items:
                    status = item.get("status", "")
                    icon = "🔴" if status == "PENDING_REVIEW" else "✅" if status == "VERIFIED" else "⏳"
                    with st.expander(f"{icon} App: **{item.get('application_id')}** | {item.get('document_type', '').replace('_', ' ').title()} | {item.get('market')} | {status}"):
                        col_a, col_b = st.columns(2)
                        col_a.write(f"**Document ID:** `{item.get('id')}`")
                        col_b.write(f"**Uploaded:** {item.get('uploaded_at', '')[:10]}")
                        col_a.write(f"**File:** {item.get('original_filename', '')}")
                        col_b.write(f"**Market:** {item.get('market', '')}")

                        if st.button("Open for Review", key=f"open_{item['id']}"):
                            st.session_state.selected_doc_id = item["id"]
                            st.session_state.selected_app_id = item.get("application_id")
                            st.rerun()
            else:
                st.info("✅ No items in queue. All documents reviewed.")
        else:
            st.error("Could not fetch queue.")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend.")


# ─────────────────────────────────────────────
# REVIEW DOCUMENT
# ─────────────────────────────────────────────
elif page == "Review Document":
    st.header("📄 Document Review")

    doc_id = st.text_input(
        "Document ID:",
        value=st.session_state.get("selected_doc_id", ""),
        placeholder="Enter document ID from work queue"
    )

    if doc_id and st.button("Load Document"):
        st.session_state.current_doc_id = doc_id

    if st.session_state.get("current_doc_id"):
        doc_id = st.session_state.current_doc_id
        try:
            response = requests.get(f"{BACKEND_URL}/api/review/{doc_id}", timeout=15)
            if response.ok:
                data = response.json()
                extractions = data.get("extractions", [])

                st.subheader(f"{data.get('document_type', '').replace('_', ' ').title()} — {data.get('market', '')} Market")
                st.caption(f"File: {data.get('original_filename', '')} | Status: {data.get('status', '')}")

                col_img, col_fields = st.columns([1, 1])

                # --- Original Document Image ---
                with col_img:
                    st.subheader("📷 Original Document")
                    image_url = data.get("image_url")
                    if image_url:
                        st.image(image_url, use_container_width=True)
                    else:
                        st.info("Document image not available")

                # --- Extracted Fields ---
                with col_fields:
                    st.subheader("🤖 AI Extracted Fields")

                    if not extractions:
                        st.warning("No extractions found for this document.")
                    else:
                        # Summary bar
                        high_conf = sum(1 for e in extractions if e.get("confidence", 0) >= 85)
                        needs_review = len(extractions) - high_conf
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Total Fields", len(extractions))
                        c2.metric("🟢 High Confidence", high_conf)
                        c3.metric("🔴 Needs Review", needs_review)

                        st.divider()

                        corrections = {}
                        for ext in extractions:
                            conf = ext.get("confidence", 0)
                            val_status = ext.get("validation_status", "PENDING")
                            current_value = ext.get("corrected_value") or ext.get("extracted_value") or ""
                            field_name = ext.get("field_name", "").replace("_", " ").title()
                            icon = confidence_colour(conf)
                            v_icon = validation_icon(val_status)

                            with st.container():
                                row1, row2 = st.columns([3, 1])
                                row1.markdown(f"**{icon} {field_name}**")
                                row2.caption(f"{v_icon} {conf}%")

                                new_val = st.text_input(
                                    f"Value for {field_name}",
                                    value=current_value,
                                    key=f"field_{ext['id']}",
                                    label_visibility="collapsed"
                                )

                                if val_status == "FAIL":
                                    st.caption(f"⚠️ {ext.get('validation_reason', '')}")

                                if new_val != current_value:
                                    corrections[ext["id"]] = new_val

                        st.divider()

                        col_c, col_d = st.columns(2)

                        if corrections and col_c.button("💾 Submit Corrections", type="primary"):
                            payload = [{"extraction_id": eid, "corrected_value": val, "corrected_by": reviewer_id}
                                       for eid, val in corrections.items()]
                            r = requests.post(f"{BACKEND_URL}/api/review/{doc_id}/correct", json=payload, timeout=10)
                            if r.ok:
                                st.success("✅ Corrections saved and document marked verified.")
                            else:
                                st.error(f"Failed: {r.text}")

                        if col_d.button("✅ Confirm All Fields Correct"):
                            r = requests.post(f"{BACKEND_URL}/api/review/{doc_id}/confirm",
                                              params={"reviewer_id": reviewer_id}, timeout=10)
                            if r.ok:
                                st.success("✅ Document confirmed as verified.")
                            else:
                                st.error(f"Failed: {r.text}")
            else:
                st.error(f"Document not found: {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend.")


# ─────────────────────────────────────────────
# LOAN DECISION (Credit Assessor only)
# ─────────────────────────────────────────────
elif page == "Loan Decision":
    st.header("⚖️ Loan Decision")

    if role != "Credit Assessor":
        st.warning("🔒 This page is only accessible to Credit Assessors.")
        st.stop()

    app_id = st.text_input(
        "Application ID:",
        value=st.session_state.get("selected_app_id", ""),
        placeholder="APP-PL-001"
    )

    if app_id and st.button("Load Application"):
        st.session_state.current_app_id = app_id

    if st.session_state.get("current_app_id"):
        app_id = st.session_state.current_app_id
        try:
            response = requests.get(f"{BACKEND_URL}/api/status/{app_id}", timeout=10)
            if response.ok:
                status = response.json()

                # Application summary
                st.subheader(f"Application: {app_id}")
                wf_status = status.get("workflow_status", "")
                docs = status.get("documents", [])
                verified = sum(1 for d in docs if d["status"] == "VERIFIED")

                col1, col2, col3 = st.columns(3)
                col1.metric("Documents", len(docs))
                col2.metric("Verified", verified)
                col3.metric("Status", wf_status)

                # Document status breakdown
                st.subheader("Document Summary")
                for doc in docs:
                    icon = "✅" if doc["status"] == "VERIFIED" else "❌"
                    st.write(f"{icon} {doc['filename']} ({doc['type']}) — {doc['status']}")

                # AI Recommendation
                recommendation = status.get("recommendation")
                if recommendation:
                    st.divider()
                    st.subheader("🤖 AI Recommendation")
                    if recommendation == "APPROVE":
                        st.success(f"AI Recommends: **{recommendation}**")
                    elif recommendation == "DECLINE":
                        st.error(f"AI Recommends: **{recommendation}**")
                    else:
                        st.warning(f"AI Recommends: **{recommendation}** (Refer to senior)")

                    st.caption("⚠️ This is an AI recommendation only. You must make the final decision.")

                # Decision
                if verified == len(docs) and len(docs) > 0:
                    st.divider()
                    st.subheader("Your Decision")
                    reason = st.text_area("Reason / Notes (optional):")
                    col_approve, col_decline = st.columns(2)

                    if col_approve.button("✅ APPROVE LOAN", type="primary", use_container_width=True):
                        payload = {
                            "decision": "APPROVE",
                            "assessor_id": reviewer_id,
                            "reason_codes": [reason] if reason else []
                        }
                        r = requests.post(f"{BACKEND_URL}/api/decision/{app_id}", json=payload, timeout=10)
                        if r.ok:
                            st.success("✅ Loan APPROVED and recorded in system.")
                            st.balloons()
                        else:
                            st.error(f"Failed: {r.text}")

                    if col_decline.button("❌ DECLINE LOAN", use_container_width=True):
                        payload = {
                            "decision": "DECLINE",
                            "assessor_id": reviewer_id,
                            "reason_codes": [reason] if reason else []
                        }
                        r = requests.post(f"{BACKEND_URL}/api/decision/{app_id}", json=payload, timeout=10)
                        if r.ok:
                            st.error("❌ Loan DECLINED and recorded in system.")
                        else:
                            st.error(f"Failed: {r.text}")
                else:
                    st.warning("⚠️ All documents must be verified before a decision can be made.")
            else:
                st.error("Application not found.")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend.")


# ─────────────────────────────────────────────
# AUDIT TRAIL
# ─────────────────────────────────────────────
elif page == "Audit Trail":
    st.header("📋 Audit Trail")

    app_id = st.text_input("Application ID:", placeholder="APP-PL-001")

    if app_id and st.button("Load Audit Trail"):
        try:
            response = requests.get(f"{BACKEND_URL}/api/audit/{app_id}", timeout=10)
            if response.ok:
                trail = response.json().get("audit_trail", [])
                if trail:
                    st.markdown(f"**{len(trail)} audit events for `{app_id}`:**")
                    for event in trail:
                        with st.expander(f"🔹 {event.get('action')} — {event.get('actor')} — {event.get('timestamp', '')[:19]}"):
                            st.json(event)
                else:
                    st.info("No audit events found.")
            else:
                st.error("Could not fetch audit trail.")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend.")
