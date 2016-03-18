# Created by olala7846@gmail.com
# appengine_config gets loaded when starting a new application instance

from google.appengine.ext import vendor

# add libraries to python path
vendor.add('lib')
vendor.add('venv/lib/python2.7/site-packages/')
