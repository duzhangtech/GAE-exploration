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
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = "asd8B*#lfiewnL#FF:OIWEfkjkdsa;fjk;;lk"

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
        username = self.read_secure_cookie('user')
        self.user = username 

class PointCount(db.Model):
    total = db.IntegerProperty()

class UserModel(db.Model):
    first_name = db.StringProperty(required = True)
    last_name = db.StringProperty(required = True)
    email = db.StringProperty(required = True)

class SellModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    amount = db.StringProperty(required = True)
    price = db.StringProperty(required = True)
    fulfilled = db.BooleanProperty(default = False)

    def render(self):
        return render_str("sellmodel.html", s = self)

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

class Buy(Handler):
    def get(self):
        self.clear_cart()
       
        query = SellModel.all().ancestor(sell_key()).filter("fulfilled =", False).order('price')
        query = list(query)
        if len(query) == 0:
            logging.error("EMPTY DB")
            count = 0
        else:
            logging.error("DB WRITE TO MC")
            count = 1

        self.render("buy.html", sells = query, count = count)

    def post(self):
        first_name = self.request.get('first_name')
        num = int(self.request.get('num')) #TODO: VALIDATE NUM

        if first_name and num:
            selected = SellModel.gql("where num = :num", num=num).get()
            amount = selected.amount
            price = selected.price

            self.new_cart(first_name) #add cookie
            self.redirect('/contact?first_name=' + first_name + "&amount=" + amount + "&price=" + price + "&num=" + str(num))
        else: 
            cart_error = "fill in all the boxes"
            self.render("buy.html", cart_error = cart_error, sells = list(sells))
        
class NewBuy(Handler):
    def get(self):
        first_name = self.request.get("first_name")
        amount = self.request.get("amount")
        price = self.request.get("price")
        num = self.request.get("num")

        if not first_name:
            logging.error("NO FIRST NAME")

        self.new_cart(first_name)
        self.render("newbuy.html", first_name=first_name, amount = amount, price = price, num = num) 
        return

    def post(self):
        first_name = self.request.get("first_name")
        amount = self.request.get("amount")
        price = self.request.get("price")
        num = self.request.get("num")

        last_name = self.request.get('last_name')
        email = self.request.get('email')

        if last_name and email:
            subject = "A BUYER!"
            sender = "bot@trademealpoints.appspotmail.com"
            
            name = self.request.get("first_name")
            amount = self.request.get("amount")
            price = self.request.get("price")
            num = self.request.get("num")

            seller = SellModel.gql("where num = :num", num = int(num)).get()
            receiver = seller.user.email

            body = (
                "Hey hey, savvy meal point seller. It looks like %s %s is interested in buying your offer of %s meal points at $%s per point! \n\n" % (first_name, last_name, amount, price) 

                + "You can reach %s %s at %s. \n \n" % (first_name, last_name, email) 

                + "To complete this transaction, arrange with %s to visit Dining Services Offices in the South Forth House to sign the transaction form.\n\n" % (first_name)

                + "Remember that WashU is going to take a 15 point transaction fee, 7.5 points per person. \n\n" 

                + "If you have any questions/comments/just want to say hi, please leave them in the feedback box on the FAQ page! \n\n"

                + "All right, I'm done now. You've been a real spiffy human to serve. Have an A1 Day! \n\n"

                + "Mechanically yours, \n"
                + "Bot\n\n"

                + "P.S. Your offer no longer appears on the 'buy' page. If you do not complete this transaction and wish to relist your offer, simply re-enter your info on the 'sell' page.")

            mail.send_mail(sender, receiver, subject, body)


            receiver = email
            subject = "MEAL POINTS"
            body = (
                "Hey hey, savvy meal point buyer. You can reach %s %s at %s regarding %s's offer of %s meal points at $%s per point. \n \n" % (seller.user.first_name, seller.user.last_name, seller.user.email, seller.user.first_name, amount, price)

                + "To complete this transaction, arrange with %s to visit Dining Services Offices in the South Forth House to sign the transaction form.\n\n" % (seller.user.first_name)

                + "Remember that WashU is going to take a 15 point transaction fee, 7.5 points per person. \n\n" 

                + "If you have any questions/comments/just want to say hi, please leave them in the feedback box on the FAQ page! \n\n"

                + "All right, I'm done now. You've been a real spiffy human to serve. Have an A1 Day!\n\n"
                + "Mechanically yours, \n"
                + "Bot")

            mail.send_mail(sender, receiver, subject, body)

            seller.fulfilled = True
            seller.put()
           
            stat = "check your inbox!"
            self.render("newbuy.html", stat = stat, first_name=first_name, amount = amount, price = price, num = num)
        else:
            error = "fill in every box"
            self.render("newbuy.html", error = error, first_name=first_name, amount = amount, price = price, num = num)

class LogSenderHandler(InboundMailHandler):
    def receive(self, mail_message):
        logging.info("from: " + mail_message.sender)
        plaintext = mail_message.bodies(content_type='text/plain')
        for text in plaintext:
            m = ""
            m = text[1].decode()
            logging.info("message: %s" % m)
            self.response.out.write(m)

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

            u = UserModel.gql('where email = :email', email = email)
            user = u.get()

            if not user:
                logging.error("USER DOESN'T EXIST, DB COMMIT")
                user = UserModel(parent = user_key(), 
                    first_name = first_name, last_name = last_name, email = email)
                user.put()            

            #assign num
            sells = SellModel.all().ancestor(sell_key())
            total_num = sells.count()

            max_num = 0
            for s in sells:
                if s.num > max_num:
                    max_num = s.num

            if max_num > total_num:
                for x in range(1, total_num+1):
                    findnum = SellModel.all().filter("num = ", x)
                    if not findnum:
                        num = x
                        break

            elif max_num == total_num:
                num = max_num + 1

            sell = SellModel(parent = sell_key(), user = user,
                amount = amount, price = price, num = num, fulfilled = False)

            sell.put()            
            sells = SellModel.all().ancestor(sell_key())

            stat = "your entry has been recorded! awesomeness"
            self.render("sell.html", stat = stat)

        else:
            error = "make sure you fill out every box"
            self.render("sell.html", 
                        amount = amount, price = price, 
                        first_name = first_name, last_name = last_name,
                        email = email, error=error)

class EditSell(Handler):
    def get(self):
        self.render("editsell.html")

    def post(self):
        email = self.request.get("email")
        current_amount = self.request.get("current_amount")
        current_price = self.request.get("current_price")
        new_amount = self.request.get("new_amount")
        new_price = self.request.get("new_price")

        if email and current_amount and current_price and new_amount and new_price:
            u = UserModel.all().filter("email", email)
            user = u.get()

            if not user:
                stat = "you haven't sold any meal points yet!"
                self.render("editsell.html", stat = stat)

            else:
                offer = SellModel.all().filter("user", user).filter("amount", current_amount).filter("price", current_price)
                offer = offer.get()

                if not offer:
                    stat = "you haven't listed this offer!"
                    self.render("editsell.html", stat = stat)

                else:
                    offer.amount = new_amount
                    offer.price = new_price
                    offer.put()

                    stat = "offer successfully changed"
                    self.render("editsell.html", stat = stat)

        else:
            stat = "fill every box"
            self.render("editsell.html", stat = stat)

class RelistSell(Handler):
    def get(self):
        self.render("relistsell.html")

    def post(self):
        email = self.request.get('email')
        amount = self.request.get('amount')
        price = self.request.get('price')

        if email and amount and price:
            u = UserModel.all().filter("email", email)
            user = u.get()

            if not user:
                stat = "you haven't sold any meal points yet!"
                self.render("relistsell.html", stat = stat)

            else:
                offer = SellModel.all().filter("user", user).filter("amount", amount).filter("price", price)
                offer = offer.get()

                if not offer:
                    stat = "you haven't listed this offer!"
                    self.render("relistsell.html", stat = stat)

                else:
                    offer.fulfilled = False
                    offer.put()

                    stat = "offer successfully relist"
                    self.render("relistsell.html", stat = stat)
        else:
            stat = "fill every box"
            self.render("relistsell.html", stat = stat)

class DeleteSell(Handler):
    def get(self):
        self.render("deletesell.html")

    def post(self):
        email = self.request.get('email')
        amount = self.request.get('amount')
        price = self.request.get('price')

        if email and amount and price:
            u = UserModel.all().filter("email", email)
            user = u.get()

            if not user:
                stat = "you haven't sold any meal points yet!"
                self.render("delete.html", stat = stat)

            else:
                offer = SellModel.all().filter("user", user).filter("amount", amount).filter("price", price)
                offer = offer.get()

                if not offer:
                    stat = "you haven't listed this offer!"
                    self.render("deletesell.html", stat = stat)

                else:
                    offer.delete()

                    stat = "offer successfully deleted"
                    self.render("deletesell.html", stat = stat)
        else:
            stat = "fill every box"
            self.render("deletesell.html", stat = stat)

class Wish(Handler):
    def get(self):
        wishes = WishModel.all()
        if wishes.count() == 0:
            count = 0
        else:
            count = 1
        self.render("wish.html", wishes = wishes, count = count)

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

            u = UserModel.gql('where email = :email', email = email)          
            user = u.get()
            
            if user is None: 
                user = UserModel(parent = user_key(), first_name = first_name, last_name = last_name, email = email)
                user.put()
                

            wishes = WishModel.all().filter("wish_amount = ", wish_amount).filter("wish_price =", wish_price)

            if wishes.count() != 0: #db duplicate!
                error = "looks like your wish has already been recorded. sweet"
                logging.error("DUPLICATE DB WISH")
                self.render("newwish.html", error = error,
                    wish_amount = wish_amount, wish_price = wish_price,
                    first_name = first_name, last_name = last_name, email = email)
                
            else: 
                wish = WishModel(parent = wish_key(), user = user, wish_amount = wish_amount, wish_price = wish_price)
                wish.put()
                wishes = WishModel.all().ancestor(wish_key())
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
                    ('/editoffer', EditSell),
                    ('/relistoffer', RelistSell),
                    ('/deleteoffer', DeleteSell),

                    ('/wish', Wish),
                    ('/newwish', NewWish),
                    ('/faq', FAQ), 
                    LogSenderHandler.mapping()],
                    debug=True)


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