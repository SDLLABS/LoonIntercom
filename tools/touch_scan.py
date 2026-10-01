"""Identify the touch chip on the LilyGO T5-4.7-S3 over the MicroPython REPL.

Usage: .venv/Scripts/python.exe tools/touch_scan.py [COMx]
Needs MicroPython on the board. Pins from LilyGO's utilities.h: SDA 18, SCL 17, touch INT 47.
"""
import sys, time
import serial
from serial.tools import list_ports

CODE = r'''
from machine import I2C, Pin
import time
i2c = I2C(0, scl=Pin(17), sda=Pin(18), freq=100000)
found = i2c.scan()
print('SCAN', [hex(a) for a in found])
print('INT47', Pin(47, Pin.IN, Pin.PULL_UP).value())
for a in (0x5D, 0x14):
    if a in found:
        i2c.writeto(a, bytes([0x81, 0x40]))
        pid = i2c.readfrom(a, 4)
        i2c.writeto(a, bytes([0x81, 0x44]))
        v = i2c.readfrom(a, 6)
        i2c.writeto(a, bytes([0x80, 0x47]))
        cfg = i2c.readfrom(a, 1)
        print('GT911@%s id=%r fw=%04x x=%d y=%d cfgver=%d' % (hex(a), pid, v[0] | v[1] << 8, v[2] | v[3] << 8, v[4] | v[5] << 8, cfg[0]))
if 0x51 in found:
    i2c.writeto(0x51, bytes([0x02]))
    r = i2c.readfrom(0x51, 7)
    print('RTC51 raw', r.hex())
print('DONE')
'''


def pick_port():
    if len(sys.argv) > 1:
        return sys.argv[1]
    for p in list_ports.comports():
        if p.vid == 0x303A:
            print('port', p.device, hex(p.vid), hex(p.pid), p.description)
            return p.device
    sys.exit('no Espressif USB port found: ' + ', '.join(p.device for p in list_ports.comports()))


s = serial.Serial(pick_port(), 115200, timeout=0.3)
s.write(b'\r\x03\x03')
time.sleep(0.5)
s.read(4096)
s.write(b'\x05')  # paste mode: the block runs as one piece
time.sleep(0.2)
s.write(CODE.encode())
s.write(b'\x04')
out, t0 = b'', time.time()
while b'DONE' not in out and time.time() - t0 < 10:
    out += s.read(4096)
text = out.decode(errors='replace')
lines = [l for l in text.splitlines() if l.startswith(('SCAN', 'INT47', 'GT911', 'RTC51', 'Traceback', '  File', 'OSError', 'DONE')) or 'Error' in l]
print('\n'.join(lines) or text)
