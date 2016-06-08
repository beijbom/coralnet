import os
import posixpath
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto import S3BotoStorage

class MediaStorageS3(S3BotoStorage):
    """
    Location defaults to the S3 bucket's AWS_LOCATION directory.
    """
    def __init__(self, **kwargs):
        self.timezone = 'UTC'
        super(MediaStorageS3, self).__init__(**kwargs)

    def path_join(self, *args):
        # For S3 paths, we join with forward slashes.
        return posixpath.join(*args)

class MediaStorageLocal(FileSystemStorage):
    """
    Location defaults to MEDIA_ROOT. That's what Django's
    default file storage class does.
    """
    def __init__(self, **kwargs):
        self.timezone = settings.TIME_ZONE
        super(MediaStorageLocal, self).__init__(**kwargs)

    def path_join(self, *args):
        # For local storage, we join paths depending on the OS rules.
        return os.path.join(*args)