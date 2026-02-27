📡 Modbus TCP Debugging & Simulation Toolkit
A professional-grade Python suite for industrial protocol testing. This toolkit allows you to simulate a Modbus TCP server (PLC/HMI) and use a multi-functional client to scan, brute-force, and write 32-bit float data across various register configurations.
---
## 🚀 Quick Start
### 1. Environment Setup
```powershell
# Clone the repository
git clone <your-repo-url>
cd modbus_debugger
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1
# Install dependencies
pip install -r requirements.txt
```
### 2. Run the Simulator (The "Device")
Starts a local Modbus server at 127.0.0.1:5020 with a test value.
```powershell
python simulator.py --val 36.5 --bo big --wo little
```
### 3. Use the Toolkit (The "Master")
In a separate terminal, scan the device to find where the data lives:
```powershell
python modbus_tool.py scan --ip 127.0.0.1
```
---
## 🛠 Features
* Multi-ID Scanning: Automatically probes Device IDs 0, 1, and 255.
* Dual Register Support: Scans both Holding Registers (HR) and Input Registers (IR).
* Auto-Endian Detection: Brute-forces all 4 combinations of Byte/Word ordering to find human-readable floats.
* Float Writer: Encodes Python floats into 16-bit register pairs for transmission using the modern device_id keyword.
---
## 📖 Technical Specifications: 32-bit Float Mapping
Modbus registers are natively 16-bit. To store a 32-bit float32, we must span two adjacent registers. Because there is no official "standard" for the sequence of these bytes, different manufacturers use different "Endianness."
### Supported Endianness Permutations
| Type | Byte Order | Word Order | Byte Sequence | Common PLC Brands |
| :--- | :--- | :--- | :--- | :--- |
| Big/Big | Big | Big | [A, B, C, D] | Motorola, Siemens (Standard) |
| Big/Little | Big | Little | [C, D, A, B] | Schneider, ABB (Modicon) |
| Little/Big | Little | Big | [B, A, D, C] | Rare / Custom |
| Little/Little | Little | Little | [D, C, B, A] | Intel-based, Opto22 |
### The "Register Offset" Logic
The scanner probes both Register N and Register N-1.
* Example: If data is stored at Address 10, reading a pair starting at 9 with Big/Little often yields the same value as reading from 10 with Big/Big. This tool helps identify the exact intended mapping for your specific hardware.
---
## 🔧 Toolkit Usage Reference
### Scan for Values
Finds any non-zero float values in the first 30 registers across all common Device IDs.
```powershell
python modbus_tool.py scan --ip <target_ip> --port 5020
```
### Write a Value
Write 98.6 to Register 10 using specific ordering:
```powershell
python modbus_tool.py write --ip 127.0.0.1 --reg 10 --val 98.6 --bo big --wo little
```
---
## 📝 Requirements
* Python 3.10+
* pymodbus >= 3.1.0 (Uses the modern device_id keyword convention)
---
Developed for industrial protocol debugging and security auditing.