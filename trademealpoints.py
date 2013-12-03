import os
import re
from string import letters

import jinja2
import webapp2
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

# pseudocode outline
# need: number of points, price per point

def post_key(name = 'default'):
    return db.Key.from_path('post', name)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class MainPage(Handler):
    def get(self):
        posts = Post.all().order('price')
        self.render('mainpage.html')


class Post(db.Model):
    amount = db.IntegerProperty(required = True)
    price = db.FloatProperty(required = True)
    first_name = db.StringProperty(required = True)
    last_name = db.StringProperty(required = True)
    email = db.EmailProperty(required = True)

    def render(self):
        return render_str("post.html", p = self)


class NewPost(Handler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        amount = self.request.get('amount')
        price = self.request.get('price')
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        email = self.request.get('email')

        if amount and price and first_name and last_name and email:
            post = Post(parent = post_key(), 
                        amount = amount, price = price, 
                        first_name = first_name, last_name = last_name,
                        email = email)
            post.put()
            stat = "your entry has been recorded"
            self.redirect('/')

        else:
            error = "sure you got everything?"
            self.render("newpost.html", 
                        amount = amount, price = price, 
                        first_name = first_name, last_name = last_name,
                        email = email, error=error)


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sell', NewPost),
], debug=True)
