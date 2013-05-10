# -*- coding: utf-8 -*-
# app engine imports
import webapp2

import re

from facturero import views

urlpatterns = (
    (r'/op/save/$', views.save_forms),
    (r'/op/notify/$', views.send_notification),
    (r'/op/index/$', views.init_handler),
    (r'/op/checkupdate/$', views.check_update),
    (r'/op/setup/get_persons/$', views.get_person_list),
    (r'/op/setup/$', views.show_setup_page),
    (r'/$', views.index_page),
)

class RequestHandler(webapp2.RequestHandler):
    pass
    
class SetupRedirectHandler(RequestHandler):
    
    def get(self):
        self.redirect("/op/setup/")
        
class PageHandler(RequestHandler):
    
    def get(self):
        self.process_handler('GET')

    def post(self):
        self.process_handler('POST')
        
    def process_handler(self, method):
        found = False
        for patt, view in urlpatterns:
            path = self.request.path
            if not path.endswith('/'): path = path + '/'
            if re.match(patt, path):
                view(self.request, self.response, method)
                found = True
        if not found: self.error(404)

class KeepAlive(RequestHandler):

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("OK")
                                
application = webapp2.WSGIApplication(
                                     [('/keepalive',KeepAlive),
                                     ('/op', SetupRedirectHandler),
                                     ('/op/', SetupRedirectHandler),
                                     ('/.*', PageHandler),],
                                     debug=True)
