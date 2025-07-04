'''
 * @file      GPS_BuiltInEx.py
 * @license   MIT
 * @copyright Copyright (c) 2025  Shenzhen Xin Yuan Electronic Technology Co.,
 * Ltd
 * @date      2025-06-24
 * @note      GPS only supports A7670X/A7608X (excluding A7670G and other
 * versions that do not support positioning).
'''
import machine
import time
from machine import UART, Pin
import utilities

# Initialize UART for modem communication
SerialAT = UART(1, baudrate=utilities.MODEM_BAUDRATE, tx=utilities.MODEM_TX_PIN, rx=utilities.MODEM_RX_PIN)

# Initialize pins
pwrkey = Pin(utilities.BOARD_PWRKEY_PIN, Pin.OUT)
poweron = Pin(utilities.BOARD_POWERON_PIN, Pin.OUT)
reset_pin = Pin(utilities.MODEM_RESET_PIN, Pin.OUT)
gps_enable = Pin(utilities.MODEM_GPS_ENABLE_GPIO, Pin.OUT)

def send_at_command(command,wait=1):
    SerialAT.write(command + "\r")
    time.sleep(wait)
    response = SerialAT.read()
    if response:
        return response.decode("utf-8", "ignore").strip()
    return ""

def modem_setup():
    global modemName
    # Turn on DC boost to power on the modem
    poweron.value(1)
    
    # Set modem reset pin ,reset modem
    reset_pin.value(not utilities.MODEM_RESET_LEVEL)
    time.sleep(0.1)
    reset_pin.value(utilities.MODEM_RESET_LEVEL)
    time.sleep(2.6)
    reset_pin.value(not utilities.MODEM_RESET_LEVEL)
    
    # Turn on modem
    pwrkey.value(0)
    time.sleep(0.1)
    pwrkey.value(1)
    time.sleep(1)
    pwrkey.value(0)
    
    print("Start modem...")
    time.sleep(3)
    
    retry = 0
    while True:
        response = send_at_command("AT")
        if "OK" in response:
            break
        print(".")
        retry += 1
        if retry > 10:
            pwrkey.value(0)
            time.sleep(0.1)
            pwrkey.value(1)
            time.sleep(1)
            pwrkey.value(0)
            retry = 0
    print()
    time.sleep(0.2)
    
    # Get modem info
    modemName = "UNKNOWN"
    while True:
        response = send_at_command("AT+CGMM")
        print(response)
        if "OK" in response:
            modemName = response.split("\r\n")[1]
            if "A7670G" in modemName:
                while True:
                    print("A7670G does not support built-in GPS function, please run examples/GPSShield")
                    time.sleep(1)
            else:
                print("Model Name:", modemName)
                break
        else:
            print("Unable to obtain module information normally, try again")
            time.sleep(1)
        time.sleep(5)
    
    # Send SIMCOMATI command
    response = send_at_command("AT+SIMCOMATI")
    print(response) 
    print("Enabling GPS/GNSS/GLONASS")
    response = send_at_command("AT+CGDRT=4,1")
    print(response)
    response = send_at_command("AT+CGSETV=4,1")
    print(response)
    while True:
        gps_enable.value(utilities.MODEM_GPS_ENABLE_LEVEL)
        response = send_at_command("AT+CGNSSPWR=1")
        print(response)
        if response:
            break
        print(".", end="")
        
    print("\nGPS Enabled")

    # Set GPS Baud to 115200
    response = send_at_command("AT+CGNSSIPR=115200")
    print(response)

def loopGPS(gnss_mode):
    print("=========================") 
    print(f"Set GPS Mode : {gnss_mode}")
    response = send_at_command(f"AT+CGNSSMODE={gnss_mode}")
    print(response)
    print("Requesting current GPS/GNSS/GLONASS location")
    while True:
        response = send_at_command("AT+CGNSSINFO")
#         print(response)
        if "+CGNSSINFO: ,,,,,,,," not in response:
            data = response.split("+CGNSSINFO: ")[1].split("\n")[0] 
            values = data.split(",")
            if len(values) >= 1:  
                fixMode = values[0]  # Fix mode
                latitude = float(values[5])  # Latitude
                longitude = float(values[7])  # Longitude
                speed = float(values[12])  # Speed
                altitude = float(values[11])  # Altitude
                
                if values[1] == "":
                    gps_satellite_num = 0
                else:
                    gps_satellite_num = int(values[1])
                if values[2] == "":
                    beidou_satellite_num = 0
                else:
                    beidou_satellite_num = int(values[2])
                if values[3] == "":
                    glonass_satellite_num = 0
                else:
                    glonass_satellite_num = int(values[3])
                if values[4] == "":
                    galileo_satellite_num = 0
                else:
                    galileo_satellite_num = int(values[4])
                
                course = 1.0
                PDOP = float(values[14])
                HDOP = float(values[15])
                VDOP = float(values[16])
                
                date_str = values[9]  # Date
                time_str = values[10]  # Time
                year2 = int(date_str[:2]) + 2001  # Year
                month2 = int(date_str[2:4])  # Month
                day2 = int(date_str[4:6])-1  # Day
                hour2 = int(time_str[:2])  # Hour
                min2 = int(time_str[2:4])  # Minute
                sec2 = float(time_str[4:])  # Second
                
                # Convert UTC time to local time by adding time zone offset
                timezone_offset = 8  # CST is UTC+8

                # Adjust hours based on timezone offset
                hour2 += timezone_offset
                if hour2 >= 24:
                    hour2 -= 24
                elif hour2 < 0:
                    hour2 += 24

                print("FixMode:", fixMode)
                print("Latitude:", latitude)
                print("tLongitude:", longitude)
                print("Speed:", speed)
                print("Altitude:", altitude)

                print("Visible Satellites:")
                print(" GPS Satellites:", gps_satellite_num)
                print(" BEIDOU Satellites:", beidou_satellite_num)
                print(" GLONASS Satellites:", glonass_satellite_num)
                print(" GALILEO Satellites:", galileo_satellite_num)

                print("Date Time:")
                print("Year:", year2,)
                print("Month:", month2)
                print("Day:", day2)
                print("Hour:", hour2)
                print("Minute:", min2)
                print("Second:", sec2)
                
                print("Course:", course)
                print("PDOP:", PDOP)
                print("HDOP:", HDOP)
                print("VDOP:", VDOP)

                gps_raw = send_at_command("AT+CGNSSINFO")
                print("GPS/GNSS Based Location String:", gps_raw.split("\r\n")[1])
                break
#         else:
#             print("Couldn't get GPS/GNSS/GLONASS location, retrying in 15s.")
# #             print(".", end="")
#             time.sleep(15)
    
    print("Disabling GPS")
    response = send_at_command("AT+CGNSSPWR=0")
    print(response)

def main():
    global modemName
    modem_setup()
    gnss_length = 0
    a76xx_gnss_mode = [1, 2, 3, 4]
    sim767x_gnss_mode = [1, 3, 5, 9, 13, 15]
    gnss_mode = None
    if modemName.startswith("A767"):  # Correct method name: startswith
        gnss_mode = a76xx_gnss_mode
        gnss_length = len(a76xx_gnss_mode)
    else:
        gnss_mode = sim767x_gnss_mode
        gnss_length = len(sim767x_gnss_mode)

    # Print the result to verify
    print("GNSS Modes:", gnss_mode)
    print("GNSS Length:", gnss_length)
    
    for i in range(gnss_length):
        '''
          Model: A76XX
          1 - GPS L1 + SBAS + QZSS
          2 - BDS B1
          3 - GPS + GLONASS + GALILEO + SBAS + QZSS
          4 - GPS + BDS + GALILEO + SBAS + QZSS.
         
          Model: SIM7670G
          1  -  GPS
          3  -  GPS + GLONASS
          5  -  GPS + GALILEO
          9  -  GPS + BDS
          13 -  GPS + GALILEO + BDS
          15 -  GPS + GLONASS + GALILEO + BDS
        '''
        loopGPS(gnss_mode[i])
    # Just echo serial data
    while True:
        if SerialAT.any():
            print(SerialAT.read().decode(), end="")
        time.sleep(0.001)

if __name__ == "__main__":
    main()
