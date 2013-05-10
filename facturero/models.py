from google.appengine.ext import db

class Person(db.Model):
    order = db.IntegerProperty(indexed=True)
    mail = db.StringProperty(indexed=True)
    name = db.StringProperty()

    @property
    def find_date(self):
        q = PersonDates.all().filter('order =',self.order)
        r = q.fetch(1)
        if len(r)>0:
            return r[0]
        return None
        
class PersonDates(db.Model):
    order = db.IntegerProperty(indexed=True)
    date = db.DateProperty()

class Config(db.Model):
    ckey = db.StringProperty()
    text = db.TextProperty()    
