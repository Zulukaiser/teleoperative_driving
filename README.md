# Teleoperated Driving - Technical University Ilmenau
This is the codebase for a demonstrator miniature vehicle. The demonstrator is a Traxxas TRX4 model vehicle. The codebase is written entirely in python.

## Concept
The main goal is to connect a demonstrator vehicle with a host pc, so an operator on the host pc can control the demonstrator and gets telemetry from the vehicle.

### 1. Vehicle
The vehicle is fitted with a Raspberry Pi 4 with 8Gb of RAM. For telemetry gathering several sensors are fitted to the vehicle. The goal was to make a somewhat realistic demonstrator to show the current state of teleoperated driving.

The sensors fitted are:
- Webcam (CON AMDIS08B)
- LiDAR (RPLIDAR A1M8)
- Inertial Measurement Unit (DEBO SENS ACC3)

Also some actuators and peripherals were fitted to make the vehicle more realistic:
- Horn (DEBO BUZZER P1)
- Lighting (LEDs)
- Solid State Flashing Relais for indicators

The power distribution is realized by using a DEBO DCDC DOWN 7 Step-Down-Converter which regulates the LiPo 11.1V to 6.5V, supplying the steering servo, and a DEBO DCDC DOWN 2 which regulates the 6.5V to 5V for the Raspberry Pi and the peripherals such as the Lidar, LED circuit and horn.

