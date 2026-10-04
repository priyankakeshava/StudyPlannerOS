"""
Discrete Mathematics - Error Control Codes
Syllabus: 7.3, 7.4
"""

def hamming_encode(data_bits: list[int]) -> list[int]:
    """
    Encodes 4 data bits into a 7-bit Hamming(7,4) codeword.
    Syllabus 7.3
    
    Data bits: d1, d2, d3, d4
    Parity bits: p1, p2, p3
    Positions: p1, p2, d1, p3, d2, d3, d4 (1 to 7)
    
    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4
    """
    if len(data_bits) != 4:
        raise ValueError("Data bits must be of length 4.")
    
    d1, d2, d3, d4 = data_bits
    
    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4
    
    return [p1, p2, d1, p3, d2, d3, d4]

def hamming_decode(received: list[int]) -> tuple[list[int], int]:
    """
    Decodes a 7-bit received word using Hamming(7,4) code.
    Computes syndrome, corrects single-bit error.
    Returns (corrected_4_data_bits, error_position) where error_position=0 means no error.
    Syllabus 7.3
    """
    if len(received) != 7:
        raise ValueError("Received bits must be of length 7.")
    
    r = list(received)
    p1, p2, d1, p3, d2, d3, d4 = r
    
    s1 = p1 ^ d1 ^ d2 ^ d4
    s2 = p2 ^ d1 ^ d3 ^ d4
    s3 = p3 ^ d2 ^ d3 ^ d4
    
    # error position = s3*4 + s2*2 + s1*1
    error_pos = s3 * 4 + s2 * 2 + s1 * 1
    
    if error_pos > 0:
        # Correct the error (1-indexed)
        r[error_pos - 1] ^= 1
        
    corrected_data = [r[2], r[4], r[5], r[6]]
    
    return corrected_data, error_pos

def hamming_distance(a: list[int], b: list[int]) -> int:
    """
    Computes the Hamming distance between two codewords.
    Syllabus 7.3
    """
    if len(a) != len(b):
        raise ValueError("Codewords must be of the same length.")
    return sum(1 for x, y in zip(a, b) if x != y)

def add_checksum(data: str) -> str:
    """
    Converts a string to binary, encodes chunks with Hamming(7,4),
    and appends a hex checksum line.
    Syllabus 7.3, 7.4
    """
    binary_data = ''.join(format(ord(c), '08b') for c in data)
    
    encoded_bits = []
    for i in range(0, len(binary_data), 4):
        chunk = binary_data[i:i+4]
        if len(chunk) < 4:
            chunk = chunk.ljust(4, '0')
        
        data_bits = [int(bit) for bit in chunk]
        encoded = hamming_encode(data_bits)
        encoded_bits.extend(encoded)
        
    # Convert encoded bits to hex
    # Pad to multiple of 4 bits for hex conversion
    padding = (4 - (len(encoded_bits) % 4)) % 4
    padded_bits = encoded_bits + [0] * padding
    
    hex_chars = []
    for i in range(0, len(padded_bits), 4):
        val = sum(bit * (2**(3-j)) for j, bit in enumerate(padded_bits[i:i+4]))
        hex_chars.append(format(val, 'x'))
        
    checksum = "".join(hex_chars)
    return data + "\n---CHECKSUM---\n" + checksum

def verify_checksum(data: str) -> tuple[bool, str]:
    """
    Verifies the data against its checksum.
    Syllabus 7.3, 7.4
    """
    if "\n---CHECKSUM---\n" not in data:
        return False, "No checksum found."
        
    content, checksum = data.rsplit("\n---CHECKSUM---\n", 1)
    
    expected_data = add_checksum(content)
    if data == expected_data:
        return True, "Checksum valid."
    
    return False, "Checksum mismatch."
