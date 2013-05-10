# -*- coding: utf-8 -*-
import logging
import datetime
from facturero.models import Person, PersonDates
from utils.holidays import is_holiday

DIFF = datetime.timedelta(days=7)

def get_date_week(date):
    if datetime.datetime.weekday(datetime.date.today()+datetime.timedelta(days=1)) == datetime.datetime.weekday(date):
        return u'Mañana'
    days = [u'Lunes',u'Martes',u'Miércoles',u'Jueves',u'Viernes',u'Sábado',u'Domingo']
    return u'El %s' % days[datetime.datetime.weekday(date)]
    
def find_person(order):
    pq = Person.all()
    pq.filter("order =", order)
    if pq.count() > 0:
        return pq.fetch(1)[0]
    return None
    
def find_person_date(order):
    pq = PersonDates.all()
    pq.filter("order =", order)
    if pq.count() > 0:
        return pq.fetch(1)[0]
    return None
    
def date_generation(startup = None, redo = None):
    qpd = PersonDates.all()
    if redo is None:
        if startup is not None:
            ld = startup
        else:
            qpd.order("-date")
            if qpd.count() > 0:
                elem = qpd.fetch(1)
                pd = elem[0]
                ld = pd.date + DIFF
            else:
                ld = datetime.date.today()
    else:
        qpd.order("order")
        if qpd.count() > 0:
            elem = qpd.fetch(1)
            pd = elem[0]
            ld = pd.date
        else:
            ld = datetime.date.today()
    logging.debug("Using date %s" % str(ld))

    pq = Person.all()
    pq.order("order")
    
    for p in pq:
        dt = ld
        while is_holiday(dt):
            logging.debug("%s is holiday" % str(dt))
            dt = dt - datetime.timedelta(days=1)
        pd = find_person_date(p.order)
        if not pd:
            pd = PersonDates(order=p.order)
        pd.date = dt
        pd.put()
        logging.debug("%s is order %s using date %s" % (p.name, p.order, str(dt)))
        ld = ld + DIFF

    logging.debug("Done generation.")
