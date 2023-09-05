# Software documentation - Teleoperated Driving Project
This is the documentation for the software for the Teleoperated Driving Project by TU Ilmenau

## Table of contents
- [Software documentation - Teleoperated Driving Project](#software-documentation---teleoperated-driving-project)
  - [Table of contents](#table-of-contents)
  - [Overview](#overview)
  - [Documentation](#documentation)
    - [*tdtp.py*](#tdtppy)
    - [*crc8.py*](#crc8py)
    - [*identifier\_mapping.py*](#identifier_mappingpy)
    - [*fanatec\_hid.py*](#fanatec_hidpy)

## Overview
The software for this project is divided into two parts. First the software for the host pc and second the software for the remote vehicle. Both parts consist of drivers and the actual script for starting the teleoperated driving. In the following table you can see the files that are on the host pc:
| Filename | Description |
| -------- | ----------- |
| *tdtp.py* | This is the communication protocol (Teleoperated Driving Transfer Protocol) and it handles the communication messages and adds features to the underlying UDP protocol |
| *crc8.py* | This file contains the class for crc8 checksum calculation |
| *identifier_mapping.py* | This file is a description file for the identifiers used in the communication. You can add or delete messages |
| *fanatec_hid.py* | This file is the driver for the Fanatec hardware. There you can remap the control mappings and add control buttons |
| *gamepadReading.py* | This file is the driver for an XBox Controller, here you can remap the controls or add control buttons |
| *teleoperative_driving.py* | This is the main file. It needs to be executed and features a GUI |

On the Raspberry Pi side, the software is quite similar. In the following table there is an overview of the files on the Raspberry Pi:

| Filename | Description |
| -------- | ----------- |
| *tdtp.py* | This is the communication protocol (Teleoperated Driving Transfer Protocol) and it handles the communication messages and adds features to the underlying UDP protocol |
| *crc8.py* | This file contains the class for crc8 checksum calculation |
| *identifier_mapping.py* | This file is a description file for the identifiers used in the communication. You can add or delete messages |
| *DEBO_SENS_ACC3.py* | This file is the driver for the IMU |
| *vehicle.py* | This file handles all the controls of the vehicle |
| *client.py* | This is the main file. It needs to be executed and handles controls of the vehicle |

In this document every file has it's own chapter, that documents how the file works and what can be added or modified to enhance the project further. The *tdtp.py*, *crc8.py* and *identifier_mapping.py* files are the same for both the host pc and Raspberry Pi. The only exception is the message length check in the *tdtp.py* file. But more on that in the corresponding chapter.

## Documentation
The following chapters contain the documentation for each file.

### *tdtp.py*
This file adds features to the underlying UDP protocol that gets used in the communication. The features are packet loss detection and latency measuring. Also it provides functionality for assembling and disassembling a message. The TDTP class generates an Object, that handles the conversion of data and identifiers into a byte message that can get transmitted via UDP. To initialize a the object, you can provide a *master* flag, to define if the object is on the master or the slave communication node. If the master flag is set, a timestamp will be updated everytime a message is assembled, otherwise the timestamp received will be saved and written to the next message in order to get the latency of the transmission. Also an crc8 object will be created to get the checksum for the data. The TDTP class consists of a **__getcrc** and **__float_to_hex** private function and a **assemble**, **disassemble** and **get_package_loss** public function.

**__getcrc**
```python
def __getcrc(self, data, crc_format="hex"):
    self.crc_object.update(data)
    if crc_format == "hex":
        return self.crc_object.hexdigest()
    elif crc_format == "bytes":
        return self.crc_object.digest()
    else:
        return False
```
This function gets the **data** as input in the form of bytes. Then the crc8 checksum is calculated. Dependent on the **crc_format** the checksum is returned as hex or bytes.

**__float_to_hex**
```python
def __float_to_hex(self, e: float) -> bytes:
    return bytes(struct.pack("d", e))
```
This function returns the data provided as **e** as bytes. The datatype of the data must be float.

**assemble**
```python
def assemble(self, identifier: int, data: float) -> bytes:
    self.package_id += 1
    if self.master:
        timestamp = round(time.time() * 1000)
    else:
        timestamp = self.timestamp_host
    package_id_bytes = self.package_id.to_bytes(8, "big")
    timestamp_bytes = timestamp.to_bytes(8, "big")
    identifier_bytes = identifier.to_bytes(1, "big")
    if identifier != [k for k, v in TDTP_IDENTIFIERS.items() if v == "PACKAGE_LOSS"][0]:
        data_bytes = self.__float_to_hex(data)
    else:
        data_bytes = self.__float_to_hex(float(self.package_loss_remote))
    crc = self.__getcrc(data_bytes).encode()

    msg = b"".join([identifier_bytes, data_bytes, crc, package_id_bytes, timestamp_bytes])
    return msg
```
This function gets an identifier and the data for the message and returns the message as bytes. It also increments the internal **package_id** variable. If the **master** flag was set in the object creation, then the current timestamp in milliseconds is stored in the **timestamp** variable. The **package_id** gets converted to 8 bytes. The **timestamp** variable is also getting converted to 8 bytes. The **identifier** is converted to 1 byte (therefore the maximum possible number of individual identifiers is 65535). If the **identifier** is not equal to 16, then the data gets converted to bytes via the **__float_to_hex** function. If the identifier is equal to 16, then the **package_loss_remote** variable is the data and gets converted to bytes. Therefore, if you change the identifier mappings so that the identifier 16 is not equal to package loss, then you need to change the this code. After converting the data to bytes the crc8 checksum gets calculated and encoded into bytes. The message gets assembled by concatenating the individual message parts.

**disassemble**
```python
def disassemble(self, msg: bytes):
    if len(msg) != self.msg_length:
        return False
    identifier = int.from_bytes(msg[:1], "big")
    data = struct.unpack("d", msg[1:9])[0]
    crc = msg[9:11]
    package_id = int.from_bytes(msg[11:19], "big")
    timestamp = int.from_bytes(msg[19:], "big")
    crc_check = self.__getcrc(msg[1:9]).encode()
    self.package_loss_remote += package_id - (self.package_id_remote + 1.0)
    self.package_id_remote = package_id
    if TDTP_IDENTIFIERS[identifier] == "PACKAGE_LOSS":
        self.package_loss = data
    if self.master:
        self.latency = round(time.time() * 1000) - timestamp
    if not self.master:
        self.timestamp_host = timestamp

    if crc == crc_check:
        return identifier, data, package_id, timestamp

    else:
        return False
```
This function gets a byte string message and returns the **identifier**, **data**, **package_id** and **timestamp** or if the checksum is incorrect **False**. in the first line, the length of the message gets checked. If the message length doesnt check out, the function returns **False**. The identifier gets cut from the message and converted to an integer. also the data gets cut from the message and converted to float. The checksum gets cut from the message as well as the **package_id** and the **timestamp**. Then a new crc8 checksum is calculated based on the received data. The **package_loss_remote** variable is incremented by the difference between the received **package_id** and the **package_id_remote + 1**. The **package_id_remote** gets then updated to the received **package_id**. The function checks if the identifier of the message corresponds to **PACKAGE_LOSS**. If so, then the **package_loss** gets saved. If the TDTP object has the **master** flag set, then the latency gets calculated by subtracting the received timestamp from the current time. If the **master** flag is not set, then the timestamp gets saved. After that, the newly calculated checksum gets compared to the received checksum. If they are the same, the **identifier**, **data**, **package_id** and **timestamp** get returned, if the checksums don't match, **False** is returned.

**get_package_loss**
```python
def get_package_loss(self) -> float:
    return (self.package_loss_remote + self.package_loss) / (
        self.package_id + self.package_id_remote
    )
```
This function reeturns the **package_loss** (0.0 ... 1.0). The calculation of the **package_loss** is done by following mathematical function:
(package_loss_remote + package_loss) / (package_id_remote + package_id)

### *crc8.py*
The *crc8.py* file is from [Nicco Kunzmann](https://github.com/niccokunzmann/crc8/blob/master/crc8.py).
The file on the host pc and Raspberry Pi are identical.

### *identifier_mapping.py*
This file contains a dictionary, that maps the identifiers to the data the message contains. The identifier is the key and the description is the value. The identifiers start at 1. The only value that has to exist is the **PACKAGE_LOSS**. But the identifer of this value can be changed. You can freely add or remove identifiers.

### *fanatec_hid.py*
