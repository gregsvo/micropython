import machine, time, network, ubinascii
from machine import Timer
from umqtt.robust import MQTTClient

adc = machine.ADC(0)

CONFIG = {
    # WIFI Configuration
    "SSID": 'WifiNameGoesHere',
    "WIFI_PASSWORD": 'WifiPasswordGoesHere',
    # MQTT Configuration
    "MQTT_BROKER": b'ip.of.broker.goes.here',
    "USER": b'greg',
    "PASSWORD": b'greg',
    "PORT": 1883,
    "CLIENT_TYPE": b'knob',
    "LAST_WILL_MESSAGE": b'OFFLINE',
    # unique identifier of the chip
    "CLIENT_ID": ubinascii.hexlify(machine.unique_id()),
}

base_topic = b'pyohio/' + CONFIG.get('USER') + b'/' + CONFIG.get('CLIENT_TYPE') + b'/' + CONFIG.get('CLIENT_ID') + b'/'


def main():
    time.sleep(1)
    if wifi_connect():
        client = mqtt_connect()
        if client:
            knob(client)


def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    while not wlan.isconnected():
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
    print("Connected to: {}".format(str(CONFIG.get('MQTT_BROKER'), 'utf-8')))
    print("Publishing at: {}#".format(str(base_topic, 'utf-8')))
    print("Ready for sweet IoT stuff.")

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


def knob(client):
    average_pot_value = 0
    pot_value_list = []
    starttime = time.time()
    while True:
        # append to list the adc reading
        pot_value_list.append(adc.read())
        # once the list hits 50 values, begin popping the oldest value off
        if len(pot_value_list) == 50:
            # take the average of the 50 readings in the list
            current_average = sum(pot_value_list) / 50
            # don't send to mqtt broker if the value hasn't changed/knob hasn't turned from current position
            if average_pot_value + 3 <= current_average or average_pot_value -3 >= current_average:
                current_average = int(round(current_average, 1))
                average_pot_value = current_average
                send_pot_value(client=client, message=average_pot_value)
            pot_value_list = []
            starttime = time.time()
        # slow it down, big fella! You're so fast your crashing! Time for a (quick) snooze.
        time.sleep_ms(10 - ((time.time() - starttime) % 10))


def send_pot_value(client, message):
    print("Sending this value to MQTT broker: {}".format(message))
    mqtt_publish_message(client=client, message=str(message), topic=base_topic + b"value")
