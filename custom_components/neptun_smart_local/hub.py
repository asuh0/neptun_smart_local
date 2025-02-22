from __future__ import annotations
from pymodbus import pymodbus_apply_logging_config
import datetime
# from pymodbus import ModbusException
# from pymodbus.client import ModbusTcpClient, AsyncModbusTcpClient
# from pymodbus.framer import FramerType
from homeassistant.components.modbus import modbus
from homeassistant.core import HomeAssistant
import logging

from pymodbus import FramerType
from pymodbus.client import AsyncModbusTcpClient

_LOGGER = logging.getLogger(__name__)
# pymodbus_apply_logging_config("DEBUG")

class modbus_hub:
    def __init__(self, hass: HomeAssistant, host, port) -> None:
        self._host = host
        self._port = port
        self._hass = hass
        self._client = AsyncModbusTcpClient(
            host=host,
            port=port,
            framer=FramerType.SOCKET,
            retries=3,
            timeout=3,
        )
        self._client_config = {
            "name": "NameNeptunSmart",
            "type": "tcp",
            "delay": 0,
            "port": self._port,
            "timeout": 3,
            "host": self._host,
        }
        self._modbus = modbus.ModbusHub(self._hass, self._client_config)

    async def connect(self):
        success = await self._modbus.async_setup()
        if success:
            _LOGGER.debug("Modbus has been setup")
        else:
            await self._modbus.async_close()
            _LOGGER.error("Modbus setup was unsuccessful")
            raise ValueError("Modbus setup was unsuccessful")

    async def disconnect(self):
        await self._modbus.async_close()

    async def read_holding_register_uint16(self, address, count):
        result_reg = await self._modbus.async_pb_call(
            240, address, 1, "holding"
        )
        result = None
        if result_reg is not None:
            result = int.from_bytes(
                result_reg.registers[0].to_bytes(2, "little", signed=False),
                "little",
                signed=True,
            )
        return result

    async def read_holding_register_uint32(self, address, count):
        result_reg = await self._modbus.async_pb_call(
            240, address, 2, "holding"
        )
        result = None
        if result_reg is not None:
            result = self._client.convert_from_registers(result_reg.registers, data_type=self._client.DATATYPE.UINT32)
        return result

    async def read_holding_register_bits(self, address, count):
        result_reg = await self._modbus.async_pb_call(
            240, address, 1, "holding"
        )
        if result_reg is not None:
            uint = int.from_bytes(
                result_reg.registers[0].to_bytes(2, "little", signed=False),
                "little",
                signed=True,
            )
            bitlist = [int(x) for x in bin(uint)[2:]]
            while len(bitlist) < 16:
                bitlist.insert(0, 0)
            return bitlist
        return None

    async def write_holding_register_bits(self, address, bits) -> None:
        value = 0
        for bit in bits:
            value = (value << 1) | bit
        await self._modbus.async_pb_call(
            240,
            address,
            value,
            "write_register",
        )

    async def write_holding_register(self, address, value) -> None:
        await self._modbus.async_pb_call(
            240,
            address,
            value,
            "write_register",
        )

