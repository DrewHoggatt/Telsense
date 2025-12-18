from machine import Pin, SPI, PWM
import time
import framebuf

# Resolution of the 0.71 inch LCD
LCD_WIDTH  = 160
LCD_HEIGHT = 160

class LCD_0inch71(framebuf.FrameBuffer):
    def __init__(self, dc, cs, rst, clk, mosi, bl=None):
        self.width = LCD_WIDTH
        self.height = LCD_HEIGHT
        
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.bl = bl
        
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=1)
        
        # Initialize SPI
        # baudrate=40000000 (40MHz) is standard for these screens
        self.spi = SPI(1, baudrate=40000000, polarity=0, phase=0, sck=clk, mosi=mosi)
        
        # Initialize Buffer (16-bit color, RGB565)
        # 160 * 160 * 2 bytes = 51,200 bytes (Fits in ESP32-C3 RAM)
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        
        # Start Init Sequence
        self.init_display()

    def write_cmd(self, cmd):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(0)
        self.dc(1)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        # Hardware Reset
        self.rst(1)
        time.sleep(0.1)
        self.rst(0)
        time.sleep(0.1)
        self.rst(1)
        time.sleep(0.1)
        
        # Initialization Sequence for GC9D01 / 0.71" 
        self.write_cmd(0xFE)
        self.write_cmd(0xEF)
        
        self.write_cmd(0x80)
        self.write_data(0xFF)
        
        self.write_cmd(0x81)
        self.write_data(0xFF)
        
        self.write_cmd(0x82)
        self.write_data(0xFF)
        
        self.write_cmd(0x83)
        self.write_data(0xFF)
        
        self.write_cmd(0x84)
        self.write_data(0xFF)

        self.write_cmd(0x89)
        self.write_data(0x03)
        
        self.write_cmd(0x8D)
        self.write_data(0x03) 
        
        self.write_cmd(0x8E)
        self.write_data(0x03) 
        
        self.write_cmd(0x8F)
        self.write_data(0x03) 
        
        self.write_cmd(0x36) # Memory Access Control
        self.write_data(0x00) # 0x00 = RGB, 0xC0 = BGR (Try changing this if colors are swapped)
        
        self.write_cmd(0x3A) # Pixel Format
        self.write_data(0x05) # 16-bit color
        
        self.write_cmd(0xC0) 
        self.write_data(0x70) 
        
        self.write_cmd(0xC3) 
        self.write_data(0x04) 
        
        self.write_cmd(0xC4) 
        self.write_data(0x0C) 
        
        self.write_cmd(0xCB) 
        self.write_data(0x00) 
        
        self.write_cmd(0xE4) # Frame Rate
        self.write_data(0x60) 
        
        self.write_cmd(0xF0) # Gamma 1
        self.write_data(0x45)
        self.write_data(0x09)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x26)
        self.write_data(0x2A) 
        
        self.write_cmd(0xF1) # Gamma 2
        self.write_data(0x43)
        self.write_data(0x70)
        self.write_data(0x72)
        self.write_data(0x36)
        self.write_data(0x37)
        self.write_data(0x6F) 

        self.write_cmd(0xF2) # Gamma 3
        self.write_data(0x45)
        self.write_data(0x09)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x26)
        self.write_data(0x2A) 

        self.write_cmd(0xF3) # Gamma 4
        self.write_data(0x43)
        self.write_data(0x70)
        self.write_data(0x72)
        self.write_data(0x36)
        self.write_data(0x37)
        self.write_data(0x6F) 
        
        self.write_cmd(0x21) # Display Inversion ON (IPS screens usually need this)
        
        self.write_cmd(0x11) # Sleep Out
        time.sleep(0.12)
        self.write_cmd(0x29) # Display ON

    def show(self):
        # Set Window to 0,0 -> 160,160
        self.write_cmd(0x2A) # Column Addr
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(LCD_WIDTH - 1)
        
        self.write_cmd(0x2B) # Row Addr
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data