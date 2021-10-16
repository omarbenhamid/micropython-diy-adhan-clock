"""
ampy --port COM3 put src
ampy --port COM3 put config.json
ampy --port COM3 put web
ampy --port COM3 put main.py

#And you're done...

"""
import sys
sys.path.append('/src')
from src.main import *
