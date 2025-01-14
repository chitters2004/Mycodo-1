# coding=utf-8
#
# Example module for measuring with the BME280 and sending
# the measurement to a serial device. For accompaniment with
# the The Things Network (TTN) Data Storage Input module
#
# Use this module to send measurements via serial to a
# LoRaWAN-enabled device, which transmits the data to TTN.
#
# Comment will be updated with other code to go along with this module
#
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
# Based on the BMP280 driver with BME280 changes provided by
# David J Taylor, Edinburgh (www.satsignal.eu)
import time

import filelock
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_altitude
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    1: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    2: {
        'measurement': 'pressure',
        'unit': 'Pa'
    },
    3: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    4: {
        'measurement': 'altitude',
        'unit': 'm'
    },
    5: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }

}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'BME280_TTN',
    'input_manufacturer': 'BOSCH',
    'input_name': 'BME280 (->Serial->TTN)',
    'measurements_name': 'Pressure/Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'measurements_use_same_timestamp': True,

    'message': "Note: This is just an informative note to the user.",

    'options_enabled': [
        'i2c_location',
        'custom_options',
        'measurements_select',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'serial', 'pyserial'),
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
        ('pip-git', 'Adafruit_BME280', 'git://github.com/adafruit/Adafruit_Python_BME280.git#egg=adafruit-bme280')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x76',
        '0x77'
    ],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'serial_device',
            'type': 'text',
            'default_value': '/dev/ttyUSB0',
            'name': lazy_gettext('Serial Device'),
            'phrase': lazy_gettext('The serial device to write to')
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the BME280's humidity, temperature,
    and pressure, them calculates the altitude and dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.timer = 0

        # Initialize custom options
        self.serial_device = None
        # Set custom options
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            from Adafruit_BME280 import BME280
            import serial

            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.sensor = BME280(address=self.i2c_address,
                                 busnum=self.i2c_bus)
            self.serial = serial
            self.serial_send = None
            self.lock_file = "/var/lock/mycodo_ttn.lock"
            self.ttn_serial_error = False

    def get_measurement(self):
        """ Gets the measurement in units by reading the """
        self.return_dict = measurements_dict.copy()

        if self.is_enabled(0):
            self.value_set(0, self.sensor.read_temperature())

        if self.is_enabled(1):
            self.value_set(1, self.sensor.read_humidity())

        if self.is_enabled(2):
            self.value_set(2, self.sensor.read_pressure())

        if (self.is_enabled(3) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            dewpoint = calculate_dewpoint(
                self.value_get(0), self.value_get(1))
            self.value_set(3, dewpoint)

        if self.is_enabled(4) and self.is_enabled(2):
            altitude = calculate_altitude(self.value_get(2))
            self.value_set(4, altitude)

        if (self.is_enabled(5) and
                self.is_enabled(0) and
                self.is_enabled(1)):
            vpd = calculate_vapor_pressure_deficit(
                self.value_get(0), self.value_get(1))
            self.value_set(5, vpd)

        try:
            now = time.time()
            if now > self.timer:
                self.timer = now + 80
                # "B" designates this data belonging to the BME280
                string_send = 'B,{},{},{}'.format(
                    self.value_get(1),
                    self.value_get(2),
                    self.value_get(0))
                self.lock_acquire(self.lock_file, timeout=10)
                if self.locked:
                    try:
                        self.serial_send = self.serial.Serial(self.serial_device, 9600)
                        self.serial_send.write(string_send.encode())
                        time.sleep(4)
                    finally:
                        self.lock_release(self.lock_file)
                self.ttn_serial_error = False
        except:
            if not self.ttn_serial_error:
                # Only send this error once if it continually occurs
                self.logger.error("TTN: Could not send serial")
                self.ttn_serial_error = True

        return self.return_dict
