from flask import Flask, render_template, request, send_file
from stego_utils import encode_image, decode_image
from werkzeug.utils import secure_filename
from PIL import Image
import os

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

    # Use message from textarea or uploaded file
    message = request.form.get("message", "")
    text_file = request.files.get("textfile")
    if text_file and text_file.filename.endswith(".txt"):
        message = text_file.read().decode("utf-8")

    original_filename = secure_filename(image.filename)
    img_path = os.path.join(UPLOAD_FOLDER, original_filename)
    image.save(img_path)

    # Convert image to BMP
    bmp_path = os.path.join(UPLOAD_FOLDER, "converted.bmp")
    try:
        img = Image.open(img_path).convert("RGB")
        img.save(bmp_path, format="BMP")
    except Exception as e:
        return f"<h3>Error converting image to BMP: {e}</h3>"

    # Encode message into BMP
    output_path = os.path.join(UPLOAD_FOLDER, "stego.bmp")
    try:
        encode_image(bmp_path, message, key, output_path)
    except Exception as e:
        return f"<h3>Error encoding image: {e}</h3>"

    return send_file(output_path, as_attachment=True)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

