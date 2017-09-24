'''

'''
import json
from time import sleep,time
from sys import exc_info
import urllib.request
from Apirate import thresh,Timer
###################################################################################

#below is the text you should be sending please pay attention to the ''' at the start and the end 
remindertxt=( '''

Hello!
This is a text that follows slack guidelines *for*  _formating_ `about` links and usernames
Make sure to change them to reflect your values if you are to use those
<@USLACKBOT|slackbot> <- This is a username
<https://slack-files.com/T5L09JNUA-F6XLDJ4Q6-18eb910248| a *SCAM* phising email >  <- this is a url
*<#C5L1R4QAL|general>*  <- This is a channel

''' )


                                                
token1 = ('xoxp-2071de56cfe') #user1  token
token2 = ('xoxb-2423cujQV') #bot1  token

period =  86400# period in seconds for which the reminders send circle will restart
msgroomid=  'G6GUDUN22' # id of the room for bot messages for reports

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
         
        do_send_botmessage('WARN:get_users error, '+str(result1['error']), msgroomid)
    result['members']=result1['members']+result['members']
    x=0 # max 50 checks for 1000 users each, just to leave the while loop if slack changes something
        # in case of more than 50K users need to adjust
    while 'response_metadata' in result1.keys() and ( 
        result1['response_metadata']['next_cursor'] )is not "" and x <50:
        
        cursor=result1['response_metadata']['next_cursor']
        url = ( 'https://slack.com/api/users.list?token='
                +token+'&limit=1&presense=false&cursor='+cursor )
        
        result1=create_request(url,timeout=0.01)
        result['members']=result1['members']+result['members']
        if result1['ok']==False:
            do_send_botmessage('WARN:get_users error, '+str(result1['error']), msgroomid)
    return result
 


def find_user_byid(userid,allusersids):
    try:
        return allusersids[0][allusersids[1].index(userid)]
    except :
        pass

def do_send_botmessage(message,roomformessage=msgroomid):
    '''sends a message as the bot user  to the admins chatroom'''
    text=urllib.parse.quote_plus(message)
    url = ( 'https://slack.com/api/chat.postMessage?token='
            +token2+'&channel='+roomformessage+'&text='+text )     
    posted,retries=False,0
    while posted == False and retries < 2 :
        
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if result['ok']==False:
            
            do_send_botmessage('WARN:do_send_botmessage error, '+str(result['error']), msgroomid)
            
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
                    do_send_botmessage('WARN:send_reminder error, '+str(result['error']), msgroomid)
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

def main1():
    results1['users.list'] = get_users(token2)
    allusersids = gather_allusers(results1)
    do_send_botmessage("INFO: Start of reminders Sending")
    for i in allusersids[1]:
        do_send_reminder(remindertxt, i, 1) 
    do_send_botmessage("INFO: End of reminders Sending")  


def main2():
    timer=Timer()
    while True:
        try:
            if timer.get_time() >= period or timer.run < 3 :
                timer.reset_time()
                try:
                    main1()
                except:
                    do_send_botmessage('CRIT:Exception in Reminders, '+str(exc_info ()[1])+
                                   '\n\n \nsleeping 60 seconds before running again')
                    sleep(60) #sleep is mostly to avoid many slack diconnection errors
        except:
            pass
main2()