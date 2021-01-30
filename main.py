
import uasyncio as aio
from machine import Pin, ADC
from lib.controller import Controller
from lib.mqtt_connect import MQTTConnect

default_rotary_encoder_pin_config = {

    # Digital input pins
    'rot_enc_clk': 27,
    'rot_enc_dt': 26,
    'rot_btn': 25,
}


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
    ctl.set_mqtt_connect(mqtt_conn)
    aio.run(aio.gather(ctl.run(), heartbeat(), mqtt_conn.run()));

main()
