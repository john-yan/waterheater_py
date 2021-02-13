
# Controller configuration
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
PILOT_EN_PIN_NUM = 13
FIRE_EN_PIN_NUM = 12
TEMPTEST_EN_PIN_NUM = 14
FAN_EN_PIN_NUM = 4
THERMO1_ADC_PIN_NUM = 32
THERMO2_ADC_PIN_NUM = 35
PILOT_ON_ADC_PIN_NUM = 33
ENABLE_FAN_SENSOR = False
FAN_ON_ADC_PIN_NUM = 34 if ENABLE_FAN_SENSOR else -1
DEFAULT_TARGET_TEMPERATURE = 50.0
DEFAULT_TARGET_DELTA = 5.0

# Display config
ENABLE_DISPLAY = True
DISPLAY_I2C_ADDR = 0x27
DISPLAY_NUM_OF_ROWS = 2
DISPLAY_NUM_OF_COLS = 16

# MQTT CONFIG
WIFI_CONFIG_FILE = 'wifi_config.txt'
MQTT_SERVER_IP = "192.168.1.132"
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

# ROTARY CONFIG
ENABLE_ROTARY_ENCODER = True
ROTARY_ENCODER_CLK_PIN_NUM = 27
ROTARY_ENCODER_DT_PIN_NUM = 26
ROTARY_ENCODER_BUTTON_PIN_NUM = 25


