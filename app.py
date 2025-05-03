from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import os
import time
import qrcode
from base64 import b64encode
from io import BytesIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Track the latest uploaded image
latest_image = None

@app.route('/')
def index():
    """Main page - welcome"""

    return render_template('index.html')

@app.route('/qr_upload', methods=['GET', 'POST'])
def qr_upload():
    global latest_image

    if request.method == 'POST':
        if 'photo' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file:
            filename = secure_filename(file.filename)
            timestamp = str(int(time.time()))
            unique_filename = f"{timestamp}_{filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(save_path)
            
            latest_image = url_for('static', filename=f'uploads/{unique_filename}')
            return redirect(url_for('upload_success'))

    # GET: render the QR code + upload form
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    upload_url = request.host_url + "/upload"
    qr.add_data(upload_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer)
    qr_image = b64encode(buffer.getvalue()).decode('utf-8')

    return render_template('qr_upload.html', qr_code=qr_image)



@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file uploads from the mobile device"""
    global latest_image
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'photo' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['photo']
        
        # If user does not select file, browser also
        # submits an empty part without filename
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file:
            # Create unique filename to avoid cache issues
            filename = secure_filename(file.filename)
            timestamp = str(int(time.time()))
            unique_filename = f"{timestamp}_{filename}"
            
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            
            # Update latest image path
            latest_image = url_for('static', filename=f'uploads/{unique_filename}')
            
            # Return success for API calls
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'image_url': latest_image})
            
            # For regular form submissions, redirect to the upload success page
            return redirect(url_for('upload_success'))
    
    # If GET request, show the upload form
    return render_template('upload.html')

@app.route('/upload-success')
def upload_success():
    """Show a success page after upload"""
    labels = [f"{chr(65 + row)}{col + 1}" for row in range(4) for col in range(4)]

    return render_template('upload_success.html', image_url=latest_image,labels=labels )

@app.route('/check-for-new-image')
def check_for_new_image():
    """API endpoint for checking if there's a new uploaded image"""
    return jsonify({'image_url': latest_image})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
