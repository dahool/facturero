import logging

import webapp2
from google.appengine.api import mail
from google.appengine.runtime import apiproxy_errors
from gae.email import settings
from gae.email import MailManager

class MailWorker(webapp2.RequestHandler):
    
    def post(self):
        logging.debug("Sending message")
        sender = self.request.get('sender')
        subject = self.request.get('subject')
        message = self.request.get('message')
        to = self.request.get('to')
        try:
            mail.send_mail(sender, to, subject, message)
        except apiproxy_errors.OverQuotaError, m:
        #except Exception, m:
            logging.warn(m)
            # lets add it to the queue again
            m = MailManager()
            m.send_mail(sender,subject, message, [to])
        except:
            raise

application = webapp2.WSGIApplication([(settings.TASK_URL, MailWorker)])
