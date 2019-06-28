# Home Simulation
This repository was made in accordance with an assignment, for Home Simulation

## Prerequisites
- Python 2.7
- GCC
- Postman

## Brief overview of the project
- This project accepts sensor data from temperature, co2 and light sensors via JSON API
- It then performs decisions based on the data
- It transfers the final decision to the C application via TCP or UDP
- It performs decisions every 5 seconds
- Average of sensor data is taken to perform a decision
- The decision is acted upon only if there is an actuator (Bulb, Door, etc.) 

## Installation Instructions
1. Download all files to a folder, or clone the repo and cd to that folder

Run the following Commands on the terminal : 

2. ```pip install python-dateutil```
3. ```pip install flask```
4. ```gcc tcp_server.c -o tcp_server```
5. ```gcc udp_server.c -o udp_server```

### Execution Instructions
1. Open two terminal windows in the directory where you downloaded the files. 
- In the first one, ```./tcp_server```
- In the second one, ```./udp_server```

2. Run the python script : ```python flaskServer.py``` using another terminal, or an IDE of your choice.

3. Open Postman 
- In the URL bar : ```127.0.0.1:5000/deviceData```
- In the Body window : Type your data.

Sample data : 
```
{
    "data": [
        {
            "mac_address": "112233445566",
            "device_type": 6,
            "rssi": -83,
            "value": "0x500",
            "timestamp": "2019-06-28T13:42:00"
        },
        {
            "mac_address": "112233445577",
            "device_type": 6,
            "rssi": -83,
            "value": "0x500",
            "timestamp": "2019-06-28T13:42:00"
        },
        {
        	"mac_address": "012345678917",
        	"device_type" : 4,
        	"rssi":-20,
        	"value":"0x1F",
        	"timestamp":"2019-06-27T20:59:00"
        },
        {
        	"mac_address": "0123456789AA",
        	"device_type" : 4,
        	"rssi":-20,
        	"value":"0x01",
        	"timestamp":"2019-06-27T20:59:00"
        }
        
    ]
}
```
c. Click on SEND, and observe the Output on the terminal running flaskServer.py


### Things to keep in mind while sending data through requests
- **Make sure your timestamp is within five minutes of current time**
- Include a "data" node inside the parent object
- Make sure the "value" parameter is a hex string.
- **Temperature values can only go upto 55, (hex 37), above which, data will be invalid
- Following is the list of device types

```
Light Sensor 0x01
Light Bulb 0x02
Thermostat 0x03
Door 0x04
TempSensor 0x05
CO2Sensor 0x06
```



### Brief overview of local data storage in the python system 
```
{
    <device_type_1> : {
                        <MACADDR1> : {
                                        'rssi' : -50,
                                        'value' : '0x04',
                                        'timestamp' : '2019-06-28T13:42:00'
                                     }
                       
                        <MACADDR2>  : {
                                        'rssi' : -49,
                                        'value' : '0x09',
                                        'timestamp' : '2019-06-28T13:42:00'
                                      }
                     }
    <device_type_2> : {
                        <MACADDR3> : {
                                        'rssi' : -50,
                                        'value' : '0x04',
                                        'timestamp' : '2019-06-28T13:42:00'
                                     }
                       
                        <MACADDR4>  : {
                                        'rssi' : -49,
                                        'value' : '0x09',
                                        'timestamp' : '2019-06-28T13:42:00'
                                      }
                     } 
}
```

### Features
- If an  signal is sent to the C application, 
1. If TCP is used, it waits for ACK signal
2. if UDP is used, fire and forget
3. E.g If an OFF signal is sent to the C application, it won't send any signal until a change from OFF to ON is observed

- Threading has been used to perform decisions every 5 seconds


### Exception Handling
- All MAC addresses are verified
- All values are Hex verfied
- All RSSI values are checked on input
- All JSON Exceptions are automatically handled by Flask
- All timestamps are verified (They mustn't be in the future)
- All socket Exceptions are handled
