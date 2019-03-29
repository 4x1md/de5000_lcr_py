'''
Created on Sep 15, 2017

@author: 4x1md
'''

from de5000 import DE5000
import sys
import time
import datetime
from serial import SerialException

PORT = "/dev/ttyUSB0"
SLEEP_TIME = 1.0

if __name__ == '__main__':
    print "Starting DE-5000 monitor..."
    
    try:
        if len(sys.argv) > 1:
            port = sys.argv[1]
        else:
            port = PORT
            
        lcr = DE5000(port)
        
        while True:
            print
            print datetime.datetime.now()
            lcr.pretty_print(disp_norm_val=True)
    
            time.sleep(SLEEP_TIME)
    except SerialException:
        print "Serial port error."
    except KeyboardInterrupt:
        print
        print "Exiting DE-5000 monitor."
        sys.exit()
