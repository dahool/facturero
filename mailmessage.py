# -*- coding: utf-8 -*-
# Le Pizze
# Copyright (C) 2010 Sergio Gabriel Teves
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import logging
from gae.email import MailManager
import settings

class Message():
    from_email = settings.SENDER
    subject = None
    body = None
    to = None
    bcc = None
    
    def __unicode__(self):
        return u"<%s> [%s]: %s" % (self.to, self.subject, self.body)
        
class EmailBackend():

    def __init__(self):
        self.manager = MailManager()

    def send_messages(self, email_messages):
        for message in email_messages:
            try:
                self.manager.send_mail(message.from_email,
                                       message.subject,
                                       message.body,
                                       to=message.to,
                                       bcc=message.bcc)
            except Exception, e:
                logging.error(e)
                raise
        return len(email_messages)
