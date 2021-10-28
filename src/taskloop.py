import time

'''
Created on Oct 28, 2021

@author: omar
'''

MIN_LOOP_TIME_MS=20

tasks=[]

def sched_task(taskfn, exectime_ms=0, repeat_ms=0):
    global tasks
    """ Call the given callable when waiting read:
    taskfn will be called.
    if exectime_ms is set, it will run when time.ticks_ms() reaches this value.
    This is mainly here to be able to handle irqs while reading ...
    """
    tasks.append([taskfn,exectime_ms,repeat_ms])

def unsched_task(taskfn, exectime_ms=None, repeat_ms=None):
    global tasks
    tasks=list(pt for pt in tasks if 
        pt[0] != taskfn or not (exectime_ms != None and pt[1] == exectime_ms) \
        or not (repeat_ms != None and pt[2] == repeat_ms))
    
    
def _perform_tasks(etick=None, clean=True):
    global tasks
    etick=etick or time.ticks_ms()
    for t in tasks:
        pendingtask,pttime,rep = t
        if pttime==None: continue
        if pttime > etick: continue #task in furter
        pendingtask()
        if rep > 0: #reschedule for next time.
            t[1]=etick+rep
        else:
            t[1]=None #disable task
    if clean:
        tasks=[ t for t in tasks if t[1] != None]

def getfalse():
    return False



def mainloop(stopcond=getfalse):
    global runloop
    print("Running mainloop, use Ctrl+C to get REPL")
    
    runloop=True
    while runloop and not stopcond():
        etick=time.ticks_ms()
        _perform_tasks(etick, False)
        slot=MIN_LOOP_TIME_MS-(time.ticks_ms()-etick)
        if slot > 0:
            time.sleep_ms(slot)
    _perform_tasks(clean=True)
        
            
def stoploop():
    global runloop
    runloop=False