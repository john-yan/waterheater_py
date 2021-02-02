
import uasyncio as aio
from machine import Pin, ADC
from lib.controller import Controller
from lib.mqtt_connect import MQTTConnect
from lib.rotary import Rotary
from lib.display import Display

async def heartbeat():
    led = Pin(2, Pin.OUT);
    while True:
        led.on();
        await aio.sleep(0.1);
        led.off();
        await aio.sleep(0.8);


def main():
    ctl = Controller();
    mqtt_conn = MQTTConnect(ctl)
    rotary = Rotary(ctl)
    display = Display(ctl)
    ctl.add_update_listener(mqtt_conn.update)
    ctl.add_update_listener(display.update)
    aio.run(aio.gather(heartbeat(),
                       ctl.monitor(),
                       ctl.action(),
                       mqtt_conn.run(),
                       rotary.run(),
                       display.run()));

main()
