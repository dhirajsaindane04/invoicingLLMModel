from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import fitz
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
API_KEY = os.getenv('GOOGLE_API_KEY')

app = Flask(__name__)

def get_gemini_response(api_key, image_data, prompt):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([image_data[0], prompt])
    return response.text

def extract_invoice_number(pdf_path):
    pdf_document = fitz.open(pdf_path)
    page = pdf_document.load_page(0)
    pix = page.get_pixmap()
    img_byte_arr = pix.tobytes("jpeg")

    # Create the prompt for extracting the invoice number
    prompt = '''From the invoice image in @docs, extract all necessary information and generate a JSON payload. The JSON should follow this structure:
{
    "buyer_address": "",
    "buyer_city": "",
    "buyer_country": "",
    "buyer_name": "",
    "buyer_postal_code": "",
    "currency": "",
    "discount": 0.0,
    "due_date": "",
    "invoice_date": "",
    "invoice_no": "",
    "items": [
        {
            "Amt": 0.0,
            "Description": "",
            "Disc": 0.0,
            "Net Amt": 0.0,
            "No.": 0,
            "Qty": 0,
            "Tax": 0.0,
            "U/Price": 0.0
        }
    ],
    "payment_term": "",
    "reference_no": "",
    "supplier_service_tax_id": "",
    "subtotal": 0.0,
    "supplier_address": "",
    "supplier_city": "",
    "supplier_contact": "",
    "supplier_country": "",
    "supplier_email": "",
    "supplier_name": "",
    "supplier_postal_code": "",
    "supplier_reg_no": "",
    "supplier_website": "",
    "total": 0.0
}
Ensure all fields, especially numerical values, are correctly interpreted and formatted.'''

    # Get the response from Gemini
    response = get_gemini_response(API_KEY, [{"mime_type": "image/jpeg", "data": img_byte_arr}], prompt)
    
    # Clean and parse the JSON response
    try:
        # Remove potential Markdown formatting
        cleaned_response = response.strip().replace('```json\n', '').replace('\n```', '')
        # Load the cleaned response as a JSON object
        json_response = json.loads(cleaned_response)
    except json.JSONDecodeError:
        return "Error: Response is not valid JSON."

    return json_response


@app.route('/extract_invoice_number', methods=['POST'])
def extract_invoice_number_from_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        file.save(file_path)

        try:
            invoice_number = extract_invoice_number(file_path)
            return jsonify({"invoice_number": invoice_number})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            os.remove(file_path)  # Clean up the uploaded file
    else:
        return jsonify({"error": "Invalid file format. Please upload a PDF."}), 400

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
