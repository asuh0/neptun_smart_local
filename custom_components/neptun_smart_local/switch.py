from __future__ import annotations

from datetime import timedelta

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from . import NeptunSmart
from .const import DOMAIN
SCAN_INTERVAL = timedelta(seconds=5)
async def async_setup_entry(HomeAssistant, config_entry, async_add_entities):
    """Set up the switch platform."""
    import logging
    _LOGGER = logging.getLogger(__name__)
    
    device: NeptunSmart = HomeAssistant.data[DOMAIN][config_entry.entry_id]
    switches = []
    switches.append(Valve_1_zone(device))
    
    dual_mode = device.get_dual_group_mode()
    _LOGGER.error(f"🔧 НАСТРОЙКА ПЕРЕКЛЮЧАТЕЛЕЙ: dual_group_mode={dual_mode}")
    
    if dual_mode:
        switches.append(Valve_2_zone(device))
        _LOGGER.error("✅ ДОБАВЛЕН ВТОРОЙ ВЕНТИЛЬ (Valve_2_zone)")
    else:
        _LOGGER.error("❌ ВТОРОЙ ВЕНТИЛЬ НЕ ДОБАВЛЕН - dual_group_mode ОТКЛЮЧЕН")
        
    switches.append(Floor_washing_mode(device=device))
    switches.append(Connecting_wireless_sensors_mode(device))
    switches.append(Dual_group_mode(device))
    switches.append((Close_valve_when_lost_sensors_mode(device)))
    switches.append(Lock_buttons(device))
    
    _LOGGER.error(f"📊 СОЗДАНО {len(switches)} ПЕРЕКЛЮЧАТЕЛЕЙ")
    async_add_entities(switches, update_before_add=False)


class Valve_1_zone(SwitchEntity):
    def __init__(self, device: NeptunSmart):
        self._device = device
        self._attr_name = "Valve First Zone"
        self._attr_unique_id = f"{device.get_name()}_Valve_1_zone"
        self._attr_is_on = self._device.get_first_group_valve_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False
        await self._device.set_first_group_valve_state(False)
        if not self._device.get_dual_group_mode():
            await self._device.set_second_group_valve_state(False)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._attr_is_on = True
        await self._device.set_first_group_valve_state(True)
        if not self._device.get_dual_group_mode():
            await self._device.set_second_group_valve_state(True)

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        self._attr_is_on = self._device.get_first_group_valve_state()
        self._attr_available = self._device.is_connected()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    @property
    def icon(self):
        return "mdi:pipe-valve"


class Valve_2_zone(SwitchEntity):
    def __init__(self, device: NeptunSmart):
        self._device = device
        self._attr_name = "Valve Second Zone"
        self._attr_unique_id = f"{device.get_name()}_Valve_2_zone"
        self._attr_is_on = self._device.get_second_group_valve_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False
        await self._device.set_second_group_valve_state(False)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._attr_is_on = True
        await self._device.set_second_group_valve_state(True)

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        self._attr_is_on = self._device.get_second_group_valve_state()
        # Вентиль доступен только при подключении к устройству
        self._attr_available = self._device.is_connected()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    @property
    def icon(self):
        return "mdi:pipe-valve"



class Floor_washing_mode(SwitchEntity):
    def __init__(self, device: NeptunSmart):
        self._device = device
        self._attr_name = "Floor Washing Mode"
        self._attr_unique_id = f"{device.get_name()}_Floor_washing_mode"
        self._attr_is_on = self._device.get_floor_washing_mode()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False
        await self._device.set_floor_washing_mode(False)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._attr_is_on = True
        await self._device.set_floor_washing_mode(True)

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        self._attr_is_on = self._device.get_floor_washing_mode()
        self._attr_available = self._device.is_connected()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    @property
    def icon(self):
        if self._device.get_floor_washing_mode():
            return "mdi:pail"
        else:
            return "mdi:pail-off"


class Connecting_wireless_sensors_mode(SwitchEntity):
    def __init__(self,device:NeptunSmart):
        self._device = device
        self._attr_name = "Connecting wireless sensors mode"
        self._attr_unique_id = f"{device.get_name()}_Connecting_wireless_sensors_mode"
        self._attr_is_on = self._device.get_connecting_wireless_sensors_mode()
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False
        await self._device.set_connecting_wireless_sensors_mode(False)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._attr_is_on = True
        await self._device.set_connecting_wireless_sensors_mode(True)

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        self._attr_is_on = self._device.get_connecting_wireless_sensors_mode()
        self._attr_available = self._device.is_connected()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    @property
    def icon(self):
        if self._device.get_connecting_wireless_sensors_mode():
            return "mdi:router-wireless"
        else:
            return "mdi:router-wireless-off"


class Dual_group_mode(SwitchEntity):
    def __init__(self, device: NeptunSmart):
        self._device = device
        self._attr_name = "Dual group mode"
        self._attr_unique_id = f"{device.get_name()}_dual_group_mode"
        self._attr_is_on = self._device.get_dual_group_mode()
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False
        await self._device.set_dual_group_mode(False)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._attr_is_on = True
        await self._device.set_dual_group_mode(True)

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        self._attr_is_on = self._device.get_dual_group_mode()
        self._attr_available = self._device.is_connected()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    @property
    def icon(self):
        if self._device.get_dual_group_mode():
            return "mdi:numeric-2-circle-outline"
        else:
            return "mdi:numeric-1-circle-outline"


class Close_valve_when_lost_sensors_mode(SwitchEntity):
    def __init__(self, device: NeptunSmart):
        self._device = device
        self._attr_name = "Close valve when lost sensors"
        self._attr_unique_id = f"{device.get_name()}_Close_valve_when_lost_sensors_mode"
        self._attr_is_on = self._device.get_close_valve_when_lost_sensors_mode()
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False
        await self._device.set_close_valve_when_lost_sensors_mode(False)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._attr_is_on = True
        await self._device.set_close_valve_when_lost_sensors_mode(True)

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        self._attr_is_on = self._device.get_close_valve_when_lost_sensors_mode()
        self._attr_available = self._device.is_connected()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    @property
    def icon(self):
       return "mdi:pipe-valve"


class Lock_buttons(SwitchEntity):
    def __init__(self, device: NeptunSmart):
        self._device = device
        self._attr_name = "Lock Buttons"
        self._attr_unique_id = f"{device.get_name()}_Lock_buttons"
        self._attr_is_on = self._device.get_lock_buttons()
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False
        await self._device.set_lock_buttons(False)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._attr_is_on = True
        await self._device.set_lock_buttons(True)

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        self._attr_is_on = self._device.get_lock_buttons()
        self._attr_available = self._device.is_connected()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    @property
    def icon(self):
        if self._device.get_lock_buttons():
            return "mdi:keyboard-off-outline"
        else:
            return "mdi:keyboard-close-outline"
