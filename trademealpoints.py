import webapp2
import jinja2
import logging
import random
import math
import json
import re

from string import letters
from decimal import *

from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler

jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader('templates'), autoescape = True) 

secret = "asd8B*#lfiewnL#FF:OIWEfkjkdsa;fjk;;lk"

def user_key():
    return db.Key.from_path('user_kind', 'user_id')

def sell_key():
    return db.Key.from_path('sell_kind', 'sell_id')

def verify_key():
    return db.Key.from_path('verify_kind', 'verify_id')

def feedback_key():
    return db.Key.from_path('feedback_kind', 'feedback_kind')

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
    feedback = db.StringProperty()

class VerifyModel(db.Model):
    email = db.StringProperty()
    code = db.StringProperty()

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def make_salt(self):
        salt = ''.join(random.choice(letters) for x in xrange(5))
        return salt

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)

class FAQ(Handler):
    def get(self):
        self.render("faq.html")

    def post(self):
        feedback = self.request.get('feedback')
        FeedbackModel(parent = feedback_key(), feedback = feedback).put()

class Buy(Handler):
    def get(self):
        sells = SellModel.all().ancestor(sell_key()).filter("fulfilled", False).order('price').order('amount')
        email = self.request.get("e")
        self.render("buy.html", sells = sells, count = sells.count(), email = email)

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
                        stat = stat, 
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
                    stat = stat, 
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

def prettyamount(amount):
    if amount.count('.') == -1: #NO DECIMAL POINT
        return re.sub("[^0-9]", "", amount.lstrip('0')) 
    else: #HAS DECIMAL POINT
        return str(math.floor(float(re.sub("[^0-9\.]", "", amount)))).strip('0').replace(".", "")
      
def prettyprice(price):
    if price.count('.') > 1: #LOLZ
        return price
    else:
        price = price.strip('0').replace(" ", "").replace("$", "")
        price = "{:3.2f}".format(float(price))
        return price

def prettyemail(email):
    return email.lower()

class Sell(Handler):
    def get(self):
        self.render("sell.html")

    def post(self):
        submit_button = self.request.get("submit_button")
        resend_button = self.request.get("resend_button")

        amount = prettyamount(self.request.get('amount'))
        price = prettyprice(self.request.get('price'))
        email = prettyemail(self.request.get('email'))

        user = UserModel.all().ancestor(user_key()).filter("email", email).get()
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        code = self.request.get('code')

        if submit_button:

            #BASIC INPUT ERRORS
            if not valid_amount(amount):
                error = "150 to 2000 mp (whole numbers)"
                self.render("sell.html", 
                        amount = amount, price = price, 
                        first_name = first_name, last_name = last_name,
                        email = email, error=error)

            elif not valid_price(price):
                error = "$0.01 to $1 per mp"
                self.render("sell.html", 
                        amount = amount, price = price, 
                        first_name = first_name, last_name = last_name,
                        email = email, error=error)


            elif not valid_email(email):
                error = "Use your wustl email"
                self.render("sell.html", 
                        amount = amount, price = price, 
                        first_name = first_name, last_name = last_name,
                        email = email, error=error)

            #BASIC INPUT OKAY
            elif amount and price and email: 
                
                if not code: #OKAY TO SUBMIT OR NEED VERIFY?
                    user = UserModel.all().ancestor(user_key()).filter("email", email).get()

                    if user: #YAY. CAN PROCEED WITH SELL
                        sell = SellModel(parent = sell_key(), user = user,
                        amount = amount, price = price, fulfilled = False)

                        sell.put()

                        v = VerifyModel.all().filter("email", email).get()

                        sender = "bot@trademealpoints.appspotmail.com"
                        receiver = email
                        subject = "MEAL POINTS: LINKS AND STUFF!"
                        
                        body =  (
                                "Hello!\n\n"
                                + "This link highlights your offer on the buy page: \n"
                                + "trademealpoints.appspot.com/buy?e=" + email
                                + "\n\nYou can edit or remove your offers here: \n" 
                                + "trademealpoints.appspot.com/change?e=" + email 
                                + "&v=" + v.code + "\n\n"
                                + "You can comment/ask for features/say hi here:\n"
                                + "trademealpoints.appspot.com/faq#feed\n\n"
                                + "Yours, \n"
                                + "Bot"
                                )

                        mail.send_mail(sender, receiver, subject, body)

                        sells = SellModel.all().ancestor(sell_key()).filter("fulfilled =", False).order('price')
                        self.redirect('/buy?e=' + email)

                    elif not user: #NEW USER OR IN LIMBO?
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

                        else: #IN LIMBO, ASK FOR CODE
                            self.render("sell.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name,
                                email = email, need_code = True, error = "Invalid code. Resend?")

                elif first_name and last_name and code: #IS VERIFY OKAY?
                    check_code = VerifyModel.all().filter("code", code).get()

                    if check_code: #YAY. COMMIT USER & OFFER

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

                        sender = "bot@trademealpoints.appspotmail.com"
                        receiver = email
                        subject = "YOUR MEAL POINTS: LINKS AND STUFF!"
                        
                        body =  (
                                "Hello!\n\n"
                                + "This link highlights your offer on the buy page: \n"
                                + "trademealpoints.appspot.com/buy?e=" + email
                                + "\n\nYou can edit or remove your offer here: \n" 
                                + "trademealpoints.appspot.com/change?e=" + email 
                                + "&v=" + code + "\n\n"
                                + "You can comment/ask for features/say hi here:\n"
                                + "trademealpoints.appspot.com/faq#feed\n\n"
                                + "Yours, \n"
                                + "Bot"
                                )

                        mail.send_mail(sender, receiver, subject, body)

                        self.redirect("/buy?e=" + email)

                    elif not check_code: #OH SNAP
                        stat = "Invalid code"
                        self.render("sell.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name,
                                email = email, need_code = True, stat = stat)

            else: #BLANK FIELD
                error = "Fill every box"
                self.render("sell.html", 
                            amount = amount, price = price, 
                            first_name = first_name, last_name = last_name,
                            email = email, error=error)

        #RESEND CODE!
        elif resend_button:
            code = VerifyModel.all().ancestor(verify_key()).filter("email", email).get().code

            sender = "bot@trademealpoints.appspotmail.com"
            receiver = email
            subject = "MEAL POINTS VERIFICATION"
            body =  ("Hello! Your verification code is " + code)
            mail.send_mail(sender, receiver, subject, body)

            self.render("sell.html", 
                amount = amount, price = price, 
                first_name = first_name, last_name = last_name,
                email = email, need_code = True, error = "code sent!")

class Edit(Handler):
    def get(self):
        self.render("edit.html")

    def post(self):
        email = self.request.get("email")

        if email:
            user = UserModel.all().filter("email", email).get()
            sell = SellModel.all().filter("user", user).get()

            if sell:
                code = VerifyModel.all().filter('email', email).get()

                if not code:
                    code = VerifyModel(parent = verify_key(), 
                                            email = email, 
                                            code = self.make_salt())

                    code.put()

                sender = "bot@trademealpoints.appspotmail.com"
                receiver = email
                subject = "EDIT MEAL POINT OFFER"
                
                body =  (
                         "Hello!\n\n"
                        + "This link highlights your offer on the buy page: \n"
                        + "trademealpoints.appspot.com/buy?e=" + email
                        + "\n\nYou can edit or remove your offer here: \n" 
                        + "trademealpoints.appspot.com/change?e=" + email 
                        + "&v=" + code.code + "\n\n"
                        + "You can comment/ask for features/say hi here:\n"
                        + "trademealpoints.appspot.com/faq#feed\n\n"
                        + "Yours, \n"
                        + "Bot"
                        )

                mail.send_mail(sender, receiver, subject, body)

                self.render("edit.html", stat = 'check your email!')

            else:
                stat = "You don't have any offers on the market"
                self.render("edit.html", stat = stat)

        else:
            stat = "(You used your wustl email)"
            self.render("edit.html", stat = stat)

class EditFinish(Handler):
    def get(self):
        email = self.request.get('e')
        code = self.request.get('v')

        okaycode = VerifyModel.all().ancestor(verify_key()).filter('email', email).filter('code', code).get()

        if okaycode:
            u = UserModel.all().filter("email", email).get()
            offer = list(SellModel.all().ancestor(sell_key()).filter('user', u))
            offer.sort(key = lambda x:((float)(x.amount), (float)(x.price)))
            self.render("editfinish.html", offer = offer)

        else:
            self.redirect('/changeoffer')

    def post(self):
        edit_button = self.request.get('edit_button')
        delete_button = self.request.get('delete_button')

        email = self.request.get("e")
        user = UserModel.all().filter("email", email).get()
        offer = list(SellModel.all().ancestor(sell_key()).filter('user', user).order('amount'))
        offer.sort(key = lambda x:((float)(x.amount), (float)(x.price)))

        if edit_button:            

            amount = self.request.get_all("amount")
            price = self.request.get_all("price")

            #FILLED FIELDS
            if (len(offer) == len(amount) and len(offer) == len(price)):
                logging.error("LENGTH: " + str(len(offer)))

                change = False
                wrongamount = False
                wrongprice = False

                for x in range(0, len(offer)):
                    logging.error(offer[x].amount)
                    logging.error(amount[x])

                    if offer[x].amount != amount[x]:
                        change = True

                        if valid_amount(amount[x]):
                            offer[x].amount = amount[x]
                            offer[x].put()
                        else:
                            wrongamount = True

                    if offer[x].price != price[x]:
                        change = True

                        if valid_price(price[x]):
                            offer[x].price = price[x] 
                            offer[x].put()
                        else:
                            wrongprice = True

                if change:
                    logging.error("CHANGE")
                    
                    if wrongamount == True:
                        offer = list(SellModel.all().ancestor(sell_key()).filter('user', user).order('amount'))
                        offer.sort(key = lambda x:((float)(x.amount), (float)(x.price)))
                        self.render("editfinish.html", offer = offer, editstat = "150 to 2000 mp")
                    elif wrongprice == True:
                        offer = list(SellModel.all().ancestor(sell_key()).filter('user', user).order('amount'))
                        offer.sort(key = lambda x:((float)(x.amount), (float)(x.price)))
                        self.render("editfinish.html", offer = offer, editstat = "0.01 to 1.00 per mp")
                    else:
                        offer = list(SellModel.all().ancestor(sell_key()).filter('user', user).order('amount'))
                        offer.sort(key = lambda x:((float)(x.amount), (float)(x.price)))
                        self.render("editfinish.html", offer = offer, editstat = "Updated successfully!")

                elif not change:
                    logging.error("NO CHANGE")
                    self.render("editfinish.html", offer = offer, editstat = "Updated successfully!")

            else: #BLANK FIELD
                self.render("editfinish.html", offer = offer, editstat = "Fill each box")

        elif delete_button: 
            delete_amount = self.request.get("delete_amount")
            delete_price = self.request.get("delete_price")

            if delete_amount and delete_price:
                derp = SellModel.all().ancestor(sell_key()).filter("user", user).filter('amount', delete_amount).filter('price', delete_price).get()

                if derp:
                    derp.delete()
                    offer = list(SellModel.all().ancestor(sell_key()).filter('user', user))
                    offer.sort(key = lambda x:((float)(x.amount), (float)(x.price)))

                    self.render("editfinish.html", offer = offer, deletestat = "Offer removed.")

                elif not derp:
                    self.render("editfinish.html", offer = offer, deletestat = "You don't have this offer on market.")

            else:
                self.render("editfinish.html", offer = offer, deletestat = "Fill each box")

class LogSenderHandler(InboundMailHandler):
    def receive(self, mail_message):
        logging.info("from: " + mail_message.sender)
        plaintext = mail_message.bodies(content_type='text/plain')
        for text in plaintext:
            m = ""
            m = text[1].decode()
            logging.info("message: %s" % m)
            self.response.out.write(m)

def valid_amount(amount):
    return amount and re.compile(r'^[1][5-9][0-9]\.?$|^[2-9][0-9]{2}\.?$|^[1][0-9]{3}\.?$|^2000\.?$').match(amount)

def valid_price(price):
    return price and re.compile(r'^[0]?\.[0-9]*$|^1$|^1\.|^1\.[0]*$').match(price)

def valid_email(email):
    return email and re.compile(r'^[\S]+(?i)(@wustl\.edu)$').match(email)

application = webapp2.WSGIApplication([
                    ('/', Buy),
                    ('/buy', Buy),
                    ('/contact', BuyContact),
                    ('/sell', Sell),
                    ('/changeoffer', Edit),
                    ('/change', EditFinish),
                    ('/faq', FAQ), 
                    LogSenderHandler.mapping()],
                    debug=True)