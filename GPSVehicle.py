import math
import json
import time
import subprocess
import pynmea2
from Utility import Utility
from WavePacketBuilder import WAVEPacketBuilder


class GPSVehicle:
    def __init__(self, vehicle_num, gps_sock, gui_sock, gui_lock):
        self.vehicle_num = vehicle_num
        self.gps_sock = gps_sock
        self.sock = gui_sock
        self.lock = gui_lock
        self.wave_builder = WAVEPacketBuilder()
        self.util = Utility()
        self.key = "keys/0/p256.key"

    def start(self):
        last_nmea = pynmea2.parse("$GPGGA,000000.00,0000.0000,N,00000.0000,E,0,99,1.0,0.0,M,0.0,M,,*5C")

        while True:
            gps_loc = self.gps_sock.recv(1024)
            nmea = pynmea2.parse(gps_loc.split(b":")[1].decode().replace("GPS_GPGGA", "").strip())
            print(nmea)

            lat = float(nmea.lat)
            lon = float(nmea.lon)
            last_lat = float(last_nmea.lat)
            last_lon = float(last_nmea.lon)

            speed = math.sqrt(math.pow(lat - last_lat, 2) + math.pow(lon - last_lon, 2)) * 36
            heading = self.get_heading(nmea, last_nmea)

            bsm_text = f"{self.vehicle_num}, {nmea.lat}, {nmea.lng}, {heading}, {speed}\n"

            message = self.build_packet(bsm_text)

            self.send_to_radio(message)
            self.send_to_gui(bsm_text)


    def get_heading(self, nmea, last_nmea):
        if nmea.lat == last_nmea.lat and last_nmea.lon == last_nmea.lon:
            return "-"

        if nmea.lat > last_nmea.lat:
            if nmea.lon > last_nmea.lon:
                return "SE"
            elif nmea.lon == last_nmea.lon:
                return "E"
            else:
                return "NE"
        elif nmea.lat < last_nmea.lat:
            if nmea.lon > last_nmea.lon:
                return "SW"
            elif nmea.lon == last_nmea.lon:
                return "W"
            else:
                return "NW"
        else:
            return "N" if nmea.lon > last_nmea.lon else "S"


    def build_packet(self, lat, lng, heading, speed, key):
        speed = str(round(speed, 2))
        return self.wave_builder.get_wsm_payload(bsm_text, key)

    def send_to_radio(self, message):
        print("Sending BSM to radio")

        bsm = self.util.inject_time(message)

        loader = subprocess.Popen(("echo", "-n", "-e", bsm), stdout=subprocess.PIPE)
        sender = subprocess.check_output(
            ("nc", "-w0", "-u", "localhost", "52001"), stdin=loader.stdout
        )

    def send_to_gui(self, message):
        print("Sending BSM to GUI")

        bsm = msg.split(",")

        decoded_data = {}

        decoded_data["id"] = bsm[0]
        decoded_data["x"] = bsm[1]
        decoded_data["y"] = bsm[2]
        decoded_data["heading"] = bsm[3]
        decoded_data["speed"] = bsm[4]

        decoded_data["sig"] = True
        decoded_data["elapsed"] = 0
        decoded_data["recent"] = True
        decoded_data["receiver"] = True

        vehicle_data_json = json.dumps(decoded_data)

        with lock:
            self.sock.send(vehicle_data_json.encode())

    def send_to_gui(self, message):
        bsm = message.split(",")
        
        decoded_data = {}
        
        decoded_data['id'] = bsm[0]
        decoded_data['x'] = bsm[1]
        decoded_data['y'] = bsm[2]
        decoded_data['heading'] = bsm[3]
        decoded_data['speed'] = bsm[4]
        
        decoded_data['sig'] = True
        decoded_data['elapsed'] = 0
        decoded_data['recent'] = True
        decoded_data['receiver'] = True
    
        vehicle_data_json = json.dumps(decoded_data)
    
        with self.lock:
            self.sock.send(vehicle_data_json.encode())
