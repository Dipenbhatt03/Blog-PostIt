
import webapp2
import jinja2
import os
import hashlib
import hmac
import random
import string
import main

from google.appengine.ext import ndb
from google.appengine.api import memcache

from models import UserDetail


template_dir=os.path.join(os.getcwd(),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),autoescape=True)




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

	

def make_salt():
	return ''.join([random.choice(string.ascii_letters) for i in range(0,5)])

def make_pw_hash(name,pw,salt=None):
	if not salt:
		salt=make_salt()

	return '{}|{}'.format(salt,hashlib.sha256(name+pw+salt).hexdigest())

def check_password(name,pw,h):
	salt=h.split('|')[0]
	return make_pw_hash(name,pw,salt)==h

def check_if_user_exist(name,password):
	users=UserDetail.query().fetch()
	for user in users:
		if user.name==name:
			h=user.password
			if check_password(name,password,h):
				return user
	return 1


def get_user(user_id):
	return UserDetail.query(UserDetail.password==user_id).fetch()


class SignUpHandler(Handler):
	def get(self):
		name=self.request.get('username')
		email=self.request.get('email')
		t=main.check_if_logged_in(self.get_user_id())
		referer=self.request.headers.get('referer')		
		if referer:
			self.set_cookie('referer',referer)
		self.render('form.html',name=name,email=email,acount=t[1],link=t[2],color='has-success')

	def post(self):
		name=self.request.get('username')
		password=self.request.get('password')
		verify=self.request.get('verify')
		email=self.request.get('email')
		Name_Error=''
		Password_Error=''
		Name_color='has-success'
		Password_color='has-success'
		if name and password and password==verify:
			val=check_if_user_exist(name,password)
			if val==1:
				salt=make_salt()
				self.response.headers.add_header('Set-Cookie', 'user-id={}; Path=/'.format(make_pw_hash(name,password,salt)))
				password_hash=make_pw_hash(name,password,salt)
				user=UserDetail(name=name,password=password_hash,email=email)
				key=user.put()
				memcache.set('LOGGED_IN',[name,'/logout',password_hash,key])

				referer=self.get_cookie('referer')			
				if referer:
					self.set_cookie('referer','')
					self.redirect(str(referer))
					return
				self.redirect("/blog")
			else:
				Name_Error='User already exist'
				Name_color='has-error'
				Password_color='has-error'
		else:
			if not name:
				Name_Error='Please enter name'
				Name_color='has-error'
			if password and not password==verify:
				Password_Error='Your password do not match'
				Password_color='has-error'
			if not password:
				Password_Error="Enter valid password"
				Password_color='has-error'
		self.render('form.html',name=name,email=email,
			Name_Error=Name_Error,Password_Error=Password_Error,
			Name_color=Name_color,Password_color=Password_color)



class LoginHandler(Handler):
	def get(self):
		username=self.request.get('username')
		password=self.request.get('password')
		referer=self.request.headers.get('referer')				
		if referer:
			self.set_cookie('referer',referer)
		self.render('Login.html',username=username,password=password,color='has-success')		

	def post(self):
		username=self.request.get('username')
		password=self.request.get('password')
		Error='Invalid Login,check username or password'
		if username and password:
			user=check_if_user_exist(username,password)
			if user!=1:
				self.response.headers.add_header('set-cookie','user-id={}; Path=/'.format(user.password))
				memcache.set('LOGGED_IN',[username,'/logout',user.password,user.key])
				#USING REFERRER FEATURE OF webapp2 WE GET THE PREVIOUS URL
				referer=self.get_cookie('referer')			
				if referer:
					self.set_cookie('referer','')
					self.redirect(str(referer))
					return

				self.redirect('/blog')

		self.render('Login.html',username=username,password=password,Error=Error,color='has-error')

class LogoutHandler(Handler):
	def get(self):
		self.response.headers.add_header('set-cookie','user-id={};Path=/'.format(''))
		memcache.set('LOGGED_IN',[])	
		referer=self.request.headers.get('referer')				
		if referer:
			print 'FROM LOGOUT'
			print referer
			self.redirect(referer)
			return
		self.redirect('/blog')



