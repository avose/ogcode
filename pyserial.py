#!/usr/bin/env python3

import serial
import sys
from time import sleep

class VISA:
    def __init__(self, tty_name):
        self.ser = serial.Serial()
        self.ser.port = tty_name
        # If it breaks try the below
        #self.serConf() # Uncomment lines here till it works
        self.ser.open()
        self.ser.flushInput()
        self.ser.flushOutput()
        return

    def cmd(self, cmd_str):
        self.ser.write(cmd_str)
        sleep(0.0001)
        return self.ser.readline()

    def serConf(self):
        self.ser.baudrate = 9600
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.timeout = 0 # Non-Block reading
        self.ser.xonxoff = False # Disable Software Flow Control
        self.ser.rtscts = False # Disable (RTS/CTS) flow Control
        self.ser.dsrdtr = False # Disable (DSR/DTR) flow Control
        self.ser.writeTimeout = 2
        return

    def close(self):
        self.ser.close()
        return

def main():
    tty = VISA('/dev/ttyACM0')
    with open(sys.argv[1], "rb") as inpf:
        print("Writing...")
        for line in inpf:
            print("=> ", str(line))
            resp = tty.cmd(line)
            print("<= ", str(resp))
    tty.close()
    print("Done.")
    return

if __name__ == "__main__":
    main()
