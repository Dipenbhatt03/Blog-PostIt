
from google.appengine.ext import ndb




class UserDetail(ndb.Model):
	name=ndb.StringProperty(required=True)
	password=ndb.StringProperty(required=True)
	email=ndb.StringProperty(required=False)
	posts=ndb.KeyProperty(kind='Post',repeated=True)

class Post(ndb.Model):
	subject=ndb.StringProperty(required=True)
	content=ndb.TextProperty(required=True)
	created=ndb.DateTimeProperty(auto_now_add=True)
	user=ndb.KeyProperty(kind='UserDetail')
	comments=ndb.KeyProperty(kind='Comment',repeated=True)

class Comment(ndb.Model):
	body=ndb.StringProperty(required=True)
	user=ndb.KeyProperty(kind='UserDetail')
	post=ndb.KeyProperty(kind='Post')