import sys
import os
import argparse
import secrets
import struct

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import SessionLogger
from core.uart_client import ChaCha20UART, CMD_INIT, CMD_DATA, CMD_END, RESP_ACK_INIT, RESP_ACK_DATA
from core.chacha_ref import chacha20_encrypt

def run_test(port, console_log, logger=None):
    if not logger:
        logger = SessionLogger("RandomStreamTest", print_to_console=console_log)
    logger.log(f"Connecting to {port}...")
    
    try:
        dev = ChaCha20UART(port, logger)
    except Exception as e:
        logger.log(f"Error opening port: {e}")
        return

    # 1. Setup Test Data
    key = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    counter = 0
    data_size = 8192 # 8KB
    test_data = secrets.token_bytes(data_size)
    
    logger.log(f"Key: {key.hex().upper()}")
    logger.log(f"Nonce: {nonce.hex().upper()}")
    
    # 2. INIT
    logger.log("Sending CMD_INIT...")
    init_payload = key + nonce + struct.pack("<I", counter)
    dev.send_packet(CMD_INIT, init_payload)
    cmd, size, payload = dev.receive_packet()
    if cmd != RESP_ACK_INIT:
        logger.log(f"Failed to INIT: Got {cmd}")
        return
    logger.log("INIT OK")

    # 3. DATA streaming
    processed_data = bytearray()
    logger.log(f"Streaming {data_size} bytes in 64-byte chunks...")
    for i in range(0, data_size, 64):
        chunk = test_data[i:i+64]
        dev.send_packet(CMD_DATA, chunk)
        cmd, size, payload = dev.receive_packet()
        if cmd != RESP_ACK_DATA:
            logger.log(f"Error at chunk {i//64}: Got {cmd}")
            break
        processed_data.extend(payload)
        
    logger.log(f"Streaming complete. Received {len(processed_data)} bytes.")

    # 4. END
    logger.log("Sending CMD_END...")
    dev.send_packet(CMD_END)
    dev.receive_packet()
    logger.log("END OK")

    # 5. Validation
    logger.log("Validating results...")
    expected_data = chacha20_encrypt(test_data, key, nonce, counter)
    
    if expected_data == processed_data:
        logger.log("SUCCESS! Embedded output matches local calculation.")
    else:
        logger.log("FAILURE! Outputs do not match.")
        
    logger.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Random Stream Test")
    parser.add_argument("port", help="Serial port (e.g., /dev/ttyACM0)")
    parser.add_argument("--console", "-c", action="store_true", help="Print logs to console")
    args = parser.parse_args()
    
    run_test(args.port, args.console)
