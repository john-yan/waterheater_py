
import uasyncio as aio
from esp32_i2c_lcd_async import I2cLcd
from machine import Pin, I2C

DEFAULT_I2C_ADDR = 0x27

class Display:

    def __init__(self, controller):

        self.controller = controller
        self.i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
        self.lcd = I2cLcd(self.i2c, DEFAULT_I2C_ADDR, 2, 16)

        self.update_requested = aio.Event()

    async def run(self):

        await self.lcd.init_hw()
        await self.lcd.clear()
        self.lcd.backlight_on()
        self.update_requested.clear()
        while True:
            await self.update_requested.wait()
            await self.lcd.move_to(0, 0)
            await self.lcd.putstr("Temp: %.1f" % self.controller.get_current_temp())
            await self.lcd.move_to(0, 1)
            await self.lcd.putstr("Target: %.1f" % self.controller.get_target_temp())
            self.update_requested.clear()
            await aio.sleep_ms(100)

    def update(self):
        self.update_requested.set()
