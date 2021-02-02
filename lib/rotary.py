
from rotary_irq_esp import RotaryIRQ
import uasyncio as aio

default_rotary_encoder_pin_config = {

    # Digital input pins
    'rot_enc_clk': 27,
    'rot_enc_dt': 26,
    'rot_btn': 25,
}

class Rotary:

    def __init__(self, controller, config = default_rotary_encoder_pin_config):
        self.controller = controller
        self.ro = RotaryIRQ(pin_num_clk = config['rot_enc_clk'],
                            pin_num_dt = config['rot_enc_dt'])
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


