import json
import logging
import pickle
from datetime import timedelta

from celery.decorators import task, periodic_task
from django.conf import settings
from django.core.files.storage import get_storage_class
from django.db import IntegrityError
from django.utils.timezone import now
from six import StringIO

from accounts.utils import get_robot_user
from annotations.models import Annotation
from api_core.models import ApiJobUnit
from images.models import Source, Image, Point
from labels.models import Label
from . import task_helpers as th
from .backends import get_backend_class
from .models import Classifier, Score



from spacer.messages import \
    ExtractFeaturesMsg, \
    TrainClassifierMsg, \
    ClassifyFeaturesMsg, \
    ClassifyImageMsg, \
    JobMsg, \
    JobReturnMsg, \
    DataLocation

logger = logging.getLogger(__name__)


@task(name="Submit Features")
def submit_features(image_id, force=False):
    """
    Submits a job to SQS for extracting features for an image.
    """
    if settings.FORCE_NO_BACKEND_SUBMIT:
        logger.info("VB task was called, but not run because backend "
                    "submissions are off.")
        return

    try:
        img = Image.objects.get(pk=image_id)
    except Image.DoesNotExist:
        logger.info("Image {} does not exist.".format(image_id))
        return
    log_str = u"Image {} [Source: {} [{}]]".format(image_id, img.source,
                                                   img.source_id)

    if img.features.extracted and not force:
        logger.info(u"{} already has features".format(log_str))
        return

    # Setup the job payload.
    storage = get_storage_class()()

    # Assemble row column information
    rowcols = [(p.row, p.column) for p in Point.objects.filter(image=img)]

    # Assemble task.
    task = ExtractFeaturesMsg(
        job_token=str(image_id),
        feature_extractor_name=img.source.feature_extractor,
        rowcols=list(set(rowcols)),
        image_loc=DataLocation(storage_type=th.storage_class_to_str(storage),
                               key=storage.path(img.original_file.name)),
        feature_loc=DataLocation(storage_type=th.storage_class_to_str(storage),
                                 key=settings.FEATURE_VECTOR_FILE_PATTERN.
                                 format(full_image_path=storage.path(
                                     img.original_file.name)))
    )

    msg = JobMsg(task_name='extract_features', tasks=[task])

    # Submit.
    backend = get_backend_class()()
    backend.submit_job(msg)

    logger.info(u"Submitted feature extraction for {}".format(log_str))
    logger.debug(u"Submitted feature extraction for {}. Message: {}".
                 format(log_str, msg.serialize()))
    return msg


@periodic_task(run_every=timedelta(hours=24),
               name='Periodic Classifiers Submit',
               ignore_result=True)
def submit_all_classifiers():
    for source in Source.objects.filter():
        if source.need_new_robot():
            submit_classifier.delay(source.id)


@task(name="Submit Classifier")
def submit_classifier(source_id, nbr_images=1e5, force=False):

    if settings.FORCE_NO_BACKEND_SUBMIT:
        logger.info(
            "VB task was called, but not run because backend submissions are"
            " off.")
        return

    try:
        source = Source.objects.get(pk=source_id)
    except Source.DoesNotExist:
        logger.info("Can't find source [{}]".format(source_id))
        return
    
    if not source.need_new_robot() and not force:
        logger.info(u"Source {} [{}] don't need new classifier.".format(
            source.name, source.pk))
        return

    logger.info(u"Preparing new classifier for {} [{}].".format(
        source.name, source.pk))
    
    # Create new classifier model
    images = Image.objects.filter(source=source, confirmed=True,
                                  features__extracted=True)[:nbr_images]
    classifier = Classifier(source=source, nbr_train_images=len(images))
    classifier.save()

    # Write train-labels to file storage
    storage = get_storage_class()()
    trainlabels = th.make_dataset([image for image in images if
                                   image.trainset])
    trainlabels_path = storage.path(settings.ROBOT_MODEL_TRAINDATA_PATTERN.
                                    format(pk=classifier.pk))
    storage.save(trainlabels_path,
                 StringIO(json.dumps(trainlabels.serialize())))

    # Write val-labels to file storage
    vallabels = th.make_dataset([image for image in images if
                                 image.valset])
    vallabels_path = storage.path(settings.ROBOT_MODEL_VALDATA_PATTERN.
                                  format(pk=classifier.pk))
    storage.save(vallabels_path,
                 StringIO(json.dumps(vallabels.serialize())))

    # This will not include the one we just created, b/c it is not valid.
    prev_classifiers = Classifier.objects.filter(source=source, valid=True)

    # Primary keys needed for collect task.
    pc_pks = [pc.pk for pc in prev_classifiers]

    # Create payload
    # TODO: add the pc_pks to job_token
    task = TrainClassifierMsg(
        job_token=str(classifier.pk),
        trainer_name='minibatch',
        nbr_epochs=settings.NBR_TRAINING_EPOCHS,
        traindata_loc=DataLocation(
            storage_type=th.storage_class_to_str(storage),
            key=storage.path(trainlabels_path)),
        valdata_loc=DataLocation(
            storage_type=th.storage_class_to_str(storage),
            key=storage.path(vallabels_path)),
        features_loc=DataLocation(
            storage_type=th.storage_class_to_str(storage),
            key=''),
        previous_model_locs=[DataLocation(
            storage_type=th.storage_class_to_str(storage),
            key=storage.path(settings.ROBOT_MODEL_FILE_PATTERN.
                             format(pk=pc.pk))) for pc in prev_classifiers],
        model_loc=DataLocation(
            storage_type=th.storage_class_to_str(storage),
            key=storage.path(settings.ROBOT_MODEL_FILE_PATTERN.
                             format(pk=classifier.pk))),
        valresult_loc=DataLocation(
            storage_type=th.storage_class_to_str(storage),
            key=storage.path(settings.ROBOT_MODEL_VALRESULT_PATTERN.
                             format(pk=classifier.pk)),
        )
    )

    # Assemble the message body.
    msg = JobMsg(task_name='train_classifier', tasks=[task])

    # Submit.
    backend = get_backend_class()()
    backend.submit_job(msg)

    logger.info(u"Submitted classifier for source {} [{}] with {} images.".
                format(source.name, source.id, len(images)))
    logger.debug(u"Submitted classifier for source {} [{}] with {} images. "
                 u"Message: {}".format(source.name, source.id,
                                       len(images), msg))
    return msg
 

@task(name="Deploy")
def deploy(job_unit_id):

    try:
        job_unit = ApiJobUnit.objects.get(pk=job_unit_id)
    except ApiJobUnit.DoesNotExist:
        logger.info("Job unit of id {} does not exist.".format(job_unit_id))
        return

    job_unit.status = ApiJobUnit.IN_PROGRESS
    job_unit.save()

    rowcols = [[point['row'], point['column']] for point in
               job_unit.request_json['points']]

    payload = {
        'pk': job_unit_id,
        'bucketname': settings.AWS_STORAGE_BUCKET_NAME,
        'im_url': job_unit.request_json['url'],
        'modelname': 'vgg16_coralnet_ver1',
        'rowcols': rowcols,
        'model': settings.ROBOT_MODEL_FILE_PATTERN.format(
            pk=job_unit.request_json['classifier_id'],
            media=settings.AWS_LOCATION),
    }

    # Assemble message body.
    messagebody = {
        'task': 'deploy',
        'payload': payload
    }

    th._submit_job(messagebody)

    logger.info(u"Submitted image at url: {} for deploy with job unit {}.".
                format(job_unit.request_json['url'], job_unit.pk))
    logger.debug(u"Submitted image at url: {} for deploy with job unit {}. "
                 u"Message: {}".format(job_unit.request_json['url'],
                                       job_unit.pk, messagebody))

    return messagebody


@task(name="Classify Image")
def classify_image(image_id):

    try:
        img = Image.objects.get(pk=image_id)
    except:
        logger.info("Image {} does not exist.".format(image_id))
        return

    if not img.features.extracted:
        return    

    classifier = img.source.get_latest_robot()
    if not classifier:
        return

    # Load model
    storage = get_storage_class()()
    classifier_model_path = settings.ROBOT_MODEL_FILE_PATTERN.format(pk=classifier.pk)
    with storage.open(classifier_model_path) as classifier_model_file:
        classifier_model = pickle.load(classifier_model_file)

    feats_path = settings.FEATURE_VECTOR_FILE_PATTERN.format(full_image_path = img.original_file.name)
    with storage.open(feats_path) as feats_file:
        feats = json.load(feats_file)


    # Classify.
    scores = classifier_model.predict_proba(feats)

    # Pre-fetch label objects
    label_objs = []
    for class_ in classifier_model.classes_:
        label_objs.append(Label.objects.get(pk=class_))

    # Add annotations if image isn't already confirmed    
    if not img.confirmed:
        try:
            th._add_annotations(image_id, scores, label_objs, classifier)
        except IntegrityError:
            logger_message = u"Failed to classify Image {} [Source: {} [{}] " \
                             u"with classifier {}. There might have been a race" \
                             u" condition when trying to save annotations. " \
                             u"Will try again later."
            logger.info(logger_message.format(img.id, img.source,
                                              img.source_id, classifier.id))
            classify_image.apply_async(args=[image_id], eta=now() + timedelta(seconds=10))
            return
    
    # Always add scores
    th._add_scores(image_id, scores, label_objs)
    
    img.features.classified = True
    img.features.save()

    logger.info(u"Classified Image {} [Source: {} [{}]] with classifier {}".
                format(img.id, img.source, img.source_id, classifier.id))


@periodic_task(run_every=timedelta(seconds=60), name='Collect all jobs', ignore_result=True)
def collect_all_jobs():
    """
    Collects and handles job results until the job result queue is empty.
    """
    logger.info('Collecting all jobs in result queue.')
    backend = get_backend_class()()
    while True:
        messagebody = backend.collect_job()
        if messagebody:
            _handle_job_result(messagebody)
        else:
            break
    logger.info('Done collecting all jobs in result queue.')


def _handle_job_result(job_res: JobReturnMsg):

    # TODO: loop over each job at the time.

    # Handle message
    pk = int(job_res.original_job.tasks[0].job_token)
    if job_res.original_job.task_name == 'extract_features':
        if th._featurecollector(job_res):
            # If job was entered into DB, submit a classify job.
            classify_image.apply_async(args=[pk], eta=now() + timedelta(seconds=10))

    elif job_res.original_job.task_name == 'train_classifier':
        print("collecting train classifier")
        if th._classifiercollector(job_res):
            # If job was entered into DB, submit a classify job for all images
            # in source.
            classifier = Classifier.objects.get(pk=pk)
            for image in Image.objects.filter(source=classifier.source,
                                              features__extracted=True,
                                              confirmed=False):
                classify_image.apply_async(args=[image.id],
                                           eta=now() + timedelta(seconds=10))
    elif job_res.original_job.task_name == 'deploy':
        # TODO, make the collectors public
        th._deploycollector(messagebody)

    else:
        logger.error('Job task type {} not recognized'.format(task))

    # Conclude
    logger.info("job {}, pk: {} collected successfully".format(task, pk))
    logger.debug("Collected job with messagebody: {}".format(job_res))


@task(name="Reset Source")
def reset_after_labelset_change(source_id):
    """
    The removes ALL TRACES of the vision backend for this source, including:
    1) Delete all Score objects for all images
    2) Delete Classifier objects
    3) Sets all image.features.classified = False
    """
    Score.objects.filter(source_id = source_id).delete()
    Classifier.objects.filter(source_id = source_id).delete()
    Annotation.objects.filter(source_id = source_id, user = get_robot_user()).delete()
    for image in Image.objects.filter(source_id = source_id):
        image.features.classified = False
        image.features.save()

    # Finally, let's train a new classifier.
    submit_classifier.apply_async(args = [source_id], eta = now() + timedelta(seconds = 10))


@task(name="Reset Features")
def reset_features(image_id):
    """
    Resets features for image. Call this after any change that affects the image 
    point locations. E.g:
    Re-generate point locations.
    Change annotation area.
    Add new poits.
    """

    img = Image.objects.get(pk = image_id)
    features = img.features
    features.extracted = False
    features.classified = False
    features.save()

    # Re-submit feature extraction.
    submit_features.apply_async(args = [img.id], eta = now() + timedelta(seconds = 10))
