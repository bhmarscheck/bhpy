import bhpy
from time import sleep


def bdu_example():
    '''Example function showing off the BDU functionalities provided by
    the python wrapper.'''

    # Construct an instance of the BDU control wrapper.
    bdu = bhpy.LVConnectBDU()

    # Check for the presence of a running BDU application by reading the
    # connected property until no ChildProcessError is raised.
    # The ChildProcessError indicates no running BDU application.
    while True:
        try:
            connected = bdu.connected
            break
        except ChildProcessError:
            print('Start the BDU application.')
            sleep(1)

    # Check if a BDU laser is connected and detected by the BDU application.
    # If not wait until a BDU laser is connected and ready to be used.
    while not connected:
        print('Connect a BDU laser.')
        sleep(3)
        connected = bdu.connected

    # Print all available information about the connected BDU laser.
    print('BDU laser connected\n'
          f'Serial number: {bdu.serial_number}\n'
          f'Firmware version: {bdu.firmware_version}\n'
          f'Wavelength [nm]: {bdu.wavelength}\n'
          f'Possible frequencies: {bdu.frequencies}\n'
          f'Current frequency: {bdu.frequency}\n'
          f'Current power [%]: {bdu.power}\n'
          f'Arming state: {"Armed" if bdu.arming else "Disarmed"}')

    # Disarm the BDU laser, set the frequency to the first frequency of
    # the BDU laser and set the laser power to 42.73 %
    try:
        bdu.arming = False
    except ChildProcessError:
        print('Missing Password, BDU is disarmed anyway')
    bdu.frequency = bdu.frequencies[0]
    bdu.power = 42.73

    # Try to arm the laser. Repeat every 3 seconds in case the password
    # is missing, indicated by a ChildProcessError being raised.
    while True:
        try:
            bdu.arming = True
            break
        except ChildProcessError:
            print('Missing Password, BDU can not be armed')
            sleep(3)

    # Wait for the laser emission. Note: bdu.emission only indicates the
    # possibility of actual emission interlock and/or external rigger signals
    # might still prevent the BDU Laser from emitting light.
    while not bdu.emission:
        print('Waiting for emission...')
        sleep(0.5)

    # Keep the BDU laser on for 10 seconds
    sleep(10)

    # Change the frequency to the last frequency of the BDU laser and set
    # the laserpower to 0.1 %.
    bdu.frequency = bdu.frequencies[-1]
    bdu.power = 0.1

    # Keep the BDU laser on for 10 seconds
    sleep(10)

    # Disarm the BDU laser and shut down the BDU application.
    bdu.arming = False
    bdu.close()


def main():
    bdu_example()


if __name__ == '__main__':
    main()
