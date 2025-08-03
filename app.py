from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from PIL import Image
import io
import stego_utils

app = Flask(__name__)
# Secret key for flash messages (use a secure random key in production)
app.secret_key = 'supersecretkey123'

@app.route('/')
def index():
    # Render the main page with forms for encrypt/decrypt.
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    # Ensure a cover image was uploaded
    if 'cover_image' not in request.files:
        flash("No image file part in request", "danger")
        return redirect(url_for('index'))
    file = request.files['cover_image']
    if file.filename == '':
        flash("No cover image selected", "danger")
        return redirect(url_for('index'))
    # Read the image
    try:
        image = Image.open(file)
    except Exception:
        flash("Invalid image file", "danger")
        return redirect(url_for('index'))

    # Get the secret message: from textarea or .txt file
    message = request.form.get('secret_message', '')
    msg_file = request.files.get('message_file')
    if msg_file and msg_file.filename:
        # If a .txt file is uploaded, use its contents instead
        if msg_file.filename.lower().endswith('.txt'):
            try:
                message = msg_file.read().decode('utf-8')
            except Exception:
                flash("Uploaded text file could not be decoded (use UTF-8)", "danger")
                return redirect(url_for('index'))
        else:
            flash("Message file must be a .txt file", "danger")
            return redirect(url_for('index'))

    # Ensure a message and key are provided
    if not message:
        flash("No message provided for encryption", "danger")
        return redirect(url_for('index'))
    key = request.form.get('encrypt_key', '')
    if not key:
        flash("Secret key is required", "danger")
        return redirect(url_for('index'))

    # Perform MSB steganography encoding
    try:
        stego_image = stego_utils.encode_image(image, message, key)
    except Exception as e:
        flash(f"Error encoding message: {str(e)}", "danger")
        return redirect(url_for('index'))

    # Send the stego image as a downloadable file (PNG format)
    img_io = io.BytesIO()
    stego_image.save(img_io, format='PNG')
    img_io.seek(0)
    download_name = f"{file.filename.rsplit('.', 1)[0]}_stego.png"
    return send_file(img_io, mimetype='image/png', as_attachment=True,
                     attachment_filename=download_name)

@app.route('/decrypt', methods=['POST'])
def decrypt():
    # Ensure a stego image was uploaded
    if 'stego_image' not in request.files:
        flash("No image file part in request", "danger")
        return redirect(url_for('index'))
    file = request.files['stego_image']
    if file.filename == '':
        flash("No stego image selected", "danger")
        return redirect(url_for('index'))
    # Read the image
    try:
        image = Image.open(file)
    except Exception:
        flash("Invalid image file", "danger")
        return redirect(url_for('index'))

    # Get the secret key for decryption
    key = request.form.get('decrypt_key', '')
    if not key:
        flash("Secret key is required for decryption", "danger")
        return redirect(url_for('index'))

    # Perform MSB steganography decoding
    try:
        message = stego_utils.decode_image(image, key)
    except Exception as e:
        flash(f"Error decoding message: {str(e)}", "danger")
        return redirect(url_for('index'))

    # Render the index page with the extracted message shown
    return render_template('index.html', decrypted_text=message)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

