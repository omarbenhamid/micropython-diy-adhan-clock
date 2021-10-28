from machine import ADC, Pin
import esp32
import taskloop
import sys


class ADCButton:
    def __init__(self, minval, maxval):
        self.min=minval
        self.max=maxval
        self._irqcallback=None
        self._lastpressed=None #Up is not pressed
        
    def match(self, reading):
        return reading > self.min and reading <= self.max
    
    def falling(self, reading): #= pressing
        pressed=self.match(reading)
        if self._lastpressed == None:
            self._lastpressed = pressed
            return False
        if self._lastpressed:
            self._lastpressed=pressed
            return False
        else:
            self._lastpressed=pressed
            return pressed #Was not pressed, return true if pressed false if not.
    
    def value(self):
        # To mimic pin buttons: 0 => Pressed, 1 => released
        if self.match(get_adc().read()): return 0
        else: return 1
        
    def triggerirq(self, pin):
        if self._irqcallback:
            self._irqcallback(pin)
        
    def irq(self, callback, trigger=Pin.IRQ_FALLING):
        if trigger != Pin.IRQ_FALLING: 
            raise Exception("Unsupported event registration for ADC Button")
        self._irqcallback=callback
        add_listen(self, self.triggerirq)

_adc=None
def get_adc():
    global _adc
    if _adc: return _adc
    
    import arch
    if arch.ADC_KEYS_PIN:
        _adc=ADC(Pin(arch.ADC_KEYS_PIN))
        _adc.atten(ADC.ATTN_11DB)
        return _adc
    return None

__adc_listeners=[]


def add_listen(pin_or_adc, callback):
    """
        call back receives pin or adc as parameter.
    """
    if isinstance(pin_or_adc, ADCButton):
        __adc_listeners.append((pin_or_adc, callback))
    elif isinstance(pin_or_adc, Pin):
        pin_or_adc.irq(callback, Pin.IRQ_FALLING)
    else:
        raise Exception("Unable to handle this type of buttons : %r" % pin_or_adc)

def setup_wakeup(pin_or_adc):
    if isinstance(pin_or_adc, ADCButton):
        import arch
        esp32.wake_on_ext0(Pin(arch.ADC_KEYS_PIN,Pin.IN,Pin.PULL_UP), esp32.WAKEUP_ALL_LOW)
    elif isinstance(pin_or_adc, Pin):
        esp32.wake_on_ext0(pin_or_adc, esp32.WAKEUP_ALL_LOW)
    else:
        raise Exception("Unable to handle this type of buttons : %r" % pin_or_adc)


def check_adc_listeners():
    global __adc_listeners
    r=get_adc().read()
    for btn, cb in __adc_listeners:
        if btn.falling(r):
            try: 
                cb(btn)
            except Exception as err:
                sys.print_exception(err)

taskloop.sched_task(check_adc_listeners, repeat_ms=20)
