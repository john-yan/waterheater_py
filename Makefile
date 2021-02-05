
all: prog dependencies

prog:
	ampy -p /dev/ttyUSB0 put main.py
	ampy -p /dev/ttyUSB0 put config.py
	ampy -p /dev/ttyUSB0 put wifi_config.txt
	ampy -p /dev/ttyUSB0 put lib/controller.py /lib/controller.py
	ampy -p /dev/ttyUSB0 put lib/mqtt_connect.py /lib/mqtt_connect.py
	ampy -p /dev/ttyUSB0 put lib/rotary.py /lib/rotary.py
	ampy -p /dev/ttyUSB0 put lib/display.py /lib/display.py

dependencies:
	ampy -p /dev/ttyUSB0 put micropython-rotary/rotary.py
	ampy -p /dev/ttyUSB0 put micropython-rotary/rotary_irq_esp.py
	ampy -p /dev/ttyUSB0 put micropython-mqtt/mqtt_as/mqtt_as.py
	ampy -p /dev/ttyUSB0 put micropython-async/v3/primitives /primitives
	ampy -p /dev/ttyUSB0 put python_lcd/lcd/esp32_i2c_lcd_async.py
	ampy -p /dev/ttyUSB0 put python_lcd/lcd/lcd_api_async.py
	ampy -p /dev/ttyUSB0 rmdir /primitives/tests


