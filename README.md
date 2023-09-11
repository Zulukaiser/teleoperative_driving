# Teleoperated Driving - Technical University Ilmenau
This is the codebase for a demonstrator miniature vehicle. The demonstrator is a Traxxas TRX4 model vehicle. The codebase is written entirely in python.

## Table of contents
- [Teleoperated Driving - Technical University Ilmenau](#teleoperated-driving---technical-university-ilmenau)
  - [Table of contents](#table-of-contents)
  - [Concept ](#concept-)
    - [1. Vehicle ](#1-vehicle-)
    - [2. Host PC ](#2-host-pc-)
  - [Software ](#software-)
    - [1. Host PC ](#1-host-pc-)
    - [2. Vehicle ](#2-vehicle-)
  - [Getting Started ](#getting-started-)
  - [Raspberry Pi Access Point ](#raspberry-pi-access-point-)


## Concept <a name="concept">
The main goal is to connect a demonstrator vehicle with a host pc, so an operator on the host pc can control the demonstrator and gets telemetry from the vehicle.

### 1. Vehicle <a name="concept-vehicle">
The vehicle is fitted with a Raspberry Pi 4 with 8Gb of RAM. For telemetry gathering several sensors are fitted to the vehicle. The goal was to make a somewhat realistic demonstrator to show the current state of teleoperated driving.

The sensors fitted are:
- Webcam (CON AMDIS08B)
- LiDAR (RPLIDAR A1M8)
- Inertial Measurement Unit (DEBO SENS ACC3)

Also some actuators and peripherals were fitted to make the vehicle more realistic:
- Horn (DEBO BUZZER P1)
- Lighting (LEDs)
- Solid State Flashing Relais for indicators

The power distribution is realized by using a DEBO DCDC DOWN 7 Step-Down-Converter which regulates the LiPo 11.1V to 6.5V, supplying the steering servo, and a DEBO DCDC DOWN 2 which regulates the 6.5V to 5V for the Raspberry Pi and another generic LM2596S DC-DC Step-Down Converter converting 6.5V to 5V for the peripherals.

For further information on the hardware see [Documentation](https://www.github.com/Zulukaiser/teleoperative_driving/tree/main/Documentation/Hardware/hardware.md)

### 2. Host PC <a name="concept-host">
The host PC is a generic Windows 11 PC with a Fanatec Podium Wheel Base DD2 Steering Wheel and Fanatec USB Pedals. Python is installed and th host PC will run the GUI for the teleoperated driving program.

## Software <a name="software">
The software for this project can be divided into two main branches. First the software that runs on the host PC which includes the GUI, communication scripts, a communication protocol for teleoperated driving and a driver for reading the steering wheel and pedal inputs. The second branch is the Raspberry Pi. Software for the Raspberry Pi includes drivers for the peripherals such as the IMU and the Lidar as welll as communication scripts, the teleoperated driving protocol and a driver for controlling the vehicle itself.

For further information on the software see [Documentation](https://www.github.com/Zulukaiser/teleoperative_driving/tree/main/Documentation/Software/software.md)

### 1. Host PC <a name="software-host">
Files on the Host PC:
| File name | Purpose |
| ----- | ----- |
| *teleoperated_driving.py* | Main program, that runs every other script. Runs the GUI |
| *fanatec_hid.py* | Driver for the Fanatec steering wheel and pedals |
| *tdtp.py* | Teleoperated Driving Transfer Protocol for communication |
| *crc8.py* | Module for Checksum calculation (CRC8) |
| *identifier_mapping.py* | Mapping for message identifiers, contains a dictionary with IDs and names |

### 2. Vehicle <a name="software-vehicle">
Files on the Vehicle:
| File name | Purpose |
| ----- | ----- |
| *client.py* | Main program, that runs every other script |
| *DEBO_SENS_ACC3.py* | Driver for the IMU |
| *tdtp.py* | Teleoperated Driving Transfer Protocol for communication |
| *vehicle.py* | Driver for the vehicle itself. Controls the Servos and driving motors |
| *crc8.py* | Module for Checksum calculation (CRC8) |
| *identifier_mapping.py* | Mapping for message identifiers, contains a dictionary with IDs and names |

## Getting Started <a name="getting-started">
In order to get started you need to connect the power cable from the 11.1V LiPo with the DEBO DCDC 7 Step-Down Converter via the XT90 connector. Then you need to ssh into the Raspberry Pi with your credentials and change directorys to the workspace directory. Then you can run the *client.py* script.

On Host PC:

To get the IP-Address of the raspberrypi type the following command in your terminal
```powershell
ping raspberrypi
```
in order to connect to the raspberrypi type the following command. After connecting you need to type the password
```powershell
ssh rp-fzt@10.3.141.1
```

On Raspberry Pi:

Change the working directory to tele
```bash
cd tele
```

Start the python script by typing the following command
```bash
python3 client.py
```

## Raspberry Pi Access Point <a name="access-point">
In order to connect to the Raspberry Pi a Ethernet communication is needed. To enhance the range of use, a WiFi connection is required. The Raspberry Pi is configured as an Access Point to generate a WiFi network with the SSID ***"teleoperative"*** and the same as the password. In order to change the SSID or the WiFi password, access to the Access Point is needed. Opening the configuration site for the Access Point is done by going to ***"10.3.141.1"*** and logging in as ***"admin"*** (Password is provided on the Hardware). There you can change the configuration of the RaspAP Access Point to your liking.