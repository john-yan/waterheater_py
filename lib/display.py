
import uasyncio as aio
from esp32_i2c_lcd_async import I2cLcd
from machine import Pin, I2C
import config as cfg


class Display:

    def __init__(self, controller):

        self.controller = controller
        self.i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
        self.lcd = I2cLcd(self.i2c, cfg.DISPLAY_I2C_ADDR,
                          cfg.DISPLAY_NUM_OF_ROWS,
                          cfg.DISPLAY_NUM_OF_COLS)

        self.update_requested = aio.Event()
        self.old_temp_str = ''
        self.old_state = ''

    async def update_temp(self, temp_str):
        if self.old_temp_str != temp_str:
            self.old_temp_str = temp_str
            await self.lcd.move_to(0, 0)
            await self.lcd.putstr(temp_str)

    async def update_state(self, state):
        if self.old_state != state:
            self.old_state = state
            await self.lcd.move_to(0, 1)
            await self.lcd.putstr(state)

    async def run(self):

        await self.lcd.init_hw()
        await self.lcd.clear()
        self.lcd.backlight_on()
        self.update_requested.clear()
        self.controller.add_update_listener(self.update)

        old_temp_str = ''
        while True:
            await self.update_requested.wait()
            temp_str = "T:%.1f (%.1f)" % (self.controller.get_current_temp(),
                                          self.controller.get_target_temp())
            await self.update_temp(temp_str)
            state = "Heat" if self.controller.fire_state() == cfg.FIRE_ON_STATE else "Idle"
            state += "(Away)" if self.controller.get_away_mode() else "      "
            await self.update_state(state)
            await aio.sleep_ms(500)
            self.update_requested.clear()

    def update(self):
        self.update_requested.set()
