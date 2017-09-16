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

## Software

## Output Examples

## Running The Script

The script can be run from command line using the following command:

```python de5000_reader.py [com_port_name]```

where ```[com_port_name]``` is the name of serial port where your IR receiver is connected. In Windows it will be ```COM1```, ```COM2``` or another COM port. In Linux the will usually be ```/dev/ttyUSB0```, ```/dev/ttyUSB1``` etc.

## Plans for future develompent

[ ] Building a custom IR receiver using a USB UART chip (for example CH340G).

## Links

1. [DER DE-5000 page in sigrok Wiki](https://sigrok.org/wiki/DER_EE_DE-5000)
2. [Cyrustek ES51919 protocol description in sigrok Wiki](https://sigrok.org/wiki/Multimeter_ICs/Cyrustek_ES51919)
3. [Cyrustek ES51919 driver in libsigrok project](https://github.com/merbanan/libsigrok/blob/master/src/lcr/es51919.c)

## Questions? Suggestions?
You are more than welcome to contact me with any questions, suggestions or propositions regarding this project. You can:

1. Visit [my QRZ.COM page](https://www.qrz.com/db/4X1MD)
2. Visit [my Facebook profile](https://www.facebook.com/Dima.Meln)
3. Write me an email to iosaaris =at= gmail dot com

73 de 4X1MD
