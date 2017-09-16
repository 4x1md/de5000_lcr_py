'''
Created on Sep 15, 2017

@author: 4x1md

Serial port settings: 9600 8N1 DTR=1 RTS=0 
'''

'''
Useful links:

https://github.com/3s1d/libsigrok-dev/tree/master/src/hardware/deree-de5000
https://github.com/3s1d/libsigrok-dev/commit/b50891952d22d1c5012a99ad643ee3dd58495420
https://github.com/merbanan/libsigrok/blob/master/src/lcr/es51919.c
https://sigrok.org/gitweb/?p=libsigrok.git;a=blob;f=src/lcr/es51919.c;hb=HEAD
https://github.com/3s1d/libsigrok-dev/blob/master/src/hardware/deree-de5000/api.c
https://sigrok.org/wiki/UNI-T_UT612
https://sigrok.org/wiki/Multimeter_ICs/Cyrustek_ES51919

http://www.ietlabs.com/pdf/Datasheets/DE_5000.pdf

'''

import serial

DEBUG = False

BAUD_RATE = 9600
BITS = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOP_BITS = serial.STOPBITS_ONE
TIMEOUT = 1
# Data packet ends with CR LF (\r \n) characters
EOL = b'\x0D\x0A'
RAW_DATA_LENGTH = 17
READ_RETRIES = 3

# Cyrustek ES51919 LCR chipset host protocol
# 0x02: Flags
# bit 0 = hold enabled
HOLD = 0b00000001
# bit 1 = reference shown (in delta mode)
REF_SHOWN = 0b00000010
# bit 2 = delta mode
DELTA = 0b00000100
# bit 3 = calibration mode
CAL = 0b00001000
# bit 4 = sorting mode
SORTING = 0b00010000
# bit 5 = LCR mode
LCR_AUTO = 0b00100000
# bit 6 = auto mode
AUTO_RANGE = 0b01000000
# bit 7 = parallel measurement (vs. serial)
PARALLEL = 0b10000000

# 0x03 bits 5-7: Frequency
FREQ = [
    '100 Hz',
    '120 Hz',
    '1 KHz',
    '10 KHz',
    '100 KHz',
    'DC'
    ]

# 0x04: Tolerance
TOLERANCE = [
    None,
    None, None,
    '+-0.25%',
    '+-0.5%',
    '+-1%',
    '+-2%',
    '+-5%',
    '+-10%',
    '+-20%',
    '-20+80%',
    ]

# 0x05-0x09: Primary measurement
# 0x05: Measured quantity
MEAS_QUANTITY_SER = [None, 'Ls', 'Cs', 'Rs', 'DCR']
MEAS_QUANTITY_PAR = [None, 'Lp', 'Cp', 'Rp', 'DCR']

# 0x06-0x07: measurement MSB and LSB (0x4e20 = 20000 = outside limits)
MAIN_OL = 20000

# 0x08 bits 3-7: Units
MAIN_UNITS = [
    '',
    'Ohm',
    'kOhm',
    'MOhm',
    None, 
    'uH',
    'mH',
    'H',
    'kH',
    'pF',
    'nF',
    'uF',
    'mF',
    '%',
    'deg',
    None, None, None, None, None, None
    ]

# 0x09 bits 0-3: Measurement status
STATUS = [
    'normal',
    'blank',
    '----',
    'OL',
    None, None, None,
    'PASS',
    'FAIL',
    'OPEn',
    'Srt'
    ]

# 0x0a-0x0e: Secondary measurement
# 0x0a: measured quantity
SEC_QUANTITY = [
    None,
    'D',
    'Q',
    'ESR',
    'Theta'
    ]
RP = 'RP'
# 0x0b-0x0e: Like primary measurement

MEAS_RES = {
    'main_quantity': None,
    'main_val': None,
    'main_units': None,
    'main_status': None,
    
    'sec_quantity': None,
    'sec_val': None,
    'sec_units': None,
    'sec_status': None,

    'freq': None,
    'tolerance': None,
    'ref_shown': False,
    'delta_mode': False,
    'cal_mode': False,
    'sorting_mode': False,
    'lcr_auto': False,
    'auto_range': False,
    'parallel': False,
    
    'data_valid': False
    }


class DE5000(object):
    
    def __init__(self, port):
        self._port = port
        self._ser = serial.Serial(self._port, BAUD_RATE, BITS, PARITY, STOP_BITS, timeout=TIMEOUT)
        self._ser.setDTR(True)
        self._ser.setRTS(False)

    def read_raw_data(self):
        '''Reads a new data packet from serial port.
        If the packet was valid returns array of integers.
        if the packet was not valid returns empty array.
        
        In order to get the last reading the input buffer is flushed
        before reading any data.
        
        If the first received packet contains less than 17 bytes, it is
        not complete and the reading is done again. Maximum number of
        retries is defined by READ_RETRIES value.
        '''
        self._ser.reset_input_buffer()
        
        retries = 0
        while retries < READ_RETRIES:
            raw_data = self._ser.read_until(EOL, RAW_DATA_LENGTH)
            # If 17 bytes were read, the packet is valid and the loop ends.
            if len(raw_data) == RAW_DATA_LENGTH:
                break
            retries += 1

        res = []
        # Check data validity
        if self.is_data_valid(raw_data):
            res = [ord(c) for c in raw_data]
        return res

    def is_data_valid(self, raw_data):
        '''Checks data validity:
        1. 17 bytes long
        2. Header bytes 0x00 0x0D
        3. Footer bytes 0x0D 0x0A'''
        # Data length
        if len(raw_data) != RAW_DATA_LENGTH:
            return False
        
        # Start bits
        if raw_data[0] != '\x00' or raw_data[1] != '\x0D':
            return False
        
        # End bits
        if raw_data[15] != '\x0D' or raw_data[16] != '\x0A':
            return False
        
        return True
    
    def read_hex_str_data(self):
        '''Returns raw data represented as string with hexadecimal values.'''
        data = self.read_raw_data()
        codes = ["0x%02X" % c for c in data]
        return " ".join(codes)
    
    def get_meas(self):
        '''Returns received measurement as dictionary'''
        res = MEAS_RES.copy()
        
        raw_data = self.read_raw_data()
        
        # If raw data is empty, return
        if len(raw_data) == 0:
            res['data_valid'] = False
            return res
        
        # Frequency
        val = raw_data[0x03]
        val &= 0b11100000
        val = val >> 5
        res['freq'] = FREQ[val]
        
        # Reference shown
        val = raw_data[0x02]
        val &= REF_SHOWN 
        res['ref_shown'] = True if val else False
        
        # Delta mode
        val = raw_data[0x02]
        val &= DELTA
        res['delta_mode'] = True if val else False

        # Calibration mode
        val = raw_data[0x02]
        val &= CAL
        res['cal_mode'] = True if val else False

        # Sorting mode
        val = raw_data[0x02]
        val &= SORTING
        res['sorting_mode'] = True if val else False

        # LCR AUTO mode
        val = raw_data[0x02]
        val &= LCR_AUTO
        res['lcr_auto'] = True if val else False

        # Auto range
        val = raw_data[0x02]
        val &= AUTO_RANGE
        res['auto_range'] = True if val else False

        # Parallel measurement
        val = raw_data[0x02]
        val &= PARALLEL
        res['parallel'] = True if val else False
        
        # Main measurement
        # Status
        val = raw_data[0x09]
        val &= 0b00001111
        res['main_status'] = STATUS[val]
        
        # Quantity
        val = raw_data[0x05]
        if res['parallel']:
            res['main_quantity'] = MEAS_QUANTITY_PAR[val]
        else:
            res['main_quantity'] = MEAS_QUANTITY_SER[val]
        
        # Value
        val = raw_data[0x06] * 0x100 + raw_data[0x07]
        mul = raw_data[0x08]
        mul &= 0b00000111
        val = val * 10**-mul
        res['main_val'] = val
        
        # Units
        val = raw_data[0x08]
        val &= 0b11111000
        val = val >> 3
        res['main_units'] = MAIN_UNITS[val]
        
        # Secondary measurement
        # Status
        val = raw_data[0x0E]
        val &= 0b00000111
        res['sec_status'] = STATUS[val]
        
        # Quantity
        val = raw_data[0x0A]
        if res['parallel'] and val == 0x03:
            res['sec_quantity'] = RP
        else:
            res['sec_quantity'] = SEC_QUANTITY[val]
        
        # Units
        val = raw_data[0x0D]
        val &= 0b11111000
        val = val >> 3
        res['sec_units'] = MAIN_UNITS[val]
        
        # Value
        val = raw_data[0x0B] * 0x100 + raw_data[0x0C]
        '''If units are % or deg, the value may be negative which is
        represented in two's complement form.
        In this case if the highest bit is 1, the value should be converted
        to negative bu substracting it from 0x10000.'''
        if res['sec_units'] in ('%', 'deg') and val & 0x1000:
            val = val - 0x10000
        mul = raw_data[0x0D]
        mul &= 0b00000111
        val = val * 10**-mul
        res['sec_val'] = val
        
        # Tolerance
        val = raw_data[0x04]
        res['tolerance'] = TOLERANCE[val]
        
        res['data_valid'] = True
        
        return res

    def pretty_print(self):
        '''Prints measurement details in pretty print.'''
        data = self.get_meas()
        
        if DEBUG:
            dic_str = "%s" % data
            dic_str = dic_str.replace(", ", ",\n")
            print dic_str
        
        if data['data_valid'] == False:
            print "DE-5000 is not connected."
            return
        
        # In calibration mode frequency is not displayed.
        if data['cal_mode']:
            print "Calibration"
        else:
            if data['sorting_mode']:
                print "SORTING Tol %s" % data['tolerance']
            print "Frequency: %s" % data['freq']
        
        # LCR autodetection mode    
        if data['lcr_auto']:
            print "LCR AUTO"
        
        # Auto range
        if data['auto_range']:
            print "AUTO RNG"
        
        # Delta mode parameters
        if data['delta_mode']:
            if data['ref_shown']:
                print "DELTA Ref"
            else:
                print "DELTA"
            
        # Main display
        if data['main_status'] == 'normal':
            print "%s = %s %s" % (data['main_quantity'], data['main_val'], data['main_units'])
        elif data['main_status'] == 'blank':
            print
        else:
            print data['main_status']
        
        # Secondary display
        if data['sec_status'] == 'normal':
                if data['sec_quantity'] is not None:
                    print "%s = %s %s" % (data['sec_quantity'], data['sec_val'], data['sec_units'])
                else:
                    print "%s %s" % (data['sec_val'], data['sec_units'])
        elif data['sec_status'] == 'blank':
            print
        else:
            print data['sec_status']

    def __del__(self):
        if hasattr(self, '_ser'):
            self._ser.close()

if __name__ == '__main__':
    pass
