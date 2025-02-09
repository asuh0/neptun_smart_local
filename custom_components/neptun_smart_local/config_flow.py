
from __future__ import annotations

import logging
from typing import Any, Optional

from pymodbus.client import  AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException
import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN
from .registers import NeptunSmartRegisters
_LOGGER = logging.getLogger(__name__)
STEP_TCP_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("name", default="Neptun_Smart"): str,
        vol.Required("host_ip"): str,
        vol.Required("host_port", default="503"): str,
    }
)

async def async_validate_device( port, address: str | None) -> None:
    client = AsyncModbusTcpClient(
        address,
        port=port,
    )
    try:
        await client.connect()
        result = await client.read_holding_registers(
            address=NeptunSmartRegisters.module_config, count=1 ,slave=240 #, slave=int(unit_id)
        )
    except ModbusException as value_error:
        client.close()
        raise ValueError("cannot_connect") from value_error
    if hasattr(result, "message"):
        client.close()
        raise ValueError("invalid_response")
    if len(result.registers) == 0:
        client.close()
        raise ValueError("invalid_response")
    client.close()


class NeptunSmartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    data: Optional[dict(str, Any)]

    async def async_step_user(self, user_input: Optional[dict(str, Any)] = None):
        """Invoke when a user initiates a flow via the user interface."""
        return await self.async_step_tcp(user_input)



    async def async_step_tcp(self, user_input: Optional[dict(str, Any)] = None):
        """Configure ModBus TCP entry."""
        errors: dict(str, str) = {}

        if user_input is not None:
            try:
                await async_validate_device(
                    user_input["host_port"],
                    user_input["host_ip"],
                )
            except ValueError as error:
                errors["base"] = str(error)
            if not errors:
                # Input is valid, set data.
                self.data = user_input
                return self.async_create_entry(title=user_input["name"], data=self.data)
        return self.async_show_form(
            step_id="tcp", data_schema=STEP_TCP_DATA_SCHEMA, errors=errors
        )

