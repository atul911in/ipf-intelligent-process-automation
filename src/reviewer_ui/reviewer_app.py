"""
IPF IPA PoC - Document Review Portal (Streamlit)
"""
import streamlit as st
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
REVIEWER_PASSWORD = os.getenv("REVIEWER_PASSWORD", "ipf-reviewer-2026")
ASSESSOR_PASSWORD = os.getenv("ASSESSOR_PASSWORD", "ipf-assessor-2026")

st.set_page_config(page_title="IPF Document Review", page_icon="", layout="wide")

def confidence_colour(score):
    if score >= 85: return ""
    elif score >= 70: return ""
    return ""

def validation_icon(status):
    return {"PASS":"","FAIL":"","WARNING":"","PENDING":""}.get(status,"")

# Auth
if "reviewer_authenticated" not in st.session_state:
    st.session_state.reviewer_authenticated = False
    st.session_state.reviewer_role = None

if not st.session_state.reviewer_authenticated:
    st.title("IPF Reviewer Portal  Login")
    role_choice = st.selectbox("Login as:", ["Document Reviewer", "Credit Assessor"])
    password = st.text_input("Password:", type="password")
    if st.button("Login"):
        expected = ASSESSOR_PASSWORD if role_choice == "Credit Assessor" else REVIEWER_PASSWORD
        if password == expected:
            st.session_state.reviewer_authenticated = True
            st.session_state.reviewer_role = role_choice
            st.session_state.reviewer_id = role_choice.lower().replace(" ","_")
            st.rerun()
        else:
            st.error("Invalid password")
    st.stop()

role = st.session_state.reviewer_role
reviewer_id = st.session_state.reviewer_id

st.title("IPF Document Review Portal")
st.caption(f"Logged in as: **{role}**")

with st.sidebar:
    st.header("Navigation")
    # Auto-navigate when a document is selected from queue
    if st.session_state.get("_goto_review"):
        st.session_state["_goto_review"] = False
        default_page_idx = 1  # "Review Document"
    else:
        default_page_idx = 0
    pages = ["Work Queue", "Application Review", "Review Document", "Audit Trail"]
    page = st.radio("", pages, index=default_page_idx)
    st.divider()
    st.caption("IPF IPA PoC v1.0")
    if st.button("Logout"):
        st.session_state.reviewer_authenticated = False
        st.rerun()

for key in ["selected_doc_id","selected_app_id","current_doc_id","current_app_id"]:
    if key not in st.session_state:
        st.session_state[key] = ""

if page == "Work Queue":
    st.header("Work Queue")
    _, col2 = st.columns([3,1])
    with col2:
        sf = st.selectbox("Filter:", ["All","PENDING_REVIEW","EXTRACTED","VERIFIED"])
    try:
        params = {} if sf == "All" else {"status": sf}
        resp = requests.get(f"{BACKEND_URL}/api/queue", params=params, timeout=10)
        if resp.ok:
            items = resp.json().get("items",[])
            if items:
                st.markdown(f"**{len(items)} item(s) in queue**")
                for item in items:
                    s = item.get("status","")
                    icon = "" if s == "PENDING_REVIEW" else "" if s == "VERIFIED" else ""
                    with st.expander(f"{icon} App: **{item.get('application_id')}** | {item.get('document_type','').replace('_',' ').title()} | {item.get('market')} | {s}"):
                        c1,c2 = st.columns(2)
                        c1.write(f"**ID:** {item.get('id')}")
                        c2.write(f"**Uploaded:** {item.get('uploaded_at','')[:10]}")
                        doc_id = item["id"]
                        app_id = item.get("application_id","")
                        btn_key = f"open_{doc_id}"
                        if st.button("Open for Review ", key=btn_key, type="primary"):
                            st.session_state.selected_doc_id = doc_id
                            st.session_state.current_doc_id = doc_id
                            st.session_state.selected_app_id = app_id
                            st.session_state.current_app_id = app_id
                            st.session_state["_goto_review"] = True
                            st.rerun()
            else:
                st.success("No items pending review.")
        else:
            st.error("Could not fetch queue.")
    except Exception as e:
        st.error(f"Cannot connect to backend: {e}")

elif page == "Application Review":
    st.header("Application Review Consolidated View")
    st.caption("Loan application, supporting documents, OCR extractions, and cross-reference discrepancies in one view")

    # Auto-load from navigation
    app_id_review = st.text_input("Application ID:", value=st.session_state.selected_app_id, key="app_review_id")
    if app_id_review and st.button("Load Application", key="load_app_review"):
        st.session_state.current_app_id = app_id_review

    if st.session_state.current_app_id:
        try:
            status_resp = requests.get(f"{BACKEND_URL}/api/status/{st.session_state.current_app_id}", timeout=10)
            loan_resp = requests.get(f"{BACKEND_URL}/api/loan-application/{st.session_state.current_app_id}", timeout=10)
            disc_resp = requests.get(f"{BACKEND_URL}/api/discrepancies/{st.session_state.current_app_id}", timeout=10)

            status = status_resp.json() if status_resp.ok else {}
            docs = status.get("documents", [])
            loan_app = loan_resp.json() if loan_resp.ok else None
            disc_data = disc_resp.json() if disc_resp.ok else {"summary": {}, "discrepancies": []}
            discrepancies = disc_data.get("discrepancies", [])
            disc_summary = disc_data.get("summary", {})

            # --- Summary Banner ---
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Documents", len(docs))
            s2.metric("Verified", sum(1 for d in docs if d["status"] == "VERIFIED"))
            s3.metric("Discrepancies", disc_summary.get("mismatches", 0) + disc_summary.get("warnings", 0))
            high = disc_summary.get("high_severity", 0)
            if high > 0:
                s4.error(f"{high} HIGH risk flags")
            else:
                s4.success("No HIGH risk flags")

            st.divider()

            # ========== PANEL A: LOAN APPLICATION ==========
            st.subheader("Panel A - Loan Application (Customer Declared)")
            if loan_app and loan_app.get("extracted_fields"):
                fields = loan_app["extracted_fields"]

                # Find the loan application document for preview
                loan_app_doc = next((d for d in docs if d.get("type") == "loan_application"), None)
                col_loan_img, col_loan_fields = st.columns([1, 1])

                with col_loan_img:
                    st.markdown("**Original Loan Application Form**")
                    if loan_app_doc:
                        prev_resp = requests.get(
                            f"{BACKEND_URL}/api/document/{loan_app_doc['id']}/preview",
                            timeout=15
                        )
                        if prev_resp.ok:
                            st.image(prev_resp.content, use_container_width=True,
                                     caption=loan_app_doc.get("filename", "Loan Application"))
                        else:
                            import base64 as _b64
                            ext_resp2 = requests.get(f"{BACKEND_URL}/api/review/{loan_app_doc['id']}", timeout=10)
                            if ext_resp2.ok:
                                b64 = ext_resp2.json().get("image_b64")
                                if b64:
                                    st.download_button("Download Loan App PDF",
                                        _b64.b64decode(b64),
                                        file_name=loan_app_doc.get("filename", "loan_app.pdf"),
                                        mime="application/pdf")
                    else:
                        st.info("Loan application document image not available")

                with col_loan_fields:
                    st.markdown("**Declared Fields**")
                    # Build cross-ref lookup for colour coding
                    field_status_map = {}
                    for disc in discrepancies:
                        fp = disc.get("field_pair")
                        if fp:
                            field_status_map[fp] = disc.get("status", "UNVERIFIABLE")

                    FIELD_DISPLAY = {
                        "applicant_full_name": "Full Name",
                        "date_of_birth": "Date of Birth",
                        "residential_address": "Residential Address",
                        "declared_net_monthly_income": "Declared Net Income",
                        "declared_income_currency": "Currency",
                        "requested_loan_amount": "Loan Amount Requested",
                        "loan_term_weeks": "Loan Term (weeks)",
                        "employment_status": "Employment Status",
                        "employer_name": "Employer",
                        "bank_account_number": "Bank Account",
                        "purpose_of_loan": "Purpose of Loan",
                    }
                    FIELD_CROSS_REF_MAP = {
                        "applicant_full_name": "applicant_full_name",
                        "date_of_birth": "date_of_birth",
                        "residential_address": "residential_address",
                        "declared_net_monthly_income": "declared_net_monthly_income",
                        "bank_account_number": "bank_account_number",
                    }

                    # Field table header
                    for field_key, display_name in FIELD_DISPLAY.items():
                        field_data = fields.get(field_key, {})
                        val = field_data.get("value") if isinstance(field_data, dict) else field_data
                        cross_ref_key = FIELD_CROSS_REF_MAP.get(field_key)
                        cross_status = field_status_map.get(cross_ref_key, "UNVERIFIABLE") if cross_ref_key else "N/A"
                        status_icon = {"MATCH": "OK", "WARNING": "WARN", "MISMATCH": "MISMATCH",
                                       "UNVERIFIABLE": "-", "N/A": ""}.get(cross_status, "-")
                        colour = {"MATCH": "green", "WARNING": "orange", "MISMATCH": "red",
                                  "UNVERIFIABLE": "grey", "N/A": ""}.get(cross_status, "grey")
                        val_str = str(val) if val and val != "None" else ""
                        st.write(f"**{display_name}**: {val_str}")
                        if cross_status not in ("N/A", "UNVERIFIABLE"):
                            st.caption(f"Cross-check: {status_icon} {cross_status}")
            else:
                st.warning("No loan application form found. Upload a loan_application document to enable cross-referencing.")

            st.divider()

            # ========== PANEL B: SUPPORTING DOCUMENTS ==========
            st.subheader("Panel B Supporting Documents & OCR Extractions")
            supporting_docs = [d for d in docs if d.get("type") != "loan_application"]

            if not supporting_docs:
                st.info("No supporting documents found for this application.")
            else:
                for doc in supporting_docs:
                    doc_type_display = doc["type"].replace("_", " ").title()
                    status_icon = "" if doc["status"] == "VERIFIED" else "" if doc["status"] == "PROCESSING" else ""
                    with st.expander(f"{status_icon} {doc_type_display} {doc['filename']} | {doc['status']}"):
                        ext_resp = requests.get(f"{BACKEND_URL}/api/review/{doc['id']}", timeout=15)
                        if ext_resp.ok:
                            ext_data = ext_resp.json()
                            extractions = ext_data.get("extractions", [])

                            col_img, col_fields = st.columns([1, 1])
                            with col_img:
                                b64 = ext_data.get("image_b64")
                                ctype = ext_data.get("content_type", "image/jpeg")
                                if b64:
                                    import base64 as _b64
                                    img_bytes = _b64.b64decode(b64)
                                    if "pdf" in ctype:
                                        prev_resp = requests.get(f"{BACKEND_URL}/api/document/{doc['id']}/preview", timeout=15)
                                        if prev_resp.ok:
                                            st.image(prev_resp.content, use_container_width=True)
                                        else:
                                            st.download_button("Download PDF", img_bytes, file_name=doc["filename"])
                                    else:
                                        st.image(img_bytes, use_container_width=True)

                            with col_fields:
                                st.markdown(f"**Extracted Fields** ({len(extractions)} fields)")
                                if extractions:
                                    high_conf = sum(1 for e in extractions if e.get("confidence",0) >= 85)
                                    c1, c2, c3 = st.columns(3)
                                    c1.metric("Fields", len(extractions))
                                    c2.metric("High", high_conf)
                                    c3.metric("Review", len(extractions)-high_conf)
                                    st.divider()
                                    for ext in extractions:
                                        conf = ext.get("confidence", 0)
                                        icon = "" if conf >= 85 else "" if conf >= 70 else ""
                                        val = ext.get("corrected_value") or ext.get("extracted_value") or ""
                                        vstat = ext.get("validation_status", "")
                                        vicon = "" if vstat == "PASS" else "" if vstat == "FAIL" else ""
                                        st.write(f"{icon} **{ext.get('field_name','').replace('_',' ').title()}**: {val} ({conf}%) {vicon}")

            st.divider()

            # ========== PANEL C: DISCREPANCY REPORT ==========
            st.subheader("Panel C Cross-Reference Discrepancy Report")
            if discrepancies:
                mismatch_count = disc_summary.get("mismatches", 0)
                warn_count = disc_summary.get("warnings", 0)
                match_count = disc_summary.get("matches", 0)

                sc1, sc2, sc3, sc4 = st.columns(4)
                sc1.metric("Total Checks", disc_summary.get("total", 0))
                sc2.metric("Mismatches", mismatch_count)
                sc3.metric("Warnings", warn_count)
                sc4.metric("Matches", match_count)
                st.divider()

                for disc in discrepancies:
                    dstatus = disc.get("status", "")
                    sev = disc.get("severity", "")
                    sev_icon = disc.get("severity_icon", "")
                    disc_id = disc.get("id", "")

                    if dstatus == "MATCH":
                        color = ""
                    elif dstatus == "WARNING":
                        color = ""
                    elif dstatus == "MISMATCH":
                        color = ""
                    else:
                        color = ""

                    override = disc.get("override_explanation")
                    override_label = f" REVIEWED" if override else ""
                    expander_label = f"{color} {disc.get('label','Field')} {dstatus} {sev_icon} {sev}{override_label}"

                    with st.expander(expander_label):
                        col_d, col_e = st.columns(2)
                        col_d.write(f"**Declared (Loan App):** {disc.get('declared_value') or ''}")
                        col_e.write(f"**Extracted (Document):** {disc.get('extracted_value') or ''}")
                        st.write(f"{disc.get('detail','')}")
                        if disc.get("source_document_type"):
                            st.caption(f"Source document: {disc['source_document_type'].replace('_',' ').title()}")

                        if override:
                            st.success(f"Override: {override} by {disc.get('override_by','')}")
                        elif dstatus in ("MISMATCH", "WARNING"):
                            with st.form(key=f"override_form_{disc_id}"):
                                explanation = st.text_input("Override explanation (required):")
                                submitted = st.form_submit_button("Mark as Reviewed")
                                if submitted and explanation:
                                    ov_resp = requests.post(
                                        f"{BACKEND_URL}/api/discrepancies/{st.session_state.current_app_id}/override",
                                        json={"discrepancy_id": disc_id, "explanation": explanation, "override_by": reviewer_id},
                                        timeout=10
                                    )
                                    if ov_resp.ok:
                                        st.success("Discrepancy marked as reviewed.")
                                        st.rerun()
                                    else:
                                        st.error(ov_resp.text)
            else:
                if loan_app:
                    st.success("No discrepancies found all cross-checks passed.")
                else:
                    st.info("Cross-reference not available no loan application form was uploaded.")

        except Exception as e:
            st.error(f"Error loading application: {e}")

elif page == "Review Document":
    st.header("Document Review")
    doc_id = st.text_input("Document ID:", value=st.session_state.selected_doc_id)
    if doc_id and st.button("Load"):
        st.session_state.current_doc_id = doc_id
    if st.session_state.current_doc_id:
        try:
            resp = requests.get(f"{BACKEND_URL}/api/review/{st.session_state.current_doc_id}", timeout=15)
            if resp.ok:
                data = resp.json()
                extractions = data.get("extractions",[])
                st.subheader(f"{data.get('document_type','').replace('_',' ').title()}  {data.get('market','')} Market")
                st.caption(f"File: {data.get('original_filename','')} | Status: **{data.get('status','')}**")
                col_img, col_fields = st.columns([1,1])
                with col_img:
                    st.subheader("Original Document")
                    b64 = data.get("image_b64")
                    ctype = data.get("content_type", "image/jpeg")
                    if b64:
                        import base64 as _b64
                        img_bytes = _b64.b64decode(b64)
                        if "pdf" in ctype:
                            # Download button
                            st.download_button("Download PDF", img_bytes,
                                file_name=data.get("original_filename","doc.pdf"),
                                mime="application/pdf")
                            # Render PDF as image via backend preview endpoint
                            preview_resp = requests.get(
                                f"{BACKEND_URL}/api/document/{doc_id}/preview",
                                timeout=15
                            )
                            if preview_resp.ok:
                                st.image(preview_resp.content, use_container_width=True,
                                         caption="PDF Page 1 Preview")
                            else:
                                st.warning("Could not render PDF preview.")
                        else:
                            st.image(img_bytes, use_container_width=True)
                    else:
                        st.info("Document image not available")
                with col_fields:
                    st.subheader("AI Extracted Fields")
                    if extractions:
                        high = sum(1 for e in extractions if e.get("confidence",0) >= 85)
                        c1,c2,c3 = st.columns(3)
                        c1.metric("Total Fields", len(extractions))
                        c2.metric("High Conf", high)
                        c3.metric("Needs Review", len(extractions)-high)
                        st.divider()
                        corrections = {}
                        for ext in extractions:
                            conf = ext.get("confidence",0)
                            vs = ext.get("validation_status","PENDING")
                            cv = ext.get("corrected_value") or ext.get("extracted_value") or ""
                            label = f"{confidence_colour(conf)} {ext.get('field_name','').replace('_',' ').title()} ({conf}%) {validation_icon(vs)}"
                            nv = st.text_input(label, value=cv, key=f"f_{ext['id']}")
                            if vs == "FAIL":
                                st.caption(f"Reason: {ext.get('validation_reason','')}")
                            if nv != cv:
                                corrections[ext["id"]] = nv
                        st.divider()
                        ca, cb = st.columns(2)
                        if corrections and ca.button("Submit Corrections", type="primary"):
                            payload = [{"extraction_id": eid, "corrected_value": v, "corrected_by": reviewer_id} for eid,v in corrections.items()]
                            r = requests.post(f"{BACKEND_URL}/api/review/{st.session_state.current_doc_id}/correct", json=payload, timeout=10)
                            if r.ok:
                                st.success("Corrections saved.")
                        else:
                            st.error(r.text)
                        if cb.button("Confirm All Correct"):
                            r = requests.post(f"{BACKEND_URL}/api/review/{st.session_state.current_doc_id}/confirm", params={"reviewer_id":reviewer_id}, timeout=10)
                            if r.ok:
                                st.success("Document confirmed.")
                        else:
                            st.error(r.text)
            else:
                st.error("Document not found.")
        except Exception as e:
            st.error(f"Error: {e}")

elif page == "Loan Decision":
    st.header("Loan Decision - Credit Assessor")
    if role != "Credit Assessor":
        st.warning("Only Credit Assessors can access this page.")
        st.stop()
    app_id = st.text_input("Application ID:", value=st.session_state.selected_app_id)
    if app_id and st.button("Load Application"):
        st.session_state.current_app_id = app_id
    if st.session_state.current_app_id:
        try:
            resp = requests.get(f"{BACKEND_URL}/api/status/{st.session_state.current_app_id}", timeout=10)
            if not resp.ok:
                st.error("Application not found.")
            else:
                status = resp.json()
                docs = status.get("documents", [])
                verified_count = sum(1 for d in docs if d["status"] == "VERIFIED")
                c1, c2, c3 = st.columns(3)
                c1.metric("Documents", len(docs))
                c2.metric("Verified", verified_count)
                c3.metric("Status", status.get("workflow_status", ""))
                for doc in docs:
                    icon = "OK" if doc["status"] == "VERIFIED" else "XX"
                    st.write(f"[{icon}] {doc['filename']} ({doc['type']}) - {doc['status']}")
                st.divider()

                # Credit Score Section
                st.subheader("Credit Assessment (Mock Bureau Score)")
                cs_resp = requests.get(f"{BACKEND_URL}/api/credit-score/{st.session_state.current_app_id}", timeout=15)
                if cs_resp.ok:
                    cs = cs_resp.json()
                    score = cs.get("score", 0)
                    band = cs.get("risk_band", "UNKNOWN")
                    risk_icon = cs.get("risk_icon", "")
                    rec_cs = cs.get("recommendation", "REFER")
                    sc1, sc2, sc3 = st.columns([1, 2, 1])
                    sc1.metric("Credit Score", f"{score} / 1000")
                    sc2.progress(cs.get("score_pct", 0) / 100, text=f"{risk_icon} {band} - {score}/1000 points")
                    if rec_cs == "APPROVE":
                        sc3.success(f"Score says: {rec_cs}")
                    elif rec_cs == "DECLINE":
                        sc3.error(f"Score says: {rec_cs}")
                    else:
                        sc3.warning(f"Score says: {rec_cs}")
                    st.caption(f"Bureau: {cs.get('bureau_name', 'Mock')} | {cs.get('disclaimer', '')}")
                    with st.expander("Score Breakdown"):
                        for item in cs.get("breakdown", []):
                            ca2, cb2, cc2 = st.columns([3, 1, 1])
                            ca2.write(f"**{item['category']}** - {item['detail']}")
                            cb2.write(f"{item['score']}/{item['max']}")
                            cc2.write(f"{item['pct']}%")
                            st.progress(item["pct"] / 100)
                    flags = cs.get("flags", [])
                    if flags:
                        st.warning("Risk Flags:")
                        for flag in flags:
                            st.write(f"  - {flag}")
                    else:
                        st.success("No risk flags detected")
                else:
                    st.info("Credit score not yet available. Ensure documents are verified.")
                st.divider()

                # AI Recommendation
                rec = status.get("recommendation")
                if rec:
                    st.subheader("AI Document Recommendation")
                    if rec == "APPROVE": st.success(f"AI recommends: {rec}")
                    elif rec == "DECLINE": st.error(f"AI recommends: {rec}")
                    else: st.warning(f"AI recommends: {rec}")
                    st.caption("AI recommendation only - final decision is always yours.")
                st.divider()

                # Final Decision
                if verified_count == len(docs) and len(docs) > 0:
                    st.subheader("Your Decision")
                    reason = st.text_area("Notes (optional):")
                    ca3, cd3 = st.columns(2)
                    if ca3.button("APPROVE LOAN", type="primary", use_container_width=True):
                        r = requests.post(f"{BACKEND_URL}/api/decision/{st.session_state.current_app_id}",
                                          json={"decision":"APPROVE","assessor_id":reviewer_id,"reason_codes":[reason] if reason else []}, timeout=10)
                        if r.ok: st.success("Loan APPROVED and recorded."); st.balloons()
                        else: st.error(r.text)
                    if cd3.button("DECLINE LOAN", use_container_width=True):
                        r = requests.post(f"{BACKEND_URL}/api/decision/{st.session_state.current_app_id}",
                                          json={"decision":"DECLINE","assessor_id":reviewer_id,"reason_codes":[reason] if reason else []}, timeout=10)
                        if r.ok: st.error("Loan DECLINED and recorded.")
                        else: st.error(r.text)
                else:
                    st.warning("All documents must be verified before a decision can be made.")
        except Exception as e:
            st.error(f"Error: {e}")

elif page == "Audit Trail":
    st.header("Audit Trail")
    st.caption("Full event history with processing status flowchart")
    app_id = st.text_input("Application ID:", placeholder="APP-PL-001")
    if app_id and st.button("Load Audit Trail"):
        try:
            resp = requests.get(f"{BACKEND_URL}/api/audit/{app_id}", timeout=10)
            if resp.ok:
                trail = resp.json().get("audit_trail", [])
                if trail:
                    PIPELINE = [
                        ("UPLOAD",           "Documents Uploaded"),
                        ("EXTRACT_LOAN_APP", "Loan App Extracted"),
                        ("EXTRACT",          "Documents Extracted"),
                        ("CROSS_REFERENCE",  "Cross-Reference Check"),
                        ("PAUSE_FOR_REVIEW", "Pending Review"),
                        ("CORRECT",          "Field Corrections"),
                        ("CONFIRM",          "Document Confirmed"),
                        ("RECOMMEND",        "AI Recommendation"),
                        ("APPROVE",          "Loan Approved"),
                        ("DECLINE",          "Loan Declined"),
                    ]
                    completed = {e.get("action", "") for e in trail}
                    failed = "WORKFLOW_FAILED" in completed
                    col_events, col_flow = st.columns([2, 1])
                    with col_flow:
                        st.subheader("Processing Flow")
                        nodes = ""
                        for key, label in PIPELINE:
                            if key in completed:
                                bg = "#28a745"; border = "3px solid #1e7e34"; tc = "white"; status = "Completed"
                            else:
                                first_pending = next((k for k, _ in PIPELINE if k not in completed), None)
                                if key == first_pending and not failed:
                                    bg = "#ffc107"; border = "3px solid #d39e00"; tc = "#212529"; status = "Processing"
                                else:
                                    bg = "#dc3545"; border = "3px solid #bd2130"; tc = "white"; status = "Not Started"
                            nodes += (
                                "<div style='display:flex;flex-direction:column;align-items:center;'>"
                                f"<div style='width:120px;height:120px;border-radius:50%;background:{bg};border:{border};"
                                "display:flex;flex-direction:column;align-items:center;justify-content:center;"
                                "text-align:center;padding:8px;box-shadow:0 2px 8px rgba(0,0,0,0.15);'>"
                                f"<div style='color:{tc};font-weight:bold;font-size:10.5px;line-height:1.3;'>{label}</div>"
                                f"<div style='color:{tc};font-size:9px;margin-top:3px;opacity:0.85;'>{status}</div>"
                                "</div>"
                                "<div style='width:3px;height:20px;background:#ced4da;'></div>"
                                "</div>"
                            )
                        total_h = len(PIPELINE) * 148 + 100
                        legend = ("<span style='background:#dc3545;color:white;padding:2px 8px;border-radius:10px;margin:2px;'>Not Started</span>"
                                  "<span style='background:#ffc107;color:#212529;padding:2px 8px;border-radius:10px;margin:2px;'>Processing</span>"
                                  "<span style='background:#28a745;color:white;padding:2px 8px;border-radius:10px;margin:2px;'>Completed</span>")
                        html = (f"<div style='display:flex;flex-direction:column;align-items:center;padding:12px;"
                                "background:#f8f9fa;border-radius:8px;font-family:-apple-system,sans-serif;'>"
                                "<div style='font-weight:bold;font-size:12px;color:#495057;margin-bottom:12px;"
                                "text-transform:uppercase;letter-spacing:1px;'>Processing Pipeline</div>"
                                + nodes +
                                f"<div style='margin-top:12px;font-size:10px;display:flex;gap:6px;flex-wrap:wrap;justify-content:center;'>{legend}</div>"
                                "</div>")
                        import streamlit.components.v1 as _c
                        _c.html(html, height=total_h, scrolling=True)
                    with col_events:
                        st.subheader(f"Event Log ({len(trail)} events)")
                        import json as _json
                        for event in trail:
                            action = event.get("action", "")
                            actor = event.get("actor", "")
                            ts = event.get("timestamp", "")[:19]
                            with st.expander(f"{action}  |  {actor}  |  {ts}"):
                                details = event.get("details", {})
                                if isinstance(details, str):
                                    try:
                                        details = _json.loads(details)
                                    except Exception:
                                        pass
                                st.json(details if details else event)
                else:
                    st.info("No audit events found.")
            else:
                st.error("Could not fetch audit trail.")
        except Exception as e:
            st.error(f"Error: {e}")

