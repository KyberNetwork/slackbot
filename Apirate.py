
from time import sleep
import time



##################
seconds=5 # after Y seconds the api rate counter will become 0
apireqs=2 # X api requests will be allowed ever Y seconds
##################
class APIcount:
    '''Class that checks that no more than `apireqs` number of API calls can be made for a period 
    of `seconds` seconds .If more calls than that are made it waits minimum 1 second until API
    calls are freed'''
    maxsecs=seconds
    maxcalls=apireqs
    def __init__(self,calls=0):
        self.calls=calls
        self.starttime=time.time()
        self.activetime=time.time()-self.starttime
    def __send(self,apicall=1):
        if self.calls==0:
            self.starttime=time.time()
        self.calls=self.calls + apicall
        self.activetime=time.time()-self.starttime
    def reset(self):
        self.calls=0
    def check(self):
        self.__send()
        if self.calls < self.maxcalls:
            pass
        elif self.calls >=self.maxcalls and self.activetime < self.maxsecs:
            time.sleep(int(round(self.maxsecs-self.activetime))+1)
            self.reset()
            pass
        elif self.calls>=self.maxcalls and self.activetime>=self.maxsecs:
            self.reset()
            #time.sleep(1)
            pass


        
class Timer:
    def __init__(self,extrasec=0):
        self.extra=extrasec
        self.start=time.time()
        self.run=1

    def get_time(self):
        self.run+=1
        return time.time()-self.start+self.extra
    def reset_time(self):
        self.run=2
        self.start=time.time()

thresh=APIcount()