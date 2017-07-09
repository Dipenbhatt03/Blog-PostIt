import time
import webapp2

from models import Post
from google.appengine.api import memcache



#START_TIME=time.time()

def get_front(update=False):
	key='top posts'
	posts=memcache.get(key)
	#memcache.set('queried',time.time()-START_TIME)
	if not posts or update:
		print "\n\n\n\nQUERY MADE \n\n\n\n\n"
		posts=Post.query().order(-Post.created).fetch()
		posts=list(posts)
		memcache.set(key,posts)
	return posts

def check_if_logged_in(user_id):
	logged=memcache.get('LOGGED_IN')
	if logged:
		if user_id==logged[2]:
			return True,'Logout({})'.format(logged[0]),'/logout',logged[0]
	return False,'Login','/login',''



			
def get_link(post_id):
	key = post_id
	t=time.time()
	post=memcache.get(key)
	if not post:
		print 'Query made'
		post=Post.get_by_id(id=int(post_id))
		if not post:
			return None
		memcache.set(key,post)
		return post

	else :
		val=memcache.get(key)
		return val
