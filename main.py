
import uasyncio as aio
from machine import Pin, ADC
from lib.controller import Controller
from lib.mqtt_connect import MQTTConnect
from lib.rotary import Rotary
from lib.display import Display
import config as cfg


async def heartbeat():
    led = Pin(2, Pin.OUT)
    while True:
        led.on()
        await aio.sleep(0.1)
        led.off()
        await aio.sleep(0.8)


def main():
    co = [heartbeat()]

    ctl = Controller()
    co.append(ctl.run())

    mqtt_conn = MQTTConnect(ctl)
    co.append(mqtt_conn.run())

    if cfg.ENABLE_ROTARY_ENCODER:
        rotary = Rotary(ctl)
        co.append(rotary.run())

    if cfg.ENABLE_DISPLAY:
        display = Display(ctl)
        co.append(display.run())

    aio.run(aio.gather(*co))


main()
