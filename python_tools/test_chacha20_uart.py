import serial
import struct
import time
import os
import secrets
import argparse
import sys

# Protocol Constants
CMD_INIT = 0x01
CMD_DATA = 0x02
CMD_END  = 0x03

RESP_ACK_INIT = 0x81
RESP_ACK_DATA = 0x82
RESP_ACK_END  = 0x83
RESP_ERROR    = 0xFF

class ChaCha20UART:
    def __init__(self, port, baudrate=38400, timeout=2, logger=None):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.logger = logger
        time.sleep(2) # Wait for STM32 reset if necessary

    def log(self, msg):
        if self.logger:
            self.logger.write(msg + "\n")
            self.logger.flush()

    def calculate_checksum(self, cmd, size, payload):
        cs = cmd ^ size
        for b in payload:
            cs ^= b
        return cs

    def send_packet(self, cmd, payload=b""):
        size = len(payload)
        cs = self.calculate_checksum(cmd, size, payload)
        packet = struct.pack("BB", cmd, size) + payload + struct.pack("B", cs)
        self.log(f"TX -> CMD: {cmd:02X}, SIZE: {size}, PAYLOAD: {payload.hex().upper()}, CS: {cs:02X}")
        self.ser.write(packet)

    def receive_packet(self):
        header = self.ser.read(2)
        if not header or len(header) < 2:
            self.log("RX <- Timeout or incomplete header")
            return None, None, None
        
        cmd, size = struct.unpack("BB", header)
        payload = self.ser.read(size)
        if len(payload) < size:
            self.log("RX <- Timeout or incomplete payload")
            return None, None, None
            
        received_cs = self.ser.read(1)
        if not received_cs:
            self.log("RX <- Timeout on checksum")
            return None, None, None
            
        calculated_cs = self.calculate_checksum(cmd, size, payload)
        self.log(f"RX <- CMD: {cmd:02X}, SIZE: {size}, PAYLOAD: {payload.hex().upper()}, CS: {received_cs[0]:02X}")
        
        if calculated_cs != received_cs[0]:
            print(f"Checksum Error: Calc {calculated_cs} != Recv {received_cs[0]}")
            self.log(f"Checksum Error: Calc {calculated_cs} != Recv {received_cs[0]}")
            return None, None, None
            
        return cmd, size, payload

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

def run_test(port, log_file=None):
    logger = None
    if log_file:
        if log_file == "-":
            logger = sys.stdout
        else:
            logger = open(log_file, "a")
            logger.write(f"\n--- New Test Session: {time.ctime()} ---\n")

    print(f"Connecting to {port}...")
    try:
        dev = ChaCha20UART(port, logger=logger)
    except Exception as e:
        print(f"Error opening port: {e}")
        if logger and logger != sys.stdout:
            logger.close()
        return

    # 1. Setup Test Data
    key = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    counter = 0
    data_size = 8192 # 8KB
    test_data = secrets.token_bytes(data_size)
    
    print(f"Key: {key.hex()}")
    print(f"Nonce: {nonce.hex()}")
    
    # 2. INIT
    print("Sending CMD_INIT...")
    init_payload = key + nonce + struct.pack("<I", counter)
    dev.send_packet(CMD_INIT, init_payload)
    cmd, size, payload = dev.receive_packet()
    if cmd != RESP_ACK_INIT:
        print(f"Failed to INIT: Got {cmd}")
        return
    print("INIT OK")

    # 3. DATA streaming
    processed_data = bytearray()
    print(f"Streaming {data_size} bytes in 64-byte chunks...")
    for i in range(0, data_size, 64):
        chunk = test_data[i:i+64]
        dev.send_packet(CMD_DATA, chunk)
        cmd, size, payload = dev.receive_packet()
        if cmd != RESP_ACK_DATA:
            print(f"Error at chunk {i//64}: Got {cmd}")
            break
        processed_data.extend(payload)
        if (i // 64) % 16 == 0 and not log_file:
            print(f"Progress: {i}/{data_size} bytes", end="\r")
    
    if not log_file:
        print(f"\nStreaming complete. Received {len(processed_data)} bytes.")
    else:
        print(f"Streaming complete. Received {len(processed_data)} bytes.")

    # 4. END
    print("Sending CMD_END...")
    dev.send_packet(CMD_END)
    dev.receive_packet()
    print("END OK")

    # 5. Validation
    print("Validating results...")
    expected_data = chacha20_encrypt(test_data, key, nonce, counter)
    
    if expected_data == processed_data:
        print("SUCCESS! Embedded output matches local calculation.")
    else:
        print("FAILURE! Outputs do not match.")
        for i in range(len(expected_data)):
            if expected_data[i] != processed_data[i]:
                print(f"First mismatch at byte {i}: Expected {expected_data[i]:02x}, Got {processed_data[i]:02x}")
                break

    if logger and logger != sys.stdout:
        logger.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChaCha20 UART Test Tool")
    parser.add_argument("port", help="Serial port (e.g., /dev/ttyACM0)")
    parser.add_argument("--log", "-l", help="Log file path. Use \"-\" to log to stdout.", default=None)
    args = parser.parse_args()
    
    run_test(args.port, args.log)
