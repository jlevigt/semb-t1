import os
import sys
import datetime

class SessionLogger:
    def __init__(self, test_name, print_to_console=True):
        self.print_to_console = print_to_console
        
        # Determine log directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_dir = os.path.join(base_dir, "executions", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = os.path.join(self.log_dir, f"{test_name}_{timestamp}.log")
        self.file = open(self.log_file_path, "a")
        self.file.write(f"--- Test Session: {test_name} at {timestamp} ---\n\n")
        
    def log(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_msg = f"[{timestamp}] {msg}"
        self.file.write(formatted_msg + "\n")
        self.file.flush()
        if self.print_to_console:
            print(formatted_msg)

    def close(self):
        self.file.close()
