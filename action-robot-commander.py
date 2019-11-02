#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from hermes_python.hermes import Hermes
from os.path import expanduser
import os
from snipshelpers.thread_handler import ThreadHandler
from snipshelpers.config_parser import SnipsConfigParser
import Queue
import serial

CONFIGURATION_ENCODING_FORMAT = "utf-8"

CONFIG_INI = "config.ini"
CACHE_INI = expanduser("~/.robot_commander_cache/cache.ini")
CACHE_INI_DIR = expanduser("~/.robot_commander_cache/")

MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

API_KEY = "api_key"
_id = "snips-skill-robot-commander"

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

class Skill_RobotCommander:
    def __init__(self):

        self.queue = Queue.Queue()
        self.thread_handler = ThreadHandler()
        self.thread_handler.run(target=self.start_blocking)
        self.thread_handler.start_run_loop()

    def start_blocking(self, run_event):
        while run_event.is_set():
            try:
                self.queue.get(False)
            except Queue.Empty:
                with Hermes(MQTT_ADDR) as h:
                    h.subscribe_intents(self.callback).start()

    # section -> extraction of slot value


    def extract_distance(self, intent_message, default_distance):
        distance = default_distance
        if intent_message.slots.distance:
            distance = intent_message.slots.distance.first().value
        if distance < 0:
            distance = 0
        if distance > 100:
            distance = 100
        return distance


    # section -> handlers of intents

    def callback(self, hermes, intent_message):
        print("[COMMAND] Received")

        intent_name = intent_message.intent.intent_name
        if ':' in intent_name:
            intent_name = intent_name.split(":")[1]
        if intent_name == 'forward':
            self.queue.put(self.forward(hermes, intent_message))
        if intent_name == 'backward':
            self.queue.put(self.backward(hermes, intent_message))
        if intent_name == 'left':
            self.queue.put(self.left(hermes, intent_message))
        if intent_name == 'right':
            self.queue.put(self.right(hermes, intent_message))
			
			
	def forward(self, hermes, intent_message):
        percent = self.extract_percentage(intent_message, None)
        if percent is None:
            self.terminate_feedback(hermes, intent_message)
            return
		ser.write(b'FORWARD')
        self.terminate_feedback(hermes, intent_message)
		
	def backward(self, hermes, intent_message):
        percent = self.extract_percentage(intent_message, None)
        if percent is None:
            self.terminate_feedback(hermes, intent_message)
            return
		ser.write(b'BACKWARD')
        self.terminate_feedback(hermes, intent_message)
		
		
    def left(self, hermes, intent_message):

        self.terminate_feedback(hermes, intent_message)

    def right(self, hermes, intent_message):

        self.terminate_feedback(hermes, intent_message)

    

    # section -> feedback reply // future function
    def terminate_feedback(self, hermes, intent_message, mode='default'):
        if mode == 'default':
            hermes.publish_end_session(intent_message.session_id, "")
        else:
            # more design
            hermes.publish_end_session(intent_message.session_id, "")


if __name__ == "__main__":
    Skill_RobotCommander()
