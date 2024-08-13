from dotenv import load_dotenv
import streamlit as st
import os
from PIL import Image
import google.generativeai as genai
from pdf2image import convert_from_bytes
import io

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to get response from Gemini model
def get_gemini_response(input_text, image_parts):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = """
               Analyze the 'Invoice' PDF in @docs. Extract all data and format it into the following JSON structure. Ensure each field is accurately filled with data from the PDF, and if any data is missing, use null for that field:

{
    "buyer_address": "",
    "buyer_city": "",
    "buyer_country": "",
    "buyer_name": "",
    "buyer_postal_code": "",
    "currency": "",
    "due_date": "",
    "einvoiceTypeCode": "",
    "invoice_date": "",
    "invoice_no": "",
    "items": [
        {
            "Amt": 0,
            "Description": "",
            "Disc": 0,
            "Net Amt": 0,
            "No.": 0,
            "Qty": 0,
            "Tax": 0,
            "U/Price": 0
        },
        {
            "Amt": 0,
            "Description": "",
            "Disc": 0,
            "Net Amt": 0,
            "No.": 0,
            "Qty": 0,
            "Tax": 0,
            "U/Price": 0
        }
    ],
    "payment_term": "",
    "reference_no": "",
    "supplier_service_tax_id": "",
    "subtotal": 0,
    "supplier_address": "",
    "supplier_city": "",
    "supplier_contact": "",
    "supplier_country": "",
    "supplier_email": "",
    "supplier_name": "",
    "supplier_postal_code": "",
    "supplier_reg_no": "",
    "supplier_website": "",
    "total": 0,
    "refund": 0,
    "service_tax": 0,
    "apply_amount": 0,
    "bank_transfer": 0
}
"""
    response = model.generate_content([input_text, image_parts[0], prompt])
    return response.text

# Function to set up input image
def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        
        # If the file is a PDF, convert it to images
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(bytes_data)
            image_parts = []
            for image in images:
                with io.BytesIO() as output:
                    image.save(output, format="PNG")
                    image_parts.append({
                        "mime_type": "image/png",
                        "data": output.getvalue()
                    })
            return image_parts
        else:
            image_parts = [
                {
                    "mime_type": uploaded_file.type,
                    "data": bytes_data
                }
            ]
            return image_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Initialize Streamlit app
st.set_page_config(page_title="Gemini Image Demo")

st.header("Gemini Application")

uploaded_file = st.file_uploader("Choose an image or PDF...", type=["jpg", "jpeg", "png", "pdf"])

image = None
if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        st.info("PDF file uploaded. Converting to images...")
        images = convert_from_bytes(uploaded_file.getvalue())
        for i, image in enumerate(images):
            st.image(image, caption=f"Page {i+1}", use_column_width=True)
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image.", use_column_width=True)

submit = st.button("Tell me about the image")

# If submit button is clicked
if submit:
    if uploaded_file is not None:
        image_data = input_image_setup(uploaded_file)
        response = get_gemini_response("Extract invoice data", image_data)
        st.subheader("The Response is")
        st.write(response)
    else:
        st.error("Please upload an image or PDF file.")
