import uasyncio as aio
from machine import Pin, ADC
from primitives.queue import Queue
import config as cfg

class Controller:
    def __init__(self):

        # create pins and adcs
        self.pins = {
            'pilot_en': Pin(cfg.PILOT_EN_PIN_NUM, Pin.OUT),
            'fire_en': Pin(cfg.FIRE_EN_PIN_NUM, Pin.OUT),
            'temptest_en': Pin(cfg.TEMPTEST_EN_PIN_NUM, Pin.OUT),
            'fan_en': Pin(cfg.FAN_EN_PIN_NUM, Pin.OUT)
        }

        self.adcs = {
            'thermo1_adc': ADC(Pin(cfg.THERMO1_ADC_PIN_NUM)),
            'thermo2_adc': ADC(Pin(cfg.THERMO2_ADC_PIN_NUM)),
            'pilot_adc': ADC(Pin(cfg.PILOT_ON_ADC_PIN_NUM)),
            'fan_adc': ADC(Pin(cfg.FAN_ON_ADC_PIN_NUM))
        }

        for adc in self.adcs.values():
            adc.atten(ADC.ATTN_11DB)

        # internal states
        self._pilot_en = False
        self._fire_en = False
        self._fan_en = False
        self.current_temp = 0.0
        self.thermo1_adc_value = 0
        self.thermo2_adc_value = 0
        self.pilot_adc_value = 0
        self.update_listener = []
        self.action_queue = Queue()

        # init pin states
        self.pilot_state(cfg.PILOT_OFF_STATE)
        self.fire_state(cfg.PILOT_OFF_STATE)
        self.fan_state(cfg.FAN_OFF_STATE)
        self.pins['temptest_en'].value(cfg.TEMPTEST_OFF_STATE)

        # Controller settings
        self.pilot_reading = 0
        self.target_temp = cfg.DEFAULT_TARGET_TEMPERATURE
        self.target_delta = cfg.DEFAULT_TARGET_DELTA
        self.report_adc = False
        self.away_mode = False
        self.operation = "unknown"

    def set_target_temp(self, temp):
        temp = round(temp, 1)
        self.target_temp = temp
        self.trigger_update()

    def add_update_listener(self, listener):
        self.update_listener.append(listener)

    def trigger_update(self):
        for listener in self.update_listener:
            listener()

    def set_report_adc(self, yes):
        self.report_adc = yes

    def set_away_mode(self, mode):
        self.away_mode = mode
        self.trigger_update()

    def get_away_mode(self):
        return self.away_mode

    def set_operation(self, op):
        self.operation = op

    def get_current_temp(self):
        return self.current_temp

    def get_target_temp(self):
        return self.target_temp

    def _adc_to_celcius(self, adc_reading):
        return cfg.ATT_MULTIPLIER * adc_reading + cfg.ATT_CONSTANT

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
        self.pilot_state(cfg.PILOT_OFF_STATE)
        if self.fire_state(cfg.FIRE_OFF_STATE) == cfg.FIRE_ON_STATE:
            print("shutdown while fire is on!!!");
            await aio.sleep(3)
            self.fan_state(cfg.FAN_OFF_STATE)

    async def start_heating(self):
        if self.fan_state(cfg.FAN_ON_STATE) == cfg.FAN_OFF_STATE:
            await aio.sleep(3)
        self.fire_state(cfg.FIRE_ON_STATE)

    async def stop_heating(self):
        if self.fire_state(cfg.FIRE_OFF_STATE) == cfg.FIRE_ON_STATE:
            await aio.sleep(3)
        self.fan_state(cfg.FAN_OFF_STATE)

    def get_thermo1_adc_value(self):
        return self.thermo1_adc_value

    def get_thermo2_adc_value(self):
        return self.thermo2_adc_value

    def get_pilot_adc_value(self):
        return self.pilot_adc_value

    async def action(self):

        while True:
            act = await self.action_queue.get()
            if act == 'shutdown':
                await self.shutdown()
            elif act == 'stop_heating':
                await self.stop_heating()
            elif act == 'start_heating':
                await self.start_heating()
            elif act == 'pilot_start':
                self.pilot_state(cfg.PILOT_ON_STATE)
            else:
                print("unknown action requested:", act)

    def request_action(self, act):
        self.action_queue.put_nowait(act)
        print("action requested:", act);

    async def monitor(self):

        while True:

            await aio.sleep(1)

            # turn on temptest
            self.pins['temptest_en'].value(cfg.TEMPTEST_ON_STATE)
            await aio.sleep_ms(10)

            # read adc values
            self.thermo1_adc_value = self.adcs['thermo1_adc'].read()
            await aio.sleep_ms(10)
            self.thermo2_adc_value = self.adcs['thermo2_adc'].read()
            await aio.sleep_ms(10)
            self.pilot_adc_value = self.adcs['pilot_adc'].read()
            await aio.sleep_ms(10)

            # turn off temptest
            self.pins['temptest_en'].value(cfg.TEMPTEST_OFF_STATE)

            self.pilot_reading = int(((self.pilot_reading << 2) + self.pilot_adc_value) / 5)

            thermo_avg = (self.thermo1_adc_value + self.thermo2_adc_value) / 2
            self.current_temp = self._adc_to_celcius(thermo_avg)

            pilot_off = self.pilot_reading <= cfg.PILOT_ON_THRESHOLD
            below_target = self.current_temp < (self.target_temp - self.target_delta)
            above_target = self.current_temp > (self.target_temp + self.target_delta)


            if pilot_off:
                self.request_action('shutdown')
            else:
                if self.pilot_state() == cfg.PILOT_OFF_STATE:
                    self.request_action('pilot_start')

                if self.away_mode:
                    if self.fire_state() == cfg.FIRE_ON_STATE:
                        self.request_action('stop_heating')
                elif below_target and self.fire_state() == cfg.FIRE_OFF_STATE:
                    self.request_action('start_heating')
                elif above_target and self.fire_state() == cfg.FIRE_ON_STATE:
                    self.request_action('stop_heating')
                elif self.operation != "unknown":
                    if self.operation == 'Heating' and self.fire_state() == cfg.FIRE_OFF_STATE:
                        self.request_action('start_heating')
                    elif self.operation == 'Idle' and self.fire_state() == cfg.FIRE_ON_STATE:
                        self.request_action('stop_heating')
                    else:
                        print('unknow operation and do nothing')

                    # complete and reset to unknown
                    self.operation = 'unknown'

            self.trigger_update()



