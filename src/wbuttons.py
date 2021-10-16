import time
from machine import ADC, Pin
import esp32

class ADCButton:
    def __init__(self, minval, maxval):
        self.min=minval
        self.max=maxval
        
    def match(self, reading):
        return reading > self.min and reading <= self.max
    
    def value(self):
        # To mimic pin buttons: 0 => Pressed, 1 => released
        if self.match(get_adc().read()): return 0
        else: return 1
        
    def irq(self, callback, trigger=Pin.IRQ_FALLING):
        if trigger != Pin.IRQ_FALLING: 
            raise Exception("Unsupported event registration for ADC Button")
        add_listen(self, callback)

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

pendingtask=pttime=None

def sched_task(self,taskfn, exectime_ms=0):
    global pendingtask, pttime
    """ Call the given callable when waiting read:
    taskfn will be called.
    if exectime_ms is set, it will run when time.ticks_ms() reaches this value.
    This is mainly here to be able to handle irqs while reading ...
    """
    pendingtask=taskfn
    pttime=exectime_ms
    
def _perform_pending():
    global pendingtask, pttime
    if pendingtask and pttime <= time.ticks_ms():
        task=pendingtask
        pendingtask=None
        task()
        return True
    return False

def getfalse():
    return False

def mainloop(stopcond=getfalse):
    global runloop
    runloop=True
    adc=get_adc()
    print("Running mainloop, use Ctrl+C to get REPL")
    while runloop and not stopcond():
        r=adc.read()
        for btn, cb in __adc_listeners:
            if btn.match(r):
                try: 
                    cb(btn)
                except:
                    pass
        if not _perform_pending():
            time.sleep_ms(20)
    _perform_pending()
        
            
def stoploop():
    global runloop
    runloop=False