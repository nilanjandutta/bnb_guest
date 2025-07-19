import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import urllib.parse
import pdfkit
import base64

# Constants
CSV_FILE = "guest_entries.csv"
PHOTO_DIR = "guest_photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")

st.set_page_config(page_title="Airbnb Guest Entry", layout="centered")
st.title("\U0001F3E0 Airbnb Guest Entry Form")

# Main Guest Info
name = st.text_input("Main Guest Name")
phone = st.text_input("Phone Number (include country code, e.g., 91XXXXXXXXXX)")
place = st.text_input("From (City/Place)")
remarks = st.text_area("Remarks")
photo = st.file_uploader("Upload Main Guest Photo/ID (optional)", type=["jpg", "jpeg", "png", "pdf"])

# Stay Info
st.subheader("\U0001F4C6 Stay Details")
stay_from = st.date_input("Stay From", date.today())
stay_to = st.date_input("Stay To", date.today())
total_guests = st.number_input("Number of Guests", min_value=1, step=1)

extra_guests = []
extra_ids = []

if total_guests > 1:
    st.markdown("### \U0001F9CD Additional Guests")
    for i in range(1, int(total_guests)):
        col1, col2 = st.columns([2, 2])
        with col1:
            guest_name = st.text_input(f"Guest {i+1} Name", key=f"name_{i}")
        with col2:
            guest_id = st.file_uploader(f"Guest {i+1} ID", type=["jpg", "jpeg", "png", "pdf"], key=f"id_{i}")
        extra_guests.append(guest_name)
        extra_ids.append(guest_id)

# WhatsApp Admin Number
ADMIN_PHONE_NUMBER = "917002296566"

def create_whatsapp_link(name, phone, place, remarks, stay_from, stay_to, total_guests, extra_guests):
    msg = f"New Airbnb Guest Entry:\nMain: {name}\nPhone: {phone}\nFrom: {place}\nStay: {stay_from} to {stay_to}\nTotal Guests: {total_guests}\n"
    if extra_guests:
        msg += "Extra Guests: " + ", ".join(extra_guests) + "\n"
    msg += f"Remarks: {remarks}"
    return f"https://wa.me/{ADMIN_PHONE_NUMBER}?text={urllib.parse.quote(msg)}"

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

        extra_id_paths = []
        for i, (gname, gfile) in enumerate(zip(extra_guests, extra_ids)):
            if gfile:
                ext = os.path.splitext(gfile.name)[-1]
                fname = f"{gname.replace(' ', '_')}_{timestamp.replace(':', '-')}_{i}{ext}"
                fpath = os.path.join(PHOTO_DIR, fname)
                with open(fpath, "wb") as f:
                    f.write(gfile.read())
                extra_id_paths.append(fname)
            else:
                extra_id_paths.append("")

        new_entry = {
            "Timestamp": timestamp,
            "Name": name,
            "Phone": phone,
            "From": place,
            "Remarks": remarks,
            "Stay_From": stay_from.strftime("%Y-%m-%d"),
            "Stay_To": stay_to.strftime("%Y-%m-%d"),
            "Total_Guests": total_guests,
            "Extra_Guests": ", ".join(extra_guests),
            "Extra_IDs": ", ".join(extra_id_paths),
            "Photo_File": photo_filename
        }

        df = pd.DataFrame([new_entry])
        df.to_csv(CSV_FILE, mode="a", header=not os.path.exists(CSV_FILE), index=False)

        st.success("✅ Entry recorded successfully!")
        wa_link = create_whatsapp_link(name, phone, place, remarks, stay_from, stay_to, total_guests, extra_guests)
        st.markdown(f"[📲 Send to WhatsApp]({wa_link})", unsafe_allow_html=True)
    else:
        st.warning("Please fill in at least Guest Name and Phone Number.")

st.markdown("---")

st.subheader("📋 View Guest Entries")
if os.path.exists(CSV_FILE):
    guest_df = pd.read_csv(CSV_FILE)
    st.dataframe(guest_df, use_container_width=True)

    st.download_button(
        "📥 Download All Entries (CSV)",
        guest_df.to_csv(index=False).encode("utf-8"),
        file_name="guest_entries.csv",
        mime="text/csv"
    )

    st.subheader("🖨️ Generate PDF for Guest")
    if "Name" in guest_df.columns:
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
            <p><strong>Stay:</strong> {row['Stay_From']} to {row['Stay_To']}</p>
            <p><strong>Total Guests:</strong> {row['Total_Guests']}</p>
            <p><strong>Extra Guests:</strong> {row['Extra_Guests']}</p>
            <p><strong>Remarks:</strong> {row['Remarks']}</p>
            <p><strong>Timestamp:</strong> {row['Timestamp']}</p>
            """

            # --- Main Guest Photo ---
            photo_file = str(row.get("Photo_File", "")).strip()
            if photo_file and photo_file.lower() != "nan":
                img_path = os.path.join(PHOTO_DIR, photo_file)
                if os.path.exists(img_path) and img_path.lower().endswith((".jpg", ".jpeg", ".png")):
                    with open(img_path, "rb") as img_file:
                        b64_img = base64.b64encode(img_file.read()).decode()
                        html += f'<p><strong>Main Guest ID:</strong><br><img src="data:image/png;base64,{b64_img}" width="250"/></p>'

            # --- Extra Guest Photos ---
            extra_ids_str = str(row.get("Extra_IDs", "")).strip()
            extra_names_str = str(row.get("Extra_Guests", "")).strip()

            extra_names = [name.strip() for name in extra_names_str.split(",") if name.strip()]
            extra_ids = [fid.strip() for fid in extra_ids_str.split(",") if fid.strip()]

            if extra_names and extra_ids:
                html += "<h3>Extra Guest ID Documents:</h3>"
                for name, file in zip(extra_names, extra_ids):
                    file_path = os.path.join(PHOTO_DIR, file)
                    if os.path.exists(file_path) and file_path.lower().endswith((".jpg", ".jpeg", ".png")):
                        with open(file_path, "rb") as img_file:
                            b64_img = base64.b64encode(img_file.read()).decode()
                            html += f'<p><strong>{name}</strong><br><img src="data:image/png;base64,{b64_img}" width="250"/></p>'

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
