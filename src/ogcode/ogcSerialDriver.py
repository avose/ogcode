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

################################################################################################

class ogcSerialWriter(Thread):
    def __init__(self, parent):
        Thread.__init__(self)
        self.parent = parent
        self.index  = 0
        self.done   = False
        return

    def run(self):
        # Loop until done.
        while not self.done:
            wait = False
            with self.parent.lock:
                if self.parent.data is None:
                    # No data, so wait patiently.
                    wait = True
                else:
                    if self.index >= len(self.parent.data):
                        # Finished writing all data.
                        self.done = True
                    else:
                        if self.parent.outstanding < self.parent.max_outstanding:
                            # Not too many outstanding writes, so write another line.
                            line = self.parent.data[self.index:].split('\n', 1)[0]
                            self.parent.serial.write(line)
                            self.index += len(line)
                            self.parent.outstanding += 1
            if wait:
                # Wait patiently.
                sleep(1/10.0)
            else:
                # Wait impatiently.
                sleep(1/10000.0)

        # Done, so clear parent's data member.
        with self.parent.lock:
            self.parent.data = None
        return

    def stop(self):
        self.done = True
        return

################################################################################################

class ogcSerialReader(Thread):
    def __init__(self, parent):
        Thread.__init__(self)
        self.parent = parent
        self.done   = False
        return

    def run(self):
        while not self.done:
            wait = False
            with self.parent.lock:
                if self.parent.data is None:
                    # No data, so wait patiently.
                    wait = True
                else:
                    if self.parent.outstanding:
                        # There are outstanding writes, so read a response line.
                        response = self.serial.readline()
                        print(response)
                        self.parent.outstanding -= 1
            if wait:
                # Wait patiently.
                sleep(1/10.0)
            else:
                # Wait impatiently.
                sleep(1/10000.0)
        return

    def stop(self):
        self.done = True
        return

################################################################################################

class ogcSerialDriver:

    @staticmethod
    def get_ports():
        # ports = [ (port, desc, hwid) ]
        ports_details = serial.tools.list_ports.comports()
        return ports_details

    def __init__(self, port_name: str, max_outstanding : int = 16):
        # Open and configure the serial port.
        self.serial = serial.Serial()
        self.serial.port = port_name
        self.configure()
        try:
            self.serial.open()
            self.serial.flushInput()
            self.serial.flushOutput()
            self.error = ""
        except serial.SerialException as e:
            self.error = str(e)
        # Initialize maximum oustanding writes and current outstanding writes.
        self.max_outstanding = max_outstanding
        self.outstanding = 0
        self.data = None
        # Create writer and reader threads.
        self.lock = Lock()
        self.writer = ogcSerialWriter(self)
        self.reader = ogcSerialReader(self)
        return

    def configure(self):
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

    def write(self, data : str):
        with self.lock:
            self.data = data
            self.outstanding = 0
            self.writer.run()
            self.reader.run()

    def read_line(self):
        return self.serial.readline()

    def close(self):
        if self.writer:
            self.writer.stop()
            self.writer = None
        if self.reader:
            self.reader.stop()
            self.reader = None
        self.serial.close()
        return

################################################################################################
