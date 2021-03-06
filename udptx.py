#!/usr/bin/env python
'''
udptx.py - Fly with Open Pilot GCS through an R/C transmitter connected via cable

Requires: PyGame, PyQuadStick

Copyright (C) 2015 Simon D. Levy

This code is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
This code is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU Lesser General Public License
along with this code. If not, see <http://www.gnu.org/licenses/>.
'''

# Choose your transmitter ======================================================

#from quadstick.axial.rc.spektrum import DX8 as Controller
from quadstick.axial.rc.frsky import Taranis as Controller

from gcsudp import GCSUDP

import time

class UDPTX(object):
    '''
    A class for flying Open Pilot GCS through an R/C transmitter connected via cable.
    '''

    def _negone(self, val):
        return val < -(1-self.zero_thresh)

    def _posone(self, val):
        return val > (1-self.zero_thresh)

    def __init__(self, delay_sec=0.1, zero_thresh=0.02):
        '''
        Creates a UDPTX object. Parameters:
        delay_sec   delay between successive messages to UDP
        zero_thresh noise threshold: values below this are converted to zero, above one minus this, to one
        '''

        # Store params
        self.delay_sec = delay_sec
        self.zero_thresh = zero_thresh

        # Initialize status flag
        self.is_running = False

        # Initiate UDP connnection
        self.gcsudp = GCSUDP()

        # Initiate controller
        try:
            self.controller = Controller(hidden=True)
        except:
            raise Exception('No transmitter')

    def holdpos(self, demands, switches):
        '''
        Accepts (pitch,roll,yaw,throttle) demands and (alt-hold,pos-hold switches and returns
        new demands.  Default method prints out demands and switches and returns demands unmodified.
        Override this method for your own alt-hold, pos-hold functionality.
        '''

        print('pitch=%+3.3f roll=%+3.3f yaw=%+3.3f throttle=%+3.3f | alt-hold=%5s pos-hold=%5s' % (demands+switches))

        return demands

    def start(self):
        '''
        Starts polling and responding to transmitter.
        '''

        # Need to turn switches on/off to make sure they're off to start
        print('Please cycle switches on/off.. ')
        while True:

            # Poll controller throttle
            (_,switches) = self.controller.poll()

            # Never gets all the way to 1.0
            if any(switches):
                break
        while True:

            # Poll controller throttle
            (_,switches) = self.controller.poll()

            # Never gets all the way to 1.0
            if not any(switches):
                break



        # Make sure throttle is in lowest position
        print('Please turn off switches and go throttle down, yaw right to start')
        moved_up = False
        while True:

            # Poll controller throttle
            ((_,_,yaw,throttle),switches) = self.controller.poll()

            # Never gets all the way to 1.0
            if (not any(switches)) and self._negone(throttle) and self._posone(yaw):
                break

        print('Ready... To quit, go throttle down, yaw left')

        self.is_running = True

        # Start a-loopin'!
        while True:

            # Get sticks, switches
            (pitch,roll,yaw,throttle), switches = self.controller.poll()

           # Avoid noise near -1
            if self._negone(throttle):
                throttle = -1 - self.zero_thresh

            # Convert throttle to [0,1]
            throttle =  throttle / 2. + 0.5

            # Quit on throttle down, yaw left
            if (throttle <= 0) and self._negone(yaw):
                break

            # Modify demands based on alt-hold, pos-hold switches
            (pitch,roll,yaw,throttle) = self.holdpos((pitch,roll,yaw,throttle),switches[0:2])

            # Set GCS UDP, reversing roll and adjusting throttle to [0,1]
            self.gcsudp.set(pitch, yaw, -roll, throttle)

            # Chill a spell
            time.sleep(self.delay_sec)

        self.is_running = False

        # Close UDP connection
        self.gcsudp.close()

if __name__ == '__main__':

    tx = UDPTX()

    tx.start()
