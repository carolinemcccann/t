from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import smtplib
from email.message import EmailMessage
import os

app = Flask(__name__)

@app.route('/send-pdf', methods=['POST'])
def send_pdf():
    file = request.files['pdf']
    emails = request.form.getlist('emails')
    smtp_server = request.form.get('smtp_server') or os.getenv('SMTP_SERVER')
    smtp_port = int(request.form.get('smtp_port') or os.getenv('SMTP_PORT', 587))
    smtp_username = request.form.get('smtp_username') or os.getenv('SMTP_USERNAME')
    smtp_password = request.form.get('smtp_password') or os.getenv('SMTP_PASSWORD')

    if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
        return jsonify({'status': 'SMTP settings missing'}), 400

    input_path = "input.pdf"
    output_path = "compressed.pdf"
    file.save(input_path)

    doc = fitz.open(input_path)
    for page in doc:
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            doc._delete_object(xref)
            page.insert_image(page.rect, stream=image_bytes, keep_proportion=True)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    try:
        msg['To'] = smtp_username  # Dummy To field to satisfy some servers\n        for email_to in emails:
            msg = EmailMessage()
            msg['Subject'] = 'Your Compressed PDF'
            msg['From'] = smtp_username
            msg['Bcc'] = email_to
            msg.set_content("Please find the attached compressed PDF.")

            with open(output_path, 'rb') as f:
                file_data = f.read()
                msg.add_attachment(file_data, maintype='application', subtype='pdf', filename='compressed.pdf')

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        return jsonify({'status': 'Emails sent successfully'})
    except Exception as e:
        return jsonify({'status': 'Failed to send email', 'error': str(e)})

if __name__ == '__main__':
    app.run()
