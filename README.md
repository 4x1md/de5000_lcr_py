# DER DE-5000 Python Library
Python library for reading data from DER DE-5000 LCR meter.

![DE-5000](https://raw.githubusercontent.com/4x1md/de5000_lcr_py/master/images/de-5000.jpg)

## Overview

This library was written as a weekend project. Its main goal was to know better the DE-5000 meter and to check the possibility to use a non-original IR receiver to read its measurements.

## Connecting to DE-5000

I bought this meter from one of Japanese sellers on eBay for about $100. The lot did not include USB module. I didn't think I'll ever need one.

The LCR meter transmits its data using IR port. I had already the RS-232 connection cable from the UNI-T UT61E multimeter and I was curious if it could work with DE-5000 as well.

![DE-5000](https://raw.githubusercontent.com/4x1md/de5000_lcr_py/master/images/de-5000_ut61e.jpg)

An experiment showed that the answer is yes. Yhe IR receiver which comes with UT61E can be used to read data from DE-500. I'm quite sure that it will work with other DER DE multimeters too. They are not compatible mechanically but when the IR receiver is placed at about 5-10 cm from the LCR meter, the reception is quite stable.

## DE-5000 protocol

The meter uses Cyrustek ES51919 chipset which is also used in other LCR meters. There is no official information about it I could found. My only source was [ES51919 protocol description](https://sigrok.org/wiki/Multimeter_ICs/Cyrustek_ES51919) and [ES51919 driver](https://github.com/merbanan/libsigrok/blob/master/src/lcr/es51919.c) in [sigrok project](https://sigrok.org/wiki/Main_Page). They did a very good job on reverse engineering!

Each packet contains 17 bytes.

```
Byte	Meaning
====	=======
0x00	Header, always 0x00
0x01	Header, always 0x0D

0x02	Flags
        bit 0: hold enabled
        bit 1: reference value shown in delta mode (delta sign is blinking)
        bit 2: delta mode
        bit 3: calibration mode
        bit 4: sorting mode
        bit 5: LCR AUTO mode
        bit 6: auto range mode (is not used in sorting mode only)
        bit 7: parallel measurement (vs. serial)

0x03	Config
        bit 0-4: unknown
        bit 5-7: test frequency
				0 = 100 Hz
				1 = 120 Hz
				2 = 1 kHz
				3 = 10 kHz
				4 = 100 kHz
				5 = 0 Hz (DC)


0x04	Tolerance in sorting mode
		0 = not set
		3 = +-0.25%
		4 = +-0.5%
		5 = +-1%
		6 = +-2%
		7 = +-5%
		8 = +-10%
		9 = +-20%
	   10 = -20+80%

Bytes 0x05-0x09 describe primary measurement
0x05	Measured quantity
		1 = inductance
		2 = capacitance
		3 = resistance
		4 = DC resistance

0x06	Measurement MSB  (0x4e20 = 20000 = outside limits)
0x07	Measurement LSB

0x08	Measurement info
		bit 0-2: decimal point multiplier (10^-val)
		bit 3-7: units
			0 = no unit
			1 = Ohm
			2 = kOhm
			3 = MOhm
			4 = ?
			5 = uH
			6 = mH
			7 = H
			8 = kH
			9 = pF
			10 = nF
			11 = uF
			12 = mF
			13 = %
			14 = degree

0x09	Measurement display status
		bit 0-3: Display mode
			0 = normal (measurement shown)
			1 = blank (nothing shown)
			2 = lines ("----")
			3 = outside limits ("OL")
			7 = PASS (sorting mode)
			8 = FAIL (sorting mode)
			9 = OPEn (calibration mode)
			10 = Srt (calibration mode)
		bit 4-6: Unknown (maybe part of same field with 0-3)
		bit 7:   Unknown

Bytes 0x0A-0x0E describe secondary measurement
0x0A	Measured quantity
		0 = none
		1 = D (dissipation factor)
		2 = Q (quality factor)
		3 = ESR/RP (serial/parallel AC resistance)
		4 = Theta (phase angle)

0x0B	Measurement MSB
0x0C	Measurement LSB

0x0D	Measurement info
		bit 0-2: decimal point multiplier (10^-val)
		bit 3-7: units (same as in primary measurement)

0x0E	Measurement display status. Same as byte 0x09 in primary measurement.

0x0F	Footer, always 0x0D
0x10	Footer, always 0x0A

```

Each measurement value is encoded by 3 bytes: two bytes for value (bytes 0x06, 0x07 for primary and 0x0B, 0x0C for secondary) and 3 bits of another byte for multiplier (bytes 0x08 for primary and 0x0D for secondary). The value can be calculated using the following formula:

```(MSB * 0x10000 + LSB) * 10^-multiplier```

## Program structure, settings and output data format

### DE5000() class

Class constructor requires serial port name only. all other settings are defined by the following constants.

```BAUD_RATE```, ```BITS```, ```PARITY```, ```STOP_BITS```: serial port settings (always 9600, 8N1).

```TIMEOUT```: serial port read timeout.

```EOL```: footer bytes of valid data packet. Always 0x0D 0x0D (CR, LF or \r\n).

```RAW_DATA_LENGTH```: data packet size.

```READ_RETRIES```: packet reading retries. This value shows how many retries to receive a valid packet should be done before returning an error.

The class contains the following functions:

```read_raw_data(self)```: reads raw data packet from serial port as array of byte values.

```is_data_valid(self, raw_data)```: returns ```True``` if the received packet is valid.

```read_hex_str_data(self)```: returns string with hexadecimal byte values of the received packet.

```get_meas(self)```: parses the received packet and returns the data as dicitonary (explained later).

```normalize_val(self, val, units)```:  normalizes the measured value to standard units (R to Ohm, C to Farad, L to Henry, others are not changed).

```pretty_print(self, disp_norm_val = False)```: prints the received measurement in human readable form.

### Returned data format

The measured value is returned by ```get_meas(self)``` function as a dictionary with the following fields:

```main_quantity```: string, main displayed quantity (Ls, Lp, Cs, Cp, Rs, Rp, DCR),

```main_val```: float, main displayed value,

```main_units```: string, main displayed units,

```main_status```: string, main display status (value, blank, OL, PASS, FAIL etc.),

```main_norm_val```: float, main displayed value, normalized to standard units (Ohm, Farad, Henry),

```main_norm_units```: string, units of normalized value, 

```sec_quantity```: string, secondary displayed quantity (D, Q, Theta, ESR etc.), 

```sec_val```: float, secondary displayed value,

```sec_units```: string, secondary display units,

```sec_status```: string, secondary display status (value, blank, OL, ---- etc.),

```sec_norm_val```: float, secondary displayed value, normalized to standard units (Ohm, Farad, Henry),

```sec_norm_units```: string, units of normalized value,

```freq```: string, test frequency,

```tolerance```: string, tolerance in sorting mode,

```ref_shown```: boolean, True if reference value is shown in REL % mode (delta sign is blinking),

```delta_mode```: boolean, True if the device is in REL % (delta) mode,

```cal_mode```: boolean, True when calibration mode is active,

```sorting_mode```: boolean, True if the device is in sorting mode,

```lcr_auto```: boolean, True if the device is in LCR AUTO mode (autodetection of DUT type),

```auto_range```: boolean, True if auto range is active (all modes except sorting),

```parallel```: boolean, True if the measurement is done in parallel mode,

```data_valid```: boolean, True if data in the dictionary is valid.

### de5000_reader.py

```PORT```: default serial port which will be used if it is not specified in command line.

```SLEEP_TIME```: time between reading measurements.

## Output examples

## Running the script

The script can be run from command line using the following command:

```python de5000_reader.py [com_port_name]```

where ```[com_port_name]``` is the name of serial port where your IR receiver is connected. In Windows it will be ```COM1```, ```COM2``` or another COM port. In Linux the will usually be ```/dev/ttyUSB0```, ```/dev/ttyUSB1``` etc.

## Plans for future develompent

1. [ ] Adding an option of saving the measured data to csv file.
2. [ ] Building a custom IR receiver using a USB UART chip (for example CH340G).

## Links

1. [DER DE-5000 page in sigrok Wiki](https://sigrok.org/wiki/DER_EE_DE-5000)
2. [Cyrustek ES51919 protocol description in sigrok Wiki](https://sigrok.org/wiki/Multimeter_ICs/Cyrustek_ES51919)
3. [Cyrustek ES51919 driver in libsigrok project](https://github.com/merbanan/libsigrok/blob/master/src/lcr/es51919.c)
4. [DER DE-5000 datasheet](http://www.ietlabs.com/pdf/Datasheets/DE_5000.pdf)

## Questions? Suggestions?
You are more than welcome to contact me with any questions, suggestions or propositions regarding this project. You can:

1. Visit [my QRZ.COM page](https://www.qrz.com/db/4X1MD)
2. Visit [my Facebook profile](https://www.facebook.com/Dima.Meln)
3. Write me an email to iosaaris =at= gmail dot com

73 de 4X1MD
