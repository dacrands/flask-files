import os
# basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
  SECRET_KEY = os.environ.get('SECRET_KEY') or 'whoops'
  UPLOAD_FOLDER = os.path.join(os.path.join(os.getcwd(),'app','uploads'))
