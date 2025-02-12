from __future__ import annotations

from collections import namedtuple
from datetime import timedelta

from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfVolume
from .const import DOMAIN
from .device import NeptunSmart, WirelessSensor, Counter

SCAN_INTERVAL = timedelta(seconds=5)
async def async_setup_entry(HomeAssistant, config_entry, async_add_entities):
    device:NeptunSmart = HomeAssistant.data[DOMAIN][config_entry.entry_id]
    sensors = []
    sensors.append(WirelessSensorsConnected(device=device))
    for i in range (0, device.get_number_of_connected_wireless_sensors()):
        sensors.append(WirelessSensorsBatteryLevel(device, i+1, device.wireless_sensors[i]))
        sensors.append(WirelessSensorsSignalLevel(device, i+1, device.wireless_sensors[i]))
    for counter in device.counters:
        sensors.append(CounterSensor(device,counter))
    async_add_entities(sensors, update_before_add=False)
class WirelessSensorsConnected(SensorEntity):
    def __init__(self, device: NeptunSmart):
        self._device = device
        self._attr_unique_id = f"{device.get_name()}_Wireless_sensors_connected"
        self._attr_name = "Connected wireless sensors"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = self._device.get_number_of_connected_wireless_sensors()

    async def async_update(self) -> None:
        self._attr_native_value = self._device.get_number_of_connected_wireless_sensors()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    @property
    def icon(self):
        return "mdi:sun-wireless-outline"


class WirelessSensorsBatteryLevel(SensorEntity):
    def __init__(self, device: NeptunSmart, sensor_number, sensor: WirelessSensor):
        self._device = device
        self._sensor_number = sensor_number
        self._sensor = sensor
        self._attr_unique_id = f"{device.get_name()}_WirelessSensors{sensor_number}BatteryLevel"
        self._attr_name = f"Wireless sensor {sensor_number} battery level"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = self._sensor.get_battery_level()

    async def async_update(self) -> None:
        self._attr_native_value = self._sensor.get_battery_level()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    @property
    def icon(self):
        return "mdi:battery-high"


class WirelessSensorsSignalLevel(SensorEntity):
    def __init__(self,device: NeptunSmart, sensor_number, sensor: WirelessSensor):
        self._device = device
        self._sensor_number = sensor_number
        self._sensor = sensor
        self._attr_unique_id = f"{device.get_name()}_WirelessSensors{sensor_number}SignalLevel"
        self._attr_name = f"Wireless sensor {sensor_number} signal level"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = self._sensor.get_signal_level()

    async def async_update(self) -> None:
        self._attr_native_value = self._sensor.get_signal_level()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    @property
    def icon(self):
        return "mdi:signal"


class CounterSensor(SensorEntity):
    def __init__(self, device: NeptunSmart, counter: Counter):
        self._device = device
        self._counter = counter
        self._attr_unique_id = f"{device.get_name()}_Counter{counter.get_address()}"
        self._attr_name = f"Counter {counter.get_address()}"
        self._attr_native_value = self._counter.get_value()/1000
        self._attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
        self._attr_device_class = SensorDeviceClass.WATER
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    async def async_update(self) -> None:
        self._attr_native_value = self._counter.get_value()/1000

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    @property
    def icon(self):
        return "mdi:counter"

