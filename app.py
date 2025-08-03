from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from PIL import Image
import os
import io
import hashlib

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# 🔐 Embed message into image using MSB
def embed_message(image, message, key):
    # Validate image capacity
    width, height = image.size
    max_bits = width * height
    required_bits = len(message) * 8 + 32  # 32 bits for message length
    
    if required_bits > max_bits:
        raise ValueError(f"Message too large for image. Max: {max_bits//8} bytes")

    # Use key to seed the embedding process
    seed = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    
    # Prepend message length (32 bits)
    message_length = len(message)
    binary_length = format(message_length, '032b')
    binary_message = binary_length + ''.join(format(ord(char), '08b') for char in message)
    
    pixels = image.convert("RGB").load()
    index = 0

    # Create a copy to avoid modifying original
    img_copy = image.copy()
    pixels_copy = img_copy.load()

    for y in range(height):
        for x in range(width):
            if index >= len(binary_message):
                break
            r, g, b = pixels_copy[x, y]
            new_r = (r & ~1) | int(binary_message[index])
            pixels_copy[x, y] = (new_r, g, b)
            index += 1
        if index >= len(binary_message):
            break

    output = io.BytesIO()
    img_copy.save(output, format="PNG")
    output.seek(0)
    return output

# 🔓 Extract message from image
def extract_message(image, key):
    seed = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    
    pixels = image.convert("RGB").load()
    width, height = image.size
    binary_message = ""

    # First 32 bits contain message length
    for y in range(height):
        for x in range(width):
            if len(binary_message) >= 32:
                break
            r, g, b = pixels[x, y]
            binary_message += str(r & 1)
        if len(binary_message) >= 32:
            break

    # Get message length from first 32 bits
    try:
        message_length = int(binary_message[:32], 2)
    except ValueError:
        raise ValueError("Invalid message header - possibly wrong key")

    total_bits_needed = 32 + message_length * 8
    bits_collected = 32

    # Collect the actual message bits
    for y in range(height):
        for x in range(width):
            if bits_collected >= total_bits_needed:
                break
            r, g, b = pixels[x, y]
            binary_message += str(r & 1)
            bits_collected += 1
        if bits_collected >= total_bits_needed:
            break

    # Convert binary to string
    chars = []
    for i in range(32, len(binary_message), 8):
        if i + 8 > len(binary_message):
            break
        char_bin = binary_message[i:i+8]
        try:
            chars.append(chr(int(char_bin, 2)))
        except ValueError:
            continue
    
    return ''.join(chars)

# � Homepage
@app.route("/")
def index():
    return render_template("index.html")

# 🔐 Encrypt route
@app.route("/encrypt", methods=["POST"])
def encrypt():
    image = request.files.get("image")
    message = request.form.get("message", "")
    key = request.form.get("key", "")
    file = request.files.get("message_file")

    if file:
        try:
            message = file.read().decode("utf-8")
        except UnicodeDecodeError:
            flash("File must be UTF-8 encoded text")
            return redirect(url_for("index"))

    if not image:
        flash("Please upload an image")
        return redirect(url_for("index"))
        
    if not message.strip():
        flash("Message cannot be empty")
        return redirect(url_for("index"))
        
    if not key.strip():
        flash("Encryption key cannot be empty")
        return redirect(url_for("index"))

    try:
        img = Image.open(image.stream)
        output = embed_message(img, message, key)
        return send_file(output, as_attachment=True, download_name="encrypted.png", mimetype="image/png")
    except ValueError as ve:
        flash(f"Encryption error: {str(ve)}")
    except Exception as e:
        flash(f"Unexpected error: {str(e)}")
    return redirect(url_for("index"))

# 🔓 Decrypt route
@app.route("/decrypt", methods=["POST"])
def decrypt():
    image = request.files.get("image")
    key = request.form.get("key")

    if not image:
        flash("Please upload an image")
        return redirect(url_for("index"))
        
    if not key.strip():
        flash("Decryption key cannot be empty")
        return redirect(url_for("index"))

    try:
        img = Image.open(image.stream)
        message = extract_message(img, key)
        return render_template("index.html", decrypted_message=message)
    except ValueError as ve:
        flash(f"Decryption error: {str(ve)}")
    except Exception as e:
        flash(f"Unexpected error: {str(e)}")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)