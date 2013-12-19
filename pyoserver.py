import OSC
import pyo
import time
import threading

address = '127.0.0.1'
port = 1066

s = OSC.OSCServer((address, port))
s.addDefaultHandlers()

p = pyo.Server().boot()
p.start()

a = pyo.Sine(freq=220, mul=0.3).out()

def pitch_handler(addr, tags, stuff, source):
    a.freq = 440 + stuff[1]

def printing_handler(addr, tags, stuff, source):
    print "---"
    print "received new osc msg from %s" % OSC.getUrlStr(source)
    print "with addr : %s" % addr
    print "typetags %s" % tags
    print "data %s" % stuff
    print "---"

s.addMsgHandler("/pitch", pitch_handler)
s.addMsgHandler("/print", printing_handler) # adding our function

# just checking which handlers we have added
print "Registered Callback-functions are :"
for addr in s.getOSCAddressSpace():
    print addr

# Start OSCServer
print "\nStarting OSCServer. Use ctrl-C to quit."
st = threading.Thread( target = s.serve_forever )
st.start()

try :
    while 1 :
        time.sleep(5)

except KeyboardInterrupt :
    print "\nClosing OSCServer."
    s.close()
    print "Waiting for Server-thread to finish"
    st.join() ##!!!
    print "Done"