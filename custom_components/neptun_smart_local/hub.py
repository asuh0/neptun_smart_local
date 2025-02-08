from __future__ import annotations

import datetime
from pymodbus import ModbusException
from pymodbus.client import ModbusTcpClient
from pymodbus.framer import FramerType


class modbus_hub:
    def __init__(self,host,port) -> None:
        self._client = ModbusTcpClient(
            host=host,
            port=port,
            framer=FramerType.SOCKET,
            retries=3,
            timeout=3,
        )

    def connect(self):
        try:
            self._client.connect()
        except ModbusException as value_error:
            self._client.close()
            raise ValueError("cannot_connect") from value_error

    def disconnect(self):
        self._client.close()

    def read_holding_register_uint16(self, address, count):
        result_reg = self._client.read_holding_registers(
            address=address, count=count, slave=240)
        result = self._client.convert_from_registers(result_reg.registers, data_type=self._client.DATATYPE.UINT16)
        return result

    def read_holding_register_uint32(self, address, count):
        result_reg = self._client.read_holding_registers(
            address=address, count=count, slave=240)
        result = self._client.convert_from_registers(result_reg.registers, data_type=self._client.DATATYPE.UINT32)
        return result

    def read_holding_register_bits(self, address, count):
        result_reg = self._client.read_holding_registers(
            address=address, count=count, slave=240)
        uint = self._client.convert_from_registers(result_reg.registers, data_type=self._client.DATATYPE.UINT16)
        bitlist = [int(x) for x in bin(uint)[2:]]
        while len(bitlist) < 16:
            bitlist.insert(0, 0)
        return bitlist

    def write_holding_register_bits(self, address, bits) ->None:
        value = 0
        for bit in bits:
            value = (value << 1) | bit
        self._client.write_register(address=address, value=value, slave=240)

    def write_holding_register(self, address, value) ->None:
        self._client.write_register(address=address, value=value, slave=240)
