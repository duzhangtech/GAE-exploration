import os
import re
import urllib
import random
from string import letters

import jinja2
import webapp2
from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import memcache


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

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

class UserModel(db.Model):
    first_name = db.StringProperty(required = True)
    last_name = db.StringProperty(required = True)
    email = db.StringProperty(required = True)

class CartModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    cart_amount = db.IntegerProperty(required = True)
    cart_price = db.FloatProperty(required = True)

    def render(self):
        return render_str("cartmodel.html", c = self)

class FeedbackModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    feedback = db.StringProperty(required = True)
    def render(self):
        return render_str("feedback.html", f = self)

class SellModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    amount = db.StringProperty(required = True)
    price = db.StringProperty(required = True)
    num = db.IntegerProperty()

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

            #check if user exists
            database = UserModel.all().filter("email =", email)

            count = 0
            if database:
                count = 1

            if count == 0: #user doesn't exist
                user = UserModel(parent = user_key(),
                    first_name = first_name, last_name = last_name, 
                    email = email)
                user.put()

            else: #user exists
                #make key
                u = UserModel.gql('where email = :email', email = email)
                user = u.get()

            #now assign num
            total_sells = SellModel.all()
            total_num = total_sells.count()

            #get max sell num
            max_num = 0
            for item in total_sells:
                if item.num > max_num:
                    max_num = item.num

            #when nums are 1, 2, 4
            #in this case, there will always be
            #unassigned integer from 0 to total_num
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
            sell.put()

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

            database = UserModel.all().filter("email =", email)

            count = 0
            if database: 
                count = 1

            #user doesn't exist
            if count == 0:
                user.put()
            #user exists
            else:
                u = UserModel.gql('where email = :email', email = email)
                user = u.get()

            wish = WishModel(parent = wish_key(), user = user, wish_amount = wish_amount, wish_price = wish_price)
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
        self.render("buy.html", sells = sells)

    def post(self):
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        email = self.request.get('email')

        num = self.request.get('num')
        #FIXME validate num

        sells = SellModel.all().ancestor(sell_key()).order('price')

        if first_name and last_name and email and num:

            #check if user exists
            database = UserModel.all().filter("email =", email)
            count = 0
            if database:
                count = 1
            #user doesn't exist
            if count == 0:
                user = UserModel(parent = user_key(),
                    first_name = first_name, last_name = last_name, 
                    email = email)
                user.put()
            #user exists
            else:
                #make key, get user from key
                u = UserModel.gql('where email = :email', email = email)
                user = u.get() 

            num = self.request.get('num')

            derp = SellModel.gql('where num = :num', num = num)
            cart_item = derp.get()

            cart_amount = cart_item.amount
            cart_price = cart_item.price

            # cart_amount = 50
            # cart_price = 0.5
            # cart_item = SellModel.all().filter('num = ', num)
            # for item in cart_item: #should only be one item
            #     cart_amount = item.amount
            #     cart_price = item.price
            cart = CartModel(parent = cart_key(), user = user, cart_amount = cart_amount, cart_price = cart_price)
            cart.put()

            self.redirect('/contact')  


        else:
            error = "plz jot down an offer # from the list to buy meal points :)"
            self.render("buy.html", error = error, sells = sells)
        
#cart view
class NewBuy(Buy):
    def get(self):
        cart = CartModel.all()
        self.render("newbuy.html", cart = cart)

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