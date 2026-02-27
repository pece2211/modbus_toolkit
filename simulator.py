#!/usr/bin/env python3
import argparse
import struct
import sys

# Modern Pymodbus 3.12.1+ imports
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
# In 3.12.1, SlaveContext is often renamed to DeviceContext
try:
    from pymodbus.datastore import ModbusDeviceContext as ModbusSlaveContext
    from pymodbus.datastore import ModbusServerContext
except ImportError:
    # Fallback for other 3.x sub-versions
    from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

def float_to_registers(value, byte_order, word_order):
    """Converts a float to two 16-bit registers with specific endianness."""
    raw = struct.pack('>f', value)
    b1, b2, b3, b4 = raw

    if byte_order == 'big' and word_order == 'big':
        ordered = [b1, b2, b3, b4]
    elif byte_order == 'big' and word_order == 'little':
        ordered = [b3, b4, b1, b2]
    elif byte_order == 'little' and word_order == 'big':
        ordered = [b2, b1, b4, b3]
    else: # little/little
        ordered = [b4, b3, b2, b1]

    reg1 = struct.unpack('>H', bytes(ordered[0:2]))[0]
    reg2 = struct.unpack('>H', bytes(ordered[2:4]))[0]
    return [reg1, reg2]

def main():
    parser = argparse.ArgumentParser(description="Pymodbus 3.12.1 Simulator")
    parser.add_argument("--port", type=int, default=5020)
    parser.add_argument("--val", type=float, default=36.5)
    parser.add_argument("--bo", choices=['big', 'little'], default='big')
    parser.add_argument("--wo", choices=['big', 'little'], default='little')
    
    args = parser.parse_args()

    # Fill datastore
    registers = [0] * 100
    encoded_val = float_to_registers(args.val, args.bo, args.wo)
    
    # Place at Register 10
    registers[10] = encoded_val[0]
    registers[11] = encoded_val[1]

    print(f"[*] Starting Simulator on 127.0.0.1:{args.port}")
    print(f"[*] Value: {args.val} at Reg 10 | Byte:{args.bo} | Word:{args.wo}")

    # Note: hr = Holding Registers, ir = Input Registers
    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, registers),
        ir=ModbusSequentialDataBlock(0, registers)
    )
    
    # single=True makes the server ignore Slave ID and always return 'store'
    context = ModbusServerContext(devices=store, single=True)

    try:
        # Pymodbus 3.x uses 'address' as a tuple (ip, port)
        StartTcpServer(context=context, address=("127.0.0.1", args.port))
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    main()