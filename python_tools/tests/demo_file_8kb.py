import sys
import os
import struct
import secrets

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.uart_client import ChaCha20UART, CMD_INIT, CMD_DATA, CMD_END, RESP_ACK_INIT, RESP_ACK_DATA

def run_demo(port):
    print("--- 8KB Random Data File-Based Demonstration ---")
    
    # 1. Setup Files
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "8kb")
    os.makedirs(data_dir, exist_ok=True)

    plaintext_file = os.path.join(data_dir, "8kb_plaintext.txt")
    ciphertext_file = os.path.join(data_dir, "8kb_ciphertext.txt")
    decrypted_file = os.path.join(data_dir, "8kb_decrypted.txt")
    
    data_size = 8192 # 8KB
    random_data = secrets.token_bytes(data_size)
    with open(plaintext_file, "w") as f:
        f.write(random_data.hex().upper())
    
    key = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    counter = 0

    try:
        dev = ChaCha20UART(port)
    except Exception as e:
        print(f"Error opening port: {e}")
        return

    # 2. ENCRYPTION PHASE
    print(f"Reading {plaintext_file} for encryption...")
    with open(plaintext_file, "r") as f:
        plaintext_hex = f.read().strip()
    plaintext = bytes.fromhex(plaintext_hex)

    print("Initializing STM32...")
    init_payload = key + nonce + struct.pack("<I", counter)
    dev.send_packet(CMD_INIT, init_payload)
    cmd, _, _ = dev.receive_packet()
    if cmd != RESP_ACK_INIT:
        print("Failed to INIT for encryption")
        return

    print("Streaming 8KB data for encryption...")
    ciphertext = bytearray()
    for i in range(0, len(plaintext), 64):
        chunk = plaintext[i:i+64]
        dev.send_packet(CMD_DATA, chunk)
        cmd, size, payload = dev.receive_packet()
        if cmd != RESP_ACK_DATA:
            print(f"Error during encryption at offset {i}")
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

    print("Streaming 8KB data for decryption...")
    decrypted_data = bytearray()
    for i in range(0, len(ciphertext_to_decrypt), 64):
        chunk = ciphertext_to_decrypt[i:i+64]
        dev.send_packet(CMD_DATA, chunk)
        cmd, size, payload = dev.receive_packet()
        if cmd != RESP_ACK_DATA:
            print(f"Error during decryption at offset {i}")
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
        print("SUCCESS: The 8KB decrypted file matches the original plaintext file.")
    else:
        print("FAILURE: The 8KB decrypted file does NOT match the original plaintext file.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="8KB Random File Demonstration")
    parser.add_argument("port", help="Serial port (e.g., /dev/ttyACM0)")
    args = parser.parse_args()
    
    run_demo(args.port)
