# Settings for a test environment which is as close to production as possible.

from .production import *


# Instead of routing emails through a mail server,
# just write emails to the filesystem.
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = SITE_DIR.child('tmp').child('emails')

# [Custom setting]
# The site domain, for the Django sites framework. This is used in places
# such as links in password reset emails, and 'view on site' links in the
# admin site's blog post edit view.
SITE_DOMAIN = 'ec2-35-162-62-60.us-west-2.compute.amazonaws.com'

# Hosts/domain names that are valid for this site.
# "*" matches anything, ".example.com" matches example.com and all subdomains
ALLOWED_HOSTS = [SITE_DOMAIN]

# Let's Encrypt doesn't accept amazonaws domain names, so we can't use
# HTTPS on the staging server.
# For this reason, it's highly recommended to use different admin passwords
# from those used at the production site.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = None
