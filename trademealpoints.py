import os
import re
import urllib
from string import letters

import jinja2
import webapp2
from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import memcache


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

def user_key(name = "default"):
    return db.Key.from_path('user', name)
        #returns key

def sell_key(name = "default"):
    return db.Key.from_path('sell', name)

def wish_key(name = "default"):
    return db.Key.from_path('wish', name)

def feedback_key(name = "default"):
    return db.Key.from_path('feedback', name)

class UserModel(db.Model):
    first_name = db.StringProperty(required = True)
    last_name = db.StringProperty(required = True)
    email = db.StringProperty(required = True)

class FeedbackModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    feedback = db.StringProperty(required = True)
    def render(self):
        return render_str("feedback.html", f = self)

class SellModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    amount = db.StringProperty(required = True)
    price = db.StringProperty(required = True)
    checked = db.BooleanProperty(default = False)

    def render(self):
        return render_str("sellmodel.html", s = self)

class WishModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    wish_amount = db.StringProperty(required = True)
    wish_price = db.StringProperty(required = True)

    def render(self):
        return render_str("wishmodel.html", w = self)

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

class FAQ(Handler):
    def get(self):
        self.render("faq.html")

    def post(self):
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        email = self.request.get('email')

        feedback = self.request.get('feedback')

        if first_name and last_name and email and feedback:
            user = UserModel(parent = user_key(),
                first_name = first_name, last_name = last_name, 
                email = email)
            user.put()

            feedback = FeedbackModel(parent = feedback_key(),
                user = user, feedback = feedback)
            feedback.put()

            stat = "gracias mucho :)"
            self.render("faq.html", stat = stat)
        else:
            error = "oops! try typing that again"
            self.render("faq.html", 
                feedback = feedback,  
                first_name = first_name, last_name = last_name, 
                email = email, error = error)

class Sell(Handler):
    def get(self):
        self.render("sell.html")

    def post(self):
        have_error = False;
        amount = self.request.get('amount')
        price = self.request.get('price')

        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        email = self.request.get('email')

        params = dict(amount = amount, 
                        price = price,
                        email = email)

        #todo: display all error messages at once; js response if right

        if not valid_amount(amount):
            params['error_amount'] = "that amount was not valid"
            have_error = True

        if not valid_amount(amount):
            params['error_price'] = "that price was not valid"
            have_error = True

        if not valid_email(email):
            params['error_email'] = "that email was't valid"
            have_error = True

        if amount and price and first_name and last_name and email and (have_error == False):
            seller = email
            sell = SellModel(parent = sell_key(seller), 
                amount = amount, price = price, 
                first_name = first_name, last_name = last_name, 
                email = email)
            sell_check_key = sell.put()
            stat = "your entry has been recorded! awesomeness"
            self.render("sell.html", stat = stat)

        else:
            error = "make sure you fill out every box"
            self.render("sell.html", 
                        amount = amount, price = price, 
                        first_name = first_name, last_name = last_name,
                        email = email, error=error)

class Wish(Handler):
    def get(self):
        wishes = WishModel.all().order('wish_price')
        self.render("wish.html", wishes = wishes)

class NewWish(Handler):
    def get(self):
        self.render("newwish.html")

    def post(self):
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        email = self.request.get('email')

        wish_amount = self.request.get("wish_amount")
        wish_price = self.request.get("wish_price")

        if wish_amount and wish_price and first_name and last_name and email:
            user = UserModel(parent = user_key(),
                    first_name = first_name, last_name = last_name, 
                    email = email)

            email = self.request.get('email')

            database = UserModel.all().filter("email =", email)

            count = 0
            for data in database:
                if data.email == email:
                    count = 1

            #user doesn't exist
            if count == 0:
                user.put()
            #user exists
            else:
                u = UserModel.gql('where email = :email', email = email)
                user = u.get()

            wish = WishModel(parent = user, wish_amount = wish_amount, wish_price = wish_price)
            wish.put()
            stat = "success! your mp wish has been recorded :D"
            self.render("newwish.html", stat = stat)
        else:
            error = "sure you got every box?"
            self.render("newwish.html", error = error,
             wish_amount = wish_amount, wish_price = wish_price,first_name = first_name, last_name = last_name, 
                    email = email)

class Buy(Handler):
    def get(self):
        sells = SellModel.all().ancestor(sell_key()).order('price')

        for sell in sells:
            sell.checked = False
            sell_check_key = sell.put()

        self.render("buy.html", sells = sells)

    def post(self):
        sells = SellModel.all().order('price')

        boxcount = 0
        for sell in sells:
            check = self.request.get('check')

            if check:
                sell.checked = True

                sell_check_key = sell.put()
                boxcount += 1

        if boxcount == 0:
            error = "plz check at least one box to buy meal points :)"
            self.render("buy.html", error = error, sells = sells)
        else:     
            self.redirect('/contact') #aka NewBuy 
               
#cart view
class NewBuy(Buy):
    def get(self):
        cart = SellModel.all().ancestor(sell_key()).filter("checked =", True).order('price')
        self.render("newbuy.html", cart = cart)

    def post(self):
        buyer_email = self.request.get('buyer_email')
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')



        # if checked:
        #     self.redirect("/newbuy.html", checked = checked)
        # else:
        #     error = "check at least one box to buy meal"
        #     self.render("buy.html", sells = sells, error = error)

        #email =
        #get seller email from sell key

        # #validate email
        # subject = "I wish to buy your meal points"
        # body = "Hi! My name is %s and I'm interested in taking up your offer of x meal points at price per point") % first_name
        # # mail.send_mail(buyer_email, email, subject, body)
        self.render("newbuy.html")

#150 mp min, 10000 mp max
AMOUNT_RE = re.compile(r'^[1-9][0-9]{0,4}$|^10000$')

#min 0.01 per mp, max 2.00 per mp
PRICE_RE = re.compile(r'^[0-1]+\.[0-9][0-9]$|^2\.00$')

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')

def valid_amount(amount):
    return amount and AMOUNT_RE.match(amount)

def valid_price(price):
    return price and PRICE_RE.match(price)

def valid_email(email):
    return email and EMAIL_RE.match(email)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

application = webapp2.WSGIApplication([
    ('/', MainPage),

    ('/buy', Buy),
    ('/contact', NewBuy),

    ('/sell', Sell),
    ('/wish', Wish),
    ('/newwish', NewWish),
    ('/faq', FAQ),

], debug=True)


#TODO
    # CHECKBOX
    # EMAIL
    # EDIT

#cool features
    #ppl watching sells; price per point + giftcards/other payment options
    #when wish sell matches sell: automatic email

    #records/stories

    #avg price over time
        #sells
        #successful transactions

    #sell amount over time
    #sell patterns by year/class

#nice to have
    #cool data facts page
    #cookie id to replace repeat user info input