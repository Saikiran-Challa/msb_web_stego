from PIL import Image
import hashlib

def text_to_bits(text):
    return ''.join(f'{ord(c):08b}' for c in text)

def bits_to_text(bits):
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    return ''.join(chr(int(b, 2)) for b in chars if len(b) == 8)

def key_to_seed(key):
    return int(hashlib.sha256(key.encode()).hexdigest(), 16)

def encode_image(img_path, message, key, output_path):
    img = Image.open(img_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    pixels = img.load()
    width, height = img.size

    msg_bits = text_to_bits(message)
    msg_len = len(msg_bits)
    max_capacity = width * height * 3

    if msg_len + 32 > max_capacity:
        raise ValueError("Message too large for image.")

    # Prefix message with 32-bit length header
    msg_len_bin = f'{msg_len:032b}'
    full_bits = msg_len_bin + msg_bits

    index = 0
    for y in range(height):
        for x in range(width):
            if index >= len(full_bits):
                break
            r, g, b = pixels[x, y]
            r = (r & ~1) | int(full_bits[index])
            index += 1
            if index < len(full_bits):
                g = (g & ~1) | int(full_bits[index])
                index += 1
            if index < len(full_bits):
                b = (b & ~1) | int(full_bits[index])
                index += 1
            pixels[x, y] = (r, g, b)
        if index >= len(full_bits):
            break

    img.save(output_path)

def decode_image(img_path, key):
    img = Image.open(img_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    pixels = img.load()
    width, height = img.size

    bits = ''
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bits += str(r & 1)
            bits += str(g & 1)
            bits += str(b & 1)

    msg_len = int(bits[:32], 2)
    msg_bits = bits[32:32+msg_len]
    return bits_to_text(msg_bits)