from __future__ import annotations

from datetime import timedelta

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory
from . import NeptunSmart
from .const import DOMAIN

from .device import WirelessSensor
SCAN_INTERVAL = timedelta(seconds=5)
async def async_setup_entry(HomeAssistant, config_entry, async_add_entities):
    device: NeptunSmart = HomeAssistant.data[DOMAIN][config_entry.entry_id]
    selects = []
    for i in 1, 2, 3, 4:
        selects.append(LineTypeConfig(device=device, line_number=i))
        selects.append(LineGroupConfig(device=device, line_number=i))
    selects.append(RelaySwitchWhenCloseValve(device))
    selects.append(RelaySwitchWhenAlert(device))
    for i in range (0, device.get_number_of_connected_wireless_sensors()):
        selects.append(WirelessSensorGroupConfig(device,device.wireless_sensors[i],i+1))
    async_add_entities(selects, update_before_add=False)
class LineTypeConfig(SelectEntity):
    def __init__(self, device: NeptunSmart, line_number):
        self._device = device
        self._line_number = line_number
        self._state = self._device.get_line_config_type(line_number=line_number)      #True = button, False = sensor
        self._attr_unique_id = f"{device.get_name()}_Line_{self._line_number}_config"
        self._attr_name = f"Line {self._line_number} type"
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC
        if self._device.get_line_config_type(line_number=line_number):
            self._attr_current_option = "Button"
        else:
            self._attr_current_option = "Sensor"

    async def async_select_option(self, option: str) -> None:
        if option == "Sensor":
            self._state = False
        else:
            self._state = True
        self._device.set_line_type(self._line_number, self._state)

    @property
    def options(self) -> list[str]:
        """Return options."""
        options = ["Sensor", "Button"]
        return options

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    async def async_update(self) -> None:
        """Fetch new state data for the select."""
        if self._device.get_line_config_type(self._line_number):
            self._attr_current_option = "Button"
        else:
            self._attr_current_option = "Sensor"


class LineGroupConfig(SelectEntity):
    def __init__(self, device: NeptunSmart, line_number):
        self._device = device
        self._line_number = line_number
        self._state = self._device.get_line_group(line_number=line_number)
        self._attr_unique_id = f"{device.get_name()}_Line_{self._line_number}_group_ config"
        self._attr_name = f"Line {self._line_number} group"
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC
        self._state = self._device.get_line_group(line_number=line_number)
        if self._state == 1:
            self._attr_current_option = "First"
        elif self._state == 2:
            self._attr_current_option = "Second"
        else:
            self._attr_current_option = "Both"

    async def async_select_option(self, option: str) -> None:
        if option == "First":
            self._state = 1
        elif option == "Second":
            self._state = 2
        else:
            self._state = 3
        self._device.set_line_group(self._line_number, self._state)

    @property
    def options(self) -> list[str]:
        """Return options."""
        options = ["First", "Second", "Both"]
        return options

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    async def async_update(self) -> None:
        """Fetch new state data for the select."""
        self._state = self._device.get_line_group(line_number=self._line_number)
        if self._state == 1:
            self._attr_current_option = "First"
        elif self._state == 2:
            self._attr_current_option = "Second"
        else:
            self._attr_current_option = "Both"


class RelaySwitchWhenCloseValve(SelectEntity):
    def __init__(self, device: NeptunSmart):
        self._device = device
        self._state = self._device.get_relay_config_valve() #0 - not switch, 1 - first group, 2 - second group, 3 - both group
        self._attr_unique_id = f"{device.get_name()}_RelaySwitchWhenCloseValve_config"
        self._attr_name = f"Switch relay when close valve"
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC
        if self._state == 0:
            self._attr_current_option = "Not Switch"
        elif self._state == 1:
            self._attr_current_option = "First group"
        elif self._state == 2:
            self._attr_current_option = "Second group"
        else:
            self._attr_current_option = "Both group"

    async def async_select_option(self, option: str) -> None:
        if option == "Not Switch":
            self._state = 0
        elif option == "First group":
            self._state = 1
        elif option == "Second group":
            self._state = 2
        else:
            self._state = 3
        self._device.set_relay_config_valve(self._state)

    @property
    def options(self) -> list[str]:
        """Return options."""
        options = ["Not Switch", "First group", "Second group", "Both group"]
        return options

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    async def async_update(self) -> None:
        """Fetch new state data for the select."""
        self._state = self._device.get_relay_config_valve()
        if self._state == 0:
            self._attr_current_option = "Not Switch"
        elif self._state == 1:
            self._attr_current_option = "First group"
        elif self._state == 2:
            self._attr_current_option = "Second group"
        else:
            self._attr_current_option = "Both group"


class RelaySwitchWhenAlert(SelectEntity):
    def __init__(self, device: NeptunSmart):
        self._device = device
        self._state = self._device.get_relay_config_alert() #0 - not switch, 1 - first group, 2 - second group, 3 - both group
        self._attr_unique_id = f"{device.get_name()}_RelaySwitchAlert_config"
        self._attr_name = f"Switch relay when alert"
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC
        if self._state == 0:
            self._attr_current_option = "Not Switch"
        elif self._state == 1:
            self._attr_current_option = "First group"
        elif self._state == 2:
            self._attr_current_option = "Second group"
        else:
            self._attr_current_option = "Both group"

    async def async_select_option(self, option: str) -> None:
        if option == "Not Switch":
            self._state = 0
        elif option == "First group":
            self._state = 1
        elif option == "Second group":
            self._state = 2
        else:
            self._state = 3
        self._device.set_relay_config_alert(self._state)

    @property
    def options(self) -> list[str]:
        """Return options."""
        options = ["Not Switch", "First group", "Second group", "Both group"]
        return options

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    async def async_update(self) -> None:
        """Fetch new state data for the select."""
        self._state = self._device.get_relay_config_alert()
        if self._state == 0:
            self._attr_current_option = "Not Switch"
        elif self._state == 1:
            self._attr_current_option = "First group"
        elif self._state == 2:
            self._attr_current_option = "Second group"
        else:
            self._attr_current_option = "Both group"


class WirelessSensorGroupConfig(SelectEntity):
    def __init__(self, device: NeptunSmart, sensor: WirelessSensor, sensor_number):
        self._device = device
        self._sensor = sensor
        self._sensor_number = sensor_number
        self._attr_unique_id = f"{device.get_name()}_WirelessSensor{self._sensor.get_address()}_group_ config"
        self._attr_name = f"Wireless Sensor {self._sensor_number} group"
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC
        self._state = self._sensor.get_group_config()
        if self._state == 1:
            self._attr_current_option = "First"
        elif self._state == 2:
            self._attr_current_option = "Second"
        else:
            self._attr_current_option = "Both"

    async def async_select_option(self, option: str) -> None:
        if option == "First":
            self._state = 1
        elif option == "Second":
            self._state = 2
        else:
            self._state = 3
        self._sensor.set_group_config(self._state)

    @property
    def options(self) -> list[str]:
        """Return options."""
        options = ["First", "Second", "Both"]
        return options

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    async def async_update(self) -> None:
        """Fetch new state data for the select."""
        self._state = self._sensor.get_group_config()
        if self._state == 1:
            self._attr_current_option = "First"
        elif self._state == 2:
            self._attr_current_option = "Second"
        else:
            self._attr_current_option = "Both"
