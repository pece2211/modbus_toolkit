#!/usr/bin/env python3
import argparse
import itertools
import struct
from pymodbus.client import ModbusTcpClient
from pymodbus.pdu import ExceptionResponse

def convert(regs, b, w, mode='decode', val=None):
    # Standard 32-bit float logic
    if mode == 'encode':
        raw = struct.pack('>f', val)
        b1, b2, b3, b4 = raw
    else:
        b1, b2, b3, b4 = struct.pack('>HH', regs[0], regs[1])
    
    orders = {
        ('big', 'big'): [b1, b2, b3, b4],
        ('big', 'little'): [b3, b4, b1, b2],
        ('little', 'big'): [b2, b1, b4, b3],
        ('little', 'little'): [b4, b3, b2, b1]
    }
    
    ordered = bytes(orders[(b, w)])
    if mode == 'encode':
        return [struct.unpack('>H', ordered[0:2])[0], struct.unpack('>H', ordered[2:4])[0]]
    return struct.unpack('>f', ordered)[0]

def cmd_scan(args):
    client = ModbusTcpClient(args.ip, port=args.port, timeout=1)
    if not client.connect(): return print("[-] Connection failed.")
    
    print(f"[*] Scanning {args.ip}:{args.port} (0-30)...")
    for d_id in [0, 1, 255]:
        for reg in range(31):
            # Try both Holding (HR) and Input (IR) registers
            for func_name, func in [("HR", client.read_holding_registers), ("IR", client.read_input_registers)]:
                res = func(address=reg, count=2, device_id=d_id)
                if isinstance(res, ExceptionResponse) or not hasattr(res, 'registers'): continue
                
                if any(res.registers):
                    for b, w in itertools.product(['big', 'little'], repeat=2):
                        val = convert(res.registers, b, w)
                        if val and abs(val) > 0.001:
                            print(f"[FOUND {func_name}] ID {d_id} | Reg {reg} -> {val:.2f} ({b}/{w})")
    client.close()

def cmd_write(args):
    client = ModbusTcpClient(args.ip, port=args.port)
    if not client.connect(): return
    regs = convert(None, args.bo, args.wo, mode='encode', val=args.val)
    res = client.write_registers(address=args.reg, values=regs, device_id=args.id)
    print("[+] Write successful" if not isinstance(res, ExceptionResponse) else f"[-] Error: {res}")
    client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="modbus_tool")
    sub = parser.add_subparsers(dest="command", required=True)
    
    s = sub.add_parser("scan")
    s.add_argument("--ip", required=True)
    s.add_argument("--port", type=int, default=5020)

    w = sub.add_parser("write")
    w.add_argument("--ip", required=True)
    w.add_argument("--reg", type=int, required=True)
    w.add_argument("--val", type=float, required=True)
    w.add_argument("--id", type=int, default=1)
    w.add_argument("--bo", choices=['big', 'little'], default='big')
    w.add_argument("--wo", choices=['big', 'little'], default='little')
    w.add_argument("--port", type=int, default=5020)

    args = parser.parse_args()
    if args.command == "scan": cmd_scan(args)
    elif args.command == "write": cmd_write(args)