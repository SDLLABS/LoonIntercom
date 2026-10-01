"""Probe what holds GPIO0 low on the WT32-ETH01, from the ROM loader (chip must wait in download mode).

GPIO0 doubles as the 50 MHz RMII clock input; the oscillator is enabled by GPIO16.
Samples GPIO0 with the pull-up on, oscillator off, then on, then off again.
Addresses: ESP32 TRM (GPIO 0x3FF44000, IO_MUX 0x3FF49000).
"""
from esptool.cmds import detect_chip

PORT = 'COM10'   # your USB-serial adapter

GPIO = 0x3FF44000
OUT_W1TS, OUT_W1TC, EN_W1TS, EN_W1TC = GPIO + 0x08, GPIO + 0x0C, GPIO + 0x24, GPIO + 0x28
STRAP, IN = GPIO + 0x38, GPIO + 0x3C
OUT_SEL16 = GPIO + 0x530 + 16 * 4
MUX_GPIO0, MUX_GPIO16 = 0x3FF49044, 0x3FF4904C
FUN_IE, FUN_WPU, FUN_WPD = 1 << 9, 1 << 8, 1 << 7

esp = detect_chip(PORT, 115200, 'no-reset', False, 2)

def sample(label, n=40):
    bits = [(esp.read_reg(IN) >> 0) & 1 for _ in range(n)]
    print(f'{label:<34} GPIO0 high in {sum(bits):2d}/{n} samples', flush=True)

print(f'strap register: 0x{esp.read_reg(STRAP):02x}')
m0 = esp.read_reg(MUX_GPIO0)
print(f'IO_MUX GPIO0 before: 0x{m0:04x} (IE={m0 >> 9 & 1} WPU={m0 >> 8 & 1} WPD={m0 >> 7 & 1})')
esp.write_reg(MUX_GPIO0, (m0 | FUN_IE | FUN_WPU) & ~FUN_WPD)
sample('pull-up on, oscillator untouched')

m16 = esp.read_reg(MUX_GPIO16)
esp.write_reg(MUX_GPIO16, (m16 & ~(7 << 12)) | (2 << 12) | FUN_IE)   # GPIO function
esp.write_reg(OUT_SEL16, 0x100)                                   # plain GPIO output
esp.write_reg(OUT_W1TC, 1 << 16)
esp.write_reg(EN_W1TS, 1 << 16)
sample('oscillator OFF (GPIO16 low)')
esp.write_reg(OUT_W1TS, 1 << 16)
sample('oscillator ON  (GPIO16 high)')
esp.write_reg(OUT_W1TC, 1 << 16)
sample('oscillator OFF again')
esp.write_reg(EN_W1TC, 1 << 16)                                   # release GPIO16
esp.write_reg(MUX_GPIO16, m16)
sample('GPIO16 released (floating)')
esp.write_reg(MUX_GPIO0, m0)
print('restored')
