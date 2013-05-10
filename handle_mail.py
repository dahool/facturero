# -*- coding: utf-8 -*-
# app engine imports
import logging, email
import webapp2 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.api import mail

from facturero.models import Person, PersonDates, Config

# other imports
import os
import datetime
import time

SENDER = 'El Facturero <lista@facturero.appspotmail.com>'
REPLY_TO = 'lista@facturero.appspotmail.com'

class MailHandler(InboundMailHandler):
    
    def receive(self, mail_message):
        pq = Person.all()
        pq.order("order")
        data = []
        for p in pq:
            pdate = p.find_date
            if pdate:
                data.append('%s - %s' % (p.name,pdate.date.strftime('%d/%m/%Y')))
            else:
                data.append('%s - UNKNOWN' % (p.name))

        mail.send_mail(sender=SENDER,
                   reply_to=REPLY_TO,
                   to=mail_message.sender,
                   subject="Lista el facturero",
                   body="\n".join(data))

application = webapp2.WSGIApplication([MailHandler.mapping()], debug=True)
