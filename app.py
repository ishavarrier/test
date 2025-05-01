# Add these routes to your Flask app.py file

import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import time

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variable to track the latest uploaded image
latest_image = None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('index.html', latest_image=latest_image)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file uploads"""
    global latest_image
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        
        # If user does not select file, browser also
        # submits an empty part without filename
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file and allowed_file(file.filename):
            # Create unique filename to avoid cache issues
            filename = secure_filename(file.filename)
            timestamp = str(int(time.time()))
            unique_filename = f"{timestamp}_{filename}"
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Update latest image path
            latest_image = f'/static/uploads/{unique_filename}'
            
            # Return success for API calls
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True, 
                    'image_url': latest_image,
                    'redirect': url_for('upload_success')
                })
            
            # For regular form submissions, redirect to the success page
            return redirect(url_for('upload_success'))
    
    # If GET request, show the upload form (if you have a separate page for this)
    return render_template('upload.html')

@app.route('/upload-success')
def upload_success():
    """Show a success page after upload"""
    return render_template('upload_success.html', image_url=latest_image)

@app.route('/check-for-new-image')
def check_for_new_image():
    """API endpoint for checking if there's a new uploaded image"""
    return jsonify({'image_url': latest_image})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)