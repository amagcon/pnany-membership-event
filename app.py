import re
import io
from datetime import datetime
import pandas as pd
import streamlit as st

# Google Sheets
import gspread
from google.oauth2.service_account import Credentials

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

st.set_page_config(page_title="PNANY Trick or Treat Event", page_icon="🎃", layout="centered")

st.title("PNANY Trick or Treat Event")
st.caption("Please complete the form below. All fields are required.")

if "submissions" not in st.session_state:
    st.session_state["submissions"] = []

with st.form("pnany_signup", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("First Name *")
        institution = st.text_input("Institution / Facility *")
        email = st.text_input("Email *")
    with col2:
        last_name = st.text_input("Last Name *")
        credentials = st.text_input("Credentials (e.g., RN, BSN) *")
        education = st.text_input("Educational Level *")

    birth_year = st.text_input("Birth Year (YYYY) *")

    submitted = st.form_submit_button("Submit")

def valid_email(addr: str) -> bool:
    if not addr:
        return False
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", addr) is not None

def valid_birth_year(year_str: str) -> bool:
    if not re.match(r"^\d{4}$", year_str.strip()):
        return False
    yr = int(year_str)
    from datetime import date
    return 1900 <= yr <= date.today().year

@st.cache_resource
def _gsheet_client():
    """Authorize using st.secrets['gcp_service_account'] (Service Account)."""
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError("Missing gcp_service_account in st.secrets. Add your service account JSON in Secrets.")
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPE)
    return gspread.authorize(creds)

def _open_worksheet():
    # Prefer secrets; fallback to the provided Sheet ID and default worksheet 'Submissions'
    spreadsheet_id = st.secrets.get("google_sheets", {}).get("spreadsheet_id", "1dnMua54Nyu7Mprz7exAwnW1rzaa86qxcE_GWZfFg94A")
    ws_name = st.secrets.get("google_sheets", {}).get("worksheet_name", "Submissions")
    gc = _gsheet_client()
    ss = gc.open_by_key(spreadsheet_id)
    try:
        ws = ss.worksheet(ws_name)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=ws_name, rows=100, cols=20)
    return ws

def append_submission_to_gsheet(entry: dict):
    ws = _open_worksheet()
    header = ["timestamp","first_name","last_name","birth_year","email","credentials","education","institution"]
    try:
        current_header = ws.row_values(1)
    except Exception:
        current_header = []
    if current_header != header:
        ws.resize(rows=1)
        ws.update("A1", [header])
    row = [entry.get(k, "") for k in header]
    ws.append_row(row, value_input_option="USER_ENTERED")

def export_downloads(df: pd.DataFrame):
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        "Download submissions (CSV)",
        data=csv_buf.getvalue(),
        file_name="pnany_submissions.csv",
        mime="text/csv",
        use_container_width=True
    )

    xlsx_buf = io.BytesIO()
    with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Submissions")
    xlsx_buf.seek(0)
    st.download_button(
        "Download submissions (Excel)",
        data=xlsx_buf.getvalue(),
        file_name="pnany_submissions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

if submitted:
    required_fields = [first_name, last_name, institution, credentials, email, education, birth_year]
    labels = ["First Name", "Last Name", "Institution / Facility", "Credentials", "Email", "Educational Level", "Birth Year"]
    missing = [lbl for lbl, val in zip(labels, required_fields) if not val.strip()]

    if missing:
        st.error("Please fill in all required fields: " + ", ".join(missing))
    elif not valid_email(email):
        st.error("Please enter a valid email address.")
    elif not valid_birth_year(birth_year):
        from datetime import date
        st.error(f"Please enter a valid birth year (1900–{date.today().year}).")
    else:
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "institution": institution.strip(),
            "credentials": credentials.strip(),
            "email": email.strip(),
            "education": education.strip(),
            "birth_year": birth_year.strip(),
        }
        st.session_state["submissions"].append(entry)

        st.success("Form submitted successfully!")
        st.image("assets/thank_you_halloween.png", caption="Thank you for your interest in PNANY!", use_column_width=True)

        # Best-effort write to Google Sheet
        try:
            append_submission_to_gsheet(entry)
            st.info("Submission saved to the shared Google Sheet.")
        except Exception as e:
            st.warning("Saved locally. Could not write to Google Sheet. Check Secrets and sharing.")
            st.caption(f"Details (owner only): {e}")

if st.session_state["submissions"]:
    st.subheader("Session submissions")
    df = pd.DataFrame(st.session_state["submissions"])
    cols = ["timestamp", "first_name", "last_name", "birth_year", "email", "credentials", "education", "institution"]
    df = df[[c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]]
    st.dataframe(df, use_container_width=True, hide_index=True)
    export_downloads(df)

st.divider()
st.markdown(
    "Thank you for participating!"
)
