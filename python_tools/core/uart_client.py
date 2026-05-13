import serial
import struct
import time

# Protocol Constants
CMD_INIT = 0x01
CMD_DATA = 0x02
CMD_END  = 0x03

RESP_ACK_INIT = 0x81
RESP_ACK_DATA = 0x82
RESP_ACK_END  = 0x83
RESP_ERROR    = 0xFF

class ChaCha20UART:
    def __init__(self, port, logger, baudrate=38400, timeout=2):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.logger = logger
        time.sleep(2) # Wait for STM32 reset if necessary

    def format_packet_log(self, direction, cmd, size, payload, checksum):
        return (f"{direction}\n"
                f"  CMD:     0x{cmd:02X}\n"
                f"  SIZE:    {size}\n"
                f"  CSUM:    0x{checksum:02X}\n"
                f"  PAYLOAD: {payload.hex().upper()}\n")

    def calculate_checksum(self, cmd, size, payload):
        cs = cmd ^ size
        for b in payload:
            cs ^= b
        return cs

    def send_packet(self, cmd, payload=b""):
        size = len(payload)
        cs = self.calculate_checksum(cmd, size, payload)
        packet = struct.pack("BB", cmd, size) + payload + struct.pack("B", cs)
        self.logger.log(self.format_packet_log("TX ->", cmd, size, payload, cs))
        self.ser.write(packet)

    def receive_packet(self):
        header = self.ser.read(2)
        if not header or len(header) < 2:
            self.logger.log("RX <- Timeout or incomplete header\n")
            return None, None, None
        
        cmd, size = struct.unpack("BB", header)
        payload = self.ser.read(size)
        if len(payload) < size:
            self.logger.log("RX <- Timeout or incomplete payload\n")
            return None, None, None
            
        received_cs = self.ser.read(1)
        if not received_cs:
            self.logger.log("RX <- Timeout on checksum\n")
            return None, None, None
            
        calculated_cs = self.calculate_checksum(cmd, size, payload)
        self.logger.log(self.format_packet_log("RX <-", cmd, size, payload, received_cs[0]))
        
        if calculated_cs != received_cs[0]:
            self.logger.log(f"Checksum Error: Calc {calculated_cs} != Recv {received_cs[0]}\n")
            return None, None, None
            
        return cmd, size, payload
