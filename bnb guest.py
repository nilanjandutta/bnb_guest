import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File path to save entries
CSV_FILE = "/Users/nilanjandutta/Desktop/guest_entries.csv"
PHOTO_DIR = "/Users/nilanjandutta/Desktop/guest_photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

st.set_page_config(page_title="Airbnb Guest Entry", layout="centered")
st.title("🏠 Airbnb Guest Entry Form")

# Input fields
name = st.text_input("Guest Name")
phone = st.text_input("Phone Number")
place = st.text_input("From (City/Place)")
remarks = st.text_area("Remarks")
photo = st.file_uploader("Upload Guest Photo/ID (optional)", type=["jpg", "jpeg", "png", "pdf"])

if st.button("Submit Entry"):
    if name and phone:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        photo_filename = ""
        
        if photo:
            ext = os.path.splitext(photo.name)[-1]
            photo_filename = f"{name.replace(' ', '_')}_{timestamp.replace(':', '-')}{ext}"
            photo_path = os.path.join(PHOTO_DIR, photo_filename)
            with open(photo_path, "wb") as f:
                f.write(photo.read())

        # Save to CSV
        new_entry = {
            "Timestamp": timestamp,
            "Name": name,
            "Phone": phone,
            "From": place,
            "Remarks": remarks,
            "Photo_File": photo_filename
        }
        df = pd.DataFrame([new_entry])
        df.to_csv(CSV_FILE, mode="a", header=not os.path.exists(CSV_FILE), index=False)

        st.success("✅ Guest entry recorded successfully!")
    else:
        st.warning("Please enter at least Guest Name and Phone Number.")

st.markdown("---")

# View past entries
st.subheader("📋 View Guest Entries")

if os.path.exists(CSV_FILE):
    guest_df = pd.read_csv(CSV_FILE)
    st.dataframe(guest_df, use_container_width=True)

    # Download CSV
    csv_data = guest_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv_data, "guest_entries.csv", "text/csv")

    # Print View
    st.subheader("🖨️ Print Guest Details")
    selected_guest = st.selectbox("Select Guest to Print", guest_df["Name"].tolist())
    selected_row = guest_df[guest_df["Name"] == selected_guest].iloc[-1]

    st.write(f"**Name:** {selected_row['Name']}")
    st.write(f"**Phone:** {selected_row['Phone']}")
    st.write(f"**From:** {selected_row['From']}")
    st.write(f"**Remarks:** {selected_row['Remarks']}")
    st.write(f"**Timestamp:** {selected_row['Timestamp']}")

    if selected_row["Photo_File"]:
        img_path = os.path.join(PHOTO_DIR, selected_row["Photo_File"])
        if os.path.exists(img_path) and img_path.endswith((".jpg", ".jpeg", ".png")):
            st.image(img_path, width=250, caption="Guest ID/Photo")

    st.button("🖨️ Print This Page (Use Browser Print Shortcut)")
else:
    st.info("No entries recorded yet.")

