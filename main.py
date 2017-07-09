import webapp2
import urllib2
import json
import jinja2
import os
import socket
import time
import logging
import user_accounts

from user_accounts import get_user


from google.appengine.api import memcache
from google.appengine.ext import ndb

from models import Post
from models import UserDetail
from models import Comment

from helper_functions import get_front,check_if_logged_in,get_link



template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))



class Handler(webapp2.RequestHandler):
	def write(self,*a,**kw):
		self.response.write(*a)

	def render_str(self,template,**kwargs):
		t=jinja_env.get_template(template)
		return t.render(**kwargs)

	def render(self,template,**kwargs):
		self.write(self.render_str(template,**kwargs))
		
	def set_cookie(self,name,value):
		self.response.headers.add_header('Set-Cookie', '{}={}; Path=/'.format(name,value))
	def get_user_id(self):
		return self.request.cookies.get('user-id')
	def get_cookie(self,cookie):
		return self.request.cookies.get(cookie)



class MainPage(Handler):

	def render_front(self,subject="",content="",error=""):
		posts=get_front()
		logged,acount,link,acount_name=check_if_logged_in(self.get_user_id())
		queried='queried {} seconds ago'.format(memcache.get('queried'))
		self.render('front.html',posts=posts,
			acount=acount,link=link,
			logged=logged,acount_name=acount_name
			)

	def get(self):
		self.render_front()



class MainPageJson(Handler):
	def get(self):
		posts=Post.query().order(-Post.created).fetch(limit=5)
		self.response.headers['Content-Type']='application/json'
		json_data=[]
		for p in posts:
			d={'content':p.content,'created':p.created.strftime('%A %b %d %H:%M:%S %Y'),'subject':p.subject}
			json_data.append(d)
		self.write(json.dumps(json_data))




class NewPostHandler(Handler):
	def get(self):
		t=check_if_logged_in(self.get_user_id())
		if t[0]:
			self.render('new post form.html',acount=t[1],link=t[2],logged=True,acount_name=t[3])
		else:
			#memcache.set('PREV_URL',self.request.path)
			self.redirect('/login')

	def post(self):

		t=check_if_logged_in(self.get_user_id())
		print t
		if not t[0]:
			self.redirect('/login')
			return

		subject=self.request.get('subject')
		content=self.request.get('content')

		if subject and content:
			user=UserDetail.query(UserDetail.password==memcache.get('LOGGED_IN')[2]).fetch()[0]
			k=Post(subject=subject,content=content,user=user.key).put()
			user.posts.append(k)
			user.put()
			#time.sleep(0.5)
			get_front(True)
			self.redirect("/blog/%d"%k.id())

		else:
			self.render('new post form.html',subject=subject,
				content=content,error="Both fields are needed"
				,logged=True,acount_name=t[3]
				)

class LinkDetailJsonHandler(Handler):
	def get(self,post_id):
		link=Post.get_by_id(id=int(post_id))
		self.response.headers['Content-Type']='application/json'
		if not link:
			self.error(404)
			return
		json_data={'content':link.content,'created':link.created.strftime('%A %b %d %H:%M:%S %Y'),'subject':link.subject}
		self.write(json.dumps(json_data))
	def post(self,post_id):
		post=get_link(post_id)


class LinkDetailHandler(Handler):
	def get(self,post_id):
		logged,acount,link,acount_name=check_if_logged_in(self.get_user_id())
		post=get_link(post_id)
		if not post:
			self.error(404)
			return
		print post.comments
		self.render('linkdetail.html',post=post,
			acount=acount,link=link,logged=logged,acount_name=acount_name
			)
	def post(self,post_id):
		
		logged,acount,link,acount_name=check_if_logged_in(self.get_user_id())

		if not logged:
			self.redirect('/login')
			return
		post=get_link(post_id)

		if not post:
			self.error(404)
			return

		comment=self.request.get('comment')
		if comment:
			user_key=memcache.get('LOGGED_IN')[3]
			comment_object=Comment(body=comment,post=post.key,user=user_key)
			comment_key=comment_object.put()
			print post.comments
			post.comments.append(comment_key)
			post.put()
			memcache.set(post_id,post)
			get_front(True)
			self.redirect(self.request.headers.get('referer'))
		else:
			self.render('linkdetail.html',post=post,
			acount=acount,link=link,logged=logged,acount_name=acount_name,
			error='How can a comment be empty dumbass::::::Have some sense people'
			)





class FlushHandler(Handler):
	def get(self):
		memcache.flush_all()
		global START_TIME
		START_TIME=time.time()
		get_front()
		self.redirect('/blog')


app = webapp2.WSGIApplication([
							(r'/blog', MainPage),
							('/blog/?.json',MainPageJson),
							(r'/blog/newpost',NewPostHandler),
							(r'/blog/(\d+)',LinkDetailHandler),
							(r'/blog/(\d+)/?.json',LinkDetailJsonHandler),
							(r'/signup',user_accounts.SignUpHandler),
							(r'/login',user_accounts.LoginHandler),
							(r'/logout',user_accounts.LogoutHandler),
							(r'/blog/flush',FlushHandler)
							
							],
							   debug=True)
