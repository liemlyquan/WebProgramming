import os
import urllib
import datetime
import logging

import jinja2
import webapp2

from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions=['jinja2.ext.autoescape'])

class CatT(ndb.Model):
  owner = ndb.UserProperty()
  name = ndb.StringProperty()
  date_of_birth = ndb.DateProperty()
  description = ndb.StringProperty(indexed=False)

class Owner(ndb.Model):
  name = ndb.StringProperty()


class Cat(ndb.Model):
  owner = ndb.KeyProperty(kind=Owner)
  name = ndb.StringProperty()
  description = ndb.StringProperty(indexed=False)
  date_of_birth = ndb.DateProperty()
  image = ndb.BlobProperty()

class ImageModel(ndb.Model):
  image = ndb.BlobProperty()


class MainPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
          
    if user:
      template_values = {
        'nickname': user.nickname(),
      }

      template = JINJA_ENVIRONMENT.get_template('index.html');
      self.response.write(template.render(template_values))
    else:
      self.redirect(users.create_login_url(self.request.uri))


class Tutorial6(webapp2.RequestHandler):
  def get(self):
    numbers = []
    for i in range(10):
      numbers.append(i)

    template_values = {
      'numbers': numbers
    }
    template = JINJA_ENVIRONMENT.get_template('/templates/tutorial6.html')
    self.response.write(template.render(template_values))


class Tutorial7(webapp2.RequestHandler):
  def get(self):
    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'
    # construct a query object, but don't execute it yet
    # -Cat.date_of_birth means that the order is descending (most recent first)
    cats_query = CatT.query().order(-CatT.date_of_birth)

    # actually fetch the cats (restrict to last 10)
    cats = cats_query.fetch(10)
    template_values = {
      'cats': cats,
      'url': url,
      'url_linktext': url_linktext,
    }
    template = JINJA_ENVIRONMENT.get_template('/templates/tutorial7.html')
    self.response.write(template.render(template_values))
  

  def post(self):
    user = users.get_current_user()

    if user:
      # ok so user is logged in
      cat = CatT()
      cat.owner = user
      cat.name = self.request.get('name')
      cat.description = self.request.get('description')
      day = self.request.get('day')
      month = self.request.get('month')
      year = self.request.get('year')
      cat.date_of_birth = datetime.date(year=int(year), month=int(month), day=int(day))

      # store the data
      cat.put()
      self.redirect('/tutorial7')
    else:
      # cannot add a cat unless we are logged in
      self.redirect(users.create_login_url(self.request.uri))


class Tutorial8(webapp2.RequestHandler):
  def get(self):
    cats_query = Cat.query().order(-Cat.date_of_birth)
    cats = cats_query.fetch(10)
    logging.info("Num cat: %s" % str(len(cats)))

    template_values = {
      'cats': cats,
    }

    template = JINJA_ENVIRONMENT.get_template('/templates/tutorial8.html')
    self.response.write(template.render(template_values))

  def post(self):
    owner_name = self.request.get("owner")
    owner = Owner.query(Owner.name == owner_name).get()

    if not owner:
      owner = Owner()
      logging.info("owner name add: %s" % (owner.name))
      owner.name = owner_name
      logging.info("(after )owner name add: %s" % (owner.name))
      owner.put()
      logging.info("Added owner: %s" % (owner.key))

    cat = Cat()
    cat.owner = owner.key
    cat.name = self.request.get('name')
    cat.description = self.request.get('description')
    day = self.request.get('day')
    month = self.request.get('month')
    year = self.request.get('year')
    cat.date_of_birth = datetime.date(year=int(year), month=int(month), day=int(day))

    cat.put()
    logging.info("Added cat: %s" % (cat.key))
    self.redirect('/tutorial8')


class OwnersPage(webapp2.RequestHandler):

    def get(self):
      cat_owners = Owner.query()
      template_values = {
        'cat_owners': cat_owners,
      }
      template = JINJA_ENVIRONMENT.get_template('/templates/owners.html')
      self.response.write(template.render(template_values))


class CatPage(webapp2.RequestHandler):

  def get(self, name):
    logging.info("Name is: %s" % name)

    cat = Cat.query(Cat.name == name).get()
    if cat is None:
      logging.info("Cannot find cat with name %s, redirecting..." % (name))
      self.redirect('/tutorial8')

    template_values = {
      'cat': cat
    }

    template = JINJA_ENVIRONMENT.get_template('/templates/cat.html')
    self.response.write(template.render(template_values))

  def post(self, name):
    if name is None:
      logging.info("No name is supplied, redirecting ....")
      self.redirect('/tutorial8')

    cat = Cat.query(Cat.name == name).get()
    if cat is None:
      logging.info("Cannot find cat with name %s, redirecting...", name)
      self.redirect('/tutorial8')

    owner_name = self.request.get("owner")
    owner = Owner.query(Owner.name == owner_name).get()

    if not owner:
      owner = Owner()
      owner.name = owner_name
      owner.put()
      logging.info("Added owner: %s", owner.key)

    cat.owner = owner.key
    cat.name = self.request.get('name')
    cat.description = self.request.get('description')
    day = self.request.get('day')
    month = self.request.get('month')
    year = self.request.get('year')
    cat.date_of_birth = datetime.date(year=int(year), month=int(month), day=int(day))
    cat.put()
    logging.info("Test")
    self.redirect('/tutorial8')

  def delete(self, cat_name):
    logging.info("in delete")

    if cat_name is None:
      self.request.out.write("NOT OK")

    logging.info("Name is: %s" % (cat_name))
    cat = Cat.query(Cat.name == cat_name).get()
    if cat is None:
      self.response.out.write("NOT OK")

    cat.key.delete()
    self.response.out.write("OK")


class MyCatsPage(webapp2.RequestHandler):

  def get(self):
    owner_name = self.request.get("name")

    if owner_name:
      owner = Owner.query(Owner.name == owner_name).get()
      if owner:
        logging.info("owner: %s" % owner.name)
        cats_query = Cat.query(Cat.owner == owner.key)
      else:
        logging.info("No owner found with name: %s" % owner_name)
        cats_query = Cat.query()
    else:
      cats_query = Cat.query()
    
    cats = cats_query.fetch(10)
    template_values = {
      'cats': cats,
    }
    template = JINJA_ENVIRONMENT.get_template('/templates/my_cats.html')
    self.response.write(template.render(template_values))


class Tutorial9(webapp2.RequestHandler):

  def get(self):
    cats_query = Cat.query().order(-Cat.date_of_birth)

    cats = cats_query.fetch(10)
    logging.info("Num cats: %s", str(len(cats)))

    template_values = {
      'cats': cats
    }

    template = JINJA_ENVIRONMENT.get_template('/templates/tutorial9.html')
    self.response.write(template.render(template_values))

  def post(self):
    owner_name = self.request.get("owner")
    owner = Owner.query(Owner.name == owner_name).get()

    if not owner:
      owner = Owner()
      owner.name = owner_name
      owner.put()
      logging.info("Added owner: %s", owner.key)

    cat = Cat()

    if self.request.get("img"):
      pic = images.resize(self.request.get('img'), 32, 32)
      cat.image = db.Blob(pic)
      logging.info("Pic post")

    cat.owner = owner.key
    logging.info("Test 1")
    cat.name = self.request.get('name')
    cat.description = self.request.get('description')
    day = self.request.get('day')
    month = self.request.get('month')
    year = self.request.get('year')
    cat.date_of_birth = datetime.date(year=int(year), month =int(month), day = int(day))
    logging.info("Test 2")
    if not (cat.image):
      logging.info("No image")
    elif not cat.name:
      logging.info("No name")
    elif not cat.description:
      logging.info("No description")
    elif not cat.date_of_birth:
      logging.info("No date")

    cat.put()
    logging.info("Added cat %s", cat.key)

    self.redirect("/tutorial9")


class ImageHandler(webapp2.RequestHandler):

  def get(self):
    cat_key = ndb.Key("Cat", int(self.request.get('img_id')))
    cat = Cat.query(Cat.key == cat_key).get()
    if cat.image:
      self.response.headers['Content-Type'] = 'image/png'
      self.response.out.write(cat.image)
    else:
      self.response.out.write('No image')
      

class Tutorial10(webapp2.RequestHandler):

  def get(self):
    template = JINJA_ENVIRONMENT.get_template('/templates/tutorial10.html')
    images = ImageModel.query().fetch(10)

    template_values = {
      'images': images,
    }
    self.response.write(template.render(template_values))

  def post(self):
    im = ImageModel()
    if self.request.get("file"):
      pic = images.resize(self.request.get('file'), 32, 32)
      im.image = db.Blob(pic)
    im.put()


class ImageHandler2(webapp2.RequestHandler):

  def get(self):
    im_key = ndb.Key("ImageModel", int(self.request.get('img_id')))
    im = ImageModel.query(ImageModel.key == im_key).get()
    if im.image:
      self.response.headers['Content-Type'] = 'image/png'
      self.response.out.write(im.image)
    else:
      self.response.out.write('No image')

application = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/tutorial6', Tutorial6),
  ('/tutorial7', Tutorial7),
  ('/tutorial8', Tutorial8),
  ('/tutorial8/cats',MyCatsPage),
  ('/tutorial8/owners', OwnersPage),
  (r'/tutorial8/cat/(\w+)', CatPage),
  ('/tutorial9', Tutorial9),
  ('/tutorial9/img', ImageHandler),
  ('/tutorial10', Tutorial10),
  ('/tutorial10/img', ImageHandler2),
], debug=True)
