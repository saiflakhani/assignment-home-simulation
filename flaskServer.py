from flask import Flask, redirect, url_for,request
import random
from datetime import datetime,timedelta
from dateutil import parser
import threading
import socket
import re

app = Flask(__name__)
list_of_essential_keys = ['mac_address','device_type','rssi','value','timestamp']
local_data = {}
socket_tcp_server = None

#### PART 1 : GET / POST REQUESTS, HANDLING AND STORING LOCALLY.


### This Function is used to check whether or not the JSON request contains valid data
def check_keys(current_device):
    for key in current_device:
        if key not in list_of_essential_keys:
            print("Essential JSON keys missing. Please look at request documentation")
            return False
        if key == 'mac address':
            if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$",
                            current_device[key].lower()): ## REGEX TO MATCH MAC ADDRESS
                print("MAC address not in correct format. Please resend request")
                return False
        if key == 'device_type':
            if current_device[key] <=0 or current_device[key] >= 7: ## DEVICE TYPE RANGES FROM 1-6
                print("Invalid Device Type. Please resend request")
                return False
        if key == 'rssi':
            if current_device[key]>=0 or current_device[key]<-100: ## RSSI CONTAINS ONLY NEGATIVE VALUES UP TO -100
                print ("RSSI contains an invalid value. Please resend request")
                return False
        if key == 'value':
            if not re.match("^(0x|0X)?[a-fA-F0-9]+$", ## REGEX TO MATCH HEXADECIMAL
                            current_device[key]):
                print('Value not hexadecimal. Please resend request.')
                return False
        if key == 'timestamp':
            try:
                parser.parse(current_device[key]) ## TRY PARSING DATE
            except:
                print("Could not parse timestamp. Please resend request.")

    return True

### This Function is used to store valid request data into local data variable
def update_local_data(current_device):
    device_type = int(current_device['device_type'])
    mac_address = current_device['mac_address']
    if device_type in local_data.keys():
        ## CHECK IF MAC ADDRESS ALREADY PRESENT
        if mac_address not in local_data[device_type].keys():
            ## MAC Address Not present. Add a node with MAC Address
            local_data[device_type][mac_address] = {}
    else:
        ## New Device type. Already checked Validity. Just Add.
        local_data[device_type] = {}
        local_data[device_type][mac_address] = {}
    local_data[device_type][mac_address]['rssi'] = current_device['rssi']
    local_data[device_type][mac_address]['value'] = current_device['value']
    local_data[device_type][mac_address]['timestamp'] = parser.parse(current_device['timestamp'])

### This function is the parent function of check_keys. It handles JSON Object vs JSON Array
def parse_json(parent_object):
    if 'data' in parent_object:
        ## Now check if data is JSON Object or JSON Array
        if type(parent_object['data']) == list:
            for currentDevice in parent_object['data']:
                if check_keys(currentDevice) == False:
                    return "Failed to parse JSON"
                update_local_data(currentDevice)
        else:
            if check_keys(parent_object['data']) == False:
                return "Failed to parse JSON"
            check_device_and_perform_decisions(parent_object['data'])
            update_local_data(currentDevice)
    else:
        print("data node not present in JSON object")

### The function that receives the request from GET or POST. JSON format sanity is automatically handled by Flask
@app.route('/deviceData', methods = ['POST', 'GET'])
def receive_request():
    if request.data is "":
        print "ERROR : No data found in the body of the request."
        return("Bad Request. No JSON encoded body.")
    else :
        parent_object = request.get_json() ## Python and Flask will automatically handle JSON exceptions here
        parse_json(parent_object)
        print("Received some data")
        return "Request Received"











#### PART 2 : LOCAL DATA PROCESSING, OCCURS EVERY FIVE SECONDS

### This function is used to send the TCP data to the C application
def connect_socket_tcp(status,device_type,device_mac,device_name):
    global socket_tcp_server
    global local_data
    try:
        host = socket.gethostname()
        port = 8099  # The same port as used by the server
        socket_tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_tcp_server.connect((host, port))
        if status=='ON':
            status = 1
        else:
            status = 0
        packet_to_send = "MAC ADDRESS: "+device_mac+" TYPE: "+str(device_type)+" STATUS: "+str(status)
        #packet_to_send = packet_to_send.encode('hex')
        #packet_to_send = packet_to_send.decode('hex')
        socket_tcp_server.sendall(packet_to_send)
        ack_data = socket_tcp_server.recv(1024)
        print("Received : "+ack_data)
    except:
        print("Something went wrong while communicating with the C Application. Please make sure they are running on the same port")
        ### Resend the data if no ACK
        local_data[device_type][device_mac]['last_update'] = "INVALID"

### This function is used to send UDP data to the C application
def connect_socket_udp(status,device_type,device_mac,device_name):
    host = socket.gethostname()
    port = 8100  # The same port as used by the server
    if status == 'ON':
        status = 1
    else:
        status = 0
    packet_to_send = "MAC ADDRESS: "+device_mac+" TYPE: "+str(device_type)+" STATUS: "+str(status)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    sock.sendto(bytes(packet_to_send), (host, port))

### Utility function to calculate average of values in a list
def average(lst):
    if len(lst)>0:
        return sum(lst) / len(lst)

### This function removes sensor data if it is greater than 5 minutes old
def check_data_age(data_timestamp):
    now = datetime.now()
    #five_minutes = now - timedelta(minutes=5)
    #print(now-data_timestamp)
    if(data_timestamp > now):
        return False
    if (now - data_timestamp) > timedelta(minutes=5):
        return False
    return True

### Function to check RSSI and decide whether to send via TCP or UDP
def send_tcp_udp_data(device,status,device_name):
    global local_data
    if device not in local_data.keys():
        print (device_name + " not found. Doing nothing")
        return

    for each_device_mac in local_data[device]:
        if 'last_update' in local_data[device][each_device_mac].keys():
            if local_data[device][each_device_mac]['last_update'] == status:
                print('Already Sent '+status+' signal to '+device_name+' : '+each_device_mac)
                continue

        if local_data[device][each_device_mac]['rssi'] > -50:
            print("Sending " + status + " to " + device_name + " with MAC : " + each_device_mac + " via TCP")
            local_data[device][each_device_mac]['last_update'] = status
            connect_socket_tcp(status,device,each_device_mac,device_name)

        else :
            print("Sending " + status + " to " + device_name + " with MAC : " + each_device_mac + " via UDP")
            local_data[device][each_device_mac]['last_update'] = status
            connect_socket_udp(status,device,each_device_mac,device_name)

### Function to turn thermostats ON / OFF based on temperature sensor values
def temperature_decisions():
    global local_data
    sensor = 5
    thermostat = 3
    ## First get all Sensor data values
    list_of_sensor_values = []
    list_of_sensors_to_remove = []
    if sensor in local_data.keys():
        for each_sensor_mac in local_data[sensor]:
            value = int(local_data[sensor][each_sensor_mac]['value'],16) ## CONVERT HEX TO INT
            if check_data_age(local_data[sensor][each_sensor_mac]['timestamp']):
                list_of_sensor_values.append(value)
            else :
                print('It looks like temperature sensor : '+each_sensor_mac+' data is more than five minutes old. Removing.')
                list_of_sensors_to_remove.append(each_sensor_mac)

        for sensor_mac in list_of_sensors_to_remove:
            local_data[sensor].pop(sensor_mac, None)  ## REMOVE DATA


        if len(local_data[sensor])==0:
            local_data.pop(sensor,None)
        avg_temperature_value = average(list_of_sensor_values)
        if len(list_of_sensor_values) > 0:
            if -30 < avg_temperature_value < 20:
                print("Temperature is Cold")
                send_tcp_udp_data(thermostat,"OFF","Thermostat")
            elif avg_temperature_value < 55 :
                print("Temperature is Hot")
                send_tcp_udp_data(thermostat, "ON","Thermostat")
            else :
                print("Temperature sensor contains an invalid value")
    else :
        print("Awaiting Temperature Sensor data")

### Function to turn bulbs ON / OFF based on Light sensor values
## This function also handles the extra case
def light_decisions():
    global local_data
    sensor = 1
    bulb = 2
    door = 4
    ## First get all Sensor data values
    list_of_sensor_values = []
    list_of_sensors_to_remove = []
    if sensor in local_data.keys():
        for each_sensor_mac in local_data[sensor]:
            value = int(local_data[sensor][each_sensor_mac]['value'],16) ## CONVERT HEX TO INT
            if check_data_age(local_data[sensor][each_sensor_mac]['timestamp']):
                list_of_sensor_values.append(value)
            else :
                print('It looks like Light sensor : '+each_sensor_mac+' data is more than five minutes old or invalid. Removing.')
                list_of_sensors_to_remove.append(each_sensor_mac)

        for sensor_mac in list_of_sensors_to_remove:
            local_data[sensor].pop(sensor_mac,None) ## REMOVE DATA
        if len(local_data[sensor])==0:
            local_data.pop(sensor,None)
        if len(list_of_sensor_values)>0:
            avg_lux_value = average(list_of_sensor_values)
            if avg_lux_value < 50:
                print("It is Dark")
                send_tcp_udp_data(bulb,"ON","Bulb")
            elif avg_lux_value >= 50 :
                print("It is Bright")
                send_tcp_udp_data(bulb, "OFF","Bulb")
                send_tcp_udp_data(door, "ON", "Door")
    else:
        print("Awaiting Light sensor data")

### Function to open / close door based on CO2 Sensor values
def co2_decisions():
    global local_data
    sensor = 6
    door = 4
    ## First get all Sensor data values
    list_of_sensor_values = []
    list_of_sensors_to_remove = []
    if sensor in local_data.keys():
        for each_sensor_mac in local_data[sensor]:
            value = int(local_data[sensor][each_sensor_mac]['value'], 16)  ## CONVERT HEX TO INT
            if check_data_age(local_data[sensor][each_sensor_mac]['timestamp']):
                list_of_sensor_values.append(value)
            else:
                print('It looks like CO2 sensor : ' + each_sensor_mac + ' data is more than five minutes old. Removing.')
                list_of_sensors_to_remove.append(each_sensor_mac)
        for sensor_mac in list_of_sensors_to_remove:
            local_data[sensor].pop(sensor_mac, None)  ## REMOVE DATA
        if len(local_data[sensor])==0:
            local_data.pop(sensor,None)
        if len(list_of_sensor_values) > 0:
            avg_ppm_value = average(list_of_sensor_values)
            if avg_ppm_value < 500:
                print("CO2 Level is Good")
                send_tcp_udp_data(door, "OFF","Door")
            elif avg_ppm_value >= 500:
                print("CO2 Level is Bad")
                send_tcp_udp_data(door, "ON","Door")
    else:
        print("Awaiting CO2 Sensor data")

### Parent function that gets called every 5 seconds, to trigger all three decisions
def perform_decision_logic():
    print("\n\n--")
    ## TODO ADD TRY CATCH HERE
    temperature_decisions()
    light_decisions()
    co2_decisions()
    threading.Timer(5.0, perform_decision_logic).start()


if __name__ == '__main__':
    print('No Local Data Present. Please send a request')
    perform_decision_logic()
    app.run()