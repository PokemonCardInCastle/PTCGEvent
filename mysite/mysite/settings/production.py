from .base import *

DEBUG = True

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '9s27@w)xfttr53(s4@)m%+8yk_urb_u$)n_2x^z=$lg#&4@s4raaan'

try:
    from .local import *
except ImportError:
    pass
