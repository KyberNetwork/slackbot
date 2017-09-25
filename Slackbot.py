from Reminders import timedsendreminders
from Messenger import send_messages
import configparser

config=configparser.ConfigParser()
config.read('config.ini')

def run_modules():
    if config['modules'].getboolean('reminders'):
        timedsendreminders()
    if config['modules'].getboolean('sendmsgs'):
        send_messages()
        
if __name__ == '__main__':
    run_modules()
