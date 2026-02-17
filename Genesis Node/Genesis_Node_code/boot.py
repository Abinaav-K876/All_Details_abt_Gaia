# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

# boot.py
import _thread
import time
import main
import website

def run_main():
    main.main()

def run_website():
    website.run()

# Start second thread FIRST
_thread.start_new_thread(run_website, ())

# Give scheduler time to start thread
time.sleep_ms(50)

# Run main logic in primary thread
run_main()