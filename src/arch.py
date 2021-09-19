from micropython import const

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
LED_PIN=const(14)
WBUTTON_PIN=const(13)

VOL_UP_PIN=const(25)
VOL_DN_PIN=const(26)

SPEAKER_PIN=None #const(2)
AUDIO_PLAYER_UART=const(2)



WEB_DIR="/web" #No / at the end please ...