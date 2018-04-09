import machine, time, network, ubinascii
from umqtt.simple import MQTTClient
from machine import Pin

CONFIG = {
    # WIFI Configuration
    "SSID": 'your_wifi_name_here',
    "WIFI_PASSWORD": 'your_wifi_password_here',
    # MQTT Configuration
    "MQTT_BROKER": b'ip.address.of.raspberry.pi.broker.goes.here', #change this
    "USER": b'username',
    "PASSWORD": b'password',
    "PORT": 1883,
    "CLIENT_TYPE": b'button',
    "LAST_WILL_MESSAGE": b'OFFLINE',
    # unique identifier of the chip
    "CLIENT_ID": ubinascii.hexlify(machine.unique_id()),
}

base_topic = b''.join((b'pyohio/', CONFIG.get('USER'), b'/', CONFIG.get('CLIENT_TYPE'), b'/', CONFIG.get('CLIENT_ID'), b'/'))


def main():
    while True:
        wifi_connect()
        client = mqtt_connect()
        button(client)


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


def send_button_value(client, message):
    mqtt_publish_message(client=client, message=str(message), topic=base_topic + b"value")


def button(client):
    white_button = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)
    red_button = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)
    green_button = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)
    blue_button = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP)

    while True:
        first_white = white_button.value()
        first_red = red_button.value()
        first_green = green_button.value()
        first_blue = blue_button.value()
        time.sleep(0.01)
        second_white = white_button.value()
        second_red = red_button.value()
        second_green = green_button.value()
        second_blue = blue_button.value()

        message = None

        if first_white and not second_white:
            message = "WHITE"
        if first_red and not second_red:
            message = "RED"
        if first_green and not second_green:
            message = "GREEN"
        if first_blue and not second_blue:
            message = "BLUE"
        if message:
            send_button_value(client=client, message=message)
