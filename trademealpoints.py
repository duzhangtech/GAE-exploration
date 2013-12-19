import os
import re
import urllib
import random
import hmac

import logging
import json
import jinja2
import webapp2

from string import letters
from datetime import datetime, timedelta

from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import memcache


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = "cherrytreeshark"

def cart_key(name="default"):
    return db.Key.from_path('cart', name)

#basic user can sell, wish, and give feedback
def user_key(name = "default"):
    return db.Key.from_path('user', name)

def sell_key(name = "default"):
    return db.Key.from_path('sell', name)

def wish_key(name = "default"):
    return db.Key.from_path('wish', name)

def feedback_key(name = "default"):
    return db.Key.from_path('feedback', name)


def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, user, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (user, cookie_val))

    def read_secure_cookie(self, user):
        cookie_val = self.request.cookies.get(user)
        return cookie_val and check_secure_val(cookie_val)

    def new_cart(self, user):
        self.set_secure_cookie('user', str(user))

    def clear_cart(self):
        self.response.headers.add_header('Set-Cookie', 'user=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user')
        self.user = uid 

class UserModel(db.Model):
    first_name = db.StringProperty(required = True)
    last_name = db.StringProperty(required = True)
    email = db.StringProperty(required = True)

class SellModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    amount = db.StringProperty(required = True)
    price = db.StringProperty(required = True)
    num = db.IntegerProperty(required = True)
    def render(self):
        return render_str("sellmodel.html", s = self)

class CartModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    num = db.IntegerProperty(required = True)
    def render(self):
        return render_str("cartmodel.html", c = self)

class FeedbackModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    feedback = db.StringProperty(required = True)
    def render(self):
        return render_str("feedback.html", f = self)

#TODO: ADD FREQUENCY PARAM
class WishModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    wish_amount = db.StringProperty(required = True)
    wish_price = db.StringProperty(required = True)

    def render(self):
        return render_str("wishmodel.html", w = self)

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
                #make key
                u = UserModel.gql('where email = :email', email = email)
                user = u.get()

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

def age_set(key, val): #WRITE VALUE, KEY, AND NOWTIME TO MEMCACHE
    save_time = datetime.utcnow()
    memcache.set(key, (val, save_time))

def age_get(key):   #GET MEMCACHE VALUE AND AGE FROM KEY
    r = memcache.get(key)
    if r:
        val, save_time = r
        age = (datetime.utcnow() - save_time).total_seconds()
    else:
        val, age = None, 0
    return val, age
    
def age_str(age):   #TIME SINCE LAST QUERY
    s = "queried %s seconds ago"
    age = int(age)
    if age == 1:
        s = s.replace('seconds', 'second')
    return s % age

def get_sells(update = False): #GET FROM/WRITE TO MEMCACHE
    q = SellModel.all()
    memcache_key = 'SELLS'

    sells, age = age_get(memcache_key)  #get from memcache
    if update or sells is None:         #if updating/not in memcache
        sells = list(q)                 #query db
        age_set(memcache_key, sells)    #update memcache
    return sells, age

def add_sell():     #COMMIT SELL TO DB, WRITE TO MEMCACHE
    sell = SellModel(parent = sell_key(), user = user,
                amount = amount, price = price, num = num)
    sell.put()                  #commit to db
    age_set("SELLS", sell)      #update memcache with new sell

def add_user(ip, user):
    user.put()
    get_user(update = True) #override memcache
    return str(user.key().id()) #return 

def get_user(email, update = False): #GET FROM or WRITE USER/AGE TO MEMCACHE
    u = UserModel.gql('where email = :email', email = email)
    memcache_key = 'USER'

    user, age = age_get(memcache_key)   #get from memcache
    if update or user is None:          #if not in memcache
        user = u.get                    #query db
        age_set(memcache_key, user)     #set key to user in memcache
    return user, age

class Buy(Handler):
    def get(self):
        sells, age = age_get("SELLS")
        if sells is None:
            sells = SellModel.all().order('price')
            logging.error("DB QUERY")
            count = 0
        else: 
            count = 1
        self.render("buy.html", sells = list(sells), count = count, age = age_str(age))

    def post(self):
        first_name = self.request.get('first_name')
        
        #TODO: VALIDATE NUM
        num = int(self.request.get('num'))

        sells, age = get_sells()

        if first_name and num:
            self.new_cart(first_name) #add cookie
            self.redirect('/contact')
        else: 
            cart_error = "fill in all the boxes"
            self.render("buy.html", cart_error = cart_error, sells = list(sells))
        
class NewBuy(Buy):
    def get(self):
        last_name = self.request.get('last_name')
        email = self.request.get('email')

        self.render("newbuy.html")

    # def post(self):
        
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

            user, age = age_get("USER")   
            if user is None:    #not in memcache
                u = UserModel.gql('where email = :email', email = email)
                user = u.get()
                if user:    #in database               
                    age_set("USER", list(user)) #write to memcache
                else:   #commit and write
                    user = UserModel(parent = user_key(), 
                        first_name = first_name, last_name = last_name, email = email)
                    user.put()
                    age_set("USER", user)
            
            #assign num
            sells, age = age_get("SELLS")  #check memcache

            if sells is None: 
                num = 1

            else: 
                total_num = len(sells)

                #get max sell num
                max_num = 0
                for sell in sells:
                    if sell.num > max_num:
                        max_num = sell.num

                #when nums are 1, 2, 4
                #in this case, there will always be
                #unassigned integer between 0 and total_num
                num = 1
                if max_num > total_num:
                    for x in range(1, total_num+1):
                        findnum = SellModel.all().filter("num = ", num)
                        if not findnum:
                            num = x
                            break

                #max_num will never be smaller than total_num
                if max_num == total_num:
                    num = max_num + 1


            sell = SellModel(parent = sell_key(), user = user,
                amount = amount, price = price, num = num)
            sell.put()                  #commit to db

            sells = SellModel.all().ancestor(sell_key())
            age_set("SELLS", list(sells))      #update memcache with new sell

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
        wishes, age = age_get("WISHES")
        if wishes is None:
            wishes = WishModel.all().order('wish_price')
            logging.error("DB QUERY")
            count = len(list(wishes))
            for wish in wishes:
                age_set("WISHES", wish)
        else:
            count = 1
        self.render("wish.html", wishes = wishes, count = count, age = age_str(age))

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
            user = UserModel(parent=user_key(), first_name = first_name, last_name = last_name, email = email)
            wishes, age = age_get("WISHES") 

            if wishes is None:
                wishes = WishModel.all().filter("wish_amount = ", wish_amount).filter("wish_price =", wish_price)

                if wishes: #db duplicate!
                    error = "this wish has already been submitted ELLOYHAY"
                    age_set("WISHES", list(wishes))
                    self.render("newwish.html", error = error,
                        wish_amount = wish_amount, wish_price = wish_price,
                        first_name = first_name, last_name = last_name, email = email)
                    
                else: 
                    user.put()
                    wish = WishModel(parent = wish_key(), user = user, wish_amount = wish_amount, wish_price = wish_price)
                    wish.put()
                    wishes = WishModel.all().ancestor(wish_key())
                    age_set("WISHES", list(wishes))
                    stat = "success! your mp wish has been recorded :D"
                    self.render("newwish.html", stat = stat)

            else:
                duplicate = False
                for wish in wishes:
                    if wish.wish_amount == wish_amount and wish.wish_price == wish_price:
                        duplicate = True

                if duplicate:
                    error = "this wish has already been submitted"
                    self.render("newwish.html", error = error,
                            wish_amount = wish_amount, wish_price = wish_price,
                            first_name = first_name, last_name = last_name, email = email)
                else:
                    user.put()
                    wish = WishModel(parent = wish_key(), user = user, wish_amount = wish_amount, wish_price = wish_price)
                    wish.put()
                    wishes = WishModel.all().ancestor(wish_key())
                    age_set("WISHES", list(wishes))
                    stat = "success! your mp wish has been recorded :D"
                    self.render("newwish.html", stat = stat)


        else:
            error = "fill in every box"
            self.render("newwish.html", error = error,
             wish_amount = wish_amount, wish_price = wish_price,first_name = first_name, last_name = last_name, 
                    email = email)

#150 mp min, 10000 mp max
AMOUNT_RE = re.compile(r'^[1-9][0-9]{0,4}$|^10000$')

#min 0.01 per mp, max 2.00 per mp
PRICE_RE = re.compile(r'^[0-1]+\.[0-9][0-9]$|^2\.00$')

#TODO: wustl.edu
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