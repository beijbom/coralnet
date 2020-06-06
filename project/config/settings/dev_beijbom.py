from .base_devserver import *

ALLOWED_HOSTS = ['127.0.0.1', 'testserver']
# Pick one.
from .storage_s3 import *
VISION_BACKEND_CHOICE = 'vision_backend.queues.SQSQueue'
# from .storage_local import *
# from .storage_s3_regtests import *
