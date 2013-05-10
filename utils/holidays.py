import urllib2
import logging
from xml.dom import minidom

URL = 'http://webapiservices.appspot.com/api/holiday/find?date=%s'

def is_holiday(date):
    try:
        handler = urllib2.urlopen(URL % urllib2.quote(date.strftime('%d-%m-%Y')))
        result = handler.read().decode('iso-8859-1').encode('utf-8')
        handler.close()
        dom = minidom.parseString(result)        
        data_dom = dom.getElementsByTagName('holidays')[0]
        return data_dom.getElementsByTagName('date')[0].childNodes[0].nodeValue == 'True'
    except Exception, e:
        logging.error(str(e))
    return False
    
if __name__ == "__main__":
    import datetime
    print is_holiday(datetime.datetime.today())
    print is_holiday(datetime.datetime.strptime('01/01/2010','%d/%m/%Y'))
