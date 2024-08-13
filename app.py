import streamlit as st
from PIL import Image, UnidentifiedImageError
import google.generativeai as genai
import fitz

def get_gemini_response(api_key, input_text, image_data, prompt):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
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

st.set_page_config(page_title="Invoice Gemini Application", layout="wide")

# Custom header with logo and title
st.markdown("""
<div style="display: flex; flex-direction: row; align-items: center; justify-content: center;">
    <a style="margin-right: 10px;" href="https://www.google.com" target="_blank">
        <img src="https://img.icons8.com/color/32/000000/google-logo.png"/>
    </a>
    <h1 style="margin-left: 10px;">Invoice Extractor Origin with Gemini Application</h1>
</div>
""", unsafe_allow_html=True)

# Settings panel with sliders and API key input
with st.sidebar:
    st.header("Gemini Settings")
    api_key = st.text_input("Enter your API Key: ", type="password")
    temperature = st.slider("Temperature (controls randomness)", 0.0, 1.0, 0.69)
    top_p = st.slider("Top P (nucleus sampling)", 0.0, 1.0, 1.0)
    top_k = st.slider("Top K (highest-probability tokens)", 0, 100, 50)
    st.info("Adjust these settings to modify the behavior of the Gemini model.")
    st.info("""
        **Temperature**: Controls the randomness of the output. Lower values make the output more deterministic.

        **Top P (nucleus sampling)**: Controls the cumulative probability cutoff for token sampling. The model considers tokens until the cumulative probability exceeds the top_p value.

        **Top K**: Controls the number of highest-probability tokens to keep for sampling.
    """)


# Main layout with tabs
tab1, tab2, tab3 = st.tabs(["Upload", "Extract", "Results"])

with tab1:
    st.header("Upload Invoice")
    uploaded_file = st.file_uploader("Choose an image or PDF...", type=["jpg", "jpeg", "png", "pdf"])
    if uploaded_file is not None:
        try:
            if uploaded_file.type in ["image/jpeg", "image/png", "image/jpg"]:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image.", use_column_width=True)
            elif uploaded_file.type == "application/pdf":
                st.write("PDF uploaded. Ready to process.")
                # JavaScript to switch tabs
                st.components.v1.html("""
                    <script>
                        const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                        if (tabs.length > 1) {
                            tabs[1].click();
                        }
                    </script>
                """, height=0)
        except UnidentifiedImageError:
            st.error("The uploaded file could not be identified as an image. Please upload a valid image file.")

with tab2:
    st.header("Extract Information")
    input_text = st.text_input("Input Prompt: ", key="input")
    options = ["Select an option", "Invoice Number", "Supplier Details", "Buyer Details", "Item Details","JSON Data","YAML Data"]
    selected_option = st.selectbox("Select the information you want to extract:", options)
    prompts = {
        "Invoice Number": "Extract the invoice number from the invoice image.",
        "Supplier Details": "Extract the supplier details from the invoice image.",
        "Buyer Details": "Extract the buyer details from the invoice image.",
        "Item Details": "Extract the item details and make sure don't include supplier and buyer detail be specific to items and their respective information only from the invoice image.",
        "JSON Data": "Extract all data in json format",
        "YAML Data": "Extract all data in Yaml format"
    }
    submit = st.button("Tell me about the invoice")

    if submit and api_key and selected_option != "Select an option":
        # JavaScript to switch tabs
        st.components.v1.html("""
            <script>
                const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                if (tabs.length > 2) {
                    tabs[2].click();
                }
            </script>
        """, height=0)

with tab3:
    st.header("Results")
    result_placeholder = st.empty()

if submit and api_key and selected_option != "Select an option":
    with st.spinner("Processing..."):
        try:
            image_data = input_image_setup(uploaded_file)
            input_prompt = prompts[selected_option]
            response = get_gemini_response(api_key, input_text, image_data, input_prompt)
            result_placeholder.subheader("The Response is")
            result_placeholder.write(response)
        except Exception as e:
            result_placeholder.error(f"Error processing the request: {e}")
elif submit:
    if not api_key:
        st.warning("Please enter your API Key.")
    elif selected_option == "Select an option":
        st.warning("Please select an option from the dropdown.")