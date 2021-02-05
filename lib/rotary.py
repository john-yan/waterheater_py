
from rotary_irq_esp import RotaryIRQ
import uasyncio as aio
from config import ROTARY_ENCODER_CLK_PIN_NUM, ROTARY_ENCODER_DT_PIN_NUM


class Rotary:

    def __init__(self, controller):
        self.controller = controller
        self.ro = RotaryIRQ(pin_num_clk=ROTARY_ENCODER_CLK_PIN_NUM,
                            pin_num_dt=ROTARY_ENCODER_DT_PIN_NUM)
        self.event = aio.Event()
        self.ro.add_listener(self.callback)

    def callback(self):
        self.event.set()

    async def run(self):
        last = self.ro.value()
        while True:
            await self.event.wait()
            val = self.ro.value()
            delta = val - last
            target_temp = self.controller.get_target_temp()
            self.controller.set_target_temp(target_temp + delta)
            last = val
            self.event.clear()
