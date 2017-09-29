
from time import time
from Reminders import create_request,do_send_botmessage,get_users
from Messenger import cleanspaces
import configparser
import requests
from Apirate import thresh,Lograte
import re
import urllib.request
import json
import asyncio
import websockets


config = configparser.ConfigParser()
config.read ( 'config.ini')

webtoken = config['realtime'].get('webtoken')
xid=config['realtime'].get('xid')
bottoken = str (config['general'].get('bottoken') ) #bot1  token 
botroomid =  str(config['reminders'].get('botroomid') ) # id of the room for bot messages for reports
teamurl = config['general'].get('teamurl')
admintoken = str (config['general'].get('admintoken') ) #user1 token

channels={}
alloweddomains = []
commandsall= []
commandprefix = '!'
alloweduserids = []
muted_users = []
results1 = {}
secfeaturesconf={}
simplecommands={}
seccommands={}
secfeatures={}
def get_config_simplecommands2():
    simplecommands={}
    if len (list(str(config['simplecommands'].get('enabled')).rsplit(sep=',')) ) >=1:
        for i in list(str(config['simplecommands'].get('enabled')).rsplit(sep=',')):
            simplecommands[cleanspaces(i)] =  str(config['simplecommands'].get(i))
    return simplecommands

def get_config_simplecommands():
    simplecommands={}
    if len ( list(str(config['simplecommands'].get('enabled')).rsplit(sep=',')) )  >= 1: 
        for i in list(str(config['simplecommands'].get('enabled')).rsplit(sep=',')) : 
            simplecommands[cleanspaces(str(config['simplecommands'].get(cleanspaces(i))))]=(
                            str(config['simplecommands'].get('text{}'.format(i[-1]))))
    return simplecommands
        
def get_config_seccommands():
    seccommands={}
    for i in config['seccommands'] :
        seccommands[i] = str(config['seccommands'].get(i))
    return seccommands

def get_config_secfeatures():
    secfeatures={}
    for i in config['secfeatures']:
        secfeatures[i] = config['secfeatures'].getboolean(i)
    return secfeatures

def get_config_secfeaturesconf():
    secfeaturesconf={}
    for i in config['secfeaturesconf']:
        if len ( list(config['secfeaturesconf'].get(i).rsplit(sep=',')) ) > 1 :
            secfeaturesconf[i]= list(config['secfeaturesconf'].get(i).rsplit(sep=',')) 
            for s in  range(len(secfeaturesconf[i])):
                secfeaturesconf[i][s]= cleanspaces(secfeaturesconf[i][s])
        else:
            secfeaturesconf[i] = config['secfeaturesconf'].get(i,'erxJpBCVmzZqzM5Vh')
    return secfeaturesconf    

def get_socket_url(token):
    url=(' https://slack.com/api/rtm.connect?token='+
    token+'&batch_presence_aware=true&presence_sub=true')
    wssurl=create_request(url)
    return wssurl

def do_kick_user(channel,user,token=admintoken):
    '''empties the channel fromt the user'''
    url = ( 'https://slack.com/api/channels.kick?token='
            +token+'&channel='+channel+'&user='+user)
    posted,retries=False,0
    while posted == False and retries < 1 :
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if result['ok']==False:
            do_send_botmessage('WARN:do_kick_user error, '+str(result['error']), botroomid)

def do_send_botephemeral(message,room,user,token=bottoken):
    '''sends an ephemeral message as the bot user  to the user in the room'''
    text=urllib.parse.quote_plus(message)
    url = ( 'https://slack.com/api/chat.postEphemeral?token='
            +token+'&channel='+room+'&text='+text+'&user='+user )     
    posted,retries=False,0
    while posted == False and retries < 3 :
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if result['ok']==False:
            do_send_botmessage('WARN:do_send_botmessage error, '+str(result['error']), botroomid)

def get_user_info(userid,token=bottoken):
    '''returns the username of the user. not very efficient, it makes a call'''
    url = ( 'https://slack.com/api/users.info?token='
            +token+'&user='+userid )
    result = create_request(url)
    return result['user']['name']


def check_prohibited(text,prohibited):
    '''Checks all words of a string, returns true if they are in list with prohibited or false'''
    a=text.lower().rsplit()
    b="".join(a)
    
    for y in prohibited:
        if bool(re.match('.?.*'+y+'.?.*',b)):
            return True
    return False        

def similar_eth(text):
    '''This function finds if a message text is similar to an ETH address'''
    for i in text.rsplit():
        a = re.match('.?.*0[x,X][0-9A-Fa-f]+',i)
        
        if bool(a) and a.span()[1] >= 42:
            return True

def similar_btc(text):
    '''This function finds if a message text is similar to a BTC address'''
    for i in text.rsplit():
        a = re.match('.?.[1,3][1-9A-HJ-NP-Za-km-z]+',i)
        
        if bool(a) and a.span()[1] >= 27 :
            return True

def similar_prv(text):
    '''This function finds if a message text is similar to an ETH private key'''
    for i in text.rsplit():
        a = re.match('.?.[0-9A-Fa-f]+',i)
        
        if bool(a) and a.span()[1] >= 64:
            return True
    

def similar_command(text):
    '''returns True if the message posted by the user looks like a command'''
    a=text.lower().rsplit()
    b="".join(a)
    if bool(re.match("\\"+commandprefix+'.*',b)) and len (b) <25 and b not in commandsall :
        return True
    return False

    
    
def clean_username(text):
    b=text[2:-1]
    return b.upper()

def check_mute(text,user):
    if text.lower()[:5]=='!mute':
        if user in alloweduserids:
            if clean_username(text.lower().rsplit()[1]) not in alloweduserids:
                return True
            
def check_ban(text,user):
    if text.lower()[:4]=='!ban' and len(text.rsplit())==2:
        if user in alloweduserids and clean_username(text.lower().rsplit()[1]) not in alloweduserids:
            return True
        
def check_unmute(text,user):   
    if text.lower()[:7]=='!unmute':
        if user in alloweduserids:
            if clean_username(text.lower().rsplit()[1]) in muted_users:
                return True
            
def check_unban(text,user):
    if text.lower()[:6]=='!unban'  and len(text.rsplit())==2 :
        if user in alloweduserids and clean_username(text.lower().rsplit()[1]) not in alloweduserids:
            return True

def do_mute(text):
    
    global muted_users
    if clean_username(text.lower().rsplit()[1]) not in muted_users:
        muted_users.append(clean_username(text.lower().rsplit()[1]))
def do_unmute(text):
    global muted_users
    if clean_username(text.lower().rsplit()[1])  in muted_users:
        muted_users.remove(clean_username(text.lower().rsplit()[1]))
        
            
def check_muted(user,muted_users=muted_users):
    if user in muted_users:
        return True

def is_url(text):
    a=text.lower().rsplit()
    c=[]
    for i in a:
        c.append(re.match ('.?.*http.?.*',i))
    matches=0
    for i in c:
        if i is not None:
            matches=matches+bool(i)
    if matches>=1:
        return True,matches
    return False,0

def is_allowedurl(text,alloweddomains):
    a=text.lower().rsplit()
    c=[]
    
    for i in a:
        for d in alloweddomains: 
            c.append(re.match ('.?.*http.?.?.?.?.*\.'+d+'\/.?.*',i))
            c.append(re.match ('.?.*http.?.?.?.?.*\.'+d+'>$',i))
            c.append(re.match ('.?.*http.?.?.?.?.*\/'+d+'>$',i))
            c.append(re.match ('.?.*http.?.?.?.?.*\/'+d+'\|'+d+'>$',i))

    matches=0
    
    for r in c:
        if r is not None:
            matches=matches+bool(i)
    if matches>=1:
        return True,matches
    return False,0

def check_forbidden(text,forbidden):
    '''Checks all words of a string, returns true if they are in forbidden or false'''
    a=text.lower().rsplit()
    b="".join(a)
    
    for i in forbidden:
        if bool(re.match('.?.*'+i+'.?.*',b)):
            return True
    return False    
    
def delete_text(channel,ts,token=admintoken):
    url = ( 'https://slack.com/api/chat.delete?token='
            +token+'&channel='+channel+'&ts='+ts) 
    '''deletes a message posted taking as input the channel and the timestamp'''
    posted,retries=False,0
    while posted == False and retries < 1 :
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if result['ok']==False:
            do_send_botmessage('WARN:do_delete_chat error,  '+str(result['error']), botroomid)
        
def delete_file(fileid,token=admintoken):
    'deletes a specified file posted'
    url = ( 'https://slack.com/api/files.delete?token='
            +token+'&file='+fileid)  
    posted,retries=False,0
    while posted == False and retries < 1 :
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if result['ok']==False:
            do_send_botmessage('WARN:do_delete_file error, '+str(result['error']), botroomid)
            
def do_pin_message(channel,timestamp,token=bottoken):
    'pins a file'
    
    url = ( 'https://slack.com/api/pins.add?token='
            +token+'&channel='+channel+'&timestamp='+timestamp )
    posted,retries=False,0
    while posted == False and retries < 1 :
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if posted==True:
            break
        if result['ok']==False:
            do_send_botmessage('WARN:do_pin_message, '+str(result['error']), botroomid)
            
def do_pin_file(channel,file,token=bottoken):  
    url = ( 'https://slack.com/api/pins.add?token='
            +token+'&channel='+channel+'&file='+file )
    posted,retries=False,0
    while posted == False and retries < 1 :
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if result['ok']==False:
            do_send_botmessage('WARN:do_pin_file, '+str(result['error']), botroomid)
            
def do_pin_filecomment(channel,filecomment,token=bottoken):
    url = ( 'https://slack.com/api/pins.add?token='
            +token+'&channel='+channel+'&file_comment='+filecomment )
    posted,retries=False,0
    while posted == False and retries < 1 :
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if result['ok']==False:
            do_send_botmessage('WARN:do_pin_filecomment, '+str(result['error']), botroomid)            
                   

def do_unpin_message(channel,timestamp,token=bottoken):
    'pins a file'
    
    url = ( 'https://slack.com/api/pins.remove?token='
            +token+'&channel='+channel+'&timestamp='+timestamp )
    posted,retries=False,0
    while posted == False and retries < 1 :
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if posted==True:
            break
        if result['ok']==False:
            do_send_botmessage('WARN:do_pin_message, '+str(result['error']), botroomid)
            
def do_unpin_file(channel,file,token=bottoken):  
    url = ( 'https://slack.com/api/pins.remove?token='
            +token+'&channel='+channel+'&file='+file )
    posted,retries=False,0
    while posted == False and retries < 1 :
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if result['ok']==False:
            do_send_botmessage('WARN:do_pin_file, '+str(result['error']), botroomid)
            
def do_unpin_filecomment(channel,filecomment,token=bottoken):
    url = ( 'https://slack.com/api/pins.remove?token='
            +token+'&channel='+channel+'&file_comment='+filecomment )
    posted,retries=False,0
    while posted == False and retries < 1 :
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if result['ok']==False:
            do_send_botmessage('WARN:do_pin_filecomment, '+str(result['error']), botroomid)

def create_banurl(teamurl=teamurl):
    base= teamurl+'/api/users.admin.setInactive?_x_id='
    ts=str(round(time(),3))
    url=base+xid+ts
    return url

def create_unbanurl(teamurl=teamurl):
    
    base= teamurl+'/api/users.admin.setRegular?_x_id='
    ts=str(round(time(),3))
    url=base+xid+ts
    return url    
        
def create_banheaders(teamurl=teamurl):
    headers = {'Origin': teamurl ,'X-Slack-Version-Ts': str(int(time()-10)) }
    return headers

def create_data(username):
    return {'user': username, 'token': webtoken , 'set_active': 'true'}

def do_ban_user(text):
    username=clean_username(text.upper().rsplit()[1])
    with requests.post(create_banurl(),data=create_data(username),
                       headers=create_banheaders()) as request:
        request.close()   
        
def do_unban_user(text):
    username=clean_username(text.upper().rsplit()[1])
    thresh.check()
    with requests.post(create_unbanurl(),data=create_data(username),
                       headers=create_banheaders()) as request:
        
        request.close() 

def get_channels(token):
    '''gets the rooms list'''
    url = ( 'https://slack.com/api/channels.list?token='
            +token+'&exclude_members=true' ) 
        
    posted,retries=False,0
    x=0
    while x<2:
        try:
            while posted == False and retries < 2 :
                result=create_request(url)
                posted,retries=result['ok'],retries+1
                if result['ok']==False:
                    do_send_botmessage('WARN:get_channels error, '+str(result['error']), botroomid)
            return result
        except:
            x=x+1
            
def gather_channels(results):
    channels= {}
    for i in range (len(results['channels.list']['channels'])):
        channels[results['channels.list']['channels'][i]['id']]= {
            'topic':results['channels.list']['channels'][i]['topic']['value'],
            'purpose': results['channels.list']['channels'][i]['purpose']['value'],
            'name':results['channels.list']['channels'][i]['name']}
                
    return channels
    
def do_set_topic(channel,topic,token=admintoken,botroomid=botroomid):
    topic = urllib.parse.quote_plus(topic)
    url= ('https://slack.com/api/channels.setTopic?token='+token+
           '&channel='+channel+'&topic='+topic)
    posted,retries=False,0

    while posted == False and retries < 2 :
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if result['ok']==False:
            do_send_botmessage('WARN:set_topic error, '+str(result['error']), botroomid)


def do_set_purpose(channel,purpose,token=admintoken):
    purpose = urllib.parse.quote_plus(purpose)
    url= ('https://slack.com/api/channels.setPurpose?token='+token+
           '&channel='+channel+'&purpose='+purpose)
    posted,retries=False,0

    while posted == False and retries < 2 :
        result=create_request(url)
        posted,retries=result['ok'],retries+1
        if result['ok']==False:
            do_send_botmessage('WARN:set_purpose error, '+str(result['error']), botroomid)
            
def similar_word(text,word):
    '''matches against a single word'''
    a = re.match('.?'+word+'.?',text.lower())
    if bool (a) and len(text)<=a.span()[1]:
        return True
    return False   

def gather_admins(results):
    
    admin_names , admin_ids = [],[]
    for i in range(len(results['users.list']['members'])):
        if results['users.list']['members'][i]['deleted']==False and (
            results['users.list']['members'][i]['is_admin']==True or
            results['users.list']['members'][i]['is_bot']==True or
            results['users.list']['members'][i]['id']=='USLACKBOT'):
            admin_names.append(results['users.list']['members'][i]['name'])
            admin_ids.append(results['users.list']['members'][i]['id'])
    admins=[admin_names,admin_ids]
    return admins

def check_rtm(response,alloweddomains,secfeaturesconf,secfeatures,seccommands,
                simplecommands,alloweduserids,channels,admins,lograte,botroomid=botroomid):

    '''Main function that reads the RTM API responses and acts accordingly'''
    if 'type' in response.keys():
        if response['type']=='file_shared' and response['user_id'] not in alloweduserids and (
            secfeatures['filedisable'] ):
            delete_file(response['file_id']) 
            do_send_botmessage('WARN:  '+str(get_user_info(response['user_id']))+
                                   ' uploaded a file and it was deleted' , botroomid)
                
        elif response['type']=='user_change' and response['user']['deleted']==False:
            if secfeatures['nameban']:
                if response['user']['profile']['display_name_normalized'] in admins[0] or (
                    response['user']['profile']['display_name_normalized'] in secfeaturesconf['namebanlist'] ):
                    with requests.post(create_banurl(),data=create_data(response['user']['id']),
                                       headers=create_banheaders()) as request:
                        request.close() 
                        do_send_botmessage('CRIT:  username: '+response['user']['name']+' with name: '+
                                   response['user']['real_name']+
                ' Changed his username to : '+response['user']['profile']['display_name_normalized']+
                ' and was banned!'  , botroomid )
                else:
                    if lograte.check_msg('WARN:  username: '+response['user']['name']+' with name: '+
                                     response['user']['real_name']+
                ' became  username: '+response['user']['profile']['display_name_normalized']+' with name: '+
                response['user']['profile']['real_name_normalized']+ ' first name: '+
                response['user']['profile']['first_name']+' last name: '+
                response['user']['profile']['last_name']):
                        do_send_botmessage('WARN:  username: '+response['user']['name']+' with name: '+
                                       response['user']['real_name']+
                    ' became  username: '+response['user']['profile']['display_name_normalized']+' with name: '+
                    response['user']['profile']['real_name_normalized']+ ' first name: '+
                    response['user']['profile']['first_name']+' last name: '+
                    response['user']['profile']['last_name'] , botroomid )   
                                     
        elif response['type']=='pin_removed' and response['user'] not in alloweduserids and (
            secfeatures['pinsoft']):
                if response['channel_id'] in channels.keys():
                    if secfeatures['pinhard'] :
                        do_kick_user(response['channel_id'], response['user'])
                        do_send_botmessage('WARN:  '+str(get_user_info(response['user']))+
                                   ' was kicked from '+channels[response['channel_id']]['name']+
                                   ' because he removed a pinned message', botroomid)
                    if response['item']['type']=='message':
                        do_pin_message(response['channel_id'],response['item']['message']['ts'])   
                    elif response['item']['type']=='file':
                        do_pin_file(response['channel_id'],response['item']['file']['id'])
                    elif response['item']['type']=='file_comment':
                        do_pin_filecomment(response['channel_id'],response['item']['comment']['id']) 
                    do_send_botmessage('WARN:  '+str(get_user_info(response['user']))+
                                   ' unpinned an item from '+
                                   channels[response['channel_id']]['name'] , botroomid)                          
                else:
                    do_send_botmessage('WARN:  '+str(get_user_info(response['user']))+
                                   ' is unpinning items in private channel and he has invited the'+
                                   ' bot user in it! ', botroomid)
                    
        elif response['type']=='pin_added' and response['user'] not in alloweduserids and ( 
        secfeatures['pinsoft']):
            if response['channel_id'] in channels.keys():
                if secfeatures['pinhard'] :
                    do_kick_user(response['channel_id'], response['user'])
                    do_send_botmessage('WARN:  '+str(get_user_info(response['user']))+
                                   ' was kicked from '+channels[response['channel_id']]['name']+
                                   ' because he added a pinned message', botroomid)
                if response['item']['type']=='message':
                    do_unpin_message(response['channel_id'],response['item']['message']['ts'])   
                elif response['item']['type']=='file':
                    do_unpin_file(response['channel_id'],response['item']['file']['id'])
                elif response['item']['type']=='file_comment':
                    do_unpin_filecomment(response['channel_id'],response['item']['comment']['id']) 
                    do_send_botmessage('WARN:  '+str(get_user_info(response['user']))+
                                   ' pinned an item in '+
                                   channels[response['channel_id']]['name'] , botroomid)                          
                else:
                    do_send_botmessage('WARN:  '+str(get_user_info(response['user']))+
                                   ' is pinning items in private channel and he has invited the'+
                                   ' bot user in it! ', botroomid)
    
    if 'text' in response.keys(): 
        if response['type']=='message' and 'subtype' in response.keys():
            if response['subtype']=='reminder_add' and secfeatures['slackbotchannel']:
                do_send_botmessage('CRIT: Reminder added in public channel '+
                                    'from user '+
                                    str(get_user_info(response['user'])), botroomid)
            elif response['subtype']=='channel_purpose' and response['user'] not in alloweduserids and (
                response['channel'] in channels.keys() and response['purpose'] !=  ( 
                    channels[response['channel']]['purpose']  ) and secfeatures['topicsoft'] ):
                if secfeatures['topichard']:
                    do_kick_user(response['channel'], response['user'])
                do_set_purpose(response['channel'], channels[response['channel']]['purpose'])
                do_send_botmessage('CRIT : Purpose changed in '+channels[response['channel']]['name']+
                                    ' from user '+
                                    str(get_user_info(response['user'])), botroomid)
            elif response['subtype']=='channel_topic' and response['user'] not in alloweduserids and (
                response['channel'] in channels.keys() and response['topic'] !=  ( 
                    channels[response['channel']]['topic']  ) and secfeatures['topicsoft'] ):
                if secfeatures['topichard']:
                    do_kick_user(response['channel'], response['user'])
                do_set_topic(response['channel'], channels[response['channel']]['topic'])
                do_send_botmessage('CRIT : Topic changed in '+channels[response['channel']]['name']+
                                    ' from user '+
                                    str(get_user_info(response['user'])), botroomid)
                                    
        if response['type']=='message' and 'user' in response.keys():
            if check_mute(response['text'],response['user']):
                do_mute(response['text'])
            elif check_unmute(response['text'], response['user']):
                do_unmute(response['text'])
            elif check_ban(response['text'],response['user']):
                do_ban_user(response['text'])
            elif check_unban(response['text'], response['user']):
                do_unban_user(response['text'])            
            elif response['user']=='USLACKBOT' and secfeatures['slackbotchannel'] :
                delete_text(response['channel'],response['ts'])
            elif check_muted(response['user']):
                delete_text(response['channel'],response['ts'])
                do_kick_user(response['channel'], response['user'])
            elif response['type']=='message' and  ( similar_eth(response['text']) 
                or similar_btc(response['text']) or similar_prv(response['text']) ) and (
                secfeatures['deleth']):
                delete_text(response['channel'],response['ts']) 
            elif check_prohibited(response['text'], secfeaturesconf['forbidden']) and(
                response['user']not in alloweduserids):
                delete_text(response['channel'],response['ts'])
                do_kick_user(response['channel'], response['user'])
                do_send_botmessage('WARN:  '+str(get_user_info(response['user']))+
                                   ' was kicked from '+channels[response['channel']]['name']+
                                   ' because he typed: '+response['text'], botroomid)
            elif (is_url(response['text'])[0]) and response['user'] not in alloweduserids and (
                is_url(response['text'])[1] > is_allowedurl(response['text'],alloweddomains)[1]  ):
                if 'subtype' in response.keys():
                    if response['subtype']!='file_share' and secfeatures['filedisable']:
                        pass
                else:                    
                    if response['channel'] in channels.keys():
                        delete_text(response['channel'],response['ts'])
                        do_send_botmessage('WARN:  '+str(get_user_info(response['user']))+
                                   ' sent the following text containing clickable URL  in '+channels[response['channel']]['name']+
                                   '  : '+response['text']+'', botroomid)  
            elif response['type']=='message' and len(response['text'].rsplit())==1 :
                for i in simplecommands.keys():
                    if similar_word(response['text'],'.?'+i+'.?') and ( 
                        response['channel'] in channels.keys() ):
                        do_send_botephemeral(simplecommands[i], response['channel'], 
                            response['user'])         
            elif similar_command(response['text']) and secfeatures['forbidrogue']:
                if response['channel'] in channels.keys():
                    delete_text(response['channel'],response['ts'])

def realtime_run():            
    lograte=Lograte(6)
    results1['users.list'] = get_users(bottoken)
    admins = gather_admins(results1)
    results1['channels.list'] = get_channels(bottoken)
    channels=gather_channels(results1)
    for i in admins[1]: alloweduserids.append(i)
    simplecommands =  get_config_simplecommands()
    seccommands = get_config_seccommands()
    secfeatures = get_config_secfeatures()
    secfeaturesconf = get_config_secfeaturesconf()
    alloweddomains = secfeaturesconf['alloweddomains']
    commandprefix = secfeaturesconf['forbidroguechar']
    async def connect(token):
        async with websockets.connect(get_socket_url(token)['url']) as websocket:
            while True:
                response=json.loads(await websocket.recv())
                check_rtm(response,alloweddomains,secfeaturesconf,secfeatures,seccommands,
                          simplecommands,alloweduserids,channels,admins,lograte)
                     
    def listener1():   
        asyncio.get_event_loop().run_until_complete(connect(bottoken))
    listener1()
    
    
    while True:
        
        listener1()   
def realtime_run_loop():
    while True:
        try:
            realtime_run()
        except:
            pass
                
if __name__ == '__main__':
    realtime_run_loop()
    