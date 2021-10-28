import sys
sys.path.append('/src')

import wifi

wifi.connect()

import livestream
import taskloop
import arch

STREAMURL="https://audio-edge-3mayu.fra.h.radiomast.io/01dfcaea-c442-4fb8-8acf-c3c83e236000"

livestream.LS_POLL_DELAY_MS=30000
livestream.LS_CB_TRIGGER_DELAY_MS=1000

def live_status_cb(available):
    arch.LED_PIN.value(available)
    print("Stream available : %r" % available)

l=livestream.LiveStream(STREAMURL, live_status_cb)

#l.set_status_callback(live_status_cb)

def on_click(pin):
    print("BTN")
    if l.isplaying():
        l.stop()
        return
    
    if not l.playnow():
        print("Stream unavailable")
    
arch.WBUTTON_PIN.irq(on_click)

taskloop.mainloop()