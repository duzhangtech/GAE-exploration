import os
import re
from string import letters

import jinja2
import webapp2
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

#cool features
    #ppl watching offers; price per point + giftcards/other payment options
    #current offers
    #current buyers
        #input for each

    #records/stories

    #avg price over time
        #offers
        #successful transactions

    #offer amount over time

#nice to have
    #cool facts page

def offer_key(name = 'default'):
    return db.Key.from_path('offer', name)

def want_key(name = 'default'):
    return db.Key.from_path('want', name)

def feedback_key(name = 'default'):
    return db.Key.from_path('feedback', name)

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
        self.render('about.html')

class Post(db.Model):
    amount = db.StringProperty(required = True)
    price = db.StringProperty(required = True)
    first_name = db.StringProperty(required = True)
    last_name = db.StringProperty(required = True)
    email = db.StringProperty(required = True)

    def render(self):
        return render_str("post.html", p = self)

class Want(db.Model):
    want_amount = db.StringProperty(required = True)
    want_price = db.StringProperty(required = True)

    def render(self):
        return render_str("want.html", w = self)

class Feedback(db.Model):
    feedback = db.StringProperty(required = True)

    def render(self):
        return render_str("feedback.html", f = self)

#input
class Sell(Handler):
    def get(self):
        self.render("sell.html")

    def post(self):
        amount = self.request.get('amount')
        price = self.request.get('price')
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        email = self.request.get('email')

        if amount and price and first_name and last_name and email:
            post = Post(parent = offer_key(), 
                amount = amount, price = price, 
                first_name = first_name, last_name = last_name, 
                email = email)
            post.put()
            stat = "your entry has been recorded! awesomeness"
            self.render("sell.html", stat = stat)

        else:
            error = "sure you got everything?"
            self.render("sell.html", 
                        amount = amount, price = price, 
                        first_name = first_name, last_name = last_name,
                        email = email, error=error)

#output
class Buy(Handler):
    def get(self):
        posts = Post.all().order('price')
        wants = Want.all().order('want_price')

        self.render("buy.html", posts = posts, wants = wants)

    def post(self):
        posts = Post.all().order('price')
        wants = Want.all().order('want_price')

        want_amount = self.request.get('want_amount')
        want_price = self.request.get('want_price')

        if want_amount and want_price:
            want = Want(parent = want_key(),
                want_amount= want_amount, want_price = want_price)
            want.put()
            stat = "kay i got this"
            self.render("buy.html", stat = stat, posts = posts, wants = wants)
        else:
            error = "sure you got all the boxes?"
            self.render("buy.html", error = error)


class FAQ(Handler):
    def get(self):
        self.render("faq.html")

    def post(self):
        feedback = self.request.get('feedback')

        if feedback:
            f = Feedback(parent = feedback_key(), feedback = feedback)
            f.put()
            stat = "gracias mucho :)"
            self.render("faq.html", stat = stat)
        else:
            error = "oops! try typing that again"
            self.render("faq.html", feedback = feedback, error = error)

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/buy', Buy),
    ('/sell', Sell),
    ('/faq', FAQ),

], debug=True)
