from micropython import const
from machine import *

## Legacy V1 archi
# LED_PIN=const(33)
# WBUTTON_PIN=const(14)
# SPEAKER_PIN=None #const(2)
# AUDIO_PLAYER_UART=const(2)

## Legacy V2 (no volume control, adjusted for soldering)
#LED_PIN=const(14)
#WBUTTON_PIN=const(26)

#VOL_UP_PIN=None
#VOL_DN_PIN=None

#SPEAKER_PIN=None #const(2)
#AUDIO_PLAYER_UART=const(2)

## V3 with volume control
#LED_PIN=Pin(14)
#WBUTTON_PIN=Pin(13)

#VOL_UP_PIN=Pin(25,Pin.IN,Pin.PULL_UP)
#VOL_DN_PIN=Pin(26,Pin.IN,Pin.PULL_UP)

#SPEAKER_PIN=None #const(2)
#AUDIO_PLAYER_UART=const(2)

## Lyrat Min
#import wbuttons
#LED_PIN=Pin(27, Pin.OUT, Pin.PULL_UP)
#ADC_KEYS_PIN=const(39)
#WBUTTON_PIN=wbuttons.ADCButton(1581,2000)
#VOL_UP_PIN=wbuttons.ADCButton(606, 1107)
#VOL_DN_PIN=wbuttons.ADCButton(0, 606)
#AUDIO_PLAYER_UART=None

# A1S 3378 ES8388
# https://docs.ai-thinker.com/en/esp32-audio-kit
# Keys: 5 18 23 19 13 36 
# Pin(23,Pin.IN,Pin.PULL_UP)

LED_PIN=Pin(19, Pin.OUT, Pin.PULL_DOWN)
LED_ON_VALUE=False
ADC_KEYS_PIN=None
WBUTTON_PIN=Pin(5,Pin.IN,Pin.PULL_UP)
VOL_UP_PIN=Pin(19,Pin.IN,Pin.PULL_UP)
VOL_DN_PIN=Pin(36,Pin.IN,Pin.PULL_UP)
AUDIO_PLAYER_UART=None

WEB_DIR="/web" #No / at the end please ...
