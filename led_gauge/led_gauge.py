import machine, neopixel, time, network, ubinascii
from umqtt.simple import MQTTClient

temp_number = 8
data_pin = 4
num_leds = 50
pin_out = machine.Pin(data_pin)
np = neopixel.NeoPixel(pin_out, num_leds)
color_state = (255, 255, 255)
gauge_number = 0

CONFIG = {
    # WIFI Configuration
    "SSID": 'WifiNameGoesHere',
    "WIFI_PASSWORD": 'WifiPasswordGoesHere',
    # MQTT Configuration
    "MQTT_BROKER": b'ip.of.broker.goes.here',
    "USER": b'greg',
    "PASSWORD": b'greg',
    "PORT": 1883,
    "CLIENT_TYPE": b'gauge',
    "LAST_WILL_MESSAGE": b'OFFLINE',
    # unique identifier of the chip
    "CLIENT_ID": ubinascii.hexlify(machine.unique_id()),
}

base_topic = b'pyohio/' + CONFIG.get('USER') + b'/' + CONFIG.get('CLIENT_TYPE') + b'/' + CONFIG.get('CLIENT_ID') + b'/'


def main():
    if wifi_connect():
        client = mqtt_connect()
        if client:
            wait_for_color_commands(client)


def wait_for_color_commands(client):
    try:
        while True:
            client.wait_msg()
    finally:
        client.disconnect()


def sub_callback(topic, msg):
    global gauge_number
    global color_state

    if topic == b'led_string/gauge':
        gauge_number = int(msg)
    elif topic == b'led_string/color':
        color_state = eval(msg)
    change_color_gauge(gauge=gauge_number, color=color_state)


def change_color_gauge(gauge, color):
    print('SETTING GAUGE TO: {}'.format(gauge))
    print('SETTING COLOR TO: {}'.format(color))
    for led in range(0, gauge):
        np[led] = color
    for led in range(gauge, np.n):
        np[led] = (0, 0, 0)
    np.write()


def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(CONFIG.get('SSID'), CONFIG.get('WIFI_PASSWORD'))
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    return True


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
    print("ID: {}".format(str(CONFIG.get('CLIENT_ID'), 'utf-8')))
    # Set callback function to be executed when a message is posted to subscribed topics
    client.set_callback(sub_callback)
    # Connect to broker
    client.connect()
    print("Connected to: {}".format(str(CONFIG.get('MQTT_BROKER'), 'utf-8')))
    # Subscribe to topic(s)
    client.subscribe(b'led_string/gauge')
    print('Subscribed to led_string/gauge')
    client.subscribe(b'led_string/color')
    print('Subscribed to led_string/color')

    return client


def mqtt_publish_message(client, message, topic):
    # Connect to the broker
    try:
        client.connect()
        client.publish(topic, message)
        time.sleep_ms(200)
        client.disconnect()
    except OSError:
        print("OSERROR - Resetting. My bad!")
        machine.reset()
