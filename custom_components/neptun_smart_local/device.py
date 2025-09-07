from __future__ import annotations

import asyncio
import datetime
import logging
import async_timeout
from asyncio.exceptions import InvalidStateError
from bitstring import BitArray
from homeassistant.core import HomeAssistant
from pymodbus import ModbusException
from pymodbus.exceptions import ModbusIOException

from .hub import modbus_hub
from .registers import NeptunSmartRegisters

_LOGGER = logging.getLogger(__name__)
class NeptunSmart:
    def __init__(self, hass: HomeAssistant, name, host_ip: str | None, host_port) ->None:
        self._name = name
        self._hass = hass
        self._hub = modbus_hub(hass=hass, host=host_ip, port=host_port)
        self._line_type = [True, True, True, True, True]
        self._line_group = [0, 0, 0, 0, 0]
        self._line_status = [True, True, True, True, True]
        self.wireless_sensors = []
        self.counters = []
        self._wireless_sensors_connected = 0
        
        # Инициализируем атрибуты, которые используются в update()
        self._first_group_valve_is_open = False
        self._second_group_valve_is_open = False
        self._floor_washing_mode = False
        self._first_group_alarm = False
        self._second_group_alarm = False
        self._discharge_wireless_sensors = False
        self._lost_wireless_sensors = False
        self._connecting_wireless_sensors_mode = False
        self._dual_group_mode = False
        self._close_valve_when_loss_sensor = False
        self._lock_buttons = False
        self._switch_when_close_valve = 0
        self._switch_when_alert = 0
        
        # Инициализируем битовые массивы
        self._config_bits = None
        self._config_line_1_2_bits = None
        self._config_line_3_4_bits = None
        self._status_wired_line_bits = None
        self._relay_config_bits = None
        
        # Флаг для отслеживания состояния подключения
        self._connection_attempts = 0
        self._last_connection_attempt = 0
        self._is_connected = False

    async def init_sensors(self):
        try:
            await self._hub.connect()
        except ValueError as e:
            _LOGGER.error(f"Не удалось подключиться к устройству {self._name}: {e}")
            # Не выбрасываем исключение, чтобы интеграция могла работать в автономном режиме
            return
        
        self._wireless_sensors_connected = await self._hub.read_holding_register_uint16(
            NeptunSmartRegisters.count_of_connected_wireless_sensors, 1)
        
        # Проверяем, что мы получили корректное значение
        if self._wireless_sensors_connected is None:
            _LOGGER.debug("Не удалось получить количество подключенных беспроводных датчиков, используем значение по умолчанию 0")
            self._wireless_sensors_connected = 0
        
        for i in range(0, self._wireless_sensors_connected):
            wireless_sensor_config = await self._hub.read_holding_register_uint16(
                NeptunSmartRegisters.first_wireless_sensor_config + i, 1)
            wireless_sensor_status_bits = await self._hub.read_holding_register_bits(
                NeptunSmartRegisters.first_wireless_sensor_status + i, 1)
            
            # Проверяем, что данные получены корректно
            if wireless_sensor_config is not None and wireless_sensor_status_bits is not None:
                self.wireless_sensors.append(
                    WirelessSensor(self._hub, NeptunSmartRegisters.first_wireless_sensor_config + i,
                                   NeptunSmartRegisters.first_wireless_sensor_status + i, wireless_sensor_config,
                                   wireless_sensor_status_bits))
            else:
                _LOGGER.warning(f"Не удалось получить данные для беспроводного датчика {i}")

        for i in range(0, 8):
            counter_status = await self._hub.read_holding_register_bits(NeptunSmartRegisters.first_counter_config + i, 1)
            if counter_status is not None and counter_status[15] == 1:
                counter_value = await self._hub.read_holding_register_uint32(NeptunSmartRegisters.first_counter + (i * 2), 2)
                if counter_value is not None:
                    self.counters.append(
                        Counter(counter_value,
                                NeptunSmartRegisters.first_counter + (i * 2), self._hub))
                else:
                    _LOGGER.debug(f"Не удалось получить значение счетчика {i}")
            elif counter_status is None:
                _LOGGER.debug(f"Не удалось получить статус счетчика {i}")

    async def _check_and_reconnect(self):
        """Проверяет подключение и пытается переподключиться при необходимости"""
        try:
            # Простая проверка - если клиент подключен, считаем что подключение есть
            if hasattr(self._hub, '_client') and self._hub._client.connected:
                self._is_connected = True
                return True
            
            # Если не подключен, пытаемся подключиться
            _LOGGER.info(f"Попытка подключения к устройству {self._name}")
            await self._hub.connect()
            self._is_connected = True
            _LOGGER.info(f"Успешно подключились к устройству {self._name}")
            return True
        except Exception as e:
            _LOGGER.error(f"Не удалось подключиться к устройству {self._name}: {e}")
            self._is_connected = False
            return False

    async def update(self):
        try:
            # Проверяем подключение
            if not await self._check_and_reconnect():
                _LOGGER.debug(f"Не удалось подключиться к устройству {self._name}, пропускаем обновление")
                self._is_connected = False
                return
                
            async with async_timeout.timeout(10):
                self._config_bits = await self._hub.read_holding_register_bits(NeptunSmartRegisters.module_config, 1)
                
                # Проверяем, что данные получены корректно
                if self._config_bits is None:
                    _LOGGER.debug("Не удалось получить конфигурационные биты модуля")
                    self._is_connected = False
                    return
                
                # Если данные получены успешно, считаем что подключение активно
                self._is_connected = True
                
                # Обновляем состояние только если данные получены корректно
                if len(self._config_bits) >= 16:  # Проверяем, что у нас достаточно битов
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
                    
                    # Детальное логирование конфигурации
                    _LOGGER.error(f"🔧 КОНФИГУРАЦИЯ МОДУЛЯ: dual_group_mode={self._dual_group_mode}, floor_washing={self._floor_washing_mode}, connecting_sensors={self._connecting_wireless_sensors_mode}")
                    _LOGGER.error(f"🚰 СОСТОЯНИЕ ВЕНТИЛЕЙ: first_valve={self._first_group_valve_is_open}, second_valve={self._second_group_valve_is_open}")
                    _LOGGER.error(f"⚠️ АВАРИИ: first_group_alarm={self._first_group_alarm}, second_group_alarm={self._second_group_alarm}")
                    _LOGGER.error(f"📡 БЕСПРОВОДНЫЕ СЕНСОРЫ: discharge={self._discharge_wireless_sensors}, lost={self._lost_wireless_sensors}")
                else:
                    _LOGGER.warning(f"Недостаточно битов в конфигурации модуля: получено {len(self._config_bits) if self._config_bits else 0} битов, требуется 16")
                self._config_line_1_2_bits = await self._hub.read_holding_register_bits(NeptunSmartRegisters.input_line_1_2_config, 1)
                
                # Проверяем, что данные получены корректно
                if self._config_line_1_2_bits is not None:
                    self._line_type[1] = bool(self._config_line_1_2_bits[5])
                    self._line_type[2] = bool(self._config_line_1_2_bits[13])
                    self._line_group[1] = BitArray([self._config_line_1_2_bits[6], self._config_line_1_2_bits[
                        7]])._getuint()  # 1 = first group, 2 = second group, 3 = both groups
                    self._line_group[2] = BitArray([self._config_line_1_2_bits[14], self._config_line_1_2_bits[
                        15]])._getuint()  # 1 = first group, 2 = second group, 3 = both groups
                else:
                    _LOGGER.debug("Не удалось получить конфигурационные биты линий 1-2")
                self._config_line_3_4_bits = await self._hub.read_holding_register_bits(NeptunSmartRegisters.input_line_3_4_config, 1)
                
                # Проверяем, что данные получены корректно
                if self._config_line_3_4_bits is not None:
                    self._line_type[3] = bool(self._config_line_3_4_bits[5])
                    self._line_type[4] = bool(self._config_line_3_4_bits[13])
                    self._line_group[3] = BitArray([self._config_line_3_4_bits[6], self._config_line_3_4_bits[
                        7]])._getuint()  # 1 = first group, 2 = second group, 3 = both groups
                    self._line_group[4] = BitArray([self._config_line_3_4_bits[14], self._config_line_3_4_bits[
                        15]])._getuint()  # 1 = first group, 2 = second group, 3 = both groups
                else:
                    _LOGGER.debug("Не удалось получить конфигурационные биты линий 3-4")
                self._status_wired_line_bits = await self._hub.read_holding_register_bits(NeptunSmartRegisters.status_wired_line, 1)
                
                # Проверяем, что данные получены корректно
                if self._status_wired_line_bits is not None:
                    self._line_status[1] = bool(self._status_wired_line_bits[15])
                    self._line_status[2] = bool(self._status_wired_line_bits[14])
                    self._line_status[3] = bool(self._status_wired_line_bits[13])
                    self._line_status[4] = bool(self._status_wired_line_bits[12])
                else:
                    _LOGGER.debug("Не удалось получить статус проводных линий")
                
                self._relay_config_bits = await self._hub.read_holding_register_bits(NeptunSmartRegisters.relay_config, 1)
                
                # Проверяем, что данные получены корректно
                if self._relay_config_bits is not None:
                    self._switch_when_close_valve = BitArray([self._relay_config_bits[12], self._relay_config_bits[13]])._getuint()
                    self._switch_when_alert = BitArray([self._relay_config_bits[14], self._relay_config_bits[15]])._getuint()
                else:
                    _LOGGER.debug("Не удалось получить конфигурацию реле")
                
                self._wireless_sensors_connected = await self._hub.read_holding_register_uint16(
                    NeptunSmartRegisters.count_of_connected_wireless_sensors, 1)
                
                # Проверяем, что данные получены корректно
                if self._wireless_sensors_connected is None:
                    _LOGGER.debug("Не удалось получить количество подключенных беспроводных датчиков")
                    self._wireless_sensors_connected = 0
                else:
                    _LOGGER.error(f"📊 ПОДКЛЮЧЕНО БЕСПРОВОДНЫХ СЕНСОРОВ: {self._wireless_sensors_connected}")
        except TimeoutError:
            _LOGGER.debug(f"Polling timed out for {self._name}")
            # Сбрасываем счетчик попыток, чтобы попробовать переподключиться в следующий раз
            self._connection_attempts = 0
            self._is_connected = False
            return
        except ModbusIOException as value_error:
            _LOGGER.debug(f"ModbusIOException for {self._name}: {value_error.string}")
            # Сбрасываем счетчик попыток, чтобы попробовать переподключиться в следующий раз
            self._connection_attempts = 0
            self._is_connected = False
            return
        except ModbusException as value_error:
            _LOGGER.debug(f"ModbusException for {self._name}: {value_error.string}")
            # Сбрасываем счетчик попыток, чтобы попробовать переподключиться в следующий раз
            self._connection_attempts = 0
            self._is_connected = False
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exceptions")
            return
        for sensor in self.wireless_sensors:
            await sensor.update()
        for counter in self.counters:
            await counter.update()

    def get_discharge_wireless_sensors(self)-> bool:
        return self._discharge_wireless_sensors

    def get_lost_wireless_sensors(self)-> bool:
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

    async def write_config_register(self):
        try:
            async with async_timeout.timeout(5):
                await self._hub.write_holding_register_bits(NeptunSmartRegisters.module_config, self._config_bits)
        except TimeoutError:
            _LOGGER.warning("Pulling timed out")
            return
        except ModbusException as value_error:
            _LOGGER.warning(f"Error write config register, modbus Exception {value_error.string}")
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exceptions")
            return
    async def set_first_group_valve_state(self,state):
        self._first_group_valve_is_open = state
        self._config_bits[7] = int(state)
        await self.write_config_register()

    def get_second_group_valve_state(self):
        return self._second_group_valve_is_open

    async def set_second_group_valve_state(self,state):
        self._second_group_valve_is_open = state
        self._config_bits[6] = int(state)
        await self.write_config_register()

    def get_floor_washing_mode(self):
        return self._floor_washing_mode

    async def set_floor_washing_mode(self, state):
        self._floor_washing_mode = state
        self._config_bits[15] = int(state)
        await self.write_config_register()

    def get_connecting_wireless_sensors_mode(self):
        return self._connecting_wireless_sensors_mode

    async def set_connecting_wireless_sensors_mode(self,state):
        self._connecting_wireless_sensors_mode = state
        self._config_bits[8] = int(state)
        await self.write_config_register()

    def get_dual_group_mode(self):
        return self._dual_group_mode
    
    def is_connected(self):
        """Возвращает состояние подключения к устройству"""
        return self._is_connected

    async def set_dual_group_mode(self,state):
        self._dual_group_mode = state
        self._config_bits[5] = int(state)
        await self.write_config_register()
        #прописываем везде обе зоны
        for i in (1, 2, 3, 4):
            await self.set_line_group(i, 3)
        for sensor in self.wireless_sensors:
            await sensor.set_group_config(3)

    def get_close_valve_when_lost_sensors_mode(self):
        return self._close_valve_when_loss_sensor

    async def set_close_valve_when_lost_sensors_mode(self,state):
        self._close_valve_when_loss_sensor = state
        self._config_bits[4] = int(state)
        await self.write_config_register()

    def get_lock_buttons(self):
        return self._lock_buttons

    async def set_lock_buttons(self,state):
        self._lock_buttons = state
        self._config_bits[3] = int(state)
        await self.write_config_register()

    def get_line_config_type(self, line_number):
        return self._line_type[line_number]

    async def set_line_type(self, line_number, state):
        self._line_type[line_number] = state
        self._set_bit_to_line_type()
        await self.write_line_config_register()

    def get_line_group(self, line_number):
        return self._line_group[line_number]

    async def set_line_group(self, line_number, state):
        # 1 = first group, 2 = second group, 3 = both groups
        self._line_group[line_number] = state
        if line_number == 1:
            await self._set_bit_to_line_1_2_group(line_number, 6, 7)
        if line_number == 2:
            await self._set_bit_to_line_1_2_group(line_number, 14, 15)
        if line_number == 3:
            await self._set_bit_to_line_3_4_group(line_number, 6, 7)
        if line_number == 4:
            await self._set_bit_to_line_3_4_group(line_number, 14, 15)
        await self.write_line_config_register()

    async def _set_bit_to_line_1_2_group(self, line_number, bit1, bit2):
        if self._line_group[line_number] == 1:
            self._config_line_1_2_bits[bit1] = 0
            self._config_line_1_2_bits[bit2] = 1
        elif self._line_group[line_number] == 2:
            self._config_line_1_2_bits[bit1] = 1
            self._config_line_1_2_bits[bit2] = 0
        else:
            self._config_line_1_2_bits[bit1] = 1
            self._config_line_1_2_bits[bit2] = 1

    async def _set_bit_to_line_3_4_group(self, line_number, bit1, bit2):
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

    async def write_line_config_register(self):
        # self._hub.connect()
        try:
            async with async_timeout.timeout(5):
                await self._hub.write_holding_register_bits(NeptunSmartRegisters.input_line_1_2_config, self._config_line_1_2_bits)
                await self._hub.write_holding_register_bits(NeptunSmartRegisters.input_line_3_4_config, self._config_line_3_4_bits)
        except TimeoutError:
            _LOGGER.warning("Pulling timed out")
            return
        except ModbusException as value_error:
            _LOGGER.warning(f"Error write line config register, modbus Exception {value_error.string}")
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exceptions")
            return
        # self._hub.disconnect()

    def get_line_status(self, line_number):
        return self._line_status[line_number]

    def get_relay_config_valve(self) -> int:
        return int(self._switch_when_close_valve)

    async def set_relay_config_valve(self, state):
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
        await self._write_relay_config_register()

    async def _write_relay_config_register(self):
        try:
            async with async_timeout.timeout(5):
                await self._hub.write_holding_register_bits(NeptunSmartRegisters.relay_config, self._relay_config_bits)
        except TimeoutError:
            _LOGGER.warning("Pulling timed out")
            return
        except ModbusException as value_error:
            _LOGGER.warning(f"Error write relay config register, modbus Exception {value_error.string}")
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exception")
            return

    def get_relay_config_alert(self) -> int:
        return int(self._switch_when_alert)

    async def set_relay_config_alert(self, state):
        self._switch_when_alert = state
        if self._switch_when_alert == 0:
            self._relay_config_bits[14] = 0
            self._relay_config_bits[15] = 0
        elif self._switch_when_alert == 1:
            self._relay_config_bits[14] = 0
            self._relay_config_bits[15] = 1
        elif self._switch_when_alert == 2:
            self._relay_config_bits[14] = 1
            self._relay_config_bits[15] = 0
        else:
            self._relay_config_bits[14] = 1
            self._relay_config_bits[15] = 3
        await self._write_relay_config_register()


class WirelessSensor():
    def __init__(self, hub: modbus_hub, address_config, address_value, config, status_bits):
        self._hub = hub
        self._address_config = address_config
        self._address_value = address_value #получаем адреса, запрашиавем данные, получаем уникальные идентификаторы
        self.update_data(config, status_bits)

    async def update(self):
        try:
            async with async_timeout.timeout(5):
                wireless_sensor_config = await self._hub.read_holding_register_uint16(
                    self._address_config, 1)
                wireless_sensor_status_bits = await self._hub.read_holding_register_bits(
                    self._address_value, 1)
                self.update_data(wireless_sensor_config, wireless_sensor_status_bits)
        except TimeoutError:
            _LOGGER.warning("Polling WirelessSensor status timed out")
            return
        except ModbusException as value_error:
            _LOGGER.error(f"Error update wireless sensor {self._address_config} modbus Exception {value_error.string}")
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exception")
            return
        except BaseException:
            _LOGGER.error("All Exceptions")
            return

    def update_data(self, config, status_bits):
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

    async def set_group_config(self, config):
        try:
            async with async_timeout.timeout(5):
                await self._hub.write_holding_register(address=self._address_config, value=config)
        except TimeoutError:
            _LOGGER.warning("Pulling timed out")
            return
        except ModbusException as value_error:
            _LOGGER.error(
                f"Error set group wireless sensor {self._address_config} modbus Exception {value_error.string}")
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exception")
            return

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

    async def update(self):
        try:
            async with async_timeout.timeout(5):
                result = await self._hub.read_holding_register_uint32(self._address, 2)
                if result is not None:
                    self._value = result
        except TimeoutError:
            _LOGGER.warning("Pulling timed out")
            return
        except ModbusException as value_error:
            _LOGGER.warning(f"Error update counter {self._address} modbus Exception {value_error.string}")
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exception")
            return
        except BaseException:
            _LOGGER.error("All Exceptions")
            return

    def get_value(self):
        return self._value

    def get_address(self):
        return self._address
