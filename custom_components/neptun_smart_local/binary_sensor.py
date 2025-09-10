from __future__ import annotations

from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
)
from . import NeptunSmart
from .device import WirelessSensor
import json
import os
SCAN_INTERVAL = timedelta(seconds=10)

def get_integration_version():
    """Получает версию интеграции из manifest.json"""
    try:
        # Получаем путь к директории текущего модуля
        current_dir = os.path.dirname(os.path.abspath(__file__))
        manifest_path = os.path.join(current_dir, "manifest.json")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            return manifest.get("version", "unknown")
    except Exception:
        return "unknown"


async def async_setup_entry(HomeAssistant, config_entry, async_add_entities):
    device: NeptunSmart = HomeAssistant.data[DOMAIN][config_entry.entry_id]
    binary_sensors = []
    binary_sensors.append(MainModule(device=device))
    binary_sensors.append(FirstGroupModuleAlert(device))
    if device.get_dual_group_mode():
        binary_sensors.append(SecondGroupModuleAlert(device))
    binary_sensors.append(DischargeWirelessSensors(device))
    binary_sensors.append(LostWirelessSensors(device))
    for i in 1, 2, 3, 4:
        binary_sensors.append(WiredLineAlertStatus(device=device, line_number=i))
    for i in range(0, device.get_number_of_connected_wireless_sensors()):
        binary_sensors.append(WirelessSensorAlertStatus(device, i+1, device.wireless_sensors[i]))
        binary_sensors.append(WirelessSensorDischargeStatus(device, i + 1, device.wireless_sensors[i]))
        binary_sensors.append(WirelessSensorLostStatus(device, i + 1, device.wireless_sensors[i]))
    async_add_entities(binary_sensors, update_before_add=True)


class MainModule(BinarySensorEntity):
    """Основной модуль - общая авария системы"""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, device: NeptunSmart):
        self._device = device
        if (self._device.get_first_group_alarm()) | (self._device.get_second_group_alarm()):
            self._is_on = True
        else:
            self._is_on = False
        # Уникальный идентификатор
        self._attr_unique_id = self._device.get_name()
        # Отображаемое имя
        self._attr_name = self._device.get_name()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())},
            "name": self._device.get_name(),
            "sw_version": get_integration_version(),
            "model": "Neptun Smart",
            "manufacturer": "Teploluxe",
        }

    @property
    def icon(self):
        # Простая иконка для HomeKit
        return "mdi:water-pump"

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_update(self) -> None:
        await self._device.update()
        if (self._device.get_first_group_alarm()) | (self._device.get_second_group_alarm()):
            self._is_on = True
        else:
            self._is_on = False


class FirstGroupModuleAlert(BinarySensorEntity):
    """Авария первой группы - датчик протечки воды"""

    _attr_device_class = BinarySensorDeviceClass.MOISTURE

    def __init__(self, device: NeptunSmart):
        self._device = device
        # Уникальный идентификатор
        self._attr_unique_id = f"{device.get_name()}_first_group_alarm_module_alert"
        # Отображаемое имя
        self._attr_name = "First group water leak"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._device.get_name())}}

    @property
    def icon(self):
        # Простая иконка для HomeKit
        return "mdi:water"

    @property
    def is_on(self) -> bool:
        return self._device.get_first_group_alarm()


class SecondGroupModuleAlert(BinarySensorEntity):
    """Авария второй группы - датчик протечки воды"""

    _attr_device_class = BinarySensorDeviceClass.MOISTURE

    def __init__(self, device: NeptunSmart):
        self._device = device
        # Уникальный идентификатор
        self._attr_unique_id = f"{device.get_name()}_second_group_alarm_module_alert"
        # Отображаемое имя
        self._attr_name = "Second group water leak"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._device.get_name())}}

    @property
    def icon(self):
        # Простая иконка для HomeKit
        return "mdi:water"

    @property
    def is_on(self) -> bool:
        return self._device.get_second_group_alarm()

    async def async_update(self) -> None:
        self._attr_available = self._device.get_dual_group_mode()


class DischargeWirelessSensors(BinarySensorEntity):
    """Разряд беспроводных датчиков"""

    _attr_device_class = BinarySensorDeviceClass.BATTERY

    def __init__(self, device: NeptunSmart):
        self._device = device
        # Уникальный идентификатор
        self._attr_unique_id = f"{device.get_name()}_discharge_wireless_sensors"
        # Отображаемое имя
        self._attr_name = "Wireless sensors battery low"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._device.get_name())}}

    @property
    def icon(self):
        # Простая иконка для HomeKit
        return "mdi:battery"

    @property
    def is_on(self) -> bool:
        return self._device.get_discharge_wireless_sensors()


class LostWirelessSensors(BinarySensorEntity):
    """Потеря связи с беспроводными датчиками"""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, device: NeptunSmart):
        self._device = device
        # Уникальный идентификатор
        self._attr_unique_id = f"{device.get_name()}_lost_wireless_sensors"
        # Отображаемое имя
        self._attr_name = "Wireless sensors connection lost"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._device.get_name())}}

    @property
    def icon(self):
        # Простая иконка для HomeKit
        return "mdi:wifi"

    @property
    def is_on(self) -> bool:
        return self._device.get_lost_wireless_sensors()


class WiredLineAlertStatus(BinarySensorEntity):
    """Статус аварии проводных линий"""

    _attr_device_class = BinarySensorDeviceClass.MOISTURE

    def __init__(self, device: NeptunSmart, line_number):
        self._device = device
        self._line_number = line_number
        # Уникальный идентификатор
        self._attr_unique_id = f"{device.get_name()}_WiredAlertStatus_line{line_number}"
        # Отображаемое имя
        self._attr_name = f"Wired line {line_number} water leak"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._device.get_name())}}

    @property
    def icon(self):
        # Простая иконка для HomeKit
        return "mdi:water"

    @property
    def is_on(self) -> bool:
        return self._device.get_line_status(line_number=self._line_number)


class WirelessSensorAlertStatus(BinarySensorEntity):
    """Статус аварии беспроводного датчика"""

    _attr_device_class = BinarySensorDeviceClass.MOISTURE

    def __init__(self, device: NeptunSmart, sensor_number, sensor: WirelessSensor):
        self._device = device
        self._sensor_number = sensor_number
        self._sensor = sensor
        # Уникальный идентификатор
        self._attr_unique_id = f"{device.get_name()}_WirelessAlertStatus_sensor{sensor_number}"
        # Отображаемое имя
        self._attr_name = f"Wireless sensor {sensor_number} water leak"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._device.get_name())}}

    @property
    def icon(self):
        # Простая иконка для HomeKit
        return "mdi:water"

    @property
    def is_on(self) -> bool:
        return self._sensor.get_alert_status()


class WirelessSensorDischargeStatus(BinarySensorEntity):
    """Статус разряда беспроводного датчика"""

    _attr_device_class = BinarySensorDeviceClass.BATTERY

    def __init__(self, device: NeptunSmart, sensor_number, sensor: WirelessSensor):
        self._device = device
        self._sensor_number = sensor_number
        self._sensor = sensor
        # Уникальный идентификатор
        self._attr_unique_id = f"{device.get_name()}_WirelessDischargeStatus_sensor{sensor_number}"
        # Отображаемое имя
        self._attr_name = f"Wireless sensor {sensor_number} battery low"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._device.get_name())}}

    @property
    def icon(self):
        # Простая иконка для HomeKit
        return "mdi:battery"

    @property
    def is_on(self) -> bool:
        return self._sensor.get_discharge_status()


class WirelessSensorLostStatus(BinarySensorEntity):
    """Статус потери связи с беспроводным датчиком"""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, device: NeptunSmart, sensor_number, sensor: WirelessSensor):
        self._device = device
        self._sensor_number = sensor_number
        self._sensor = sensor
        # Уникальный идентификатор
        self._attr_unique_id = f"{device.get_name()}_WirelessLostStatus_sensor{sensor_number}"
        # Отображаемое имя
        self._attr_name = f"Wireless sensor {sensor_number} connection lost"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._device.get_name())}}

    @property
    def icon(self):
        # Простая иконка для HomeKit
        return "mdi:wifi"

    @property
    def is_on(self) -> bool:
        return self._sensor.get_lost_sensor_status()
