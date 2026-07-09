# dfplayer.py – Minimal DFPlayer Mini Bibliothek für MicroPython
# Kompatibel mit Raspberry Pi Pico (UART)
# Unterstützt grundlegende Steuerbefehle

class DFPlayer:
    def __init__(self, uart):
        self.uart = uart

    def _send_cmd(self, cmd, param=0):
        cmd_line = bytearray(10)
        cmd_line[0] = 0x7E
        cmd_line[1] = 0xFF
        cmd_line[2] = 0x06
        cmd_line[3] = cmd
        cmd_line[4] = 0x00  # Keine Rückmeldung
        cmd_line[5] = (param >> 8) & 0xFF
        cmd_line[6] = param & 0xFF
        checksum = 0 - sum(cmd_line[1:7])
        cmd_line[7] = (checksum >> 8) & 0xFF
        cmd_line[8] = checksum & 0xFF
        cmd_line[9] = 0xEF
        self.uart.write(cmd_line)

    def play(self, track):
        self._send_cmd(0x03, track)  # Track aus Root (0001.mp3 → track=1)

    def play_folder(self, folder, file):
        param = (folder << 8) | file
        self._send_cmd(0x0F, param)  # Datei im Ordner abspielen

    def stop(self):
        self._send_cmd(0x16)

    def pause(self):
        self._send_cmd(0x0E)

    def resume(self):
        self._send_cmd(0x0D)

    def next(self):
        self._send_cmd(0x01)

    def previous(self):
        self._send_cmd(0x02)

    def volume(self, level):
        self._send_cmd(0x06, level)  # 0–30