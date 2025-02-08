from __future__ import annotations

import datetime
import logging

from bitstring import BitArray
from homeassistant.components.modbus import modbus
from homeassistant.core import HomeAssistant

from .hub import modbus_hub
from .registers import NeptunSmartRegisters


class NeptunSmart:
    def __init__(self,hass: HomeAssistant, name, host_ip: str | None,host_port) ->None:
        self._name = name
        self._hub = modbus_hub(host=host_ip, port=host_port)
        self._hub.connect()
        self._config_bits = self._hub.read_holding_register_bits(NeptunSmartRegisters.module_config,1)
        self._first_group_valve_is_open = bool(self._config_bits[7])
        self._second_group_valve_is_open = bool(self._config_bits[6])
        self._floor_washing_mode = bool(self._config_bits[15])
        self._first_group_alarm = bool(self._config_bits[14])
        self._second_group_alarm = bool(self._config_bits[13])
        self._discharge_wireless_sensors = bool(self._config_bits[12])
        self._lost_wireless_sensors = bool(self._config_bits[11])
        self._connecting_wireless_sensors_mode = bool(self._config_bits[8])
        self._dual_group_mode = bool(self._config_bits[5])
        self._close_valve_when_loss_sensor = bool(self._config_bits[4])
        self._lock_buttons = bool(self._config_bits[3])
        self._config_line_1_2_bits = self._hub.read_holding_register_bits(NeptunSmartRegisters.input_line_1_2_config, 1)
        self._line_type = [True,True,True,True,True]
        self._line_group = [0, 0, 0, 0, 0]
        self._line_type[1] = bool(self._config_line_1_2_bits[5])
        self._line_type[2] = bool(self._config_line_1_2_bits[13])
        self._line_group[1] = BitArray([self._config_line_1_2_bits[6], self._config_line_1_2_bits[7]])._getuint() #1 = first group, 2 = second group, 3 = both groups
        self._line_group[2] = BitArray([self._config_line_1_2_bits[14], self._config_line_1_2_bits[15]])._getuint() #1 = first group, 2 = second group, 3 = both groups
        self._config_line_3_4_bits = self._hub.read_holding_register_bits(NeptunSmartRegisters.input_line_3_4_config, 1)
        self._line_type[3] = bool(self._config_line_3_4_bits[5])
        self._line_type[4] = bool(self._config_line_3_4_bits[13])
        self._line_group[3] = BitArray([self._config_line_3_4_bits[6], self._config_line_3_4_bits[7]])._getuint()  # 1 = first group, 2 = second group, 3 = both groups
        self._line_group[4] = BitArray([self._config_line_3_4_bits[14], self._config_line_3_4_bits[15]])._getuint()  # 1 = first group, 2 = second group, 3 = both groups
        self._status_wired_line_bits = self._hub.read_holding_register_bits(NeptunSmartRegisters.status_wired_line, 1)
        self._line_status = [True, True, True, True, True]
        self._line_status[1] = bool(self._status_wired_line_bits[15])
        self._line_status[2] = bool(self._status_wired_line_bits[14])
        self._line_status[3] = bool(self._status_wired_line_bits[13])
        self._line_status[4] = bool(self._status_wired_line_bits[12])
        self._relay_config_bits = self._hub.read_holding_register_bits(NeptunSmartRegisters.relay_config, 1)
        self._switch_when_close_valve = BitArray([self._relay_config_bits[12], self._relay_config_bits[13]])._getuint()
        self._switch_when_alert = BitArray([self._relay_config_bits[14], self._relay_config_bits[15]])._getuint()
        self._wireless_sensors_connected = self._hub.read_holding_register_uint16(
            NeptunSmartRegisters.count_of_connected_wireless_sensors, 1)
        self.wireless_sensors = []
        for i in range(0, self._wireless_sensors_connected):
            wireless_sensor_config = self._hub.read_holding_register_uint16(NeptunSmartRegisters.first_wireless_sensor_config+i,1)
            wireless_sensor_status_bits = self._hub.read_holding_register_bits(NeptunSmartRegisters.first_wireless_sensor_status+i,1)
            self.wireless_sensors.append(WirelessSensor(self._hub, NeptunSmartRegisters.first_wireless_sensor_config+i,NeptunSmartRegisters.first_wireless_sensor_status+i, wireless_sensor_config,wireless_sensor_status_bits))
        self.counters = []
        for i in range(0, 8):
            if self._hub.read_holding_register_bits(NeptunSmartRegisters.first_counter_config+i, 1)[15] == 1:
                self.counters.append(Counter(self._hub.read_holding_register_uint32(NeptunSmartRegisters.first_counter+(i*2), 2), NeptunSmartRegisters.first_counter+(i*2), self._hub))
        self._hub.disconnect()

    def update(self):
        self._hub.connect()
        self._config_bits = self._hub.read_holding_register_bits(NeptunSmartRegisters.module_config, 1)
        self._first_group_valve_is_open = bool(self._config_bits[7])
        self._second_group_valve_is_open = bool(self._config_bits[6])
        self._floor_washing_mode = bool(self._config_bits[15])
        self._first_group_alarm = bool(self._config_bits[14])
        self._second_group_alarm = bool(self._config_bits[13])
        self._discharge_wireless_sensors = bool(self._config_bits[12])
        self._lost_wireless_sensors = bool(self._config_bits[11])
        self._connecting_wireless_sensors_mode = bool(self._config_bits[8])
        self._dual_group_mode = bool(self._config_bits[5])
        self._close_valve_when_loss_sensor = bool(self._config_bits[4])
        self._lock_buttons = bool(self._config_bits[3])
        self._config_line_1_2_bits = self._hub.read_holding_register_bits(NeptunSmartRegisters.input_line_1_2_config, 1)
        self._line_type = [True, True, True, True, True]
        self._line_group = [0, 0, 0, 0, 0]
        self._line_type[1] = bool(self._config_line_1_2_bits[5])
        self._line_type[2] = bool(self._config_line_1_2_bits[13])
        self._line_group[1] = BitArray([self._config_line_1_2_bits[6], self._config_line_1_2_bits[
            7]])._getuint()  # 1 = first group, 2 = second group, 3 = both groups
        self._line_group[2] = BitArray([self._config_line_1_2_bits[14], self._config_line_1_2_bits[
            15]])._getuint()  # 1 = first group, 2 = second group, 3 = both groups
        self._config_line_3_4_bits = self._hub.read_holding_register_bits(NeptunSmartRegisters.input_line_3_4_config, 1)
        self._line_type[3] = bool(self._config_line_3_4_bits[5])
        self._line_type[4] = bool(self._config_line_3_4_bits[13])
        self._line_group[3] = BitArray([self._config_line_3_4_bits[6], self._config_line_3_4_bits[
            7]])._getuint()  # 1 = first group, 2 = second group, 3 = both groups
        self._line_group[4] = BitArray([self._config_line_3_4_bits[14], self._config_line_3_4_bits[
            15]])._getuint()  # 1 = first group, 2 = second group, 3 = both groups
        self._status_wired_line_bits = self._hub.read_holding_register_bits(NeptunSmartRegisters.status_wired_line, 1)
        self._line_status = [True, True, True, True, True]
        self._line_status[1] = bool(self._status_wired_line_bits[15])
        self._line_status[2] = bool(self._status_wired_line_bits[14])
        self._line_status[3] = bool(self._status_wired_line_bits[13])
        self._line_status[4] = bool(self._status_wired_line_bits[12])
        self._relay_config_bits = self._hub.read_holding_register_bits(NeptunSmartRegisters.relay_config, 1)
        self._switch_when_close_valve = BitArray([self._relay_config_bits[12], self._relay_config_bits[13]])._getuint()
        self._switch_when_alert = BitArray([self._relay_config_bits[14], self._relay_config_bits[15]])._getuint()
        self._wireless_sensors_connected = self._hub.read_holding_register_uint16(
            NeptunSmartRegisters.count_of_connected_wireless_sensors, 1)
        self._hub.disconnect()
        for sensor in self.wireless_sensors:
            sensor.update()
        for counter in self.counters:
            counter.update()

    def get_discharge_wireless_sensors(self)->bool:
        return self._discharge_wireless_sensors

    def get_lost_wireless_sensors(self)->bool:
        return self._lost_wireless_sensors

    def get_number_of_connected_wireless_sensors(self):
        return self._wireless_sensors_connected

    def get_name(self):
        return self._name

    def get_first_group_alarm(self):
        return self._first_group_alarm

    def get_second_group_alarm(self):
        return self._second_group_alarm

    def get_first_group_valve_state(self):
        return self._first_group_valve_is_open

    def write_config_register(self):
        self._hub.connect()
        self._hub.write_holding_register_bits(NeptunSmartRegisters.module_config, self._config_bits)
        self._hub.disconnect()

    def set_first_group_valve_state(self,state):
        self._first_group_valve_is_open = state
        self._config_bits[7] = int(state)
        self.write_config_register()

    def get_second_group_valve_state(self):
        return self._second_group_valve_is_open

    def set_second_group_valve_state(self,state):
        self._second_group_valve_is_open = state
        self._config_bits[6] = int(state)
        self.write_config_register()

    def get_floor_washing_mode(self):
        return self._floor_washing_mode

    def set_floor_washing_mode(self,state):
        self._floor_washing_mode = state
        self._config_bits[15] = int(state)
        self.write_config_register()

    def get_connecting_wireless_sensors_mode(self):
        return self._connecting_wireless_sensors_mode

    def set_connecting_wireless_sensors_mode(self,state):
        self._connecting_wireless_sensors_mode = state
        self._config_bits[8] = int(state)
        self.write_config_register()

    def get_dual_group_mode(self):
        return self._dual_group_mode

    def set_dual_group_mode(self,state):
        self._dual_group_mode = state
        self._config_bits[5] = int(state)
        self.write_config_register()

    def get_close_valve_when_lost_sensors_mode(self):
        return self._close_valve_when_loss_sensor

    def set_close_valve_when_lost_sensors_mode(self,state):
        self._close_valve_when_loss_sensor = state
        self._config_bits[4] = int(state)
        self.write_config_register()

    def get_lock_buttons(self):
        return self._lock_buttons

    def set_lock_buttons(self,state):
        self._lock_buttons = state
        self._config_bits[3] = int(state)
        self.write_config_register()

    def get_line_config_type(self,line_number):
        return self._line_type[line_number]

    def set_line_type(self,line_number,state):
        self._line_type[line_number] = state
        self._set_bit_to_line_type()
        self.write_line_config_register()

    def get_line_group(self, line_number):
        return self._line_group[line_number]

    def set_line_group(self,line_number,state):
        # 1 = first group, 2 = second group, 3 = both groups
        self._line_group[line_number] = state
        if line_number == 1:
            self._set_bit_to_line_1_2_group(line_number, 6, 7)
        if line_number == 2:
            self._set_bit_to_line_1_2_group(line_number, 14, 15)
        if line_number == 3:
            self._set_bit_to_line_3_4_group(line_number, 6, 7)
        if line_number == 4:
            self._set_bit_to_line_3_4_group(line_number, 14, 15)
        self.write_line_config_register()

    def _set_bit_to_line_1_2_group(self,line_number, bit1, bit2):
        if self._line_group[line_number] == 1:
            self._config_line_1_2_bits[bit1] = 0
            self._config_line_1_2_bits[bit2] = 1
        elif self._line_group[line_number] == 2:
            self._config_line_1_2_bits[bit1] = 1
            self._config_line_1_2_bits[bit2] = 0
        else:
            self._config_line_1_2_bits[bit1] = 1
            self._config_line_1_2_bits[bit2] = 1

    def _set_bit_to_line_3_4_group(self, line_number, bit1, bit2):
        if self._line_group[line_number] == 1:
            self._config_line_3_4_bits[bit1] = 0
            self._config_line_3_4_bits[bit2] = 1
        elif self._line_group[line_number] == 2:
            self._config_line_3_4_bits[bit1] = 1
            self._config_line_3_4_bits[bit2] = 0
        else:
            self._config_line_3_4_bits[bit1] = 1
            self._config_line_3_4_bits[bit2] = 1

    def _set_bit_to_line_type(self):
        # update config bits
        self._config_line_1_2_bits[5] = self._line_type[1]
        self._config_line_1_2_bits[13] = self._line_type[2]
        self._config_line_3_4_bits[5] = self._line_type[3]
        self._config_line_3_4_bits[13] = self._line_type[4]

    def write_line_config_register(self):
        self._hub.connect()
        self._hub.write_holding_register_bits(NeptunSmartRegisters.input_line_1_2_config, self._config_line_1_2_bits)
        self._hub.write_holding_register_bits(NeptunSmartRegisters.input_line_3_4_config, self._config_line_3_4_bits)
        self._hub.disconnect()

    def get_line_status(self, line_number):
        return self._line_status[line_number]

    def get_relay_config_valve(self) -> int:
        return int(self._switch_when_close_valve)

    def set_relay_config_valve(self,state):
        self._switch_when_close_valve = state
        if self._switch_when_close_valve == 0:
            self._relay_config_bits[12] = 0
            self._relay_config_bits[13] = 0
        elif self._switch_when_close_valve == 1:
            self._relay_config_bits[12] = 0
            self._relay_config_bits[13] = 1
        elif self._switch_when_close_valve == 2:
            self._relay_config_bits[12] = 1
            self._relay_config_bits[13] = 0
        else:
            self._relay_config_bits[12] = 1
            self._relay_config_bits[13] = 3
        self._write_relay_config_register()

    def _write_relay_config_register(self):
        self._hub.connect()
        self._hub.write_holding_register_bits(NeptunSmartRegisters.relay_config, self._relay_config_bits)
        self._hub.disconnect()

    def get_relay_config_alert(self) -> int:
        return int(self._switch_when_alert)

    def set_relay_config_alert(self, state):
        self._switch_when_close_valve = state
        if self._switch_when_close_valve == 0:
            self._relay_config_bits[14] = 0
            self._relay_config_bits[15] = 0
        elif self._switch_when_close_valve == 1:
            self._relay_config_bits[14] = 0
            self._relay_config_bits[15] = 1
        elif self._switch_when_close_valve == 2:
            self._relay_config_bits[14] = 1
            self._relay_config_bits[15] = 0
        else:
            self._relay_config_bits[14] = 1
            self._relay_config_bits[15] = 3
        self._write_relay_config_register()


class WirelessSensor():
    def __init__(self, hub: modbus_hub, address_config, address_value, config, status_bits):
        self._hub = hub
        self._address_config = address_config
        self._address_value = address_value #получаем адреса, запрашиавем данные, получаем уникальные идентификаторы
        self.update_data(config, status_bits)

    def update(self):
        self._hub.connect()
        wireless_sensor_config = self._hub.read_holding_register_uint16(
            self._address_config, 1)
        wireless_sensor_status_bits = self._hub.read_holding_register_bits(
            self._address_value, 1)
        self._hub.disconnect()
        self.update_data(wireless_sensor_config, wireless_sensor_status_bits)

    def update_data(self,config, status_bits):
        self._config = config
        self._status_bits = status_bits
        self._battery_level = BitArray(
            [self._status_bits[0], self._status_bits[1], self._status_bits[2], self._status_bits[3],
             self._status_bits[4], self._status_bits[5], self._status_bits[6], self._status_bits[7]])._getuint()
        self._alert = bool(self._status_bits[15])
        self._discharge = bool(self._status_bits[14])
        self._lost_sensor = bool(self._status_bits[13])
        self._signal_level = BitArray([self._status_bits[12], self._status_bits[11], self._status_bits[10]])._getuint()

    def get_group_config(self):
        return self._config

    def set_group_config(self, config):
        self._hub.connect()
        self._hub.write_holding_register(address=self._address_value,value=config)
        self._hub.disconnect()

    def get_battery_level(self):
        return self._battery_level

    def get_signal_level(self):
        return self._signal_level

    def get_alert_status(self):
        return self._alert
    def get_lost_sensor_status(self):

        return self._lost_sensor
    def get_discharge_status(self):

        return self._discharge
    def get_address(self):
        return self._address_config


class Counter():
    def __init__(self, value, address, hub: modbus_hub):
        self._value = value
        self._address = address
        self._hub = hub

    def update(self):
        self._hub.connect()
        self._value = self._hub.read_holding_register_uint32(self._address, 2)
        self._hub.disconnect()

    def get_value(self):
        return self._value

    def get_address(self):
        return self._address