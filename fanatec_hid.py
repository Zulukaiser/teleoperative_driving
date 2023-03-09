import sys
import usb1
import time

VENDOR_ID = 0x0EB7
DEVICE_ID = 0x0007
# DEVICE_ID_WHEEL = 0x0007
# DEVICE_ID_PEDALS = 0x183b

CMD_BASE = [0x01]
CMD_LED_BASE = [0xF8]
CMD_BASE_LED = [0x13]  # CMD_BASE+CMD_LED_BASE+CMD_BASE_LED+[val]
CMD_WHEEL_LED = [0x09, 0x08, 0x00]  # CMD_BASE+CMD_LED_BASE+CMD_WHEEL_LED+[val]

CMD_SIMPLE_SPRING_ENABLE = [0x11, 0x0B]
CMD_SIMPLE_SPRING_DISABLE = [0x13, 0x0B]
CMD_SIMPLE_SPRING_ARGS = [
    0x80,
    0x80,
    0x10,
    0x00,
    0x00,
]  # offset?, offset?, coefficient, ??, saturation

CMD_FORCE_SPRING = [
    0x01,
    0x08,
]  # CMD_BASE+CMD_FORCE_SPRING+[val] # val 0x80 -> no force; val 0x00 -> full force to the left
CMD_FORCE_SPRING_DISABLE = [0x03, 0x08]


def payload(args):
    p = bytearray(CMD_BASE + args)
    # p.extend(args)
    # pad with zeros
    p.extend([0] * (8 - len(p)))
    print(p)
    return p


if __name__ == "__main__":
    val = None
    if len(sys.argv) == 2:
        val = int(sys.argv[1])

    with usb1.USBContext() as context:
        handle = context.openByVendorIDAndProductID(
            VENDOR_ID,
            DEVICE_ID,
            skip_on_error=True,
        )
        if handle is None:
            print("Device not found")
            sys.exit(1)

        handle.setAutoDetachKernelDriver(True)
        with handle.claimInterface(0):
            # request reading of current value
            handle.interruptWrite(0x01, payload(CMD_LED_BASE + CMD_WHEEL_LED + [val]))
            # handle.interruptWrite(0x01, payload(CMD_FORCE_SPRING+[val]))
            # time.sleep(1)
            # handle.interruptWrite(0x01, payload(CMD_FORCE_SPRING_DISABLE))
            # handle.interruptWrite(0x01, payload(CMD_SIMPLE_SPRING_ENABLE+CMD_SIMPLE_SPRING_ARGS))
            # time.sleep(5)
            # handle.interruptWrite(0x01, payload(CMD_SIMPLE_SPRING_DISABLE))
