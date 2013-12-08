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

def user_key(name = "default"):
    return db.Key.from_path('user', name)

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
    feedback = db.StringProperty(required = True)
    def render(self):
        return render_str("feedback.html", f = self)

class SellModel(db.Model):
    amount = db.StringProperty(required = True)
    price = db.StringProperty(required = True)
    checked = db.BooleanProperty(default = False)

    def render(self):
        return render_str("sellmodel.html", s = self)

class WishModel(db.Model):
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
                email = email, 
                sells = FeedbackModel(parent = feedback_key(), feedback = feedback))
            user.put()

            # feedback = FeedbackModel(parent = feedback_key(),
            #     user = user, feedback = feedback)
            # feedback.put()

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

        if have_error:
            self.render("sell.html", **params)


        if amount and price and first_name and last_name and seller_email and (have_error == False):
            seller = seller_email
            sell = SellModel(parent = sell_key(seller), 
                amount = amount, price = price, 
                first_name = first_name, last_name = last_name, 
                seller_email = seller_email)
            sell_check_key = sell.put()
            stat = "your entry has been recorded! awesomeness"
            self.render("sell.html", stat = stat)

        else:
            error = "make sure you fill out every box"
            self.render("sell.html", 
                        amount = amount, price = price, 
                        first_name = first_name, last_name = last_name,
                        seller_email = seller_email, error=error)

class Wish(Handler):
    def get(self):
        wishes = WishModel.all().order('wish_price')
        self.render("wish.html", wishes = wishes)

class NewWish(Handler):
    def get(self):
        self.render("newwish.html")

    def post(self):
        wish_amount = self.request.get("wish_amount")
        wish_price = self.request.get("wish_price")

        if wish_amount and wish_price:
            wish = WishModel(parent = wish_key(), 
                            wish_amount = wish_amount, wish_price = wish_price)
            wish.put()
            stat = "success! your mp wish has been recorded :D"
            self.render("newwish.html", stat = stat, 
                            wish_amount = wish_amount, wish_price = wish_price)
        else:
            error = "sure you got both boxes?"
            self.render("newwish.thml", error = error,
                            wish_amount = wish_amount, wish_price = wish_price)

class Buy(Handler):
    def get(self):
        sells = SellModel.query(ancestor = sell_key).order(SellModel.price)
        #sells = sell_check_key.get()

        for sell in sells:
            sell.checked = False
            sell_check_key = sell.put()

        self.render("buy.html", sells = sells)

    def post(self):
        sells = SellModel.query(ancestor = sell_key).order(SellModel.price)
        #sells = sell_check_key.get()

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
        #cart = SellModel.query(SellModel.checked == True)
        cart = sell_check_key.get(checked == True)
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

        #seller_email =
        #get seller email from sell key

        # #validate email
        # subject = "I wish to buy your meal points"
        # body = "Hi! My name is %s and I'm interested in taking up your offer of x meal points at price per point") % first_name
        # # mail.send_mail(buyer_email, seller_email, subject, body)
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
