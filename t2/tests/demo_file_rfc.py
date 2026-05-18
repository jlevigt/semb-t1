import sys
import os
import struct

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.uart_client import ChaCha20UART, CMD_INIT, CMD_DATA, CMD_END, RESP_ACK_INIT, RESP_ACK_DATA

def run_demo(port):
    print("--- RFC 8439 File-Based Demonstration ---")
    
    # 1. Setup Files
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rfc")
    os.makedirs(data_dir, exist_ok=True)
    
    plaintext_file = os.path.join(data_dir, "rfc_plaintext.txt")
    ciphertext_file = os.path.join(data_dir, "rfc_ciphertext.hex")
    decrypted_file = os.path.join(data_dir, "rfc_decrypted.txt")
    
    rfc_text = "Ladies and Gentlemen of the class of '99: If I could offer you only one tip for the future, sunscreen would be it."
    with open(plaintext_file, "w") as f:
        f.write(rfc_text)
    
    key = bytes(range(32))
    nonce = bytes([0, 0, 0, 0, 0, 0, 0, 0x4a, 0, 0, 0, 0])
    counter = 1

    try:
        dev = ChaCha20UART(port)
    except Exception as e:
        print(f"Error opening port: {e}")
        return

    # 2. ENCRYPTION PHASE
    print(f"Reading {plaintext_file} for encryption...")
    with open(plaintext_file, "rb") as f:
        plaintext = f.read()

    print("Initializing STM32...")
    init_payload = key + nonce + struct.pack("<I", counter)
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

    # 3. DECRYPTION PHASE
    print(f"Reading {ciphertext_file} for decryption...")
    with open(ciphertext_file, "r") as f:
        ciphertext_hex = f.read().strip()
    ciphertext_to_decrypt = bytes.fromhex(ciphertext_hex)

    print("Re-initializing STM32 for decryption...")
    dev.send_packet(CMD_INIT, init_payload)
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
    with open(decrypted_file, "wb") as f:
        f.write(decrypted_data)

    # 4. VERIFICATION
    print("\n--- VERIFICATION ---")
    if plaintext == decrypted_data:
        print("SUCCESS: The decrypted file matches the original plaintext file.")
    else:
        print("FAILURE: The decrypted file does NOT match the original plaintext file.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RFC 8439 File Demonstration")
    parser.add_argument("port", help="Serial port (e.g., /dev/ttyACM0)")
    args = parser.parse_args()
    
    run_demo(args.port)
