import sys
import os
import struct
import secrets

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.uart_client import ChaCha20UART, CMD_INIT, CMD_DATA, CMD_END, RESP_ACK_INIT, RESP_ACK_DATA

def run_demo(port):
    print("--- Negative File-Based Demonstration (Wrong Key) ---")
    
    # 1. Setup Files
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "negative")
    os.makedirs(data_dir, exist_ok=True)

    plaintext_file = os.path.join(data_dir, "negative_plaintext.txt")
    ciphertext_file = os.path.join(data_dir, "negative_ciphertext.txt")
    decrypted_file = os.path.join(data_dir, "negative_decrypted.txt")
    
    test_text = "This is a secret message. If you use the wrong key, you will not be able to read it!"
    with open(plaintext_file, "w") as f:
        f.write(test_text)
    
    correct_key = secrets.token_bytes(32)
    wrong_key = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    counter = 0

    try:
        dev = ChaCha20UART(port)
    except Exception as e:
        print(f"Error opening port: {e}")
        return

    # 2. ENCRYPTION PHASE (Correct Key)
    print(f"Reading {plaintext_file} for encryption...")
    with open(plaintext_file, "rb") as f:
        plaintext = f.read()

    print("Initializing STM32 for encryption with CORRECT KEY...")
    init_payload = correct_key + nonce + struct.pack("<I", counter)
    dev.send_packet(CMD_INIT, init_payload)
    cmd, _, _ = dev.receive_packet()
    if cmd != RESP_ACK_INIT:
        print("Failed to INIT for encryption")
        return

    print("Streaming data for encryption...")
    ciphertext = bytearray()
    for i in range(0, len(plaintext), 64):
        chunk = plaintext[i:i+64]
        dev.send_packet(CMD_DATA, chunk)
        cmd, size, payload = dev.receive_packet()
        if cmd != RESP_ACK_DATA:
            print("Error during encryption")
            return
        ciphertext.extend(payload)

    dev.send_packet(CMD_END)
    dev.receive_packet()

    print(f"Saving ciphertext to {ciphertext_file}...")
    with open(ciphertext_file, "w") as f:
        f.write(ciphertext.hex().upper())

    # 3. DECRYPTION PHASE (Wrong Key)
    print(f"\nReading {ciphertext_file} for decryption...")
    with open(ciphertext_file, "r") as f:
        ciphertext_hex = f.read().strip()
    ciphertext_to_decrypt = bytes.fromhex(ciphertext_hex)

    print("Re-initializing STM32 for decryption with WRONG KEY...")
    init_payload_wrong = wrong_key + nonce + struct.pack("<I", counter)
    dev.send_packet(CMD_INIT, init_payload_wrong)
    cmd, _, _ = dev.receive_packet()
    if cmd != RESP_ACK_INIT:
        print("Failed to INIT for decryption")
        return

    print("Streaming data for decryption...")
    decrypted_data = bytearray()
    for i in range(0, len(ciphertext_to_decrypt), 64):
        chunk = ciphertext_to_decrypt[i:i+64]
        dev.send_packet(CMD_DATA, chunk)
        cmd, size, payload = dev.receive_packet()
        if cmd != RESP_ACK_DATA:
            print("Error during decryption")
            return
        decrypted_data.extend(payload)

    dev.send_packet(CMD_END)
    dev.receive_packet()

    print(f"Saving decrypted data to {decrypted_file}...")
    with open(decrypted_file, "w") as f:
        f.write(decrypted_data.hex().upper())

    # 4. VERIFICATION
    print("\n--- VERIFICATION ---")
    if plaintext == decrypted_data:
        print("FAILURE: The decrypted data surprisingly matches the plaintext despite a wrong key!")
    else:
        print("SUCCESS: As expected, the decrypted data DOES NOT match the original plaintext.")
        print(f"Original text: {plaintext.decode('utf-8', errors='replace')}")
        print(f"Decrypted gibberish (hex): {decrypted_data.hex().upper()}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Negative File Demonstration (Wrong Key)")
    parser.add_argument("port", help="Serial port (e.g., /dev/ttyACM0)")
    args = parser.parse_args()
    
    run_demo(args.port)
