# -*- coding: utf-8 -*-
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
from google.appengine.api import memcache

import gdata.urlfetch
gdata.service.http_request_handler = gdata.urlfetch

# other imports
import os
import datetime
import time

class TokenRepo(db.Model):
    token = db.StringProperty()
    
class Config(db.Model):
    ckey = db.StringProperty()
    text = db.TextProperty()
    
def get_info(auth, force=False):
    if not force:
        data = memcache.get("factura-web-data")
        if data is not None:
            return data
    client = gdata.spreadsheet.service.SpreadsheetsService()
    #gdata.alt.appengine.run_on_appengine(client)
    gdata.alt.appengine.run_on_appengine(client, store_tokens=False,single_user_mode=True)
    #client.email = 'facturaweb@sgtdev.com.ar'
    #client.password = 'factura483@hsbc'
    client.source = 'factura-web'
    client.account_type = 'GOOGLE'
    #client.ProgrammaticLogin()
    client.SetAuthSubToken(auth)

    # This assume the sheet exists
    q = gdata.spreadsheet.service.DocumentQuery()
    q['title']='Facturas'
    q['title-exact']='true'
    sheets = client.GetSpreadsheetsFeed(query=q)
    sheetId = sheets.entry[0].id.text.rsplit('/',1)[1]

    wsheets = client.GetWorksheetsFeed(sheetId)
    workId = wsheets.entry[0].id.text.rsplit('/',1)[1]
    
    cells = client.GetListFeed(sheetId,workId)
    memcache.set("factura-web-data", cells)  
    return cells
    
def strip_data_entry(entry):
    '''return tupple
    '''
    name = entry.title.text.strip()
    content = entry.content.text.split(',')
    date = content[0].split(':')[1].strip()
    email = content[1].split(':')[1].strip()
    notify = content[2].split(':')[1].strip()
    return (name, date, email, notify)
