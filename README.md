# Security Slackbot
## Some security enhancement bots for Slack workspaces.
Currenty the following operations are supported:
1) Sending Reminders to all  users in a Schedule

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

As you see fit , we don't allow
       
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

### Script
For the *Reminders.py* script you will need to input the following things , there are examples  in the script commets:

`period` seconds that you want the  send reminders operation to start. So if you put it 86400 it will start every day  
Please notice that the time for the reminder circle to run will be about  total users * 2.5 seconds 
 
`token1` user token ( user that the reminders will be requested from to the slackbot )  
`token2` bot token  
`remindertext` ( the text for your reminders, please leave the triple quotes as they are  )  
`msgroomid` A room ID of a  private room, that the bot will report  to you for script operations (start / end of process and any error should those occur )  How to get  this: Please alter your slack from a between different rooms, you will see the url being changed  CXXXXX is a public room, DXXXXX is a DM room, GXXXXX is a private room/group conversation.  For bot reporting it would be better if  you should input a private room ID.

Be sure to **invite the bot user to the private room** so that the bot has access to  send messages to it. It's better if that room is monitored by several admins. So invite the people that you deem necessary, there will be lots of notifications in the next bot updates.

If you also use other slack bots then you might need to finetune the rate at  which requests are sent to the slack API, please edit the *Apirate.py*  file, it has 2 variables for editing, `seconds` and `apireqs`   2 and 1 means that your app will make  1 api request every 2 seconds.  3 and 1 means 1 api request every 3 seconds.  The default values should be OK if you are not making other API requests.   Actually slack claims ( https://api.slack.com/docs/rate-limits ) that it allows 1 request per second, but during our test, we have found this not to be true. In case of a request being  blocked by slack due to violation of the API rate limits, please alter the *Apirate.py* file accordingly.
