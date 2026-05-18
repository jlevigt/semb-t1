import struct

def rotate_left(x, n):
    return ((x << n) & 0xFFFFFFFF) | (x >> (32 - n))

def quarter_round(x, a, b, c, d):
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF; x[d] ^= x[a]; x[d] = rotate_left(x[d], 16)
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF; x[b] ^= x[c]; x[b] = rotate_left(x[b], 12)
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF; x[d] ^= x[a]; x[d] = rotate_left(x[d], 8)
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF; x[b] ^= x[c]; x[b] = rotate_left(x[b], 7)

def chacha20_block(key, nonce, counter):
    state = [0] * 16
    state[0] = 0x61707865
    state[1] = 0x3320646e
    state[2] = 0x79622d32
    state[3] = 0x6b206574
    
    for i in range(8):
        state[4+i] = struct.unpack("<I", key[i*4:i*4+4])[0]
        
    state[12] = counter
    
    for i in range(3):
        state[13+i] = struct.unpack("<I", nonce[i*4:i*4+4])[0]
        
    initial_state = list(state)
    
    for _ in range(10):
        quarter_round(state, 0, 4, 8, 12)
        quarter_round(state, 1, 5, 9, 13)
        quarter_round(state, 2, 6, 10, 14)
        quarter_round(state, 3, 7, 11, 15)
        quarter_round(state, 0, 5, 10, 15)
        quarter_round(state, 1, 6, 11, 12)
        quarter_round(state, 2, 7, 8, 13)
        quarter_round(state, 3, 4, 9, 14)
        
    output = b""
    for i in range(16):
        res = (state[i] + initial_state[i]) & 0xFFFFFFFF
        output += struct.pack("<I", res)
    return output

def chacha20_encrypt(data, key, nonce, counter=0):
    output = bytearray()
    for i in range(0, len(data), 64):
        block = data[i:i+64]
        keystream = chacha20_block(key, nonce, counter + (i // 64))
        for j in range(len(block)):
            output.append(block[j] ^ keystream[j])
    return bytes(output)
