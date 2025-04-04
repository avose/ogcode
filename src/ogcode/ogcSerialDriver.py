################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for IO with the microcontroller consuming the G-Code data.
'''
################################################################################################

import serial
import serial.tools.list_ports

from time import sleep
from threading import Thread, Lock
from datetime import datetime

################################################################################################

class ogcSerialWriter(Thread):
    '''
    Thread which writes data to the serial port one line at a time until all data is sent.
    Writer will not have more outstanding line writes than parent ogcSerialDriver's set maximum.
    Writer increments parent's outsanding counter, and reader decrements, to track this.
    '''
    def __init__(self, parent, serial, iota: float = 0.000001):
        Thread.__init__(self)
        self.parent = parent
        self.lock   = self.parent.lock
        self.serial = serial
        self.index  = 0
        self.done   = False
        self.iota   = iota
        return

    def run(self):
        # Wait patiently for reader thread to be ready.
        ready = False
        while not self.done and not ready:
            with self.lock:
                ready = self.parent.reader.ready
            sleep(1/100.0)

        # Loop until done.
        while not self.done:
            with self.lock:
                # Wait patiently if no data available to write.
                if self.parent.data is None:
                    sleep(1/100.0)
                    continue
                # Check if finished writing data.
                if self.index >= len(self.parent.data):
                    self.done = True
                    continue
                # Write a line if there are not too many outstanding writes.
                if self.parent.outstanding < self.parent.max_outstanding:
                    line = self.parent.data[self.index:].split("\n", 1)[0] + "\n"
                    if line:
                        line = line.encode(encoding="utf-8")
                        self.serial.write(line)
                        self.index += len(line)
                        self.parent.outstanding += 1
                        if self.parent.debug:
                            print(f"Serial Write [{self.parent.outstanding}][{self.index}]: {line}")
                        continue
            # Yield the CPU to other threads if no write attempted due to max outstanding.
            sleep(self.iota)

        # Writer thread is done.
        if self.parent.debug:
            print("!! serial writer done")
        with self.lock:
            self.parent.message("Writing completed.")
        return

    def stop(self):
        # Set done flag so writer thread will exit.
        if self.parent.debug:
            print("!! serial writer stop")
        self.done = True
        return

################################################################################################

class ogcSerialReader(Thread):
    '''
    Thread which reads responses from the serial port until all responses are read.
    Writer will not have more outstanding line writes than parent ogcSerialDriver's set maximum.
    Writer increments parent's outsanding counter, and reader decrements, to track this.
    '''
    def __init__(self, parent, serial, iota: float = 0.000001):
        Thread.__init__(self)
        self.parent = parent
        self.lock   = self.parent.lock
        self.serial = serial
        self.done   = False
        self.ready  = False
        self.iota   = iota
        return

    def run(self):
        # Flush any existing data from serial port and set ready flag.
        with self.lock:
            if not self.done:
                self.serial.reset_input_buffer()
            self.ready = True

        # Loop until done.
        while not self.done:
            # Read if there is an outstanding write, else wait patiently.
            response = None
            with self.lock:
                if self.parent.data is not None:
                    if self.parent.outstanding:
                        # There are outstanding write(s), so read a response line.
                        response = self.serial.readline()
                    elif self.parent.writer and self.parent.writer.done:
                        # There are no outstanding write(s) and writer is done.
                        self.done = True
                        continue
            response = response.strip() if response is not None else response
            # Yield the CPU to other threads if no data read.
            if not response:
                sleep(self.iota)
                continue
            # Decrement outstanding count if "ok" message received.
            if response == b'ok':
                with self.lock:
                    self.parent.outstanding -= 1
                    if self.parent.debug:
                        print(f"Serial Read  [{self.parent.outstanding}]")
                continue
            # Skip some debug response message lines.
            if response.startswith(b'Processing Mcode'):
                continue
            if response.startswith(b'code'):
                continue
            if len(response) == 5:
                try:
                    temperature = float(response)
                    continue
                except ValueError:
                    pass
            # Any other response is an error.
            with self.lock:
                error = f"Laser error: {response}"
                self.parent.error(error)
                if self.parent.debug:
                    print(error)
            # Yield the CPU to other threads.
            sleep(self.iota)

        # Reader thread is done.
        if self.parent.debug:
            print("!! serial reader done")
        with self.lock:
            self.parent.message("Reading completed.")
            elapsed = datetime.now() - self.parent.write_start_time
            self.parent.message(f"Engrave time: {elapsed}")
        return

    def stop(self):
        # Set done flag so reader thread will exit.
        if self.parent.debug:
            print("!! serial reader stop")
        self.done = True
        return

################################################################################################

class ogcSerialDriver:
    '''
    Class to manage serial port and perform reading and writing with threads.
    Writer will not have more outstanding line writes than ogcSerialDriver's set maximum.
    Writer increments parent's outsanding counter, and reader decrements, to track this.
    '''
    @staticmethod
    def get_ports():
        # ports = [ (port, desc, hwid) ]
        ports_details = serial.tools.list_ports.comports()
        return ports_details

    def __init__(self, port_name: str, max_outstanding: int = 128):
        # Open and configure the serial port.
        self.debug = False
        self.serial = serial.Serial()
        self.serial.port = port_name
        self.configure()
        self.errors = []
        self.messages = []
        try:
            self.serial.open()
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
        except serial.SerialException as e:
            self.error(str(e))
        # Initialize maximum oustanding writes and current outstanding writes.
        self.max_outstanding = max_outstanding
        self.outstanding = 0
        self.data = None
        # Clear writer and reader threads.
        self.lock = Lock()
        self.writer = None
        self.reader = None
        # Record message for initialization completed.
        self.message(f"Serial port '{port_name}' initialized.")
        return

    def configure(self):
        # Configure serial port settings.
        self.serial.bytesize = serial.EIGHTBITS
        self.serial.baudrate = 9600
        self.serial.parity = serial.PARITY_NONE
        self.serial.stopbits = serial.STOPBITS_ONE
        self.serial.timeout = 0     # For non-blocking reading.
        self.serial.xonxoff = False # Disable software flow control.
        self.serial.rtscts = False  # Disable (RTS/CTS) flow control.
        self.serial.dsrdtr = False  # Disable (DSR/DTR) flow control.
        self.serial.writeTimeout = 0
        return

    def write(self, data: str):
        # Do nothing if there is an error.
        if self.errors:
            return
        # Create message for this write and record start time.
        self.write_start_time = datetime.now()
        lines = data.count("\n") + 1
        with self.lock:
            self.message(f"Writing {len(data)} bytes with {lines} lines to laser.")
        # Set error if already running.
        with self.lock:
            if (self.writer and not self.writer.done or
                self.reader and not self.reader.done):
                self.error("I/O already in progress.")
                return
        # Set data field and start reader and writer threads.
        with self.lock:
            self.data = data
            self.outstanding = 0
            self.writer = ogcSerialWriter(self, self.serial)
            self.reader = ogcSerialReader(self, self.serial)
            self.writer.start()
            self.reader.start()
        return

    def message(self, msg: str):
        # Generate a timestamp string from current date and time.
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.messages.append(f"[{timestamp}] - {msg}")
        return

    def clear_messages(self):
        # Clear accumulated messages.
        self.messages = []
        return

    def error(self, err: str):
        # Generate a timestamp string from current date and time.
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{timestamp}] - {err}"
        self.errors.append(msg)
        self.messages.append(msg)
        return

    def clear_errors(self):
        # Clear error state.
        self.errors = []
        return

    @property
    def finished(self):
        # Finished if no data.
        if self.data is None:
            return True
        # Finished if no reader and writer threads.
        if not self.reader and not self.writer:
            return True
        # Finished if reader and writer threads are done.
        with self.lock:
            finished = self.reader.done and self.writer.done
        return finished

    @property
    def progress(self):
        # Return IO progress as a percentage.
        if not self.writer or not self.data:
            return 0
        with self.lock:
            return 100 * self.writer.index / len(self.data)

    def stop(self):
        # Stop reader and writer threads, reset data.
        if self.writer:
            self.writer.stop()
            self.writer.join()
            self.writer = None
        if self.reader:
            self.reader.stop()
            self.reader.join()
            self.reader = None
        self.data = None
        # Write G-Code to turn off laser and end current program.
        if self.debug:
            print("!! serial stop laser and flush")
        if self.serial.is_open:
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            self.serial.write("\nM5\nM2".encode(encoding="utf-8"))
            self.serial.flush()
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
        self.message("Serial port stopped.")
        return

    def close(self):
        # Stop IO and close serial port.
        self.stop()
        if self.serial.is_open:
            self.serial.close()
        self.message("Serial port closed.")
        return

################################################################################################
