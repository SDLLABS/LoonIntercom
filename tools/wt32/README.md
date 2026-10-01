# WT32-ETH01 boot-fault probes

Two small scripts from diagnosing a WT32-ETH01 that always started in download mode. Both need the
chip to be waiting in its ROM loader (download mode) and talk to it with
[esptool](https://github.com/espressif/esptool) (`pip install esptool`). Set the serial port at the
top of each script.

- [`wdt_reset_listen.py`](wdt_reset_listen.py): resets the whole chip through its RTC watchdog, straight
  from the ROM loader, and reads the first boot line on the same open port. Useful with USB-serial
  adapters that have no DTR/RTS lines: replugging always misses the first seconds of the boot log.
  The ROM prints `boot:0xNN`; on the ESP32, bit 0x10 is GPIO0, so `0x3` means IO0 was low.
- [`probe_io0.py`](probe_io0.py): samples IO0 with the internal pull-up on, then with the board's
  Ethernet oscillator switched off and on through GPIO16. If IO0 stays low while the oscillator is off
  but toggles while it runs, no wire is shorting it: the oscillator itself pulls it down.

Register addresses are from the ESP32 Technical Reference Manual. The scripts only read pins, drive
GPIO16 and arm the watchdog; nothing is written to flash.
