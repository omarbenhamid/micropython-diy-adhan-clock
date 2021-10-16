# Manipulating buttons
=> Need to setup ATTN_11DB to use the full range of voltage and be able to identify all buttons.

```
>>> b=ADC(Pin(39))
>>> b.atten(ADC.ATTN_11DB)
>>> b.read()
4095
>>> b.read()
336
>>> b.read()
873
>>> b.read()
1337
>>> b.read()
1824
>>> b.read()
2324
>>> b.read()
2859
>>> b.read()
4095
>>> b.read()
2859
>>> b.read()
4095
```
# Getting SDCard to woork

=> Need to pull down PIN13 to turnon card reader.
```
from machine import *
import os

s=SDCard()
iop=Pin(13,Pin.OUT, Pin.PULL_DOWN)
s.info()
os.mount(s,'/sdcard')
```

# Play adhan

```
import audio

p=audio.player(None)
p.vol(50)
p.play('file://sdcard/01/003.mp3')
```

# Wake on buttons
```
import esp32
from machine import *

esp32.wake_on_ext0(Pin(39,Pin.IN,Pin.PULL_UP), esp32.WAKEUP_ALL_LOW)
machine.deepsleep()
```
# Sys leds 
```
p=Pin(22, Pin.OUT, Pin.PULL_UP)
p.on()
# 27 is blue led.
```
