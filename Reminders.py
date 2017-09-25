'''

'''
import json
from time import sleep
from sys import exc_info
import urllib.request
from Apirate import thresh,Timer
import configparser

config= configparser.ConfigParser()
config.read('config.ini')
remindertxt= str(config['reminders'].get('remindertxt'))
token1 = str(config['reminders'].get('usertoken') ) #user1  token
token2 = str (config['general'].get('bottoken') ) #bot1  token
rperiod =  int(config['reminders'].get('rperiod') )# period in seconds for which the reminders send circle will restart
botroomid=  str(config['reminders'].get('botroomid') ) # id of the room for bot messages for reports

########################################################################################
timeout=2  #timeout in seconds for http requests
allusersids=[]
results1={}


def create_request(url,timeout=timeout,headers={},data=None): 
    cr=urllib.request.Request(url)
    thresh.check()
    with urllib.request.urlopen(cr,timeout=timeout) as req:
        x=0
        while x<2:
            try:
                result=json.loads(req.read().decode('utf-8'))
                return result
            except:
                x=x+1
    


def get_users(token):
    '''gets the users list'''
    cursor=""
    url = ( 'https://slack.com/api/users.list?token='
            +token+'&limit=1000&presence=false' ) 
        
    result={'members':[]} 
    result1=  create_request(url)
    if result1['ok']==False:
        do_send_botmessage('WARN:get_users error, '+str(result1['error']), botroomid)
    result['members']=result1['members']+result['members']
    x=0 # max 50 checks for 1000 users each, just to leave the while loop if slack changes something
        # in case of more than 50K users need to adjust
    while 'response_metadata' in result1.keys() and ( 
        result1['response_metadata']['next_cursor'] )is not "" and x <50:
        
        cursor=result1['response_metadata']['next_cursor']
        url = ( 'https://slack.com/api/users.list?token='
                +token+'&limit=1&presence=false&cursor='+cursor )
        sleep(15) # Slack is very aggressive with this request, they throw 429 very easily
        result1=create_request(url,timeout=0.01)
        x+=1
        result['members']=result1['members']+result['members']
        if result1['ok']==False:
            do_send_botmessage('WARN:get_users error, '+str(result1['error']), botroomid)
    return result
 


def find_user_byid(userid,allusersids):
    try:
        return allusersids[0][allusersids[1].index(userid)]
    except :
        pass

def do_send_botmessage(message,roomformessage=botroomid):
    '''sends a message as the bot user  to the admins chatroom'''
    text=urllib.parse.quote_plus(message)
    url = ( 'https://slack.com/api/chat.postMessage?token='
            +token2+'&channel='+roomformessage+'&text='+text )     
    posted,retries=False,0
    while posted == False and retries < 2 :
        
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if result['ok']==False:
            
            do_send_botmessage('WARN:do_send_botmessage error, '+str(result['error']), botroomid)
            
def do_send_reminder(message,username,intime):
    '''sends a reminder message to user in intime seconds'''
    text=urllib.parse.quote_plus(message)
    url = ( 'https://slack.com/api/reminders.add?token='
            +token1+'&text='+text+
            '&time='+str(intime)+'&user='+username)
    posted,retries=False,0
    x=0
    while x<3:
        try:
            while posted == False and retries < 3 :
                
                result=create_request(url)
                posted,retries=result['ok'],retries+1
                x=3
                if result['ok']==False:
                    do_send_botmessage('WARN:send_reminder error, '+str(result['error']), botroomid)
        except:
            x=x+1
            
def gather_allusers(results1):
    '''returns list with 2 elements, users and userids'''
    allusers=[]
    allids=[]
    for i in range(len(results1['users.list']['members'])):
        if (results1['users.list']['members'][i]['deleted']
            ==False) and results1['users.list']['members'][i]['is_bot']==False and(
                results1['users.list']['members'][i]['id'] !=  'USLACKBOT' ):
            allusers.append(results1['users.list']
                            ['members'][i]['name'])
            allids.append(results1['users.list']
                            ['members'][i]['id'])
    return allusers,allids

def sendreminders():
    results1['users.list'] = get_users(token2)
    allusersids = gather_allusers(results1)
    do_send_botmessage("INFO: Start of reminders Sending")
    for i in allusersids[1]:
        do_send_reminder(remindertxt, i, 1) 
    do_send_botmessage("INFO: End of reminders Sending")  


def timedsendreminders():
    timer=Timer()
    while True:
        try:
            if timer.get_time() >= rperiod or timer.run < 3 :
                timer.reset_time()
                try:
                    sendreminders()
                except:
                    do_send_botmessage('CRIT:Exception in Reminders, '+str(exc_info ()[1])+
                                   '\n\n \nsleeping 60 seconds before running again')
                    sleep(60) #sleep is mostly to avoid many slack diconnection errors
        except:
            pass
        
if __name__ == '__main__':
    timedsendreminders()