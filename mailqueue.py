from google.appengine.api import mail
#from google.appengine.api.labs import taskqueue
from google.appengine.api import taskqueue
import logging, email

class MailQueue:
    
    def __init__(self, start=1, limit=5):
        self.timer = start
        self.limit = limit

    def add(self, lista, url, arg_dict):
        while len(lista)>0:
            partlist = []
            try:
                for i in range(0,self.limit):
                    partlist.append(lista.pop())
            except IndexError:
                pass                
            arg_dict['bcc'] = "|".join(partlist)
            self.add_task(url, arg_dict)

    def add_task(self, url, arg_dict):
        taskqueue.add(url=url, params=arg_dict, countdown=self.timer)
        self.timer+=65
        
    def send(self, request):
        subject = request.get('subject')
        message = request.get('message')
        sender = request.get('sender')
        reply_to = request.get('reply_to')
        bcc = request.get('bcc')
        cc = request.get('cc')
        to = request.get('to')
        
        logging.debug("Sending message")
        message = mail.EmailMessage(sender=sender,
                                    subject=subject,
                                    body=message)
        if reply_to:
            message.reply_to=reply_to
        if bcc:
            message.bcc = bcc.split("|")
            logging.debug("BCC %s" % message.bcc)
        if to:
            message.to = to.split("|")
            logging.debug("TO %s" % message.cc)
        if cc:
            message.cc = cc.split("|")
            logging.debug("CC %s" % message.to)
        message.send()
