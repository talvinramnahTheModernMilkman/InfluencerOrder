import streamlit as st
import pandas as pd
import gspread
import os
import json
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# Google Sheets setup for Streamlit Cloud
def connect_to_google_sheet(sheet_url):
    # Load credentials from environment variable
    creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_json:
        raise ValueError("Google Sheets credentials not found in environment variables.")
    creds_dict = json.loads(creds_json)

    # Authenticate with Google Sheets API
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    return sheet

# Replace with your Google Sheets URL
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/your-spreadsheet-id"

# Load the delivery schedule CSV
@st.cache
def load_postcode_data():
    url = "https://raw.githubusercontent.com/talvinramnahTheModernMilkman/InfluencerPortal/refs/heads/main/active%20postcodes%20with%20delivery%20sched.csv"
    return pd.read_csv(url)

postcode_data = load_postcode_data()

# UI for input
st.title("Influencer Order Automation")

# Input fields
email = st.text_input("Enter Email:")
username = st.text_input("Enter Username:")
postcode = st.text_input("Enter Postcode:")
phone_number = st.text_input("Enter Phone Number:")
bundle_type = st.selectbox("Select Bundle", ["vegan", "non-vegan"])

if postcode:
    # Auto-format postcode
    formatted_postcode = postcode.replace(" ", "").upper()
    matched_row = postcode_data[postcode_data["Postcode"] == formatted_postcode]
    if not matched_row.empty:
        sched = matched_row.iloc[0]["Sched"]
        st.success(f"Delivery schedule for {formatted_postcode}: {sched}")

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
        st.error(f"Postcode {formatted_postcode} is not found in the delivery schedule.")
else:
    st.info("Enter a postcode to check delivery schedule and select a start date.")

# Submit button
if st.button("Submit"):
    if not email or not username or not formatted_postcode or not phone_number or not bundle_type:
        st.error("Please complete all fields with valid data before submitting.")
    else:
        # Format data to save to Google Sheets
        data_to_save = {
            "Email": email,
            "Username": username,
            "Postcode": formatted_postcode,
            "Phone Number": phone_number,
            "Bundle Type": bundle_type,
            "Start Date": start_date.strftime("%Y-%m-%d"),
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            # Connect to Google Sheets and save the data
            sheet = connect_to_google_sheet(GOOGLE_SHEET_URL)
            worksheet = sheet.sheet1  # Assumes data is saved in the first worksheet
            worksheet.append_row(list(data_to_save.values()))
            st.success("Data saved to Google Sheets successfully!")
        except Exception as e:
            st.error("Failed to save data to Google Sheets.")
            st.error(f"Error: {e}")
