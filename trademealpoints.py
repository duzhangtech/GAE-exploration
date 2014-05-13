import webapp2
import jinja2
import logging
import random
import math
import re
import stripe

from string import letters
from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler

jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader('templates'), autoescape = True) 

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
    phone = db.StringProperty(required = False)
    email = db.StringProperty(required = True)

class SellModel(db.Model):
    user = db.ReferenceProperty(UserModel)
    amount = db.StringProperty(required = True)
    price = db.StringProperty(required = True)
    fulfilled = db.BooleanProperty(default = False)
    created = db.DateTimeProperty(auto_now = True)

class FeedbackModel(db.Model):
    feedback = db.TextProperty()

class VerifyModel(db.Model):
    email = db.StringProperty()
    code = db.StringProperty()

class HistoryModel(db.Model):
    description = db.StringProperty(required = True)
    amount = db.StringProperty(required = True)

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

# def okaycoffee(payment):
#     if payment.count('.') > 1 or len(payment) == 0: 
#         return False

#     else: #has . or none
#         if len(payment) == 1 and payment.count('.') == 1: #entry is just .
#             return False

#         elif payment.count('.') == 1:
#             payment = payment.strip('0')
#             return payment and re.compile(r'^[0-9]?\.[0-9]*$').match(payment)

#         elif payment.count('.') == 0:
#             return payment and re.compile(r'^[0-9]+$').match(payment)

# class PayMe(Handler):
#     def get(self):
#         self.render("payme.html")

#     def post(self):
#         # https://manage.stripe.com/account/apikeys

#         token = self.request.get('stripeToken')
#         email  = self.request.get('email')
#         amount = self.request.get('amount')

#         somethingwrong = False

#         params = dict(amount = amount, email = email)

#         if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
#             somethingwrong = True
#             params['emailstat'] = "Please enter a valid email"

#         if not okaycoffee(amount):
#             somethingwrong = True
#             params['amountstat'] = "Please enter a valid amount"

#         elif okaycoffee(amount):
#             amount = float(amount)
#             if amount < 1:
#                 somethingwrong = True
#                 params['amountstat'] = "Coffee costs at least $1"

#         if somethingwrong:
#             self.render("payme.html", **params)

#         else: 
#             try: 
#                 customer = stripe.Customer.create(
#                   card=token,
#                   email=email
#                 )
#                 amount=int(amount)
#                 charge = stripe.Charge.create(
#                   customer=customer.id,
#                   amount=amount*1000, #cents
#                   currency="usd"
#                 )              

#                 logging.error("amount " + str(amount*1000))

#                 self.render("payme.html", woohoo = True)

#             except stripe.CardError, e: 
#                 params['stat'] = "Your card was declined."
#                 self.render("payme.html", **params)


class FAQ(Handler):
    def get(self):
        self.render("faq.html")

class Summary(Handler):
    def get(self):
        sells = list(SellModel.all().ancestor(sell_key()).filter("fulfilled", True).order('created'))
        last = sells[-1]
        last = last.amount + "," + last.price
        k = HistoryModel(description = 'last_transaction', amount = last)
        k.put()
        if len(sells) == 0:
            total_transaction = 0
        else:
            total_transaction = 1000 + sum([(int)(sells[x].amount) for x in range(0, len(sells))])
        a = HistoryModel.all().filter('description', 'total_transaction').get()
        if a is None:
            t = HistoryModel(description = 'total_transaction', amount = str(total_transaction))
            t.put()
        else:
            a.amount = str(total_transaction)
            a.put()

class SubmitFeed(Handler):
    def post(self):
        feedback = self.request.get('feedback')
        FeedbackModel(parent = feedback_key(), feedback = feedback).put()

class Buy(Handler):
    def get(self):
        sells = memcache.get("SELLS")

        if sells is None:
            sells = list(SellModel.all().ancestor(sell_key()).filter("fulfilled", False).order('price'))
            if len(sells) != 0:
                memcache.set("SELLS", sells.sort(key = lambda x:((float)(x.price), (int)(x.amount))))
        else:
            sells.sort(key = lambda x:((float)(x.price), (int)(x.amount)))

        count = len(sells)

        email = self.request.get("e")
        
        a = HistoryModel.all().filter('description', 'total_transaction').get()
        last = HistoryModel.all().filter('description', 'last_transaction').get().amount.split(",")
        last = {'dd': last[0], 'dollar': last[1]}
        self.render("buy.html", sells = sells, count = count, email = email, total_transaction = a.amount, last = last)

class BuyContact(Handler):
    def contact_seller(self, amount, price, myemail):
        subject = "A BUYER!"
        sender = "duzhangtech@gmail.com"
        
        seller = SellModel.all().ancestor(sell_key()).filter("amount", amount).filter("price", price).get()
        logging.error("AMOUNT: " + amount + "PRICE" + price)
        buyer = UserModel.all().ancestor(user_key()).filter("email", myemail).get()

        receiver = seller.user.email

        body = (
            "Hey hey, savvy Dining Dollar seller. It looks like %s %s is interested in buying your offer of %s Dining Dollars at $%s per point! \n\n" % (buyer.first_name, buyer.last_name, amount, price) 

            + "You can reach %s %s at %s. \n \n" % (buyer.first_name, buyer.last_name, myemail) 

            + "To complete this transaction, arrange with %s to visit https://hdh.ucsd.edu/sso/DDContribution \n\n" % (buyer.first_name)

            + "If you have any questions/comments/just want to say hi, please leave them in the feedback box on the FAQ page! \n\n"

            + "P.S. Your offer no longer appears on the 'buy' page. If you do not complete this transaction and wish to relist your offer, simply re-enter your info on the 'sell' page."
            )

        mail.send_mail(sender, receiver, subject, body)

        receiver = myemail
        subject = "Dining Dollars"
        body = (
            "Hey hey, savvy Dining Dollar buyer. You can reach %s %s at %s or at %s regarding %s's offer of %s Dining Dollars at $%s per point. \n \n" % (seller.user.first_name, seller.user.last_name, seller.user.email, seller.user.phone, seller.user.first_name, amount, price)

            + "To complete this transaction, arrange with %s to visit https://hdh.ucsd.edu/sso/DDContribution \n\n" % (seller.user.first_name)

            + "If you have any questions/comments/just want to say hi, please leave them in the feedback box on the FAQ page! \n\n"
        )

        mail.send_mail(sender, receiver, subject, body)

        seller.fulfilled = True
        seller.put()
        
        sells = SellModel.all().ancestor(sell_key()).filter("fulfilled =", False).order('price')
        if sells.count() == 0:
            memcache.delete("SELLS")
            memcache.set("SELLS", None)
        else:
            memcache.delete("SELLS")
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

        phone = self.request.get('phone')
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

                            sender = "duzhangtech@gmail.com"
                            receiver = email
                            subject = "Dining Dollars VERIFICATION"
                            body =  ("Hello! Your verification code is" + code)
                            mail.send_mail(sender, receiver, subject, body)

                            self.render("newbuy.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name, phone = phone, 
                                email = email, need_code = True)

                        elif waiting_for_verify: #ASK FOR CODE
                            self.render("newbuy.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name, phone = phone, 
                                email = email, need_code = True)

                    elif user: #VERIFIED, CAN CONTACT SELLER
                        self.contact_seller(amount, price, email)

                elif code and first_name and phone and last_name:
                    logging.error("CODE")
                    check_code = VerifyModel.all().filter("code", code).get()

                    if check_code: #DELETE CODE, COMMIT USER & SEND EMAIL
                        logging.error("CHECK CODE")
                        check_code.delete()

                        user = UserModel(parent = user_key(),
                                    first_name = first_name, 
                                    last_name = last_name,
                                    phone = phone, 
                                    email = email)
                        user.put()

                        self.contact_seller(amount, price, email)

                    elif not check_code: #OH SNAP
                        self.render("newbuy.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name, phone = phone, 
                                email = email, need_code = True, stat = "invalid code")

                elif code and not first_name or not last_name:
                    self.render("newbuy.html", 
                        first_name=first_name, 
                        amount = amount, 
                        price = price, 
                        stat = "Fill each box", 
                        need_code = True,
                        phone = phone, 
                        last_name=last_name, 
                        email = email,
                        code = code)

            elif first_name and last_name and phone and not valid_email(email):
                self.render("newbuy.html", 
                            amount = amount, 
                            price = price, 
                            need_code = True,
                            first_name = first_name, 
                            last_name = last_name,
                            phone = phone, 
                            email = email, 
                            stat = "What's your UCSD email?")

            elif not email or not valid_email(email):
                self.render("newbuy.html", 
                    first_name=first_name, 
                    amount = amount, 
                    price = price, 
                    stat = "What's your UCSD email?", 
                    last_name=last_name, 
                    phone = phone, 
                    email = email)

        elif resend_button:
            code = VerifyModel.all().ancestor(verify_key()).filter("email", email).get().code

            sender = "duzhangtech@gmail.com"
            receiver = email
            subject = "Dining Dollars VERIFICATION"
            body =  ("Hello! Your verification code is " + code)
            mail.send_mail(sender, receiver, subject, body)

            self.render("newbuy.html", 
                amount = amount, price = price, 
                first_name = first_name, last_name = last_name, phone = phone, 
                email = email, need_code = True)

def prettyamount(amount):
    if amount.count('.') == -1: #DERP
        return re.sub("[^0-9]", "", amount.lstrip('0')) 
    elif len(amount) == 1 and amount.count('.') == 1: #why would you type this
        return "0.0"    
    elif amount.count('.') >1:
        return amount
    else: 
        return str(math.floor(float(re.sub("[^0-9\.]", "", amount)))).strip('0').replace(".", "")
    
def prettyprice(price):
    if price.count('.') > 1 or len(price) == 0: #LOLZ
        return price
    else: #has . or is 1
        price = price.strip('0').replace(" ", "").replace("$", "")
        price = re.sub("[^0-9\.]", "", price)

        if len(price) == 1 and price.count('.') == 1:
            return "0"
        elif len(price) != 0: #should be okay here
            price = "{:3.2f}".format(float(price))
            return price
        else: #SERIOUSLY PEOPLE
            return price

def prettyemail(email):
    return email.lower()

class Sell(Handler):
    def get(self):
        self.render("sell.html")

    def post(self):
        submit_button = self.request.get("submit_button")
        resend_button = self.request.get("resend_button")

        amount = self.request.get('amount')
        price = self.request.get('price')
        email = self.request.get('email')

        
        user = UserModel.all().ancestor(user_key()).filter("email", email).get()
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        phone = self.request.get('phone')
        code = self.request.get('code')

        if submit_button:

            if not amount or not price or not email: #BLANK FIELD
                self.render("sell.html", amount = amount, price = price, 
                            first_name = first_name, last_name = last_name,
                            email = email, phone = phone, stat="Fill every box")

            elif amount and price and email: 
                amount = prettyamount(amount)
                price = prettyprice(price)
                email = prettyemail(email)

                #BASIC INPUT ERRORS
                if not valid_amount(amount):
                    self.render("sell.html", 
                            amount = amount, price = price, 
                            first_name = first_name, last_name = last_name, phone = phone, 
                            email = email, stat="10 to 2000 dd (whole numbers)")

                elif not valid_price(price):
                    self.render("sell.html", 
                            amount = amount, price = price, 
                            first_name = first_name, last_name = last_name, phone = phone, 
                            email = email, stat="$0.01 to $1 per dd")


                elif not valid_email(email):
                    self.render("sell.html", 
                            amount = amount, price = price, 
                            first_name = first_name, last_name = last_name, phone = phone, 
                            email = email, stat="Use your UCSD email")

                #AMOUNT, PRICE, EMAIL OKAY
                elif not code: #OKAY TO SUBMIT OR NEED TO VERIFY?
                    user = UserModel.all().ancestor(user_key()).filter("email", email).get()

                    if user: #YAY. CAN PROCEED WITH SELL
                        sell = SellModel(parent = sell_key(), user = user,
                        amount = amount, price = price, fulfilled = False)
                        sell.put()

                        v = VerifyModel.all().filter("email", email).get()

                        sender = "duzhangtech@gmail.com"
                        receiver = email
                        subject = "Dining Dollars: LINKS AND STUFF!"
                        
                        body =  (
                                "Hello!\n\n"
                                + "This link highlights your offer on the buy page: \n"
                                + "ucsdexchange.appspot.com/buy?e=" + email
                                + "\n\nYou can edit or remove your offers here: \n" 
                                + "ucsdexchange.appspot.com/change?e=" + email 
                                + "&v=" + v.code + "\n\n"
                                + "You can comment/ask for features/say hi here:\n"
                                + "ucsdexchange.appspot.com/faq#feed\n\n"
                                )

                        mail.send_mail(sender, receiver, subject, body)

                        sells = SellModel.all().ancestor(sell_key()).filter("fulfilled =", False).order('price')
                        memcache.delete("SELLS")
                        memcache.set("SELLS", list(sells))

                        self.redirect('/buy?e=' + email)

                    elif not user: #NEW USER OR IN LIMBO?
                        waiting_for_verify = VerifyModel.all().filter("email", email).get()

                        if not waiting_for_verify: #NEW USER, PUT IN LIMBO
                            code = self.make_salt()
                            VerifyModel(parent = verify_key(), 
                                            email = email, 
                                            code = code).put()

                            sender = "duzhangtech@gmail.com"
                            receiver = email
                            subject = "Dining Dollars VERIFICATION"
                            body =  ("Hello! Your verification code is " + code)
                            mail.send_mail(sender, receiver, subject, body)

                            self.render("sell.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name, phone = phone, 
                                email = email, need_code = True)

                        else: #IN LIMBO, ASK FOR CODE
                            self.render("sell.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name, phone = phone, 
                                email = email, need_code = True, stat = "Invalid code. Resend?")

                elif phone and first_name and last_name and code: #ALL FIELDS FILLED. IS CODE OKAY?
                    check_code = VerifyModel.all().filter("code", code).get()

                    if check_code: #YAY. COMMIT USER & OFFER

                        user = UserModel(parent = user_key(),
                                    first_name = first_name, 
                                    last_name = last_name,
                                    phone = phone, 
                                    email = email)
                        user.put()

                        SellModel(parent = sell_key(),
                                    user = user, 
                                    amount = amount,
                                    price = price).put()

                        sender = "duzhangtech@gmail.com"
                        receiver = email
                        subject = "YOUR Dining Dollars: LINKS AND STUFF!"
                        
                        body =  (
                                "Hello!\n\n"
                                + "This link highlights your offer on the buy page: \n"
                                + "ucsdexchange.appspot.com/buy?e=" + email
                                + "\n\nYou can edit or remove your offer here: \n" 
                                + "ucsdexchange.appspot.com/change?e=" + email 
                                + "&v=" + code + "\n\n"
                                + "You can comment/ask for features/say hi here:\n"
                                + "ucsdexchange.appspot.com/faq#feed\n\n"
                                )

                        mail.send_mail(sender, receiver, subject, body)

                        sells = SellModel.all().ancestor(sell_key()).filter("fulfilled", False)
                        memcache.delete("SELLS")
                        memcache.set("SELLS", list(sells))
                        
                        self.redirect("/buy?e=" + email)

                    elif not check_code: #OH SNAP
                        stat = "Invalid code"
                        self.render("sell.html", 
                                amount = amount, price = price, 
                                first_name = first_name, last_name = last_name, phone = phone, 
                                email = email, need_code = True, stat = stat)

                else: #MISSING FIRST OR LAST NAME
                    self.render("sell.html", amount = amount, price = price, 
                            first_name = first_name, last_name = last_name, phone = phone, 
                            email = email, stat="Fill every box")

        #RESEND CODE!
        elif resend_button:
            code = VerifyModel.all().ancestor(verify_key()).filter("email", email).get().code

            sender = "duzhangtech@gmail.com"
            receiver = email
            subject = "Dining Dollars VERIFICATION"
            body =  ("Hello! Your verification code is " + code)
            mail.send_mail(sender, receiver, subject, body)

            self.render("sell.html", 
                amount = amount, price = price, 
                first_name = first_name, last_name = last_name, phone = phone, 
                email = email, need_code = True, stat = "code sent!")

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

                sender = "duzhangtech@gmail.com"
                receiver = email
                subject = "EDIT Dining Dollar OFFER"
                
                body =  (
                         "Hello!\n\n"
                        + "This link highlights your offer on the buy page: \n"
                        + "ucsdexchange.appspot.com/buy?e=" + email
                        + "\n\nYou can edit or remove your offer here: \n" 
                        + "ucsdexchange.appspot.com/change?e=" + email 
                        + "&v=" + code.code + "\n\n"
                        + "You can comment/ask for features/say hi here:\n"
                        + "ucsdexchange.appspot.com/faq#feed\n\n"
                        + "Yours, \n"
                        + "Bot"
                        )

                mail.send_mail(sender, receiver, subject, body)

                self.render("edit.html", stat = 'check your email!')

            else:
                stat = "You don't have any offers on the market"
                self.render("edit.html", stat = stat)

        else:
            stat = "(You used your UCSD email)"
            self.render("edit.html", stat = stat)

class EditFinish(Handler):
    def get(self):
        email = self.request.get('e')
        code = self.request.get('v')
        okaycode = VerifyModel.all().ancestor(verify_key()).filter('email', email).filter('code', code).get()

        if okaycode:
            user = UserModel.all().filter("email", email).get()
            offer = list(SellModel.all().ancestor(sell_key()).filter('user', user).filter('fulfilled', False))
            offer.sort(key = lambda x:((float)(x.amount), (float)(x.price)))

            #TEMPORARY FIX UP FOR PRE PY REGEX COMMITS
            for x in range(0, len(offer)):
                offer[x].amount = prettyamount(offer[x].amount)
                offer[x].price = prettyprice(offer[x].price)
                offer[x].put()

            self.render("editfinish.html", offer = offer)

        else:
            self.redirect('/changeoffer')
        

    def post(self):
        edit_button = self.request.get('edit_button')
        email = self.request.get("e")
        user = UserModel.all().filter("email", email).get()
        offer = list(SellModel.all().ancestor(sell_key()).filter('user', user).filter('fulfilled', False).order('amount'))
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

                    if prettyamount(offer[x].amount) != prettyamount(amount[x]):
                        change = True

                        if valid_amount(prettyamount(amount[x])):
                            offer[x].amount = prettyamount(amount[x])
                            offer[x].put()
                        else:
                            wrongamount = True

                    if prettyprice(offer[x].price) != prettyprice(price[x]):
                        change = True

                        if valid_price(prettyprice(price[x])):
                            offer[x].price = prettyprice(price[x])
                            offer[x].put()
                        else:
                            wrongprice = True

                if change:
                    logging.error("CHANGE")
                    
                    if wrongamount == True: #HAS TO REFETCH FOR NEW VALUES...AJAX FIXME?
                        offer = list(SellModel.all().ancestor(sell_key()).filter('user', user).filter('fulfilled', False).order('amount'))
                        offer.sort(key = lambda x:((float)(x.amount), (float)(x.price)))
                        self.render("editfinish.html", offer = offer, editstat = "Wow. Such typing. Make sure your offer is between 150 and 2000 mp")
                    elif wrongprice == True:
                        offer = list(SellModel.all().ancestor(sell_key()).filter('user', user).filter('fulfilled', False).order('amount'))
                        offer.sort(key = lambda x:((float)(x.amount), (float)(x.price)))
                        self.render("editfinish.html", offer = offer, editstat = "0.01 to 1.00 per mp")
                    else:
                        offer = list(SellModel.all().ancestor(sell_key()).filter('user', user).filter('fulfilled', False).order('amount'))
                        offer.sort(key = lambda x:((float)(x.amount), (float)(x.price)))

                        memcache.delete("SELLS")

                        self.render("editfinish.html", offer = offer, editstat = "Updated successfully!")

                elif not change:
                    logging.error("NO CHANGE")
                    self.render("editfinish.html", offer = offer, editstat = "Updated successfully!")

            else: #BLANK FIELD
                self.render("editfinish.html", offer = offer, editstat = "Fill each box")


class DeleteOffer(Handler):
    def post(self):
        email = self.request.get('email')
        amount = self.request.get('amount')
        price = self.request.get('price')

        user = UserModel.all().filter('email', email).get()
        offer = SellModel.all().filter('user', user).filter('fulfilled', False).filter('amount', amount).filter('price', price).get()
        offer.delete()
        logging.error("OKAY DELETED YAY")
        memcache.delete("SELLS")

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
    return amount and re.compile(r'^[0-9][0-9]\.?$|^[0-9][0-9]{2}\.?$|^[1][0-9]{3}\.?$|^2000\.?$').match(amount)

def valid_price(price):
    return price and re.compile(r'^[0]?\.[0-9]*$|^1$|^1\.|^1\.[0]*$').match(price)

def valid_email(email):
    return email and re.compile(r'^[\S]+(?i)(@gmail\.com)$|^[\S]+(?i)(\.edu)$').match(email)


application = webapp2.WSGIApplication([
                    ('/', Buy),
                    ('/buy', Buy),
                    ('/contact', BuyContact),
                    ('/sell', Sell),
                    ('/changeoffer', Edit),
                    ('/change', EditFinish),
                    ('/delete', DeleteOffer),
                    ('/faq', FAQ), 
                    ('/submitfeed', SubmitFeed),
                    ('/summary', Summary),
                    # ('/getkarma', PayMe),
                    LogSenderHandler.mapping()],
                    debug=True)