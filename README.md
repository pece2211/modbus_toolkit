# Modbus TCP Debugging Toolkit

A robust Python toolkit for simulating Modbus TCP devices and brute-forcing/scanning registers for 32-bit float values.

## Setup
1. Create venv: `python -m venv venv`
2. Activate venv: `.\venv\Scripts\Activate.ps1`
3. Install dependencies: `pip install -r requirements.txt`

## Usage
### Start Simulator
```powershell
python simulator.py --val 36.5 --bo big --wo little


### Scan/Debug Device
```powerShell
python modbus_tool.py scan --ip 127.0.0.1

### Write to Device
```powerShell
python modbus_tool.py write --ip 127.0.0.1 --reg 10 --val 100.0 --bo big --wo little