# -*- coding: utf-8 -*-

import os
import datetime
import re
import logging

# app engine imports
from jinja2 import Template

from mailmessage import EmailBackend, Message
from facturero import date_generation, find_person_date, find_person, get_date_week
from facturero.models import Person, PersonDates, Config
from utils.encoding import force_unicode
from facturero.filters import datetimeformat
from utils.holidays import is_holiday

from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__),'pages')))
env.filters['date'] = datetimeformat

def render_to_response(response, template, data):
    t = env.get_template(template)
    v = t.render(data)
    response.headers['Content-Type'] = 'text/html'
    response.out.write(v)
       
def save_forms(request, response, method='GET'):
    response.headers['Content-Type'] = 'application/json'
    if method == 'POST':
        # parse persons
        toDelete = request.get_all('del')
        data = request.get_all('order')
        order = 0
        for pid in data:
            try:
                delete = False
                if pid.startswith("#"):
                    name, mail = pid[1:].split("|")
                    p = Person()
                else:
                    tokens = pid.split("|")
                    cid, name, mail = tokens[0],tokens[1],tokens[2]
                    try:
                        d = tokens[3]
                        if d == '@':
                            delete = True
                    except:
                        pass
                    p = Person.get_by_id(long(cid))
                if delete:
                    p.delete()
                else:
                    order += 1
                    p.name = name
                    p.mail = mail
                    p.order = order
                    p.put()
            except Exception, e:
                logging.error(str(e))
            
        pdq = PersonDates.all().filter('order >',order)
        for pdqe in pdq:
            pdqe.delete()
        
        # parse message options
        args = ['MAIL_BODY','MAIL_TITLE','MAIL_TITLE_ALL']
        for arg in args:
            q = Config.all().filter('ckey =', arg)
            if q.count()>0:
                c = q.fetch(1)[0]
                c.text = request.get(arg)
            else:
                c = Config(ckey=arg, text=request.get(arg))
            c.put()
        
        response.out.write('{"success": true, "message": "Actualizado."}')
    else:
        response.out.write('{"success": false, "message": "Forbidden."}')

def get_person_list(request, response, method='GET'):
    pq = Person.all()
    pq.order("order")
    data = {'persons': pq}
    render_to_response(response, 'persons.html', data)
    
def show_setup_page(request, response, method='GET'):
    pq = Person.all()
    pq.order("order")
    data = {'persons': pq}
    cfg = Config.all()
    for item in cfg:
        data[item.ckey]=item.text
    render_to_response(response, 'setup.html', data)

def init_handler(request, response, method='GET'):
    response.headers['Content-Type'] = 'application/json'
    startup = request.get('data', None)
    if startup is not None:
        try:
            startup = datetime.datetime.strptime(startup, '%d/%m/%Y').date()
        except:
            startup = None
    redo = request.get('redo', None)
    try:
        date_generation(startup, redo)
    except Exception, e:
        logging.exception(e)
        response.out.write('{"success": false, "message": "%s"}' % str(e))
    else:
        response.out.write('{"success": true, "message": "Indice generado."}')
    
def index_page(request, response, method='GET'):
    pdq = PersonDates.all()
    pdq.order("date")
    data = []
    data.append('<table>')
    for pd in pdq:
        p = find_person(pd.order)
        date = pd.date.strftime('%d/%m/%Y')
        if datetime.date.today() == pd.date:
            cls="today"
        elif datetime.date.today() > pd.date:
            cls="pass"
        else:
            cls="future"
        data.append('<tr class="%s"><td>%s</td><td>%s</td></tr>' % (cls,p.name,date))
    data.append('</table>')
    render_to_response(response, 'index.html', {'table': ''.join(data)})
    
def check_update(request, response, method='GET'):
    response.headers['Content-Type'] = 'application/json'
    today = datetime.date.today()
    pq = PersonDates.all()
    pq.order("-date")
    r = pq.fetch(1)
    if len(r) > 0:
        pd = r[0]
        if pd.date < today:
            try:
                date_generation()
            except Exception, e:
                logging.exception(e)
                response.out.write('{"success": false, "message": "%s"}' % str(e))
            else:
                response.out.write('{"success": true, "message": "Indice generado."}')
            return
    response.out.write('{"success": true, "message": "OK."}')

def get_next_day():
    today = datetime.date.today()
    if datetime.datetime.isoweekday(today)==6 or datetime.datetime.isoweekday(today)==7 or is_holiday(today):
         # si es weekend salimos
        return None
    elif (datetime.datetime.isoweekday(today)==5):
        # si es viernes buscamos el lunes
        to_date = (today + datetime.timedelta(days=3))
    else:
        to_date = (today + datetime.timedelta(days=1))
    # vemos si el día seleccionado o el siguiente son feriados    
    if is_holiday(to_date):
        to_date = (to_date + datetime.timedelta(days=1))
        if is_holiday(to_date):    
            to_date = (to_date + datetime.timedelta(days=1))
    return to_date
    
def send_notification(request, response, method='GET'):
    response.headers['Content-Type'] = 'application/json'
    to_date = get_next_day()
    if not to_date:
        response.out.write('{"success": true, "message": "Weekend"}')
        return
    
    mess = get_date_week(to_date)
    
    others = []
    responsable = {}
    pq = Person.all()
    pq.order("order")
    force = int(request.get('order', 0))
    reason = request.get('reason', None)
    for p in pq:
        if force > 0:
            if p.order == force:
                responsable = {'name': p.name, 'email': p.mail}
            else:
                others.append({'name': p.name, 'email': p.mail})
        else:
            pd = find_person_date(p.order)
            if to_date == pd.date:
                responsable = {'name': p.name, 'email': p.mail}
            else:
                others.append({'name': p.name, 'email': p.mail})

    if len(responsable)>0:
        cfg_body = Config.all().filter('ckey =', 'MAIL_BODY').fetch(1)[0].text
        cfg_title = Config.all().filter('ckey =', 'MAIL_TITLE').fetch(1)[0].text
        cfg_title2 = Config.all().filter('ckey =', 'MAIL_TITLE_ALL').fetch(1)[0].text
        
        if reason:
            cfg_title = '%s %s' % (cfg_title, reason)
            cfg_title2 = '%s %s' % (cfg_title2, reason)
        
        body = force_unicode(cfg_body)

        email = EmailBackend()
        messages = []
        m = Message()
        m.subject = force_unicode(cfg_title).replace("$DAY", mess)
        m.to = ["%(name)s <%(email)s>" % responsable]
        m.body = body
        messages.append(m)            
        
        subject = force_unicode(cfg_title2).replace("$DAY", mess).replace("$NAME", force_unicode(responsable['name']))
        
        for item in others:
            m = Message()
            m.subject = subject
            m.to = ["%(name)s <%(email)s>" % item]
            m.body = body
            messages.append(m)
        
        if force >= 0:
            email.send_messages(messages)
        else:
            logging.debug("This is only a test")
            for m in messages:
                logging.debug(force_unicode(m))
                
        response.out.write('{"success": true, "message": "Responsable %s - %s"}' % (responsable['name'], mess))
    else:
        response.out.write('{"success": true, "message": "No se enviaron notificationes"}')
