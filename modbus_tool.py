#!/usr/bin/env python3
import argparse
import itertools
import struct
import time
from pymodbus.client import ModbusTcpClient
from pymodbus.pdu import ExceptionResponse
from pymodbus.exceptions import ModbusIOException

# Type mapping configuration: (format_string, byte_count, is_floattype)
TYPE_MAP = {
    'u16': ('>H', 1, False),
    'i16': ('>h', 1, False),
    'u32': ('>I', 2, False),
    'i32': ('>i', 2, False),
    'f32': ('>f', 2, True),
    'u64': ('>Q', 4, False),
    'f64': ('>d', 4, True),
}

def universal_convert(regs, fmt, b_order, w_order, mode='decode', val=None):
    """
    Handles conversion for all types with configurable Endianness.
    """
    # 1. Determine how many bytes we are dealing with
    byte_count = struct.calcsize(fmt)
    
    if mode == 'encode':
        raw_bytes = struct.pack(fmt, val)
    else:
        # Flatten registers into a single byte array
        raw_bytes = b"".join([struct.pack('>H', r) for r in regs])

    # 2. Re-order bytes based on Word/Byte Endianness (for multi-register types)
    # This is a simplified block-swap logic
    if byte_count >= 4:
        # Split into 16-bit chunks (words)
        words = [raw_bytes[i:i+2] for i in range(0, len(raw_bytes), 2)]
        if b_order == 'little':
            words = [w[::-1] for w in words]
        if w_order == 'little':
            words = words[::-1]
        final_bytes = b"".join(words)
    else:
        # Single register (16-bit)
        final_bytes = raw_bytes[::-1] if b_order == 'little' else raw_bytes

    if mode == 'encode':
        # Return as list of 16-bit integers
        return [struct.unpack('>H', final_bytes[i:i+2])[0] for i in range(0, len(final_bytes), 2)]
    
    return struct.unpack(fmt, final_bytes)[0]

def cmd_scan(args):
    client = ModbusTcpClient(args.ip, port=args.port, timeout=args.timeout)
    if not client.connect(): 
        return print(f"[-] Connection failed to {args.ip}")

    fmt, reg_count, is_float = TYPE_MAP[args.type]
    target_ids = [int(i.strip()) for i in args.ids.split(",")]

    print(f"[*] Scanning {args.ip} | Type: {args.type} | IDs: {target_ids}")

    for d_id in target_ids:
        for reg in range(args.start, args.end + 1):
            for func_name, func in [("HR", client.read_holding_registers), ("IR", client.read_input_registers)]:
                try:
                    res = func(address=reg, count=reg_count, slave=d_id)
                    if res is None or isinstance(res, (ExceptionResponse, ModbusIOException)):
                        continue
                    
                    # For multi-register types, we brute force word/byte orders
                    # For u16/i16, we only check byte order
                    orders = itertools.product(['big', 'little'], repeat=2) if reg_count > 1 else [('big', 'na'), ('little', 'na')]
                    
                    for b, w in orders:
                        try:
                            val = universal_convert(res.registers, fmt, b, w)
                            
                            # Filter logic
                            if args.min <= (val if not is_float else abs(val)) <= args.max:
                                order_str = f"{b}/{w}" if reg_count > 1 else f"{b}"
                                print(f"[FOUND {func_name}] ID {d_id} | Reg {reg} -> {val} ({order_str})")
                        except: continue
                    
                    time.sleep(args.delay)
                except: continue
    client.close()

def cmd_write(args):
    client = ModbusTcpClient(args.ip, port=args.port, timeout=args.timeout)
    if not client.connect(): return
    fmt, reg_count, _ = TYPE_MAP[args.type]
    try:
        regs = universal_convert(None, fmt, args.bo, args.wo, mode='encode', val=args.val)
        res = client.write_registers(address=args.reg, values=regs, slave=args.id)
        print(f"[+] Write {'Success' if not isinstance(res, ExceptionResponse) else 'Failed'}")
    except Exception as e: print(f"[-] Error: {e}")
    finally: client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="modbus_tool")
    sub = parser.add_subparsers(dest="command", required=True)
    
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--ip", required=True)
    parent.add_argument("--port", type=int, default=502)
    parent.add_argument("--timeout", type=int, default=3)
    parent.add_argument("--type", choices=TYPE_MAP.keys(), default='f32', help="Data type: u16, i16, u32, i32, f32, u64, f64")

    s = sub.add_parser("scan", parents=[parent])
    s.add_argument("--start", type=int, default=0)
    s.add_argument("--end", type=int, default=30)
    s.add_argument("--ids", type=str, default="1")
    s.add_argument("--min", type=float, default=-1000000)
    s.add_argument("--max", type=float, default=1000000)
    s.add_argument("--delay", type=float, default=0.01)

    w = sub.add_parser("write", parents=[parent])
    w.add_argument("--reg", type=int, required=True)
    w.add_argument("--val", type=float, required=True)
    w.add_argument("--id", type=int, default=1)
    w.add_argument("--bo", choices=['big', 'little'], default='big')
    w.add_argument("--wo", choices=['big', 'little'], default='little')

    args = parser.parse_args()
    if args.command == "scan": cmd_scan(args)
    elif args.command == "write": cmd_write(args)