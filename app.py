from dotenv import load_dotenv
import streamlit as st
import os
from PIL import Image, UnidentifiedImageError
import google.generativeai as genai
import fitz 

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=api_key)

def get_gemini_response(input_text, image_data, prompt):
    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([input_text, image_data[0], prompt])
    return response.text

def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        if uploaded_file.type == "application/pdf":
           
            pdf_document = fitz.open(stream=bytes_data, filetype="pdf")
            page = pdf_document.load_page(0)
            pix = page.get_pixmap()
            img_byte_arr = pix.tobytes("jpeg")
            image_parts = [
                {
                    "mime_type": "image/jpeg",
                    "data": img_byte_arr
                }
            ]
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


st.set_page_config(page_title="Gemini Application")
st.header("Invoicing Origin")

input_text = st.text_input("Input Prompt: ", key="input")

uploaded_file = st.file_uploader("Choose an image or PDF...", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file is not None:
    try:
        if uploaded_file.type in ["image/jpeg", "image/png", "image/jpg"]:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image.", use_column_width=True)
        elif uploaded_file.type == "application/pdf":
            st.write("PDF uploaded. Ready to process.")
    except UnidentifiedImageError:
        st.error("The uploaded file could not be identified as an image. Please upload a valid image file.")

submit = st.button("Tell me about the invoice")

input_prompt = """
               You are an expert in understanding invoices.
               You will receive input images as invoices &
               you will have to answer questions based on the input image.
               """

if submit:
    try:
        image_data = input_image_setup(uploaded_file)
        response = get_gemini_response(input_text, image_data, input_prompt)
        st.subheader("The Response is")
        st.write(response)
    except Exception as e:
        st.error(f"Error processing the request: {e}")
