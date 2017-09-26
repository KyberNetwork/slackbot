# Security Slackbot
## Some security enhancement bots for Slack workspaces.

### Disclaimer:  This software is provided **AS IS** without any warranties and support. No responsibility or liability for the use of the software is assumed. You are free to redistribute and modify. Please read the license.

#### Currenty the following operations are supported:
1) Sending Reminders to all  users in a Schedule
2) Sending X messages to Y rooms every S time with O offset


## Instructions:

### Server
Install Python 3.6 on a server of your choice, preferably linux( windows) so that you can add a  cronjob(scheduled task) that checks  if the script is running,  and if it's not, it starts it.

Sample cron line : 

`*/1 * * * * /home/slackadmin/SlackBot-Police/slackReminders.sh`  

The above line checks every minute  with the *slackReminders.sh* script  if *Reminders.py*  python script is running. If it does not run, it starts it. 
To edit your crontab file run  `crontab -e` from the user (not root ) that will be running the script in your server

Sample *slackReminders.sh* :
```
#!/bin/sh
if ps -ef | grep -v grep | grep Reminders.py ; then
        exit 0
else
        /usr/local/bin/python3.6 /home/slackadmin/SlackBot-Police/SlackBot-Police/Reminders.py &
        exit 0
fi
```
Don't forget to make *slackReminders.sh* executable by running `chmod +x slackReminders.sh`

Also edit the cron task in the cron line and the *slackReminders.sh* script to match your paths  

You can edit the script to add other python modules of the slackbot or add new scripts for them  

### Slack
Security settings review:
Go to  yourteamurl.slack.com/apps/manage/permissions

>Approved Apps

**Set this to ON**

>These people can manage Approved Apps and custom integrations
> Workspace Owners only	 
>Workspace Owners and selected members or groups

If the latter is checked the selected group should be only 'WorkSpace Admins'

>Allow members to request additions to Approved Apps

As you see fit

Then go to yourteamurl.slack.com/apps/manage

Remove / disable all unknown (not added by you and don't know exactly what they are doing and why ) applications and confirurations from there!! It's important, since attackers may have generated API keys to gather information and  automate messaging actions

Then in order to create an APP for the reminders :
https://api.slack.com/apps   and select **Create New App**
Add a name and select the workspace for that APP

Then go to **Bot Users**  on the left and **Add a Bot User**  for your application, select the 'always show my bot as online'

Select **OAuth & Permissions** and then go to Scopes :
Add the following : `chat:write:bot`  , `reminders:write`   , `users:read`  and save changes
Also, in the **Restrict API Token Usage** below you should put for security the Static IP address of the server that will be running the scripts. This is important because in case your token is compromised Slack will  not allow other IP addresses to use the token.

Then you should go to the **Install App** section and **Install  App To Workspace**
Then  on this **Install App** section you will have one **OAuth Access Token** and one **Bot User OAuth Access Token**. The first is for the user the second is for the bot.  These Tokens are Private!! Treat those as passwords.

Note : Since bot users cannot send reminders, the reminders will  appear as being requested by you. If you want another user to be showing as the sender of the reminders, you should go to **Collaborators** and  add that user as a collaborator and only then he will be able to install this application from the https://api.slack.com/apps    page

If you want the user that will generate the reminders to by another than you, after inviting him as collaborator  he should install the application and you will use his **OAuth Access Token** in the script and not yours. Bot token is the same always.

In the **Basic information** you can customize logo, color etc.

### config.ini configuration file
The configuration file provided should be self explanatory in the comments ( prefixed by # ) section after each variable.
You can put your variables there and the scripts will run those (please be careful for typos like o instead of 0 in field when a number should be put etc.  

`[general]apirequests`  number of api requests that will be done every `seconds` seconds  
`[general]seconds` number of seconds that the above `apirequests` api request timer will be reset  
 The default values  of 2 reques every 5 seconds should be OK (do not got more aggressive than 2 request every 3 seconds ) if you are not making other API requests.   Actually slack claims ( https://api.slack.com/docs/rate-limits ) that it allows 1 request per second, but during our test, we have found this not to be true, there are certain calls that are heavily rate limited (like getting the users with pagination which is useful for workspaces of more than 20000 members ). Also, if you are using other bots or consuming api calls in other ways, please take those into consideration when altering the above values.

`[reminders]usertoken` this is the token of the user that will be requesting the reminders   
`[reminders]rperiod`   period in seconds that you want the  send reminders operation to start. So if you put it 86400 it will start every 24 hours from the script run   
Please notice that the time for the reminder circle to run will be about  total users * 2.5 seconds with the default `[general]` settings so that in cases that you have more than 34000 users 86400 might not be enough since the operation will restart before the last users get their reminders    
 `[reminders]botroomid` a string with the the channel that the reminder bot will send reports to. How to get  this: Please alter your slack from a between different rooms, you will see the url being changed  CXXXXX is a public room, DXXXXX is a DM room, GXXXXX is a private room/group conversation.  For bot reporting it would be better if  you should input a private room ID. Also the bot should be invited in the room that the message will be sent, or else the sending will fail.  
`[reminders]remindertxt`  the text for your reminders, please **pay attention** to the indents for new lines. Every new line in your message has to be idented.  

`[sendmsgs]enabled` you put the messages that are enabled, for example `enabled = msg2  ` or `enabled = msg1,msg2,msg3  ` . Use comma for multiple values.   
`[sendmsgs]msg1` the text of the first message, please **pay attention** to the indents for new lines. Every new line in your message has to be idented.   
`[sendmsgs]speriod1` the period in number of seconds that this message will be sent   
`[sendmsgs]offset1` the offset in seconds that will be added to the original message second counter. # In case you have two messages that you want to repeat every  X seconds, since both of them would arrive at the X second mark, the offset value adds seconds to one of those. If you have two messages  both set to 100 seconds and one has offset 30, they will be both be sent every 100 seconds but will have a 30 seconds difference.  
`[sendmsgs]room1` the string with the name of the room that you want the message to be sent to. How to get  this: Please alter your slack from a between different rooms, you will see the url being changed  CXXXXX is a public room, DXXXXX is a DM room, GXXXXX is a private room/group conversation.  For bot reporting it would be better if  you should input a private room ID. Also the bot should be invited in the room that the message will be sent, or else the sending will fail.  You can put multiple rooms for the same message separating them with commas   
You can also add `msg2,speriod2,offset2,room2` and have multiple messaging combinations. Remember to enable your messages in the `[sendmsgs]enabled`  section.   


### Scripts
The  *Reminders.py* script will use the `[general]` and `[reminders]` configuration sections to send the reminders. Run it by calling `python3.6 Reminders.py &`   
The *Messenger.py* script will use the `[general]` and  `[sendmsgs]` configuration sections to send messages to the rooms at the predefined times and offsets. Call it by using `python3.6 Reminders.py &`

