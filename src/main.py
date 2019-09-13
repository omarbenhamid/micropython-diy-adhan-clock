# Ecrit ton programme ici ;
from microbit import *
import DS1302

ds=DS1302.DS1302(clk=pin13, dio=pin14, cs=pin15)
display.scroll(str(ds.DateTime()))
