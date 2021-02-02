
import uasyncio as aio
from mqtt_as import MQTTClient
from mqtt_as import config
from primitives.queue import Queue

MQTT_ROOT_TOPIC = "water_heater"
MQTT_STATE_TOPIC = MQTT_ROOT_TOPIC + "/state"
MQTT_OPERATION_TOPIC = MQTT_ROOT_TOPIC + "/operation"
MQTT_AWAY_MODE_TOPIC = MQTT_ROOT_TOPIC + "/away_mode"
MQTT_TEMP_TOPIC = MQTT_ROOT_TOPIC + "/temperature"
MQTT_ADC_TOPIC = MQTT_ROOT_TOPIC + "/adc"
MQTT_CUR_TEMP_TOPIC = MQTT_TEMP_TOPIC + "/current"
MQTT_TARGET_TEMP_TOPIC = MQTT_TEMP_TOPIC + "/target"

MQTT_SET_STATE_TOPIC = MQTT_STATE_TOPIC + "/set"
MQTT_SET_OPERATION_TOPIC = MQTT_OPERATION_TOPIC + "/set"
MQTT_SET_AWAY_MODE_TOPIC = MQTT_AWAY_MODE_TOPIC + "/set"
MQTT_SET_ADC_TOPIC = MQTT_ADC_TOPIC + "/set"
MQTT_SET_TARGET_TEMP_TOPIC = MQTT_TARGET_TEMP_TOPIC + "/set"

subscription_list = [
    MQTT_SET_STATE_TOPIC,
    MQTT_SET_OPERATION_TOPIC,
    MQTT_SET_AWAY_MODE_TOPIC,
    MQTT_SET_ADC_TOPIC,
    MQTT_SET_TARGET_TEMP_TOPIC,
]

class MQTTConnect:
    def __init__(self, controller, config_file = 'wifi_config.txt'):

        # Define configuration
        config['subs_cb'] = self.topic_handler
        config['wifi_coro'] = self.wifi_handler
        config['connect_coro'] = self.conn_handler
        config['clean'] = True

        with open(config_file) as f:
            config['ssid'] = f.readline().strip()
            print('wifi ssid:', config['ssid']);
            config['wifi_pw'] = f.readline().strip()
            print('wifi pw:', config['wifi_pw']);
            config['server'] = f.readline().strip()
            print('server:', config['server']);

        self.client = MQTTClient(config)
        self.send_queue = Queue()
        self.controller = controller

        self.last_state = None
        self.last_temp = None
        self.last_op = None
        self.last_mode = False
        self.is_report_adc = False
        self.last_target = 50.0

    async def wifi_handler(self, state):
        print('Wifi is', 'up' if state else 'down')
        await aio.sleep(1)

    async def conn_handler(self, client):
        for topic in subscription_list:
            await self.client.subscribe(topic, 1)
            print('subscribe to', topic);

    def try_publish(self, topic, msg, qos = 1, retain = False):
        if self.send_queue.qsize() < 20:
            self.send_queue.put_nowait([topic, msg, qos, retain])

    def report_adc_value(self, thermo1, thermo2, pilot):
        msg = str(thermo1)
        msg += " " + str(thermo2)
        msg += " " +  str(pilot)
        self.try_publish(MQTT_ADC_TOPIC, msg)

    def report_current_state(self, state):
        # state could be 'on' or 'off'
        if state != self.last_state:
            self.try_publish(MQTT_STATE_TOPIC, state)
            self.last_state = state

    def report_current_temp(self, temp):
        if temp != self.last_temp:
            self.try_publish(MQTT_TEMP_TOPIC, str(temp))
            self.last_temp = temp

    def report_away_mode(self, mode):
        if self.last_mode != mode:
            self.try_publish(MQTT_AWAY_MODE_TOPIC, 'on' if mode else 'off')
            self.last_mode = mode

    def report_target_temp(self, temp):
        if self.last_target != temp:
            self.try_publish(MQTT_TARGET_TEMP_TOPIC, str(temp))
            self.last_target = temp

    def report_current_operation(self, op):
        # operation could be 'Heating' or 'Idle'
        if op != self.last_op:
            self.try_publish(MQTT_OPERATION_TOPIC, op)
            self.last_op = op

    # update callback
    def update(self):

        from controller import PILOT_OFF_STATE, FIRE_ON_STATE

        if self.is_report_adc:
            thermo1_adc_value = self.controller.get_thermo1_adc_value
            thermo2_adc_value = self.controller.get_thermo2_adc_value
            pilot_adc_value = self.controller.get_pilot_adc_value
            self.report_adc_value(thermo1_adc_value, thermo2_adc_value, pilot_adc_value)
        self.report_current_state("off" if self.controller.pilot_state() == PILOT_OFF_STATE else "on")
        self.report_current_temp(round(self.controller.get_current_temp(), 0))
        self.report_current_operation('Heating' if self.controller.fire_state() == FIRE_ON_STATE else 'Idle')
        self.report_away_mode(self.controller.get_away_mode())
        self.report_target_temp(self.controller.get_target_temp())

    async def run(self):
        await self.client.connect()

        while True:
            payload = await self.send_queue.get()
            topic, msg, qos, retain = payload
            await self.client.publish(topic, msg, qos, retain)

    def topic_handler(self, topic_b, msg_b, retain):

        topic = topic_b.decode('ascii')
        msg = msg_b.decode('ascii')

        print("Receive:", topic, msg, retain)

        if topic == MQTT_SET_STATE_TOPIC:
            print("unable to handle set state request");

        elif topic == MQTT_SET_OPERATION_TOPIC:
            self.controller.set_operation(msg);

        elif topic == MQTT_SET_AWAY_MODE_TOPIC:
            # msg == 'on' or 'off'
            self.controller.set_away_mode(True if 'on' == msg else False)

        elif topic == MQTT_SET_ADC_TOPIC:
            # msg == 'on' or 'off'
            self.is_report_adc = True if 'on' == msg else False

        elif topic == MQTT_SET_TARGET_TEMP_TOPIC:
            self.controller.set_target_temp(float(msg))

        else:
            print('Unknow topic')



