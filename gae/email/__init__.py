import logging
from gae.email import settings
from gae.queue import taskqueue

class MissingRecipients(Exception):
    pass

class MissingArguments(Exception):
    pass

class MailQueue(object):
    
    def __init__(self):
        self.queue = taskqueue.Queue(settings.QUEUE_NAME)
        
    def add(self, params):
        # limits are handled in the queue itself
        logging.debug("Add mail to queue [%s]" % params)
        task = taskqueue.Task(url=settings.TASK_URL, params=params)
        self.queue.add(task)

class MailManager(object):
    
    def __init__(self):
        self.queue = MailQueue()
        
    def _process_recipients(self, sender, subject, message, recipients):
        if recipients:
            params = {'sender': sender,
                      'subject': subject,
                      'message': message}
            for r in recipients:
                params['to']=r
                self.queue.add(params)
        
    def _build_message(self, sender, subject, message, to, cc, bcc):
        if not (to or cc or bcc):
            raise MissingRecipients()
        if not sender:
            raise MissingArguments('Sender cannot be empty')        
        if not subject:
            raise MissingArguments('Subject cannot be empty')
        if not message:
            message = ''
        self._process_recipients(sender, subject, message, to)
        self._process_recipients(sender, subject, message, cc)
        self._process_recipients(sender, subject, message, bcc)
    
    def send_mail(self, sender, subject, message, to=None, cc=None, bcc=None):
        self._build_message(sender, subject, message, to, cc, bcc)            