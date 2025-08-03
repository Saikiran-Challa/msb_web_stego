# app.py
from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image
import io
import os

app = Flask(__name__)

# Utility Functions
def encode_msb(image, message, key):
    binary_message = ''.join(f'{ord(c):08b}' for c in message)
    key_binary = ''.join(f'{ord(c):08b}' for c in key)
    binary_message += key_binary + '1111111111111110'  # End pattern

    img = image.convert("RGB")
    pixels = img.load()

    idx = 0
    for y in range(img.height):
        for x in range(img.width):
            if idx >= len(binary_message):
                break
            r, g, b = pixels[x, y]
            r = (r & 0x7F) | (int(binary_message[idx]) << 7)
            pixels[x, y] = (r, g, b)
            idx += 1
        if idx >= len(binary_message):
            break

    return img

def decode_msb(image, key):
    img = image.convert("RGB")
    pixels = img.load()
    bits = ""

    for y in range(img.height):
        for x in range(img.width):
            r, g, b = pixels[x, y]
            bits += str((r & 0x80) >> 7)

    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    decoded = ""
    for ch in chars:
        if ch == '11111110':  # End pattern
            break
        decoded += chr(int(ch, 2))

    if key not in decoded:
        return None
    return decoded.replace(key, "")

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/encrypt", methods=["POST"])
def encrypt():
    image_file = request.files["image"]
    message = request.form["message"]
    key = request.form["key"]

    if not image_file or not message or not key:
        return "Missing data"

    image = Image.open(image_file.stream)
    encoded_image = encode_msb(image, message, key)

    img_io = io.BytesIO()
    encoded_image.save(img_io, format="PNG")
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png", as_attachment=True, download_name="encoded_image.png")

@app.route("/decrypt", methods=["GET", "POST"])
def decrypt():
    if request.method == "GET":
        return redirect(url_for("index"))

    image_file = request.files["image"]
    key = request.form["key"]

    if not image_file or not key:
        return "Missing image or key"

    image = Image.open(image_file.stream)
    message = decode_msb(image, key)

    if message is None:
        return "Incorrect key or message not found."

    return render_template("index.html", decrypted_message=message)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

