
import uasyncio as aio
from mqtt_as import MQTTClient
import config as cfg
from mqtt_as import config
from primitives.queue import Queue


class MQTTConnect:
    def __init__(self, controller):

        # Define configuration
        config['subs_cb'] = self.topic_handler
        config['wifi_coro'] = self.wifi_handler
        config['connect_coro'] = self.conn_handler
        config['clean'] = True
        config['server'] = cfg.MQTT_SERVER_IP

        with open(cfg.WIFI_CONFIG_FILE) as f:
            config['ssid'] = f.readline().strip()
            print('wifi ssid:', config['ssid'])
            config['wifi_pw'] = f.readline().strip()
            print('wifi pw:', config['wifi_pw'])

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

    async def conn_handler(self, client):
        for topic in cfg.subscription_list:
            await self.client.subscribe(topic, 1)
            print('subscribe to', topic)

    def try_publish(self, topic, msg, qos=1, retain=False):
        if self.send_queue.qsize() < 20:
            self.send_queue.put_nowait([topic, msg, qos, retain])

    def report_adc_value(self, thermo1, thermo2, pilot):
        msg = str(thermo1)
        msg += " " + str(thermo2)
        msg += " " + str(pilot)
        self.try_publish(cfg.MQTT_ADC_TOPIC, msg)

    def report_current_state(self, state):
        # state could be 'on' or 'off'
        if state != self.last_state:
            self.try_publish(cfg.MQTT_STATE_TOPIC, state)
            self.last_state = state

    def report_current_temp(self, temp):
        if temp != self.last_temp:
            self.try_publish(cfg.MQTT_TEMP_TOPIC, str(temp))
            self.last_temp = temp

    def report_away_mode(self, mode):
        if self.last_mode != mode:
            self.try_publish(cfg.MQTT_AWAY_MODE_TOPIC, 'on' if mode else 'off')
            self.last_mode = mode

    def report_target_temp(self, temp):
        if self.last_target != temp:
            self.try_publish(cfg.MQTT_TARGET_TEMP_TOPIC, str(temp))
            self.last_target = temp

    def report_current_operation(self, op):
        # operation could be 'Heating' or 'Idle'
        if op != self.last_op:
            self.try_publish(cfg.MQTT_OPERATION_TOPIC, op)
            self.last_op = op

    # update callback
    def update(self):

        if self.is_report_adc:
            thermo1_adc_value = self.controller.get_thermo1_adc_value()
            thermo2_adc_value = self.controller.get_thermo2_adc_value()
            pilot_adc_value = self.controller.get_pilot_adc_value()
            self.report_adc_value(
                thermo1_adc_value,
                thermo2_adc_value,
                pilot_adc_value)
        self.report_current_state(
            "off" if self.controller.pilot_state() == cfg.PILOT_OFF_STATE else "on")
        self.report_current_temp(round(self.controller.get_current_temp(), 0))
        self.report_current_operation(
            'Heating' if self.controller.fire_state() == cfg.FIRE_ON_STATE else 'Idle')
        self.report_away_mode(self.controller.get_away_mode())
        self.report_target_temp(self.controller.get_target_temp())

    async def run(self):
        await self.client.connect()
        self.controller.add_update_listener(self.update)

        while True:
            payload = await self.send_queue.get()
            topic, msg, qos, retain = payload
            await self.client.publish(topic, msg, qos, retain)

    def topic_handler(self, topic_b, msg_b, retain):

        topic = topic_b.decode('ascii')
        msg = msg_b.decode('ascii')

        print("Receive:", topic, msg, retain)

        if topic == cfg.MQTT_SET_STATE_TOPIC:
            print("unable to handle set state request")

        elif topic == cfg.MQTT_SET_OPERATION_TOPIC:
            self.controller.set_operation(msg)

        elif topic == cfg.MQTT_SET_AWAY_MODE_TOPIC:
            # msg == 'on' or 'off'
            self.controller.set_away_mode(True if 'on' == msg else False)

        elif topic == cfg.MQTT_SET_ADC_TOPIC:
            # msg == 'on' or 'off'
            self.is_report_adc = True if 'on' == msg else False

        elif topic == cfg.MQTT_SET_TARGET_TEMP_TOPIC:
            self.controller.set_target_temp(float(msg))

        else:
            print('Unknow topic')
