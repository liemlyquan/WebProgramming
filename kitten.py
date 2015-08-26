import os
import urllib
import datetime

from datetime import timedelta

import jinja2
import webapp2

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import mail
 
JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions=['jinja2.ext.autoescape'])

class Order(ndb.Model):
  date = ndb.DateTimeProperty(auto_now_add=True)
  customer = ndb.UserProperty()
  status = ndb.StringProperty()
  total = ndb.FloatProperty()


class Kitten(ndb.Model):
  type = ndb.StringProperty()
  size = ndb.StringProperty()
  topping = ndb.StringProperty()
  number = ndb.IntegerProperty()
  price = ndb.FloatProperty()
  order = ndb.KeyProperty(kind=Order)


class MainPage(webapp2.RequestHandler):

  def get(self):
    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'
    template_values = {
      'url': url,
      'url_linktext': url_linktext,
    }
    template = JINJA_ENVIRONMENT.get_template('/kitten/index.html')
    self.response.write(template.render(template_values))


class AdminPage(webapp2.RequestHandler):
  
  def get(self):
    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
      if users.is_current_user_admin():
        orders_query = Order.query(ndb.OR(Order.status == "Pending", Order.status == "Completed")).order(-Order.status).order(Order.date)
        orders = orders_query.fetch()

        template_values ={
          'url': url,
          'url_linktext': url_linktext,
          'orders': orders,
        }
        template = JINJA_ENVIRONMENT.get_template('/kitten/templates/admin.html')
        self.response.write(template.render(template_values))
      else:
        self.redirect('/kitten/')
    else:
      self.redirect(users.create_login_url(self.request.uri)) 

  def delete(self):
    # Delete orders that have been created, but not checked out for 3 minutes (in reality, time length can be changed, 3 minutes are just for testing)
    orders_query = Order.query(ndb.AND(Order.status == "Processing", Order.date < datetime.datetime.now() - timedelta(minutes=3)))
    orders = orders_query.fetch()
    for order in orders:
      order.key.delete()
      kittens_query = Kitten.query(order.key == Kitten.order)
      kittens = kittens_query.fetch()
      for kitten in kittens:
        kitten.key.delete()


class AdminOrderViewPage(webapp2.RequestHandler):

  def get(self, id):
    if users.get_current_user():
      if not users.is_current_user_admin():
        self.redirect('/kitten/order')
    else:
      self.redirect(users.create_login_url(self.request.uri)) 
    
    url = users.create_logout_url(self.request.uri)
    url_linktext = 'Logout'
    try:
      order = Order.get_by_id(int(id))
      if order is None:
        self.redirect("/kitten/html/adminordernotfound.html")
      elif (order.status == "Processing"):
        self.redirect("/kitten/html/adminorderprocessing.html")
      else:
        kittens_query = Kitten.query(Kitten.order == order.key)
        kittens = kittens_query.fetch()
        template_values = {
          'kittens': kittens,
          'order': order,
          'url': url,
          'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('/kitten/templates/adminorderview.html')
        self.response.write(template.render(template_values))

    except ValueError:
      self.redirect("/kitten/html/adminordernotfound.html")
      # this exception can prevent error such as /admin/656a (include character in id)

  def post(self, id):
      complete_button = self.request.get('complete')
      order = Order.get_by_id(int(id))
      if complete_button:
        order.status = "Completed"
      else:
        order.status = "Pending"
      order.put()
      self.redirect('/kitten/admin')


class OrderProcessPage(webapp2.RequestHandler):

  def get(self):
    if users.get_current_user():
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
    else:
    	url = users.create_login_url(self.request.uri)
    	url_linktext = 'Login'
    template_values = {
      'url': url,
      'url_linktext': url_linktext,
    }

    template = JINJA_ENVIRONMENT.get_template('/kitten/templates/orderprocess.html')
    self.response.write(template.render(template_values))

  def post(self):
    if users.get_current_user():
      order = Order()
      order.status= "Processing"
      order.customer = users.get_current_user()
      order.total = 0
      order.put()
      self.redirect('/kitten/order/%s' % order.key.id())
    else:
  	  self.redirect(users.create_login_url(self.request.uri))


class OrderPage(webapp2.RequestHandler):
  def get(self,id):
    try:
      order = Order.get_by_id(int(id))
      if order is None:
        self.redirect('/kitten/html/ordernotfound.html')
      elif not users.get_current_user():
        self.redirect('/kitten/')
      else:
        if (users.get_current_user() == order.customer):
          if (order.status == "Pending"):
            self.redirect('/kitten/html/ordercheckedout.html')
          elif (order.status == "Completed"):
            self.redirect('/kitten/html/ordercompleted.html')
          else:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            kittens_query = Kitten.query(order.key == Kitten.order).order(-Kitten.price)
            kittens = kittens_query.fetch()

            template_values = {
              'kittens': kittens,
              'order': order,
              'url': url,
              'url_linktext': url_linktext,
            }

            template = JINJA_ENVIRONMENT.get_template('/kitten/templates/order.html')
            self.response.write(template.render(template_values))

        else:
          self.redirect('/kitten/html/ordernotyours.html') 

    except ValueError:
      self.redirect('/kitten/html/ordernotfound.html')

  def post(self,id):
    order = Order.get_by_id(int(id))
    if order is None:
      self.redirect('/kitten/html/ordernotfound.html')
    else:
      add1_button = self.request.get('add1')
      add2_button = self.request.get('add2')
      add3_button = self.request.get('add3')
      add4_button = self.request.get('add4')
      add5_button = self.request.get('add5')
      add6_button = self.request.get('add6')
      create_button = self.request.get('create')
      if (add1_button or add2_button or add3_button or add4_button or add5_button or add6_button):
        kitten = Kitten()
        if (add1_button):
          kitten.topping = "SalamiAndCheese"
          toppingPrice = 45
        elif (add2_button):
          kitten.topping = "Pesto"
          toppingPrice = 47
        elif (add3_button):
          kitten.topping = "MozzarellaAndTomato"
          toppingPrice = 49
        elif (add4_button):
          kitten.topping = "OliveRedPepperAndMushroom"
          toppingPrice = 51
        elif (add5_button):
          kitten.topping = "ChocalateAndPrinkle"
          toppingPrice = 53
        else:    
          kitten.topping = "BlueSauceAndFairyDust"
          toppingPrice = 55

        kitten.size = self.request.get('size')
        if (kitten.size == 'Big'):
          sizeRate = 1.2
        elif (kitten.size == 'Medium'):
          sizeRate = 1.0
        else:
          sizeRate = 0.8

        kitten.type = self.request.get('type')
        if (kitten.type == 'Black' or kitten.type == 'White'):
          typePrice = 40
        else:
          typePrice = 60

        try:
          kitten.number = int(self.request.get('number'))
        except ValueError:
          kitten.number = 1
        # The try except block is to prevent the user who use browser that does not support input type number to enter characters that are digits, e.g: Firefox 9+

        if (kitten.number < 1):
          kitten.number = 1;
        # This condition is to prevent the user who use browser that does not support input type number to enter negative number or 0, e.g: Firefox 9+
        if (kitten.number > 100):
          kitten.number = 100;
        # This condition is to prevent the user to enter number larger than 100
        # In fact, this can also prevent ProtocolBufferEncodeError, which can be caused when you enter 1000.. ( a lot of 0) in the quantity

        kitten.price = ((typePrice  * sizeRate) + toppingPrice)  * kitten.number
        kitten.order = order.key

        kitten.put()
        order.total += kitten.price
        order.put()

        self.redirect('/kitten/order/%s' % order.key.id())

      elif (create_button):
        self.redirect('/kitten/order')
        order = Order()
        order.status= "Processing"
        order.customer = users.get_current_user()
        order.total = 0
        order.put()
        self.redirect('/kitten/order/%s' % order.key.id())
      else:
        kittens_query = Kitten.query(order.key == Kitten.order).order(-Kitten.price)
        kittens = kittens_query.fetch()
        email_body = "Dear %s, This email to confirm that the following order has been received and in pending\n" % (str(order.customer))
        email_body += "Order ID : " + str(order.key.id()) + "\n"
        for kitten in kittens:
          email_body += ("Topping: %-35sType: %-10sSize: %-15sQuantity: %-5s$%-10s\n" % (str(kitten.topping), str(kitten.type), str(kitten.size), str(kitten.number), str(kitten.price)))
        email_body += "Total is: $" + str(order.total) + "\n"
        email_body += "Please reply this email with the location you want to receive this order and we will prepare it in NO MORE THAN 3 DAYS \n"
        email_body += "Thank you for your purchase\n"
        email_body += "Liem"
        # plain text version, not very good formatting
        email_body_html = """
        <html>
        <head></head>
        <body>
        <p>Dear %s,this email is to confirm that the following order has been received</p>
        Order ID: %s
        <table border="1">
        <tr>
        <td>Type</td>
        <td>Size</td>
        <td>Topping</td>
        <td>Quantity</td>
        <td>Price</td>
        </tr>
        """ % (str(order.customer), str(order.key.id()))
        for kitten in kittens:
          email_body_html += """
        <tr>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>$%s</td>
        </tr>
        """ % (str(kitten.type), str(kitten.size), str(kitten.topping), str(kitten.number), str(kitten.price))
        email_body_html += """
        <tr>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        <td>$%s</td>
        </tr>
        </table>
        <p>Please reply this email with the location you want to receive this order and we will prepare it in NO MORE THAN 3 DAYS</p>
        <p>Thank you for your purchase</p>
        <p>Liem</p>
        </body>
        </html> 
        """ % (str(order.total))
        mail.send_mail(sender="liemlyquan@gmail.com", to=order.customer.email(), subject="Kitten order " + str(order.key.id()) + " confirmation", body=email_body, html=email_body_html)
        # Send confirmation email, html have better formatting 
        order.status = "Pending"
        order.date = datetime.datetime.now() + timedelta(hours = 7)
        # The above line added 7 hours to make it GMT+7/UTC+7 time
        order.put()
        self.redirect('/kitten/')

  def delete(self,id):
    order = Order.get_by_id(int(id))
    order.key.delete()
    kittens_query = Kitten.query(order.key == Kitten.order)
    kittens = kittens_query.fetch()
    for kitten in kittens:
      kitten.key.delete()


class PlacesPage(webapp2.RequestHandler):
  def get(self):
    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
      'url': url,
      'url_linktext': url_linktext,
    }
    template = JINJA_ENVIRONMENT.get_template('/kitten/templates/places.html')
    self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
  ('/kitten/', MainPage),
  ('/kitten/admin', AdminPage),
  ('/kitten/admin/(\w+)', AdminOrderViewPage),
  ('/kitten/order', OrderProcessPage),
  (r'/kitten/order/(\w+)', OrderPage),
  ('/kitten/places',PlacesPage),
], debug=True)
