import configparser
from Apirate import Timer
from Reminders import do_send_botmessage

messages=[]
def cleanspaces(astring):
    return astring.rstrip().lstrip()

def get_config():
    messages=[]
    config=configparser.ConfigParser()
    config.read('config.ini')
    if len ( list(str(config['sendmsgs'].get('enabled')).rsplit(sep=',')) )  >= 1: 
        for i in list(str(config['sendmsgs'].get('enabled')).rsplit(sep=',')) :
            if len(list(str(config['sendmsgs'].get('room{}'.format(i[-1]))).rsplit(sep=',') )) >1:
                for r in list(str(config['sendmsgs'].get('room{}'.format(i[-1]))).rsplit(sep=',') ):
                    message= {'msg':str(config['sendmsgs'].get(i)),
                  'speriod':int(config['sendmsgs'].get('speriod{}'.format(i[-1]))),
                  'offset':int(config['sendmsgs'].get('offset{}'.format(i[-1]))),
                  'room':cleanspaces(r)}
                    messages.append(message)
            else:  
                message={'msg':str(config['sendmsgs'].get(i)),
                  'speriod':int(config['sendmsgs'].get('speriod{}'.format(i[-1]))),
                  'offset':int(config['sendmsgs'].get('offset{}'.format(i[-1]))),
                  'room':str(config['sendmsgs'].get('room{}'.format(i[-1])))}
                messages.append(message)
    return messages

def send_messages(messages):
    if len(messages)>=1:
        timers={}
        for n,m in enumerate(messages):
            timers[str(n)]=Timer(m['offset'])
        while True:
            try: 
                for n,m in enumerate( messages ):
                    if timers[str(n)].get_time()>m['speriod']:
                        timers[str(n)].reset_time()
                        do_send_botmessage(m['msg'], m['room'])
            except:
                pass
                    
if __name__ == '__main__':
    messages=get_config()
    send_messages(messages)
