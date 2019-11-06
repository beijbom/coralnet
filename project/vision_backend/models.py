from __future__ import unicode_literals

from datetime import datetime

from django.db import models
from django.conf import settings

from labels.models import Label, LocalLabel
from lib.utils import direct_s3_read
import pickle

class Classifier(models.Model):
    """
    Computer vision classifier.
    """

    # pointer to the source
    source = models.ForeignKey('images.Source', on_delete=models.CASCADE)

    # An instance is valid if 1) it has been trained and 2) it performed better than previous models
    valid = models.BooleanField(default=False)

    # Training runtime in secondsd
    runtime_train = models.BigIntegerField(default = 0)

    # Accuracy as evaluated on the validation set
    accuracy = models.FloatField(null = True)

    # Epoch reference set accuracy (for bookkeeping mostly)
    epoch_ref_accuracy = models.CharField(max_length = 512, null = True)

    # Number of image (val + train) that were used to train this classifier
    nbr_train_images = models.IntegerField(null = True)

    # Create date
    create_date = models.DateTimeField('Date created', auto_now_add=True, editable=False)
    
    @property
    def valres(self):
        valres = direct_s3_read(settings.ROBOT_MODEL_VALRESULT_PATTERN.format(pk = self.pk, media = settings.AWS_LOCATION), 'json')
        valres['gt'] = [int(g) for g in valres['gt']]
        valres['est'] = [int(e) for e in valres['est']]
        return valres


    def get_process_date_short_str(self):
        """
        Return the image's (pre)process date in YYYY-MM-DD format.

        Advantage over YYYY-(M)M-(D)D: alphabetized = sorted by date
        Advantage over YYYY(M)M(D)D: date is unambiguous
        """
        return "{0}-{1:02}-{2:02}".format(self.create_date.year, self.create_date.month, self.create_date.day)


    def __unicode__(self):
        """
        To-string method.
        """
        return "Version %s for source %s" % (self.id, self.source.name)


class Features(models.Model):
    """
    This class manages the bookkeeping of features for each image.
    """
    image = models.OneToOneField('images.Image', on_delete=models.CASCADE)

    # Indicates whether the features are extracted. Set when jobs are colected
    extracted = models.BooleanField(default = False)

    # Indicates whether the features are classified (by any version of the robot).
    classified = models.BooleanField(default = False)

    # total runtime for job
    runtime_total = models.IntegerField(null = True)

    # runtime for the call to caffe
    runtime_core = models.IntegerField(null = True)

    # whether the model needed to be downloaded from S3
    model_was_cashed = models.NullBooleanField(null = True)

    # When were the features extracted
    extracted_date = models.DateTimeField(null = True)



class Score(models.Model):
    """
    Tracks scores for each point in each image. For each point,
    scores for only the top NBR_SCORES_PER_ANNOTATION labels are saved.
    """
    label = models.ForeignKey(Label, on_delete = models.CASCADE)
    point = models.ForeignKey('images.Point', on_delete = models.CASCADE)
    source = models.ForeignKey('images.Source', on_delete = models.CASCADE)
    image = models.ForeignKey('images.Image', on_delete = models.CASCADE)

    # Integer between 0 and 99, representing the percent probability
    # that this point is this label according to the backend. Although
    # scores are only saved for the top NBR_SCORES_PER_ANNOTATION labels,
    # this is the probability among all labels in the labelset.
    score = models.IntegerField(default = 0)

    @property
    def label_code(self):
        local_label = LocalLabel.objects.get(
            global_label=self.label, labelset=self.source.labelset)
        return local_label.code

    def __unicode__(self):
        return "%s - %s - %s - %s" % (
            self.image, self.point.point_number, self.label_code, self.score)


    