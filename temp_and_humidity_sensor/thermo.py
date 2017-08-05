import time, machine, dht, onewire, ds18x20, network, ubinascii
from umqtt.simple import MQTTClient

CONFIG = {
    # WIFI Configuration
    "SSID": 'WifiNamegoesHere',
    "WIFI_PASSWORD": 'WifiPasswordGoesHere',
    # MQTT Configuration
    "MQTT_BROKER": b'ip.address.of.raspberry.pi.broker.goes.here',
    "USER": b'username',
    "PASSWORD": b'password',
    "PORT": 1883,
    "CLIENT_TYPE": b'thermo',
    "LAST_WILL_MESSAGE": b'OFFLINE',
    # unique identifier of the chip
    "CLIENT_ID": ubinascii.hexlify(machine.unique_id()),
}

base_topic = b''.join((b'pyohio/', CONFIG.get('USER'), b'/', CONFIG.get('CLIENT_TYPE'), b'/', CONFIG.get('CLIENT_ID'), b'/'))


def main():
	while True:
		wifi_connect()
		client = mqtt_connect()
		thermo(client)


def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(CONFIG.get('SSID'), CONFIG.get('WIFI_PASSWORD'))
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())


def mqtt_connect():
    print('connecting to mqtt broker...')
    # Create client object
    client = MQTTClient(CONFIG.get('CLIENT_ID'),
                        CONFIG.get('MQTT_BROKER'),
                        user=CONFIG.get('USER'),
                        password=CONFIG.get('PASSWORD'),
                        port=CONFIG.get('PORT'))
    # Set last will and it's topic
    client.set_last_will(topic=base_topic + b'status',
                         msg=CONFIG.get('LAST_WILL_MESSAGE'),
                         retain=False, qos=0)
    print("ID: {}".format(str(CONFIG.get('CLIENT_ID'),'utf-8')))
    print("Connected to: {}".format(str(CONFIG.get('MQTT_BROKER'),'utf-8')))
    print("Publishing at: {}#".format(str(base_topic,'utf-8')))
    print("Ready for sweet IoT stuff.")

    return client


def mqtt_publish_message(client, message, topic):
	# Connect to the broker
    try:
        client.connect()
        client.publish(topic, message)
        client.disconnect()
    except OSError:
        print("OSERROR - Resetting. My bad!")
        machine.reset()


def send_thermo_values(client, message_list):
	for message in message_list:
		topic = base_topic + message.get('topic')
		message = message.get('data')
		mqtt_publish_message(client=client, message=message, topic=topic)

# create dht object
def setup_DHT():
	dht_object = dht.DHT22(machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP))
	return dht_object

# create the ds18x20/onewire object
def setup_DS():
	roms_list = []
	while len(roms_list) == 0:
		ds_object = ds18x20.DS18X20(onewire.OneWire(machine.Pin(12)))
		roms_list = ds_object.scan()
	print('found devices:', roms_list)
	return ds_object, roms_list


def fetch_ds_data(ds_object, roms_list):
	ds_object.convert_temp()
	#DHT 22 can only be read every 2 seconds, 750ms for dat + 1250 for dht = 2 sec
	time.sleep_ms(2000)
	for rom in roms_list:
		liquid_temperature = ds_object.read_temp(rom)
	return liquid_temperature


def fetch_dht_data(dht_object):
	dht_object.measure()
	air_temperature = dht_object.temperature()
	air_humidity = dht_object.humidity()

	return air_temperature, air_humidity


def thermo(client):
	dht_object = setup_DHT()
	ds_object, roms_list = setup_DS()

	if dht_object and ds_object and roms_list:
		while True:
			liquid_temperature = fetch_ds_data(ds_object, roms_list)
			air_temperature, air_humidity = fetch_dht_data(dht_object)

			message_list = [
				{'topic':b'temperature/liquid', 'data' : str(liquid_temperature)},
				{'topic':b'temperature/air', 'data' : str(air_temperature)},
				{'topic':b'humidity/liquid', 'data' : '100'},
				{'topic':b'humidity/air', 'data' : str(air_humidity)}
			]
			send_thermo_values(client, message_list)
