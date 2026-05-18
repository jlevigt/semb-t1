import sys
import os
import argparse
import secrets
import struct

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import SessionLogger
from core.uart_client import ChaCha20UART, CMD_INIT, CMD_DATA, CMD_END, RESP_ACK_INIT, RESP_ACK_DATA

def stream_data(dev, logger, data_in, expected_size):
    processed_data = bytearray()
    for i in range(0, len(data_in), 64):
        chunk = data_in[i:i+64]
        dev.send_packet(CMD_DATA, chunk)
        cmd, size, payload = dev.receive_packet()
        if cmd != RESP_ACK_DATA:
            logger.log(f"Error at chunk {i//64}: Got {cmd}")
            break
        processed_data.extend(payload)
    return processed_data

def run_test(port, console_log, logger=None):
    if not logger:
        logger = SessionLogger("RoundtripTest", print_to_console=console_log)
    logger.log(f"Connecting to {port}...")
    
    try:
        dev = ChaCha20UART(port, logger)
    except Exception as e:
        logger.log(f"Error opening port: {e}")
        return

    # 1. Setup Test Data (8KB of 'A's)
    key = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    counter = 0
    data_size = 8192 # 8KB
    plaintext = b"A" * data_size
    
    logger.log(f"Key: {key.hex().upper()}")
    logger.log(f"Nonce: {nonce.hex().upper()}")
    
    # 2. INIT (First Pass - Encrypt)
    logger.log("\n--- FIRST PASS: ENCRYPTION ---")
    logger.log("Sending CMD_INIT...")
    init_payload = key + nonce + struct.pack("<I", counter)
    dev.send_packet(CMD_INIT, init_payload)
    cmd, size, payload = dev.receive_packet()
    if cmd != RESP_ACK_INIT:
        logger.log(f"Failed to INIT: Got {cmd}")
        return
        
    logger.log(f"Streaming {data_size} bytes in 64-byte chunks...")
    ciphertext = stream_data(dev, logger, plaintext, data_size)
    
    logger.log("Sending CMD_END...")
    dev.send_packet(CMD_END)
    dev.receive_packet()
    
    # Save ciphertext to file (as requested)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exec_dir = os.path.join(base_dir, "executions")
    os.makedirs(exec_dir, exist_ok=True)
    cipher_file_path = os.path.join(exec_dir, "roundtrip_ciphertext.bin")
    with open(cipher_file_path, "wb") as f:
        f.write(ciphertext)
    logger.log(f"Ciphertext saved to {cipher_file_path}")

    # 3. INIT (Second Pass - Decrypt)
    logger.log("\n--- SECOND PASS: DECRYPTION ---")
    logger.log("Sending CMD_INIT...")
    # Counter must be reset to the same initial value to decrypt!
    dev.send_packet(CMD_INIT, init_payload)
    cmd, size, payload = dev.receive_packet()
    if cmd != RESP_ACK_INIT:
        logger.log(f"Failed to INIT: Got {cmd}")
        return
        
    logger.log(f"Streaming {len(ciphertext)} bytes of ciphertext in 64-byte chunks...")
    recovered_plaintext = stream_data(dev, logger, ciphertext, len(ciphertext))
    
    logger.log("Sending CMD_END...")
    dev.send_packet(CMD_END)
    dev.receive_packet()

    # Save recovered plaintext to file
    recovered_file_path = os.path.join(exec_dir, "roundtrip_recovered.txt")
    with open(recovered_file_path, "wb") as f:
        f.write(recovered_plaintext)
    logger.log(f"Recovered plaintext saved to {recovered_file_path}")

    # 4. Validation
    logger.log("\n--- VALIDATION ---")
    if recovered_plaintext == plaintext:
        logger.log("SUCCESS! The recovered plaintext exactly matches the original 8KB 'A's.")
    else:
        logger.log("FAILURE! Outputs do not match.")
        
    logger.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Roundtrip Encryption/Decryption Test")
    parser.add_argument("port", help="Serial port (e.g., /dev/ttyACM0)")
    parser.add_argument("--console", "-c", action="store_true", help="Print logs to console")
    args = parser.parse_args()
    
    run_test(args.port, args.console)
