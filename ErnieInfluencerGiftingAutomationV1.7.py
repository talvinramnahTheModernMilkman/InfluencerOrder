import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import gspread

# Authenticate with Google Sheets
def authenticate_google_sheets():
    try:
        # Create a copy of the secrets to avoid modifying st.secrets directly
        creds_dict = dict(st.secrets["google_service_account"])
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")  # Ensure proper formatting

        # Authenticate with Google Sheets API
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Failed to authenticate with Google Sheets. Error: {e}")
        raise

# Load the delivery schedule CSV
@st.cache_data
def load_postcode_data():
    url = "https://raw.githubusercontent.com/talvinramnahTheModernMilkman/InfluencerPortal/refs/heads/main/active%20postcodes%20with%20delivery%20sched.csv"
    return pd.read_csv(url)

postcode_data = load_postcode_data()

# Streamlit App
st.title("Influencer Order Automation")

# User inputs
email = st.text_input("Enter Email:")
username = st.text_input("Enter Instagram Username:")
postcode = st.text_input("Enter Postcode:").upper().replace(" ", "")  # Format postcode
phone_number = st.text_input("Enter Phone Number:")
bundle_type = st.selectbox("Select Bundle", ["vegan", "non-vegan"])

if postcode:
    matched_row = postcode_data[postcode_data["Postcode"] == postcode]
    if not matched_row.empty:
        sched = matched_row.iloc[0]["Sched"]
        st.success(f"Delivery schedule for {postcode}: {sched}")

        # Define valid days based on schedule
        valid_days = {"MWF": [0, 2, 4], "TTS": [1, 3, 5]}  # Monday, Wednesday, Friday (MWF) and Tuesday, Thursday, Saturday (TTS)
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
    if not all([email, username, postcode, phone_number, bundle_type]):
        st.error("Please complete all fields before submitting.")
    else:
        try:
            # Authenticate and access Google Sheets
            client = authenticate_google_sheets()
            sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1bVXh9cRk1rx3cqbx7V8vOq4WIuQ8yVP439lsZ535RXs/edit#gid=0")
            worksheet = sheet.sheet1

            # Format data
            formatted_date = start_date.strftime("%d/%m/%Y")
            data = [email, username, postcode, phone_number, bundle_type, formatted_date]

            # Append data to Google Sheets
            worksheet.append_row(data)
            st.success("Data saved to Google Sheets successfully!")
        except Exception as e:
            st.error(f"Failed to save data to Google Sheets. Error: {e}")
