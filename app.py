import re
import io
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="PNANY Membership Event: 'Trick or Treat'", page_icon="🎃", layout="centered")

st.title("PNANY Membership Event")
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
    """Check if birth year is a 4-digit number between 1900 and current year."""
    if not re.match(r"^\d{4}$", year_str.strip()):
        return False
    yr = int(year_str)
    return 1900 <= yr <= 2025

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
        st.error(f"Please enter a valid birth year (1900–2025).")
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

if st.session_state["submissions"]:
    st.subheader("Session submissions")
    df = pd.DataFrame(st.session_state["submissions"])
    cols = ["timestamp", "first_name", "last_name", "birth_year", "email", "credentials", "education", "institution"]
    df = df[[c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]]
    st.dataframe(df, use_container_width=True, hide_index=True)
    export_downloads(df)

st.divider()
st.markdown(
    "Need a shared destination for submissions (e.g., Google Sheet)? "
    "Add it later by using `st.secrets` and the Google Sheets API."
)
