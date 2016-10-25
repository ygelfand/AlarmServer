import time, datetime, sys, re
from tornado import gen
import requests
import json

#alarmserver logger
import logger

#import config
from config import config
from events import events


class Client(object):
    def __init__(self):
        logger.debug('Starting Smartthings Client')

        # Register events for alarmserver requests -> envisalink
        #events.register('alarm_update', self.request_action)

        # Register events for envisalink proxy
        events.register('alarm', self.callbackurl_event)
        self.do_setup()

    @gen.coroutine
    def do_setup(self):
        partitionjson = json.dumps(config.PARTITIONNAMES)
        zonejson = json.dumps(config.ZONENAMES)

        headers = {'content-type': 'application/json'}

        # create zone devices
        myURL = config.CALLBACKURL_BASE + '/' + config.CALLBACKURL_APP_ID + '/installzones' + '?access_token=' + config.CALLBACKURL_ACCESS_TOKEN
        if (config.LOGURLREQUESTS):
          logger.debug('myURL: %s' % myURL)
        requests.post(myURL, data=zonejson, headers=headers)

        # create partition devices
        myURL = config.CALLBACKURL_BASE + '/' + config.CALLBACKURL_APP_ID + '/installpartitions' + '?access_token=' + config.CALLBACKURL_ACCESS_TOKEN
        if (config.LOGURLREQUESTS):
          logger.debug('myURL: %s' % myURL)
        requests.post(myURL, data=partitionjson, headers=headers)
    
    @gen.coroutine
    def callbackurl_event(self, eventType,  type, parameters, code, event, message, status):
        myEvents = config.CALLBACKURL_EVENT_CODES.split(',')
        # Determin what events we are sending to smartthings then send if we match
        if str(code) in myEvents:
           # Now check if Zone has a custom name, if it does then send notice to Smartthings
           # Check for event type
           if event['type'] == 'partition':
             # Is our partition setup with a custom name?
             if int(parameters) in config.PARTITIONNAMES:
               if str(code)=='652' and message.endswith('Stay'):
                   code='666'
               myURL = config.CALLBACKURL_BASE + "/" + config.CALLBACKURL_APP_ID + "/panel/" + str(code) + "/" + str(int(parameters)) + "?access_token=" + config.CALLBACKURL_ACCESS_TOKEN
             else:
               # We don't care about this partition
               return
           elif event['type'] == 'zone':
             # Is our zone setup with a custom name, if so we care about it
             if config.ZONENAMES[int(parameters)]: 
               myURL = config.CALLBACKURL_BASE + "/" + config.CALLBACKURL_APP_ID + "/panel/" + str(code) + "/" + str(int(parameters)) + "?access_token=" + config.CALLBACKURL_ACCESS_TOKEN
             else:
               # We don't care about this zone
               return
           else:
             # Unhandled event type..
             return

           # If we made it here we should send to Smartthings
           try:
             # Note: I don't currently care about the return value, fire and forget right now
             requests.get(myURL)
             if (config.LOGURLREQUESTS):
                logger.debug("myURL: %s " % myURL)
                logger.debug("Exit code: %s" % r.status_code)
                logger.debug("Response data: %s " % r.text)
                time.sleep(0.5)
           except:
             print sys.exc_info()[0]

