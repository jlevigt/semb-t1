import sys
import os
import argparse
import secrets
import struct

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import SessionLogger
from core.uart_client import ChaCha20UART, CMD_INIT, CMD_DATA, CMD_END, RESP_ACK_INIT, RESP_ACK_DATA

def stream_data(dev, logger, data_in):
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

def run_test(port, console_log):
    logger = SessionLogger("NegativeTest", print_to_console=console_log)
    logger.log(f"Connecting to {port}...")
    
    try:
        dev = ChaCha20UART(port, logger)
    except Exception as e:
        logger.log(f"Error opening port: {e}")
        return

    # 1. Setup Original Test Data (4KB)
    key_orig = secrets.token_bytes(32)
    nonce_orig = secrets.token_bytes(12)
    counter_orig = 0
    data_size = 4096 
    plaintext = b"B" * data_size
    
    logger.log(f"Original Key: {key_orig.hex().upper()}")
    logger.log(f"Original Nonce: {nonce_orig.hex().upper()}")
    
    # 2. Encrypt to get valid Ciphertext
    logger.log("\n--- STEP 1: ENCRYPTION ---")
    dev.send_packet(CMD_INIT, key_orig + nonce_orig + struct.pack("<I", counter_orig))
    cmd, size, payload = dev.receive_packet()
    if cmd != RESP_ACK_INIT: return
    
    ciphertext = stream_data(dev, logger, plaintext)
    dev.send_packet(CMD_END)
    dev.receive_packet()
    
    logger.log("Encryption complete.")

    def attempt_decrypt(test_name, key, nonce, counter):
        logger.log(f"\n--- STEP 2: {test_name} ---")
        dev.send_packet(CMD_INIT, key + nonce + struct.pack("<I", counter))
        cmd, size, payload = dev.receive_packet()
        if cmd != RESP_ACK_INIT: return False
        
        recovered = stream_data(dev, logger, ciphertext)
        dev.send_packet(CMD_END)
        dev.receive_packet()
        
        if recovered == plaintext:
            logger.log("FAIL: The plaintext was recovered when it shouldn't have been!")
            return False
        else:
            logger.log("PASS: The recovered data does NOT match the plaintext. Expected behavior.")
            return True

    # 3. Test Wrong Key
    wrong_key = secrets.token_bytes(32)
    res_key = attempt_decrypt("DECRYPT WITH WRONG KEY", wrong_key, nonce_orig, counter_orig)

    # 4. Test Wrong Nonce
    wrong_nonce = secrets.token_bytes(12)
    res_nonce = attempt_decrypt("DECRYPT WITH WRONG NONCE", key_orig, wrong_nonce, counter_orig)

    # 5. Test Wrong Counter
    wrong_counter = 5
    res_counter = attempt_decrypt("DECRYPT WITH WRONG COUNTER", key_orig, nonce_orig, wrong_counter)

    logger.log("\n--- SUMMARY ---")
    if res_key and res_nonce and res_counter:
        logger.log("ALL NEGATIVE TESTS PASSED! Decryption safely fails with incorrect parameters.")
    else:
        logger.log("SOME NEGATIVE TESTS FAILED. Cryptographic integrity compromised.")

    logger.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Negative Decryption Tests")
    parser.add_argument("port", help="Serial port (e.g., /dev/ttyACM0)")
    parser.add_argument("--console", "-c", action="store_true", help="Print logs to console")
    args = parser.parse_args()
    
    run_test(args.port, args.console)
