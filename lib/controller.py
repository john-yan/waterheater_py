import uasyncio as aio
from machine import Pin, ADC

PILOT_ON_THRESHOLD = 200
PILOT_ON_STATE = 0
PILOT_OFF_STATE = 1
FIRE_ON_STATE = 0
FIRE_OFF_STATE = 1
FAN_ON_STATE = 1
FAN_OFF_STATE = 0
TEMPTEST_ON_STATE = 1
TEMPTEST_OFF_STATE = 0
ATT_MULTIPLIER = -0.028675
ATT_CONSTANT = 115.63

default_controller_pin_config = {

    # Digital output pins
    'pilot_en': 13,
    'fire_en': 12,
    'temptest_en': 14,
    'fan_en': 4,

    # ADC pins
    'thermo1_adc': 32,
    'thermo2_adc': 35,
    'pilot_adc': 33,
    'fan_adc': 34
}

class Controller:
    def __init__(self, config = None):

        # verify configuration
        controller_pin_config = config
        if controller_pin_config == None:
            controller_pin_config = default_controller_pin_config
        else:
            for key in default_controller_pin_config.keys():
                assert(key in config and isinstance(config[key], int))

        # create pins and adcs
        self.pins = {}
        self.adcs = {}
        for key in controller_pin_config.keys():
            if 'adc' in key:
                self.adcs[key] = ADC(Pin(controller_pin_config[key]))
                self.adcs[key].atten(ADC.ATTN_11DB)
            else:
                self.pins[key] = Pin(controller_pin_config[key], Pin.OUT)

        # internal states
        self._pilot_en = False
        self._fire_en = False
        self._fan_en = False
        self.current_temp = 0.0

        # temptest is reversed
        self.pilot_state(PILOT_OFF_STATE)
        self.fire_state(PILOT_OFF_STATE)
        self.fan_state(FAN_OFF_STATE)
        self.pins['temptest_en'].value(TEMPTEST_OFF_STATE)

        # Controller settings
        self.pilot_reading = 0
        self.target_temp = 50.0
        self.target_delta = 5
        self.mqtt = None
        self.report_adc = False
        self.away_mode = False
        self.operation = "unknown"

    def set_target_temp(self, temp):
        temp = round(temp, 1)
        self.target_temp = temp
        self.mqtt.report_target_temp(temp)

    def set_mqtt_connect(self, mqtt_conn):
        self.mqtt = mqtt_conn

    def set_report_adc(self, yes):
        self.report_adc = yes

    def set_away_mode(self, mode):
        self.away_mode = mode
        self.mqtt.report_away_mode(mode)

    def set_operation(self, op):
        self.operation = op

    def get_current_temp(self):
        return self.current_temp

    def get_target_temp(self):
        return self.target_temp

    def _adc_to_celcius(self, adc_reading):
        return ATT_MULTIPLIER * adc_reading + ATT_CONSTANT

    def pilot_state(self, state = None):
        if state == None:
            return self._pilot_en
        else:
            #print("set pilot state to ", state);
            old_state = self._pilot_en
            self._pilot_en = state
            self.pins['pilot_en'].value(state)
            return old_state

    def fire_state(self, state = None):
        if state == None:
            return self._fire_en
        else:
            #print("set fire state to ", state);
            old_state = self._fire_en
            self._fire_en = state
            self.pins['fire_en'].value(state)
            return old_state

    def fan_state(self, state = None):
        if state == None:
            return self._fan_en
        else:
            #print("set fan state to ", state);
            old_state = self._fan_en
            self._fan_en = state
            self.pins['fan_en'].value(state)
            return old_state

    async def shutdown(self):
        # this should not have normally happen
        self.pilot_state(PILOT_OFF_STATE)
        if self.fire_state(FIRE_OFF_STATE) == FIRE_ON_STATE:
            print("shutdown while fire is on!!!");
            await aio.sleep(3)
            self.fan_state(FAN_OFF_STATE)

    async def start_heating(self):
        if self.fan_state(FAN_ON_STATE) == FAN_OFF_STATE:
            await aio.sleep(3)
        self.fire_state(FIRE_ON_STATE)

    async def stop_heating(self):
        if self.fire_state(FIRE_OFF_STATE) == FIRE_ON_STATE:
            await aio.sleep(3)
        self.fan_state(FAN_OFF_STATE)

    async def monitor(self):
        # turn on temptest
        self.pins['temptest_en'].value(TEMPTEST_ON_STATE)
        await aio.sleep_ms(10)

        # read adc values
        thermo1_adc = self.adcs['thermo1_adc'].read()
        await aio.sleep_ms(10)
        thermo2_adc = self.adcs['thermo2_adc'].read()
        await aio.sleep_ms(10)
        pilot_adc = self.adcs['pilot_adc'].read()
        await aio.sleep_ms(10)

        # turn off temptest
        self.pins['temptest_en'].value(TEMPTEST_OFF_STATE)

        self.pilot_reading = int(((self.pilot_reading << 2) + pilot_adc) / 5)
        pilot_off = self.pilot_reading <= PILOT_ON_THRESHOLD

        thermo_avg = (thermo1_adc + thermo2_adc) / 2
        self.current_temp = self._adc_to_celcius(thermo_avg)

        below_target = self.current_temp < (self.target_temp - self.target_delta)
        above_target = self.current_temp > (self.target_temp + self.target_delta)

        if pilot_off:
            await self.shutdown()
        else:
            self.pilot_state(PILOT_ON_STATE)

            if self.away_mode:
                await self.stop_heating()
            elif below_target:
                await self.start_heating()
            elif above_target:
                await self.stop_heating()
            elif self.operation != "unknown":
                if self.operation == 'Heating':
                    await self.start_heating()
                elif self.operation == 'Idle':
                    await self.stop_heating()
                else:
                    print('unknow operation and do nothing')

                # complete and reset to unknown
                self.operation = 'unknown'


        # reporting
        if self.report_adc:
            self.mqtt.report_adc(thermo1_adc, thermo2_adc, pilot_adc)
        self.mqtt.report_current_state("off" if pilot_off else "on")
        self.mqtt.report_current_temp(round(self.current_temp, 0))
        self.mqtt.report_current_operation('Heating' if self.fire_state() == FIRE_ON_STATE else 'Idle')

    async def run(self):
        while True:
            await aio.sleep(1)
            await self.monitor()



