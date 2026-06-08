from machine import Pin, SPI
import framebuf
import time


# 2.13" e-Paper HAT (B) V3 - 212x104 tri-color (black/white/red)
EPD_WIDTH = 104
EPD_HEIGHT = 212


class EPD2in13B_V3:
    def __init__(self):
        # Wiring from user
        self.spi = SPI(
            1,
            baudrate=4_000_000,
            polarity=0,
            phase=0,
            sck=Pin(12),
            mosi=Pin(11),
        )
        self.cs = Pin(7, Pin.OUT, value=1)
        self.dc = Pin(6, Pin.OUT, value=0)
        self.rst = Pin(5, Pin.OUT, value=1)
        self.busy = Pin(4, Pin.IN)

        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

    def _cmd(self, c):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([c]))
        self.cs.value(1)

    def _data(self, d):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(bytearray([d]))
        self.cs.value(1)

    def _wait_busy(self):
        # Busy low = panel busy, wait until it goes high.
        self._cmd(0x71)
        while self.busy.value() == 0:
            self._cmd(0x71)
            time.sleep_ms(100)
            print("panel busy")

    def reset(self):
        self.rst.value(1)
        time.sleep_ms(200)
        self.rst.value(0)
        time.sleep_ms(2)
        self.rst.value(1)
        time.sleep_ms(200)

    def init(self):
        self.reset()

        self._cmd(0x04)  # POWER_ON
        self._wait_busy()

        self._cmd(0x00)  # PANEL_SETTING
        self._data(0x0F)
        self._data(0x89)

        self._cmd(0x61)  # RESOLUTION_SETTING
        self._data(0x68)  # 104
        self._data(0x00)
        self._data(0xD4)  # 212

        self._cmd(0x50)  # VCOM_AND_DATA_INTERVAL_SETTING
        self._data(0x77)

    def display(self, black_buf, red_buf):
        self._cmd(0x10)  # Black RAM
        for b in black_buf:
            self._data(b)

        self._cmd(0x13)  # Red RAM
        for b in red_buf:
            self._data(b)

        self._cmd(0x12)  # DISPLAY_REFRESH
        time.sleep_ms(100)
        self._wait_busy()

    def sleep(self):
        self._cmd(0x50)
        self._data(0xF7)
        self._cmd(0x02)  # POWER_OFF
        self._wait_busy()
        self._cmd(0x07)  # DEEP_SLEEP
        self._data(0xA5)


def main():
    epd = EPD2in13B_V3()
    epd.init()

    # 1 = white, 0 = colored pixel in each RAM
    black = bytearray([0xFF] * (EPD_WIDTH * EPD_HEIGHT // 8))
    red = bytearray([0xFF] * (EPD_WIDTH * EPD_HEIGHT // 8))

    fb_black = framebuf.FrameBuffer(black, EPD_WIDTH, EPD_HEIGHT, framebuf.MONO_HLSB)
    fb_red = framebuf.FrameBuffer(red, EPD_WIDTH, EPD_HEIGHT, framebuf.MONO_HLSB)

    fb_black.fill(1)
    fb_red.fill(1)

    # Draw text: "hello" in red, "world" in black
    fb_red.text("hello", 10, 40, 0)
    fb_black.text("world", 10, 60, 0)

    epd.display(black, red)
    epd.sleep()


main()
