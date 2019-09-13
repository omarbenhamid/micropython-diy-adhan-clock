from microfs import main; 
import sys

sys.argv=['ufs','put','src/main.py']
main()
sys.argv=['ufs','put','DS1302/DS1302.py']
main()


