from machine import Pin, SPI, PWM
import time
import lcd

# --- PIN DEFINITIONS (Waveshare ESP32-C3-0.71) ---
PIN_BL   = 2
PIN_DC   = 4
PIN_CS   = 5
PIN_CLK  = 6
PIN_MOSI = 7
PIN_RST  = 8

# 1. Turn on Backlight (Essential!)
# We use PWM to set brightness (0-65535)
pwm = PWM(Pin(PIN_BL))
pwm.freq(1000)
pwm.duty_u16(40000) # ~60% Brightness

# 2. Initialize the LCD Driver
lcd = LCD_0inch71.LCD_0inch71(
    dc=Pin(PIN_DC),
    cs=Pin(PIN_CS),
    rst=Pin(PIN_RST),
    clk=Pin(PIN_CLK),
    mosi=Pin(PIN_MOSI)
)

# 3. Clear Screen to Red (to test color)
# Color format is RGB565 in Hex
# Red: 0xF800, Green: 0x07E0, Blue: 0x001F, White: 0xFFFF, Black: 0x0000
lcd.fill(0xF800) 
lcd.show()
time.sleep(1)

# 4. Clear to Black and Draw Text
lcd.fill(0x0000)
lcd.text("MicroPython", 35, 60, 0xFFFF) # x=35, y=60, color=White
lcd.text("Success!", 45, 80, 0x07E0)    # x=45, y=80, color=Green

# 5. Draw a box
lcd.rect(50, 100, 60, 20, 0x001F)       # x, y, w, h, color

# 6. Send data to screen
lcd.show()

print("Screen updated!")