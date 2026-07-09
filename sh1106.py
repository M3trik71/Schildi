# SH1106 I2C-Treiber für MicroPython
# Kompatibel mit 128x64 SH1106 OLED

from micropython import const
import framebuf
import time

SET_CONTRAST        = const(0x81)
SET_ENTIRE_ON       = const(0xA4)
SET_NORM_INV        = const(0xA6)
SET_DISP            = const(0xAE)
SET_MEM_ADDR        = const(0x20)
SET_COL_ADDR        = const(0x21)
SET_PAGE_ADDR       = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP       = const(0xA1)
SET_MUX_RATIO       = const(0xA8)
SET_COM_OUT_DIR     = const(0xC8)
SET_DISP_OFFSET     = const(0xD3)
SET_COM_PIN_CFG     = const(0xDA)
SET_DISP_CLK_DIV    = const(0xD5)
SET_PRECHARGE       = const(0xD9)
SET_VCOM_DESEL      = const(0xDB)
SET_CHARGE_PUMP     = const(0x8D)

class SH1106_I2C:
    def __init__(self, width, height, i2c, addr=0x3c, external_vcc=False):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,
            SET_DISP_CLK_DIV, 0x80,
            SET_MUX_RATIO, self.height - 1,
            SET_DISP_OFFSET, 0x00,
            SET_DISP_START_LINE | 0x00,
            SET_CHARGE_PUMP, 0x14 if not self.external_vcc else 0x10,
            SET_MEM_ADDR, 0x00,
            SET_SEG_REMAP | 0x01,
            SET_COM_OUT_DIR | 0x08,
            SET_COM_PIN_CFG, 0x12,
            SET_CONTRAST, 0xCF,
            SET_PRECHARGE, 0xF1 if not self.external_vcc else 0x22,
            SET_VCOM_DESEL, 0x40,
            SET_ENTIRE_ON,
            SET_NORM_INV,
            SET_DISP | 0x01):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytearray([0x80, cmd]))

    def show(self):
        for page in range(0, self.pages):
            self.write_cmd(0xB0 + page)
            self.write_cmd(0x02)
            self.write_cmd(0x10)
            start = self.width * page
            end = start + self.width
            self.i2c.writeto(self.addr, bytearray([0x40]) + self.buffer[start:end])

    def fill(self, col):
        self.framebuf.fill(col)

    def pixel(self, x, y, col):
        self.framebuf.pixel(x, y, col)

    def text(self, string, x, y, col=1):
        self.framebuf.text(string, x, y, col)

    def scroll(self, dx, dy):
        self.framebuf.scroll(dx, dy)

    def blit(self, fbuf, x, y):
        self.framebuf.blit(fbuf, x, y)