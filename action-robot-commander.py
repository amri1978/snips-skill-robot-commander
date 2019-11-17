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
#Message Format : (RGHT|LEFT|FRWD|BKWD):(S|M|F):Distance in cm or angle in degree
class Skill_RobotCommander:
    def __init__(self):

        self.queue = Queue.Queue()
        self.thread_handler = ThreadHandler()
        self.thread_handler.run(target=self.start_blocking)
        self.thread_handler.start_run_loop()
        print(ser)

    def start_blocking(self, run_event):
        while run_event.is_set():
            try:
                self.queue.get(False)
            except Queue.Empty:
                with Hermes(MQTT_ADDR) as h:
                    h.subscribe_intents(self.callback).start()

    # section -> extraction of slot value


    def extract_angle(self, intent_message, default_angle):
        angle = default_angle
        if intent_message.slots.angle:
            angle = intent_message.slots.angle.first().value
        if angle < 0:
            angle = 0
        if angle > 360:
            angle = 360
        return angle
        
    def extract_distance(self, intent_message, default_distance):
        distance = default_distance
        if intent_message.slots.distance:
            distance = intent_message.slots.distance.first().value
        if distance < 0:
            distance = 0
        return distance
        
    def extract_speed(self, intent_message, default_speed):
        speed = default_speed
        if intent_message.slots.speed:
            speed = intent_message.slots.speed.first().value
            if speed == 'fast':
                speed = 'F'
            elif speed == 'slow':
                speed = 'S'
            else:
                speed = 'M'        
        print (speed)
        return speed
   

    # section -> handlers of intents

    def callback(self, hermes, intent_message):
        print("[COMMAND] Received")
        intent_name = intent_message.intent.intent_name
        print(intent_name)
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
        distance = self.extract_distance(intent_message, 10)
        speed = self.extract_speed(intent_message, 'M')
        command = b"".join(['FRWD:', speed, ':',str(int(distance)),'\n'])
        print(command)
        ser.write(command)
        self.terminate_feedback(hermes, intent_message)
		
    def backward(self, hermes, intent_message):
        distance = self.extract_distance(intent_message, 10)
        speed = self.extract_speed(intent_message, 'M')
        command = b"".join(['BKWD:', speed, ':',str(int(distance)),'\n'])
        print(command)
        ser.write(command)
        self.terminate_feedback(hermes, intent_message)
				
    def left(self, hermes, intent_message):
        angle = self.extract_angle(intent_message, 45)
        command = b"".join(['LEFT:S:',str(int(angle)),'\n'])
        ser.write(command)
        self.terminate_feedback(hermes, intent_message)

    def right(self, hermes, intent_message):
        angle = self.extract_angle(intent_message, 45)
        command = b"".join(['RGHT:S:',str(int(angle)),'\n'])
        ser.write(command)
        self.terminate_feedback(hermes, intent_message)

    
    def terminate_feedback(self, hermes, intent_message, mode='default'):
        if mode == 'default':
            hermes.publish_end_session(intent_message.session_id, "")
        else:
            # more design
            hermes.publish_end_session(intent_message.session_id, "")


if __name__ == "__main__":
    Skill_RobotCommander()

