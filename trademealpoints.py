import webapp2
import jinja2
import logging
import random
import json
import re

from string import letters

from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler


jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader('templates'), autoescape = True) 

secret = "asd8B*#lfiewnL#FF:OIWEfkjkdsa;fjk;;lk"

#basic user can sell, wish, and give feedback
def user_key():
    return db.Key.from_path('user_kind', 'user_id')

def sell_key():
    return db.Key.from_path('sell_kind', 'sell_id')

def verify_key():
    return db.Key.from_path('verify_kind', 'verify_id')

def feedback_key():
    return db.Key.from_path('feedback_kind', 'feedback_kind')

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

    def make_salt(self):
        salt = ''.join(random.choice(letters) for x in xrange(5))
        return salt

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        self.user = self.read_secure_cookie('user')

class UserModel(db.Model):
    first_name = db.StringProperty(required = True)
    last_name = db.StringProperty(required = True)
    email = db.StringProperty(required = True)

class SellModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    amount = db.StringProperty(required = True)
    price = db.StringProperty(required = True)
    fulfilled = db.BooleanProperty(default = False)
    created = db.DateTimeProperty(auto_now = True)

class FeedbackModel(db.Model):
    name = db.StringProperty()
    email = db.StringProperty()
    feedback = db.StringProperty()

class VerifyModel(db.Model):
    email = db.StringProperty()
    code = db.StringProperty()

class FAQ(Handler):
    def get(self):
        self.render("faq.html")

    def post(self):
        name = self.request.get('name')
        email = self.request.get('email')

        feedback = self.request.get('feedback')

        if feedback:
            f = FeedbackModel(parent = feedback_key(), feedback = feedback)
            if name:
                f.name = name
            if email:
                f.email = email

            f.put()
    

class Buy(Handler):
    def get(self):
        sells = memcache.get("SELLS")

        if sells is None:
            logging.error("EMPTY MC")
            sells = SellModel.all().filter("fulfilled", False).order('price')
            sells = list(sells)

            if len(sells) == 0:
                logging.error("EMPTY DB")
                count = 0
            else:
                logging.error("DB WRITE TO MC")
                memcache.set("SELLS", sells.sort(key = lambda x:((float)(x.price), (int)(x.amount))))
                count = len(sells)

        else:
            logging.error("SELLS IN MC")
            sells.sort(key = lambda x:((float)(x.price), (int)(x.amount)))
            count = len(sells)

        self.render("buy.html", sells = sells, count = count)


class BuySortMP(Handler):
    def get(self):
        sells = memcache.get("SELLS")

        if sells is None:
            logging.error("EMPTY MC")
            sells = SellModel.all().filter("fulfilled", False).order('price')
            sells = list(sells)

            if len(sells) == 0:
                logging.error("EMPTY DB")
                count = 0
            else:
                logging.error("DB WRITE TO MC")
                memcache.set("SELLS", sells.sort(key = lambda x:((int)(x.amount), (float)(x.price))))
                count = len(sells)

        else:
            logging.error("SELLS IN MC")
            sells.sort(key = lambda x:((int)(x.amount), (float)(x.price)))
            count = len(sells)

        self.render("buy.html", sells = sells, count = count)


class BuySortPrice(Handler):
    def get(self):
        sells = SellModel.all().filter("fulfilled", False).order('price')
        sells = list(sells)
        logging.error("PRICESORT")

        if len(sells) == 0:
            count = 0
        else:
            count = len(sells)

            db = sells
            sells = []

            for s in db:
                cost = (float)(s.price) * (int)(s.amount)

                sells.append((s, cost))

            sells.sort(key=lambda x: x[1])

        self.render("buy.html", sells = sells, count = count, pricesort = True)


class BuyContact(Handler):
    def contact_seller(self, amount, price, myemail):
        subject = "A BUYER!"
        sender = "bot@trademealpoints.appspotmail.com"
        
        seller = SellModel.all().ancestor(sell_key()).filter("amount", amount).filter("price", price).get()
        logging.error("AMOUNT: " + amount + "PRICE" + price)
        buyer = UserModel.all().ancestor(user_key()).filter("email", myemail).get()

        receiver = seller.user.email

        body = (
            "Hey hey, savvy meal point seller. It looks like %s %s is interested in buying your offer of %s meal points at $%s per point! \n\n" % (buyer.first_name, buyer.last_name, amount, price) 

            + "You can reach %s %s at %s. \n \n" % (buyer.first_name, buyer.last_name, myemail) 

            + "To complete this transaction, arrange with %s to visit Dining Services Offices in the South Forth House to sign the transaction form.\n\n" % (buyer.first_name)

            + "Remember that WashU is going to take a 15 point transaction fee, 7.5 points per person. \n\n" 

            + "If you have any questions/comments/just want to say hi, please leave them in the feedback box on the FAQ page! \n\n"

            + "All right, I'm done now. You've been a real spiffy human to serve. Have an A1 Day! \n\n"

            + "Mechanically yours, \n"
            + "Bot\n\n"

            + "P.S. Your offer no longer appears on the 'buy' page. If you do not complete this transaction and wish to relist your offer, simply re-enter your info on the 'sell' page.")

        mail.send_mail(sender, receiver, subject, body)

        receiver = myemail
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
        
        sells = SellModel.all().ancestor(sell_key()).filter("fulfilled =", False).order('price')
        if sells.count() == 0:
            memcache.set("SELLS", None)
        else:
            memcache.set("SELLS", list(sells))

        stat = "check your inbox!"
        self.render("newbuy.html", stat = stat, amount = amount, price = price)

    def get(self):
        amount = self.request.get("amount")
        price = self.request.get("price")

        if not amount or not price:
            self.redirect("/buy")
        else:
            self.render("newbuy.html", amount = amount, price = price) 

    def post(self):
        logging.error("SUBMIT BUTTON")
        submit_button = self.request.get("submit_button")
        resend_button = self.request.get("resend_button")
        code = self.request.get("code")

        amount = self.request.get("amount")
        price = self.request.get("price")

        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        email = self.request.get('email')

        if submit_button:
            logging.error("SUBMIT BUTTON")

            if valid_email(email):
                if not code:
                    logging.error("NOT CODE")
                    user = UserModel.all().ancestor(user_key()).filter("email", email).get()

                    if not user:
                        logging.error("NOT USER")
                        waiting_for_verify = VerifyModel.all().filter("email", email).get()

                        if not waiting_for_verify: #NEW USER, PUT IN LIMBO
                            code = self.make_salt()
                            VerifyModel(parent = verify_key(), 
                                            email = email, 
                                            code = code).put()

                            sender = "bot@trademealpoints.appspotmail.com"
                            receiver = email
                            subject = "MEAL POINTS VERIFICATION"
                            body =  ("Hello! Your verification code is" + code)
                            mail.send_mail(sender, receiver, subject, body)

                            self.render("newbuy.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name,
                                email = email, need_code = True)

                        elif waiting_for_verify: #ASK FOR CODE
                            self.render("newbuy.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name,
                                email = email, need_code = True)

                    elif user: #VERIFIED, CAN CONTACT SELLER
                        self.contact_seller(amount, price, email)

                elif code and first_name and last_name:
                    logging.error("CODE")
                    check_code = VerifyModel.all().filter("code", code).get()

                    if check_code: #DELETE CODE, COMMIT USER & SEND EMAIL
                        logging.error("CHECK CODE")
                        check_code.delete()

                        user = UserModel(parent = user_key(),
                                    first_name = first_name, 
                                    last_name = last_name,
                                    email = email)
                        user.put()

                        self.contact_seller(amount, price, email)

                    elif not check_code: #OH SNAP
                        stat = "invalid code"
                        self.render("newbuy.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name,
                                email = email, need_code = True, stat = stat)

                elif code and not first_name or not last_name:
                    error = "fill in every box"
                    self.render("newbuy.html", 
                        first_name=first_name, 
                        amount = amount, 
                        price = price, 
                        error = error, 
                        need_code = True,
                        last_name=last_name, 
                        email = email,
                        code = code)

            elif first_name and last_name and not valid_email(email):
                stat = "use your wustl email"
                self.render("newbuy.html", 
                            amount = amount, 
                            price = price, 
                            need_code = True,
                            first_name = first_name, 
                            last_name = last_name,
                            email = email, 
                            stat = stat)

            elif not email or not valid_email(email):
                error = "use your wustl email"
                self.render("newbuy.html", 
                    first_name=first_name, 
                    amount = amount, 
                    price = price, 
                    error = error, 
                    last_name=last_name, 
                    email = email)

        elif resend_button:
            code = VerifyModel.all().ancestor(verify_key()).filter("email", email).get().code

            sender = "bot@trademealpoints.appspotmail.com"
            receiver = email
            subject = "MEAL POINTS VERIFICATION"
            body =  ("Hello! Your verification code is " + code)
            mail.send_mail(sender, receiver, subject, body)

            self.render("newbuy.html", 
                amount = amount, price = price, 
                first_name = first_name, last_name = last_name,
                email = email, need_code = True)


class Sell(Handler):
    def get(self):
        self.render("sell.html")

    def post(self):
        something_wrong = False
        submit_button = self.request.get("submit_button")
        resend_button = self.request.get("resend_button")

        amount = self.request.get('amount')
        price = self.request.get('price')

        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')

        email = self.request.get('email')
        user = UserModel.all().ancestor(user_key()).filter("email", email).get()

        code = self.request.get('code')

        params = dict(amount = amount, 
                        price = price,
                        email = email)

        if not valid_amount(amount):
            params['error_amount'] = "150 meal point minimum"
            something_wrong = True

        if not valid_price(price):
            params['error_price'] = "0.01 to 2.00 per meal point"
            something_wrong = True

        if not valid_email(email):
            params['error_email'] = "use your wustl email"
            something_wrong = True

        if submit_button:
            logging.error("SUBMIT")
            if amount and price and email and (something_wrong == False):
                
                if not code:
                    logging.error("NOT CODE")
                    user = UserModel.all().ancestor(user_key()).filter("email", email).get()

                    if not user:
                        waiting_for_verify = VerifyModel.all().filter("email", email).get()

                        if not waiting_for_verify: #NEW USER, PUT IN LIMBO
                            code = self.make_salt()
                            VerifyModel(parent = verify_key(), 
                                            email = email, 
                                            code = code).put()

                            sender = "bot@trademealpoints.appspotmail.com"
                            receiver = email
                            subject = "MEAL POINTS VERIFICATION"
                            body =  ("Hello! Your verification code is " + code)
                            mail.send_mail(sender, receiver, subject, body)

                            self.render("sell.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name,
                                email = email, need_code = True)

                        else: #ASK FOR CODE
                            self.render("sell.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name,
                                email = email, need_code = True)

                    elif user: #VERIFIED, CAN PROCEED WITH SELL
                        sell = SellModel(parent = sell_key(), user = user,
                        amount = amount, price = price, fulfilled = False)

                        sell.put()

                        sells = SellModel.all().ancestor(sell_key()).filter("fulfilled =", False).order('price')
                        memcache.delete("SELLS")
                        memcache.set("SELLS", list(sells))

                        self.redirect('/buy')

                elif first_name and last_name and code:
                    logging.error("CODE")
                    check_code = VerifyModel.all().filter("code", code).get()

                    if check_code: #DELETE CODE, COMMIT USER & OFFER
                        check_code.delete()

                        user = UserModel(parent = user_key(),
                                    first_name = first_name, 
                                    last_name = last_name,
                                    email = email)
                        user.put()

                        SellModel(parent = sell_key(),
                                    user = user, 
                                    amount = amount,
                                    price = price).put()

                        sells = SellModel.all().ancestor(sell_key()).filter("fulfilled", False)
                        memcache.set("SELLS", list(sells))

                        self.redirect("/buy")

                    elif not check_code: #OH SNAP
                        stat = "invalid code"
                        self.render("sell.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name,
                                email = email, need_code = True, stat = stat)


            #BASIC INPUT ERROR
            elif amount and price  and email and something_wrong == True:

                if not valid_amount(amount):
                    error = "150 mp min, 4000 mp max"
                    self.render("sell.html", 
                            amount = amount, price = price, 
                            first_name = first_name, last_name = last_name,
                            email = email, error=error)

                elif not valid_price(price):
                    error = "0.01 to 2.00 per meal point"
                    self.render("sell.html", 
                            amount = amount, price = price, 
                            first_name = first_name, last_name = last_name,
                            email = email, error=error)


                elif not valid_email(email):
                    error = "use your wustl email"
                    self.render("sell.html", 
                            amount = amount, price = price, 
                            first_name = first_name, last_name = last_name,
                            email = email, error=error)

            else:
                error = "Fill every box"
                self.render("sell.html", 
                            amount = amount, price = price, 
                            first_name = first_name, last_name = last_name,
                            email = email, error=error)

        elif resend_button:
            code = VerifyModel.all().ancestor(verify_key()).filter("email", email).get().code

            sender = "bot@trademealpoints.appspotmail.com"
            receiver = email
            subject = "MEAL POINTS VERIFICATION"
            body =  ("Hello! Your verification code is" + code)
            mail.send_mail(sender, receiver, subject, body)

            self.render("sell.html", 
                amount = amount, price = price, 
                first_name = first_name, last_name = last_name,
                email = email, need_code = True)

class PasswordModel(db.Model):
    email = db.StringProperty()
    code = db.StringProperty()

class Edit(Handler):
    def get(self):
        self.render("edit.html")

    def post(self):
        email = self.request.get("email")

        if email:
            user = UserModel.all().filter("email", email).get()
            sell = SellModel.all().filter("user", user).get()

            if sell:
                code = self.make_salt()
                PasswordModel(parent = verify_key(), 
                                    email = email, 
                                    code = code).put()

                sender = "bot@trademealpoints.appspotmail.com"
                receiver = email
                subject = "EDIT MEAL POINT OFFER"
                body =  (
                        "Hello! You can click on this link to edit or (gasp) delete your offer. \n\n" 
                        + "trademealpoints.appspot.com/change?e=" + email 
                        + "&v=" + code+ "\n\n"
                        + "Have a good one, \n\n"
                        + "Bot"
                        )

                mail.send_mail(sender, receiver, subject, body)

                self.render("edit.html", stat = 'check your email!')

            else:
                stat = "you don't have any offers on the market"
                self.render("edit.html", stat = stat)

        else:
            stat = "(you used your wustl email)"
            self.render("edit.html", stat = stat)


class EditFinish(Handler):
    def get(self):
        email = self.request.get('e')
        code = self.request.get('v')

        okaycode = VerifyModel.all().ancestor(verify_key()).filter('email', email).filter('code', code).get()

        if okaycode:
            offer = SellModel.all().filter('user', user).get()
            self.render("editfinish.html", offer = offer)

        else:
            self.redirect('/changeoffer')

    def post(self):
        edit_button = self.request.get('edit_button')
        delete_button = self.request.get('delete_button')

        if edit_button:
            email = self.request.get("email")
       
            new_amount = self.request.get("new_amount")
            new_price = self.request.get("new_price")

            u = UserModel.all().filter("email", email)
            user = u.get()

            
            offer = SellModel.all().filter("user", user).filter("amount", current_amount).filter("price", current_price)
            offer = offer.get()

               
            offer.amount = new_amount
            offer.price = new_price
            offer.put()

            stat = "offer successfully changed"
            self.render("edit.html", stat = stat)

        elif delete_button:

            delete_amount = self.request.get("delete_amount")
            delete_price = self.request.get("delete_price")
            
            stat = "fill every box"
            self.render("edit.html", stat = stat)


class LogSenderHandler(InboundMailHandler):
    def receive(self, mail_message):
        logging.info("from: " + mail_message.sender)
        plaintext = mail_message.bodies(content_type='text/plain')
        for text in plaintext:
            m = ""
            m = text[1].decode()
            logging.info("message: %s" % m)
            self.response.out.write(m)

AMOUNT_RE = re.compile(r'^[1][5-9][0-9]$|^[2-9][0-9]{2}$|^[1-3][0-9]{3}$|^4000$')

PRICE_RE = re.compile(r'^[0-1]+\.[0-9][0-9]?$|^2\.00$')

EMAIL_RE  = re.compile(r'^[\S]+(?i)(@wustl\.edu)$')

NUM_RE = re.compile(r'^[0-9]*$')

def valid_amount(amount):
    return amount and AMOUNT_RE.match(amount)

def valid_price(price):
    return price and PRICE_RE.match(price)

def valid_email(email):
    return email and EMAIL_RE.match(email)

def valid_num(num):
    return num and NUM_RE.match(str(num))

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

application = webapp2.WSGIApplication([
                    ('/', Buy),
                    ('/buy', Buy),
                    ('/buysortprice', BuySortPrice),
                    ('/buysortmp', BuySortMP),

                    ('/contact', BuyContact),

                    ('/sell', Sell),

                    ('/changeoffer', Edit),
                    ('/change', EditFinish),


                    ('/faq', FAQ), 
                    LogSenderHandler.mapping()],
                    debug=True)