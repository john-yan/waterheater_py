
import uasyncio as aio
from machine import Pin, ADC

async def blink(led):
    while True:
        led.on();
        print("led is on\n");
        await aio.sleep(0.1);
        led.off();
        print("led is off\n");
        await aio.sleep(0.8);


async def adctest():
    adc = ADC(Pin(32));
    adc.atten(ADC.ATTN_11DB);
    while True:
        print("read adc value = ", adc.read());
        await aio.sleep(0.7);

def main():
    led = Pin(2, Pin.OUT);
    aio.run(aio.gather(adctest(), blink(led)));

main()
