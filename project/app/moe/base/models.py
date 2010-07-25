from google.appengine.ext import db

class Area(db.Model):
    name = db.StringProperty()
    owner = db.StringProperty()
