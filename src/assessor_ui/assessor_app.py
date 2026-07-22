"""
IPF IPA PoC - Credit Assessor Portal
Clean decision-making interface for Credit Assessors only.
No raw OCR data, no confidence scores - just the summary needed to make a decision.
Port: 8503
"""
import streamlit as st
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ASSESSOR_PASSWORD = os.getenv("ASSESSOR_PASSWORD", "ipf-assessor-2026")

st.set_page_config(
    page_title="IPF Credit Assessor Portal",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom teal theme header
st.markdown("""
<style>
    .main-header {background: linear-gradient(90deg, #0d7377, #14a085); padding: 1rem 2rem;
                  border-radius: 8px; margin-bottom: 1rem; color: white;}
    .main-header h1 {color: white; margin: 0; font-size: 1.6rem;}
    .main-header p {color: #d4f5f3; margin: 0; font-size: 0.85rem;}
    .metric-card {background: #f8f9fa; border-left: 4px solid #0d7377;
                  padding: 1rem; border-radius: 4px; margin: 0.5rem 0;}
    .risk-high {border-left-color: #dc3545;}
    .risk-medium {border-left-color: #ffc107;}
    .risk-low {border-left-color: #28a745;}
</style>
""", unsafe_allow_html=True)

#  AUTH 
if "assessor_authenticated" not in st.session_state:
    st.session_state.assessor_authenticated = False

if not st.session_state.assessor_authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""<div class="main-header">
            <h1>IPF Credit Assessor Portal</h1>
            <p>Secure login for qualified credit decision makers</p>
        </div>""", unsafe_allow_html=True)
        st.text_input("Assessor Password:", type="password", key="login_pwd")
        if st.button("Login", type="primary", use_container_width=True):
            if st.session_state.login_pwd == ASSESSOR_PASSWORD:
                st.session_state.assessor_authenticated = True
                st.session_state.assessor_id = "credit_assessor"
                st.rerun()
            else:
                st.error("Invalid password")
    st.stop()

#  MAIN APP 
st.markdown("""<div class="main-header">
    <h1>IPF Credit Assessor Portal</h1>
    <p>Review verified applications and make final loan decisions</p>
</div>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio("", ["Decision Queue", "Application Summary", "Loan Decision", "Decision History"])
    st.divider()
    st.caption("Logged in as: Credit Assessor")
    st.caption("IPF IPA PoC v1.0")
    if st.button("Logout"):
        st.session_state.assessor_authenticated = False
        st.rerun()

for k in ["selected_app_id", "current_app_id"]:
    if k not in st.session_state:
        st.session_state[k] = ""

# 
# DECISION QUEUE
# 
if page == "Decision Queue":
    st.header("Applications Awaiting Decision")
    st.caption("Applications that have passed document verification and are ready for your decision")

    try:
        resp = requests.get(f"{BACKEND_URL}/api/queue", params={"status": "PENDING_REVIEW"}, timeout=10)
        all_resp = requests.get(f"{BACKEND_URL}/api/queue", timeout=10)

        all_items = all_resp.json().get("items", []) if all_resp.ok else []

        # Group by application_id
        by_app = {}
        for item in all_items:
            app_id = item.get("application_id", "")
            if app_id not in by_app:
                by_app[app_id] = []
            by_app[app_id].append(item)

        if by_app:
            for app_id, docs in by_app.items():
                all_verified = all(d["status"] == "VERIFIED" for d in docs)
                any_review = any(d["status"] == "PENDING_REVIEW" for d in docs)
                verified_count = sum(1 for d in docs if d["status"] == "VERIFIED")

                # Get credit score to show risk level
                cs_resp = requests.get(f"{BACKEND_URL}/api/credit-score/{app_id}", timeout=10)
                cs = cs_resp.json() if cs_resp.ok else {}
                score = cs.get("score", 0)
                band = cs.get("risk_band", "UNKNOWN")
                risk_icon = cs.get("risk_icon", "")

                disc_resp = requests.get(f"{BACKEND_URL}/api/discrepancies/{app_id}", timeout=10)
                disc = disc_resp.json() if disc_resp.ok else {"summary": {}}
                mismatches = disc.get("summary", {}).get("mismatches", 0)

                market = docs[0].get("market", "") if docs else ""

                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
                col1.markdown(f"**{app_id}**")
                col2.write(f"{market}")
                col3.write(f"{verified_count}/{len(docs)} docs")
                col4.write(f"{risk_icon} {score}/1000")
                if mismatches > 0:
                    col4.caption(f"{mismatches} mismatches")

                if col5.button("Review & Decide", key=f"q_{app_id}", type="primary"):
                    st.session_state.selected_app_id = app_id
                    st.session_state.current_app_id = app_id
                    st.rerun()
                st.divider()
        else:
            st.info("No applications in queue. Documents are being processed.")
    except Exception as e:
        st.error(f"Error fetching queue: {e}")

# 
# APPLICATION SUMMARY
# 
elif page == "Application Summary":
    st.header("Application Summary")

    app_id = st.text_input("Application ID:", value=st.session_state.selected_app_id, placeholder="APP-PL-GOOD-001")
    if app_id and st.button("Load Application", key="load_summary"):
        st.session_state.current_app_id = app_id

    if st.session_state.current_app_id:
        aid = st.session_state.current_app_id
        try:
            status_resp = requests.get(f"{BACKEND_URL}/api/status/{aid}", timeout=10)
            loan_resp = requests.get(f"{BACKEND_URL}/api/loan-application/{aid}", timeout=10)
            cs_resp = requests.get(f"{BACKEND_URL}/api/credit-score/{aid}", timeout=10)
            disc_resp = requests.get(f"{BACKEND_URL}/api/discrepancies/{aid}", timeout=10)

            if not status_resp.ok:
                st.error("Application not found")
            else:
                status = status_resp.json()
                docs = status.get("documents", [])
                verified = sum(1 for d in docs if d["status"] == "VERIFIED")
                loan_app = loan_resp.json() if loan_resp.ok else None
                cs = cs_resp.json() if cs_resp.ok else {}
                disc_data = disc_resp.json() if disc_resp.ok else {"summary": {}, "discrepancies": []}
                discrepancies = disc_data.get("discrepancies", [])
                disc_summary = disc_data.get("summary", {})

                # Top summary row
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Documents", f"{verified}/{len(docs)} verified")
                c2.metric("Credit Score", f"{cs.get('score', 0)}/1000")
                c3.metric("Risk Band", f"{cs.get('risk_icon', '')} {cs.get('risk_band', 'N/A')}")
                mismatches = disc_summary.get("mismatches", 0)
                if mismatches > 0:
                    c4.error(f"{mismatches} Discrepancies")
                else:
                    c4.success("No Discrepancies")

                st.divider()

                # Two columns: applicant details + credit assessment
                col_left, col_right = st.columns([1, 1])

                with col_left:
                    st.subheader("Applicant Details")
                    if loan_app and loan_app.get("extracted_fields"):
                        fields = loan_app["extracted_fields"]
                        SHOW = {
                            "applicant_full_name": "Full Name",
                            "date_of_birth": "Date of Birth",
                            "residential_address": "Address",
                            "declared_net_monthly_income": "Declared Income",
                            "declared_income_currency": "Currency",
                            "requested_loan_amount": "Loan Requested",
                            "loan_term_weeks": "Term (weeks)",
                            "employment_status": "Employment",
                            "employer_name": "Employer",
                            "purpose_of_loan": "Purpose",
                        }
                        for fk, label in SHOW.items():
                            fd = fields.get(fk, {})
                            val = fd.get("value") if isinstance(fd, dict) else fd
                            if val and val != "None":
                                st.write(f"**{label}:** {val}")
                    else:
                        st.info("No loan application form uploaded")

                with col_right:
                    st.subheader("Credit Assessment")
                    score = cs.get("score", 0)
                    band = cs.get("risk_band", "N/A")
                    st.progress(cs.get("score_pct", 0) / 100,
                               text=f"{cs.get('risk_icon', '')} {band}  {score}/1000 points")
                    st.caption(f"Bureau: {cs.get('bureau_name', 'Mock')}")

                    with st.expander("Score Breakdown"):
                        for item in cs.get("breakdown", []):
                            st.write(f"**{item['category']}**: {item['score']}/{item['max']}  {item['detail']}")

                    FLAG_EXPLANATIONS = {
                        "Income": "The declared income on the loan application does not match the figure on the payslip or income certificate. A variance above 10% is a lending policy concern and may indicate misrepresentation.",
                        "income": "The declared income on the loan application does not match the figure on the payslip or income certificate. A variance above 10% is a lending policy concern and may indicate misrepresentation.",
                        "Employment": "No employer details could be extracted from the submitted income documents. Employment status and stability are key affordability factors for this product.",
                        "employment": "No employer details could be extracted from the submitted income documents. Employment status and stability are key affordability factors for this product.",
                        "expired": "The submitted identity document has passed its expiry date and is no longer valid under EU and national identity verification regulations. A renewed document must be obtained before proceeding.",
                        "Expired": "The submitted identity document has passed its expiry date and is no longer valid under EU and national identity verification regulations. A renewed document must be obtained before proceeding.",
                        "national ID": "The national identification number (PESEL, CNP, Rodne cislo, or personal ID) failed the built-in checksum or format validation. This may indicate a data entry error or a fraudulent document.",
                        "Address": "The residential address declared on the loan application does not match the address shown on the proof-of-address document. This discrepancy requires verification before disbursement.",
                        "address": "The residential address declared on the loan application does not match the address shown on the proof-of-address document. This discrepancy requires verification before disbursement.",
                        "Age": "The applicant's age falls outside the eligible lending range (18-70 years). This is a product eligibility requirement enforced by IPF policy across all markets.",
                        "age": "The applicant's age falls outside the eligible lending range (18-70 years). This is a product eligibility requirement enforced by IPF policy across all markets.",
                        "Name": "There is an inconsistency between the applicant name on the loan application and the name extracted from the identity document. Minor spelling variants may be acceptable with verification.",
                        "name": "There is an inconsistency between the applicant name on the loan application and the name extracted from the identity document. Minor spelling variants may be acceptable with verification.",
                    }

                    def get_flag_explanation(flag_text):
                        for keyword, explanation in FLAG_EXPLANATIONS.items():
                            if keyword.lower() in flag_text.lower():
                                return explanation
                        return "This flag requires manual review by the assessor before a final decision is made."

                    if cs.get("flags"):
                        st.warning("Risk Flags Detected - Review Required")
                        for flag in cs["flags"]:
                            with st.expander(f"Flag: {flag}"):
                                st.write(get_flag_explanation(flag))
                                st.caption("Source: AI document analysis | This explanation is system-generated to assist the assessor.")

                # Discrepancy summary (simplified)
                if discrepancies:
                    st.divider()
                    st.subheader("Document Discrepancies")
                    mismatches_list = [d for d in discrepancies if d.get("status") == "MISMATCH"]
                    warnings_list = [d for d in discrepancies if d.get("status") == "WARNING"]

                    if mismatches_list:
                        for d in mismatches_list:
                            st.error(f"**{d.get('label')}** MISMATCH  Declared: {d.get('declared_value', '')} | Document: {d.get('extracted_value', '')}")
                    if warnings_list:
                        for d in warnings_list:
                            st.warning(f"**{d.get('label')}** WARNING  {d.get('detail', '')}")
                    if not mismatches_list and not warnings_list:
                        st.success("All checked fields are consistent")

                st.divider()
                if st.button("Proceed to Decision ?", type="primary"):
                    st.session_state.current_app_id = aid
                    st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")

# 
# LOAN DECISION
# 
elif page == "Loan Decision":
    st.header("Loan Decision")
    st.caption("Make the final approve or decline decision. This is irreversible and will be logged.")

    app_id = st.text_input("Application ID:", value=st.session_state.current_app_id, placeholder="APP-PL-GOOD-001")
    if app_id and st.button("Load for Decision", key="load_decision"):
        st.session_state.current_app_id = app_id

    if st.session_state.current_app_id:
        aid = st.session_state.current_app_id
        try:
            status_resp = requests.get(f"{BACKEND_URL}/api/status/{aid}", timeout=10)
            cs_resp = requests.get(f"{BACKEND_URL}/api/credit-score/{aid}", timeout=10)
            disc_resp = requests.get(f"{BACKEND_URL}/api/discrepancies/{aid}", timeout=10)
            loan_resp = requests.get(f"{BACKEND_URL}/api/loan-application/{aid}", timeout=10)

            status = status_resp.json() if status_resp.ok else {}
            cs = cs_resp.json() if cs_resp.ok else {}
            disc_data = disc_resp.json() if disc_resp.ok else {"summary": {}}
            loan_app = loan_resp.json() if loan_resp.ok else None
            docs = status.get("documents", [])
            verified = sum(1 for d in docs if d["status"] == "VERIFIED")

            # Quick status bar
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Documents", f"{verified}/{len(docs)}")
            c2.metric("Credit Score", f"{cs.get('score', 0)}/1000")
            c3.metric("Risk", f"{cs.get('risk_band', 'N/A')}")
            mismatches = disc_data.get("summary", {}).get("mismatches", 0)
            if mismatches:
                c4.error(f"{mismatches} mismatches")
            else:
                c4.success("No mismatches")

            # Applicant name
            if loan_app and loan_app.get("extracted_fields"):
                name_fd = loan_app["extracted_fields"].get("applicant_full_name", {})
                name = name_fd.get("value") if isinstance(name_fd, dict) else name_fd
                if name:
                    st.info(f"Applicant: **{name}** | Application: **{aid}**")

            # AI recommendation
            rec = status.get("recommendation") or cs.get("recommendation")
            if rec:
                st.subheader("AI Recommendation")
                if rec == "APPROVE":
                    st.success(f"AI recommends: **APPROVE**")
                elif rec == "DECLINE":
                    st.error(f"AI recommends: **DECLINE**")
                else:
                    st.warning(f"AI recommends: **{rec}** (refer)")
                st.caption("This is an AI recommendation only. The final decision is always yours.")

            st.divider()
            st.subheader("Your Decision")

            if verified < len(docs) and len(docs) > 0:
                st.warning(f"Only {verified}/{len(docs)} documents verified. Ensure all documents are reviewed before deciding.")

            reason_codes = st.multiselect(
                "Reason codes (select all that apply):",
                ["Income sufficient", "Identity verified", "Address verified",
                 "Income insufficient", "Income discrepancy", "Identity concerns",
                 "Address mismatch", "Expired document", "Policy compliance",
                 "Other - see notes"]
            )
            notes = st.text_area("Additional notes:")

            col_approve, col_spacer, col_decline = st.columns([2, 1, 2])

            with col_approve:
                st.markdown("### Approve")
                st.caption("Loan application meets all criteria")
                if st.button("APPROVE LOAN", type="primary", use_container_width=True, key="btn_approve"):
                    r = requests.post(f"{BACKEND_URL}/api/decision/{aid}",
                                      json={"decision": "APPROVE",
                                            "assessor_id": "credit_assessor",
                                            "reason_codes": reason_codes + ([notes] if notes else [])},
                                      timeout=10)
                    if r.ok:
                        st.success("Loan APPROVED and recorded in system.")
                        st.balloons()
                    else:
                        st.error(r.text)

            with col_decline:
                st.markdown("### Decline")
                st.caption("Application does not meet lending criteria")
                if st.button("DECLINE LOAN", use_container_width=True, key="btn_decline"):
                    if not reason_codes and not notes:
                        st.warning("Please provide at least one reason code or note before declining.")
                    else:
                        r = requests.post(f"{BACKEND_URL}/api/decision/{aid}",
                                          json={"decision": "DECLINE",
                                                "assessor_id": "credit_assessor",
                                                "reason_codes": reason_codes + ([notes] if notes else [])},
                                          timeout=10)
                        if r.ok:
                            st.error("Loan DECLINED and recorded in system.")
                        else:
                            st.error(r.text)

        except Exception as e:
            st.error(f"Error: {e}")

# 
# DECISION HISTORY
# 
elif page == "Decision History":
    st.header("Decision History")
    st.caption("All loan decisions made by credit assessors")
    try:
        resp = requests.get(f"{BACKEND_URL}/api/upload/history", timeout=10)
        if resp.ok:
            uploads = resp.json().get("uploads", [])
            decided = [u for u in uploads if u.get("status") == "DECIDED"]
            if decided:
                for u in decided:
                    disc_resp = requests.get(f"{BACKEND_URL}/api/discrepancies/{u['application_id']}", timeout=5)
                    disc_sum = disc_resp.json().get("summary", {}) if disc_resp.ok else {}
                    cs_resp = requests.get(f"{BACKEND_URL}/api/credit-score/{u['application_id']}", timeout=5)
                    cs = cs_resp.json() if cs_resp.ok else {}
                    with st.expander(f"{u['application_id']} | Score: {cs.get('score', '')}/1000 | {u.get('market', '')} | {u.get('started_at', '')[:10]}"):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Credit Score", f"{cs.get('score', 0)}/1000")
                        c2.metric("Risk Band", cs.get("risk_band", "N/A"))
                        c3.metric("Discrepancies", disc_sum.get("mismatches", 0))
                        audit_resp = requests.get(f"{BACKEND_URL}/api/audit/{u['application_id']}", timeout=5)
                        if audit_resp.ok:
                            decisions = [e for e in audit_resp.json().get("audit_trail", [])
                                        if e.get("action") in ("APPROVE", "DECLINE")]
                            for d in decisions:
                                icon = "" if d["action"] == "APPROVE" else ""
                                st.write(f"{icon} **{d['action']}** by {d.get('actor', '')} on {d.get('timestamp', '')[:19]}")
            else:
                st.info("No decisions recorded yet.")
        else:
            st.warning("Could not fetch decision history.")
    except Exception as e:
        st.error(f"Error: {e}")
