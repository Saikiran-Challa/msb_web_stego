from flask import Flask, render_template, request, send_file
import os
from stego_utils import encode_image, decode_image
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/encrypt", methods=["POST"])
def encrypt():
    image = request.files["image"]
    key = request.form["key"]

    # Handle message input via textarea or .txt file
    message = request.form.get("message", "")
    text_file = request.files.get("textfile")
    if text_file and text_file.filename.endswith(".txt"):
        message = text_file.read().decode("utf-8")

    if not image.filename.endswith(".bmp"):
        return "<h3>Error: Please upload a BMP image file (.bmp)</h3>"

    filename = secure_filename(image.filename)
    img_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(img_path)

    output_path = os.path.join(UPLOAD_FOLDER, "stego.bmp")
    try:
        encode_image(img_path, message, key, output_path)
    except Exception as e:
        return f"<h3>Error during encryption: {e}</h3>"

    return send_file(output_path, as_attachment=True)

@app.route("/decrypt", methods=["POST"])
def decrypt():
    image = request.files["image"]
    key = request.form["key"]

    if not image.filename.endswith(".bmp"):
        return "<h3>Error: Please upload a BMP image file (.bmp)</h3>"

    filename = secure_filename(image.filename)
    img_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(img_path)

    try:
        hidden_message = decode_image(img_path, key)
    except Exception as e:
        return f"<h3>Error during decryption: {e}</h3>"

    return render_template("index.html", decrypted_text=hidden_message)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
