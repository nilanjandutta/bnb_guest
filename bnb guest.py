import streamlit as st
import pandas as pd
from datetime import datetime
import os
import urllib.parse
import pdfkit
import base64

# File & folder setup
CSV_FILE = "guest_entries.csv"
PHOTO_DIR = "guest_photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

# Path to wkhtmltopdf binary (adjust if needed)
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")

st.set_page_config(page_title="Airbnb Guest Entry", layout="centered")
st.title("🏠 Airbnb Guest Entry Form")

# --- Input Fields ---
name = st.text_input("Guest Name")
phone = st.text_input("Phone Number (with country code, e.g., 91XXXXXXXXXX)")
place = st.text_input("From (City/Place)")
remarks = st.text_area("Remarks")
photo = st.file_uploader("Upload Guest Photo/ID (optional)", type=["jpg", "jpeg", "png", "pdf"])

# --- WhatsApp Message Helper ---

# Replace this with your hotel/staff number (include country code, no + sign)
ADMIN_PHONE_NUMBER = "917002296566"

def create_whatsapp_link(name, phone, place, remarks):
    msg = f"New Airbnb Guest Entry:\nName: {name}\nPhone: {phone}\nFrom: {place}\nRemarks: {remarks}"
    return f"https://wa.me/{ADMIN_PHONE_NUMBER}?text={urllib.parse.quote(msg)}"

# --- Submission ---
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

        st.success("✅ Entry recorded successfully!")
        wa_link = create_whatsapp_link(name, phone, place, remarks)
        st.markdown(f"[📲 Send to WhatsApp]({wa_link})", unsafe_allow_html=True)
    else:
        st.warning("Name and phone number are required.")

st.markdown("---")

# --- Guest List ---
st.subheader("📋 View Guest Entries")
if os.path.exists(CSV_FILE):
    guest_df = pd.read_csv(CSV_FILE)
    st.dataframe(guest_df, use_container_width=True)

    # Download CSV
    st.download_button(
        "📥 Download All Entries (CSV)",
        guest_df.to_csv(index=False).encode("utf-8"),
        file_name="guest_entries.csv",
        mime="text/csv"
    )

    # --- PDF Generator ---
    st.subheader("🖨️ Generate PDF for Guest")

    selected_guest = st.selectbox("Select Guest", guest_df["Name"].unique())
    selected_row = guest_df[guest_df["Name"] == selected_guest].iloc[-1]

    def generate_html(row):
        html = f"""
        <html>
        <body>
        <h2>Guest Entry Details</h2>
        <p><strong>Name:</strong> {row['Name']}</p>
        <p><strong>Phone:</strong> {row['Phone']}</p>
        <p><strong>From:</strong> {row['From']}</p>
        <p><strong>Remarks:</strong> {row['Remarks']}</p>
        <p><strong>Timestamp:</strong> {row['Timestamp']}</p>
        """

        if row["Photo_File"]:
            img_path = os.path.join(PHOTO_DIR, row["Photo_File"])
            if os.path.exists(img_path) and img_path.endswith((".jpg", ".jpeg", ".png")):
                with open(img_path, "rb") as img_file:
                    b64_img = base64.b64encode(img_file.read()).decode()
                    html += f'<img src="data:image/png;base64,{b64_img}" width="250"/>'

        html += "</body></html>"
        return html

    html_content = generate_html(selected_row)
    pdf_path = f"{selected_guest.replace(' ', '_')}_entry.pdf"
    pdfkit.from_string(html_content, pdf_path, configuration=PDFKIT_CONFIG)

    with open(pdf_path, "rb") as pdf_file:
        st.download_button(
            label="📄 Download Guest PDF",
            data=pdf_file.read(),
            file_name=pdf_path,
            mime="application/pdf"
        )
else:
    st.info("No entries yet.")
