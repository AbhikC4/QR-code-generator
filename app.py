from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import qrcode
import uuid
import os

app = Flask(__name__)
CORS(app)

# Folders for images and generated QR codes
QR_FOLDER = os.path.join('static', 'qrcodes')
IMAGE_FOLDER = os.path.join('static', 'uploaded_images')
os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    try:
        if request.content_type.startswith('multipart/form-data'):
            input_data = None
            qr_type = request.form.get('type', '')
            fill_color = request.form.get('color', '#000000')
            back_color = request.form.get('bg', '#ffffff')
            selected_size = str(request.form.get('size', '150'))

            if qr_type == 'image':
                image_file = request.files.get('file')
                if not image_file:
                    return jsonify({'error': 'No image uploaded'}), 400
                filename = f"{uuid.uuid4().hex}_{image_file.filename}"
                filepath = os.path.join(IMAGE_FOLDER, filename)
                image_file.save(filepath)

                # QR code will link to the image URL
                input_data = f"http://127.0.0.1:5000/static/uploaded_images/{filename}"
            else:
                return jsonify({'error': 'Unsupported multipart type'}), 400
        else:
            data = request.get_json()
            input_data = data.get('input', '').strip()
            qr_type = data.get('type', '')
            fill_color = data.get('color', '#000000')
            back_color = data.get('bg', '#ffffff')
            selected_size = str(data.get('size', '150'))

        if not input_data:
            return jsonify({'error': 'No input provided'}), 400

        # Special handling for link validation
        if qr_type == 'link':
            if '.' not in input_data and '@' not in input_data:
                return jsonify({'error': 'Invalid link or UPI format'}), 400
            if '.' in input_data and '@' in input_data:
                return jsonify({'error': 'Cannot contain both "." and "@"'}), 400

        size_map = {
            "150": 1,
            "200": 5,
            "300": 10
        }
        version = size_map.get(selected_size, 1)

        qr = qrcode.QRCode(
            version=version,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(input_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        qr_filename = f"{uuid.uuid4().hex}.png"
        qr_filepath = os.path.join(QR_FOLDER, qr_filename)
        img.save(qr_filepath)

        return jsonify({'filename': qr_filename})

    except Exception as e:
        print("QR generation error:", e)
        return jsonify({'error': 'QR generation failed'}), 500

@app.route('/static/qrcodes/<filename>')
def serve_qr(filename):
    return send_from_directory(QR_FOLDER, filename)

@app.route('/static/uploaded_images/<filename>')
def serve_uploaded_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
