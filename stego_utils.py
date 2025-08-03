from PIL import Image

def encode_image(cover_image: Image.Image, message: str, key: str) -> Image.Image:
    """
    Embed a secret message into the image using MSB steganography.
    The message is first XOR-encrypted with the key, then bits are written into the MSB of each RGB channel.
    Returns a new PIL.Image with the hidden message.
    """
    # Convert image to RGB
    image = cover_image.convert('RGB')
    width, height = image.size
    pixels = image.load()

    # Encode and encrypt message
    message_bytes = message.encode('utf-8')
    key_bytes = key.encode('utf-8')
    if len(key_bytes) == 0:
        raise ValueError("Encryption key cannot be empty")
    # XOR-encrypt the message bytes with the key
    encrypted = bytes([message_bytes[i] ^ key_bytes[i % len(key_bytes)] 
                       for i in range(len(message_bytes))])
    length = len(encrypted)
    if length == 0:
        raise ValueError("Message is empty")

    # Prepare the bit string: 32-bit length header + message bits
    length_bits = format(length, '032b')  # fixed 32-bit header
    message_bits = ''.join(format(byte, '08b') for byte in encrypted)
    data_bits = length_bits + message_bits

    # Check capacity
    capacity = width * height * 3
    if len(data_bits) > capacity:
        raise ValueError("Image is too small to hold the message (need {} bits, have {})"
                         .format(len(data_bits), capacity))

    # Embed bits into image MSBs
    bit_index = 0
    for y in range(height):
        for x in range(width):
            if bit_index >= len(data_bits):
                break
            r, g, b = pixels[x, y]
            # Embed bit into Red channel MSB
            if bit_index < len(data_bits):
                r = (r & 0x7F) | (int(data_bits[bit_index]) << 7)
                bit_index += 1
            # Embed bit into Green channel MSB
            if bit_index < len(data_bits):
                g = (g & 0x7F) | (int(data_bits[bit_index]) << 7)
                bit_index += 1
            # Embed bit into Blue channel MSB
            if bit_index < len(data_bits):
                b = (b & 0x7F) | (int(data_bits[bit_index]) << 7)
                bit_index += 1
            pixels[x, y] = (r, g, b)
        if bit_index >= len(data_bits):
            break

    return image

def decode_image(stego_image: Image.Image, key: str) -> str:
    """
    Extract a hidden message from the image using MSB steganography.
    Reads the 32-bit length header and then the message bits, then XOR-decrypts with the key.
    Returns the decoded string message.
    """
    image = stego_image.convert('RGB')
    width, height = image.size
    pixels = image.load()

    def bits_generator():
        """Generator yielding MSB bits from the image pixels."""
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                yield (r >> 7) & 1
                yield (g >> 7) & 1
                yield (b >> 7) & 1

    gen = bits_generator()
    # Read the first 32 bits to get the message length
    length_bits = ''
    try:
        for _ in range(32):
            length_bits += str(next(gen))
    except StopIteration:
        raise ValueError("Image is too small or does not contain a hidden message")

    length = int(length_bits, 2)
    if length <= 0:
        raise ValueError("No hidden message found (length is zero)")
    # Read the next length*8 bits as the message
    message_bits = ''
    try:
        for _ in range(length * 8):
            message_bits += str(next(gen))
    except StopIteration:
        raise ValueError("Image does not contain full message data")

    # Convert bits to bytes
    encrypted_bytes = bytes(int(message_bits[i:i+8], 2) 
                            for i in range(0, len(message_bits), 8))

    # Decrypt with key (XOR)
    key_bytes = key.encode('utf-8')
    if len(key_bytes) == 0:
        raise ValueError("Decryption key cannot be empty")
    decrypted = bytes([encrypted_bytes[i] ^ key_bytes[i % len(key_bytes)] 
                       for i in range(len(encrypted_bytes))])
    # Decode to string
    try:
        message = decrypted.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError("Failed to decode message. Wrong key or corrupted data.")
    return message
