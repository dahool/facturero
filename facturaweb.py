# -*- coding: utf-8 -*-
# app engine imports
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

# google service imports
try: 
    from xml.etree import ElementTree
except ImportError:  
    from elementtree import ElementTree
import gdata.spreadsheet.service
import gdata.service
import gdata.auth
import atom.service
import gdata.spreadsheet
import atom
import gdata.alt.appengine

import gdata.urlfetch
gdata.service.http_request_handler = gdata.urlfetch

from google.appengine.api import memcache

# other imports
import os
import datetime
import time

from datamanager import *

from mailmessage import EmailBackend, Message
import settings

class AuthRequestPage(webapp.RequestHandler):
    
    def __init__(self):
        self.client = gdata.spreadsheet.service.SpreadsheetsService()
        gdata.alt.appengine.run_on_appengine(self.client)
    
    def get(self):
        auth_token = gdata.auth.extract_auth_sub_token_from_url(self.request.uri)
        
        if auth_token:
            session_token = self.client.upgrade_to_session_token(auth_token)
            self.client.SetAuthSubToken(session_token)

            token = TokenRepo()
            token.token = session_token.get_token_string()
            token.put()
            
            self.redirect('/')
            return
        else:
            next = HOST + '/auth'
            scope = 'http://spreadsheets.google.com/feeds/'
            secure = False  # set secure=True to request secure AuthSub tokens
            session = True
            auth_sub_url = self.client.GenerateAuthSubURL(next, scope, secure=secure, session=session)
            
            self.response.headers['Content-Type'] = 'text/html'
            self.response.out.write('<a href="%s">here</a>' % auth_sub_url)
        
        
class CommonPage(webapp.RequestHandler):

    def __init__(self):
        tokens = TokenRepo.gql("LIMIT 1")
        if tokens.count()==0:
            self.token = None
        else:
            self.token = tokens[0].token
        
    def _get_info(self):
        return get_info(self.token)
    
    def _strip_entry(self, entry):
        return strip_data_entry(entry)
            
class MainPage(CommonPage):
    def get(self):
        if not self.token:
            self.redirect('/auth')
            return
        
        data = memcache.get('index-page')
        if data:
            return self.response.out.write(data)
            
        cells = self._get_info()
        data = []
        data.append('<table>')
        for i,entry in enumerate(cells.entry):
            name, date, email, notify = self._strip_entry(entry)
            date = datetime.datetime.strptime(date,'%m/%d/%Y')
            if datetime.date.today() == date.date():
                cls="today"
            elif datetime.date.today() > date.date():
                cls="pass"
            else:
                cls="future"
            data.append('<tr class="%s"><td>%s</td><td>%s</td></tr>' % (cls,name,date.strftime('%d/%m/%Y')))
        data.append('</table>')
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        v = template.render(path, {'table': ''.join(data)})
        memcache.set('index-page', v, 60)
        self.response.out.write(v)

class NotifyPage(CommonPage):
    def get(self):
        cells = self._get_info()
        data = []
        today = datetime.datetime.now()
        # si es viernes movemos para el sábado
        if (datetime.datetime.isoweekday(today)==5):
            to_date = (today + datetime.timedelta(days=3)).date()
            mess = "El lunes"
        else:
            to_date = (today + datetime.timedelta(days=1)).date()
            mess = "Mañana"
        others = []
        responsable = {}
        for i,entry in enumerate(cells.entry):
            name, date, email, notify = self._strip_entry(entry)
            dd = datetime.datetime.strptime(date,'%m/%d/%Y')
            if to_date == dd.date():
                responsable = {'name': name, 'email': email}
            else:
                if notify == "1":
                    others.append({'name': name, 'email': email})

        if len(responsable)>0:
            cfg_body = Config.all().filter('ckey =', 'MAIL_BODY').fetch(1)[0]
            cfg_title = Config.all().filter('ckey =', 'MAIL_TITLE').fetch(1)[0]
            cfg_title2 = Config.all().filter('ckey =', 'MAIL_TITLE_ALL').fetch(1)[0]
            
            body = cfg_body.text.encode('utf-8')

            email = EmailBackend()
            messages = []
            m = Message()
            m.subject = cfg_title.text.encode('utf-8') % {'day': mess}
            m.to = ["%(name)s <%(email)s>" % responsable]
            m.body = body
            messages.append(m)            
            
            subject = cfg_title2.text.encode('utf-8') % {'day': mess.lower(),'name': responsable['name']}
            
            for item in others:
                m = Message()
                m.subject = subject
                m.to = ["%(name)s <%(email)s>" % item]
                m.body = body
                messages.append(m)
            
            email.send_messages(messages)       
            
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write("Notified")                
        else:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write("Noone notified")                

class MailWorker(webapp.RequestHandler):
    
    def post(self):
        mq = MailQueue()
        mq.send(self.request)
        
class SetupPage(webapp.RequestHandler):
    
    def get(self):
        cfg = Config.all()
        res = {}
        for item in cfg:
            res[item.ckey]=item.text
        path = os.path.join(os.path.dirname(__file__), 'setup.html')
        self.response.out.write(template.render(path, res))
                
    def post(self):
        args = ['MAIL_BODY','MAIL_TITLE','MAIL_TITLE_ALL']
        for arg in args:
            q = Config.all().filter('ckey =', arg)
            if q.count()>0:
                c = q.fetch(1)[0]
                c.text = self.request.get(arg)
            else:
                c = Config(ckey=arg, text=self.request.get(arg))
            c.put()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("Saved %s." % ", ".join(args))
                                
class KeepAlive(webapp.RequestHandler):

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("OK")

class Startup(webapp.RequestHandler):

    def __init__(self):
        tokens = TokenRepo.gql("LIMIT 1")
        if tokens.count()==0:
            self.token = None
        else:
            self.token = tokens[0].token

    def get(self):
        get_info(self.token, force=True)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("OK")
                
application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                     ('/mailworker',MailWorker),
                                     ('/facturas',NotifyPage),
                                     ('/setup',SetupPage),
                                     ('/keepalive',KeepAlive),
                                     ('/startup',Startup),
                                     ('/auth',AuthRequestPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)
  
if __name__ == "__main__":
  main()
