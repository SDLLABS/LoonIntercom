"""Full-chip reset of a classic ESP32 via its RTC watchdog, from the ROM loader,
then read the boot log on the same (still open) port.

The ROM prints 'rst:0x10 (RTCWDT_RTC_RESET),boot:0xNN (...)' first: boot:0xNN is the
latched strapping value, which shows why the chip picks download mode.
Register layout: ESP32 TRM, RTC_CNTL (base 0x3FF48000).
"""
import sys, time
from esptool.cmds import detect_chip

PORT = 'COM10'   # your USB-serial adapter

RUN_S = float(sys.argv[1]) if len(sys.argv) > 1 else 40
WDTCONFIG0, WDTCONFIG1, WDTWPROTECT = 0x3FF4808C, 0x3FF48090, 0x3FF480A4
WKEY = 0x50D83AA1

esp = detect_chip(PORT, 115200, 'no-reset', False, 2)
print('connected to ROM loader, arming RTC watchdog (stage 0 = full RTC reset)', flush=True)
try:
    esp.write_reg(WDTWPROTECT, WKEY)          # unlock
    esp.write_reg(WDTCONFIG1, 3000)           # ~20 ms at the 150 kHz slow clock
    esp.write_reg(WDTCONFIG0, (1 << 31) | (4 << 28) | (7 << 11) | (7 << 14))
    esp.write_reg(WDTWPROTECT, 0)             # lock
except Exception as e:  # the chip may reset before the last reply
    print(f'(during arm: {type(e).__name__}: {e})', flush=True)
port = esp._port
port.timeout = 0.3
t0 = time.time()
while time.time() - t0 < RUN_S:
    line = port.readline()
    if line:
        text = line.decode('utf-8', 'replace').rstrip()
        sys.stdout.buffer.write(f'[{time.time() - t0:6.1f}] {text}\n'.encode('utf-8', 'backslashreplace'))
        sys.stdout.flush()
print('done', flush=True)
