################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for IO with the microcontroller consuming the G-Code data.
'''
################################################################################################

import serial

################################################################################################

class ogcSerialDriver:

    def __init__(self, port_name):
        # Open and configure the serial port.
        self.serial = serial.Serial()
        self.serial.port = port_name
        self.confifure()
        self.serial.open()
        self.serial.flushInput()
        self.serial.flushOutput()
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

    def write(self, data):
        self.serial.write(data)

    def read_line(self):
        return self.serial.readline()

    def close(self):
        self.serial.close()
        return

################################################################################################
