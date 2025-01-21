import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# Load Google Sheets credentials
def get_gspread_client():
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["google_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Failed to authenticate with Google Sheets. Error: {e}")
        raise

def append_to_google_sheet(data):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key("1bVXh9cRk1rx3cqbx7V8vOq4WIuQ8yVP439lsZ535RXs")
        worksheet = sheet.get_worksheet(0)  # First sheet
        worksheet.append_row(data)
        st.success("Data saved to Google Sheets successfully!")
    except Exception as e:
        st.error(f"Failed to save data to Google Sheets. Error: {e}")

# Cache the postcode data for performance
@st.cache
def load_postcode_data():
    url = "https://raw.githubusercontent.com/talvinramnahTheModernMilkman/InfluencerPortal/refs/heads/main/active%20postcodes%20with%20delivery%20sched.csv"
    return pd.read_csv(url)

postcode_data = load_postcode_data()

# Streamlit UI
st.title("Influencer Order Automation")

# User inputs
email = st.text_input("Enter Email:")
username = st.text_input("Enter Username:")
postcode = st.text_input("Enter Postcode:").upper().replace(" ", "")  # Auto-format
phone_number = st.text_input("Enter Phone Number:")
bundle_type = st.selectbox("Select Bundle", ["vegan", "non-vegan"])

if postcode:
    matched_row = postcode_data[postcode_data["Postcode"] == postcode]
    if not matched_row.empty:
        sched = matched_row.iloc[0]["Sched"]
        st.success(f"Delivery schedule for {postcode}: {sched}")

        # Define valid days based on schedule
        valid_days = {"MWF": [0, 2, 4], "TTS": [1, 3, 5]}  # Monday, Wednesday, Friday; Tuesday, Thursday, Saturday
        valid_weekdays = valid_days.get(sched, [])

        # Create datepicker with only valid days selectable
        today = datetime.today().date()
        def disable_invalid_days(date):
            return date.weekday() not in valid_weekdays

        start_date = st.date_input(
            "Select Start Date (valid days only)",
            value=today,
            min_value=today,
            max_value=today + timedelta(days=30),
            help="Select a date based on your delivery schedule."
        )

        if disable_invalid_days(start_date):
            st.warning("Selected date is invalid for this postcode schedule. Please select a valid day.")
    else:
        st.error(f"Postcode {postcode} is not found in the delivery schedule.")
else:
    st.info("Enter a postcode to check delivery schedule and select a start date.")

# Submit button
if st.button("Submit"):
    if not email or not username or not postcode or not phone_number or not bundle_type:
        st.error("Please complete all fields before submitting.")
    else:
        # Format date for submission
        formatted_date = start_date.strftime("%d/%m/%Y")

        # Prepare data for Google Sheets
        data = [email, username, postcode, phone_number, bundle_type, formatted_date]

        # Append data to Google Sheets
        append_to_google_sheet(data)
