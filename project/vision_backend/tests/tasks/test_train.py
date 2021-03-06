import math
import mock

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.test import override_settings
from django.test.utils import patch_logger
import spacer.config as spacer_config
from spacer.data_classes import ValResults

from vision_backend.models import Classifier
from vision_backend.tasks import collect_all_jobs
from .utils import BaseTaskTest


class TrainClassifierTest(BaseTaskTest):

    def test_success(self):
        # Provide enough data for training, and extract features.
        self.upload_images_for_training(
            train_image_count=spacer_config.MIN_TRAINIMAGES, val_image_count=1)
        collect_all_jobs()

        # Create a classifier
        job_msg = self.submit_classifier_with_filename_based_valset(
            self.source.id)

        # This source should now have a classifier (though not trained yet)
        self.assertTrue(
            Classifier.objects.filter(source=self.source).count() > 0)

        # Process training result
        collect_all_jobs()

        # Now we should have a trained classifier whose accuracy is the best so
        # far (due to having no previous classifiers), and thus it should have
        # been marked as valid
        latest_classifier = self.source.get_latest_robot()
        self.assertTrue(latest_classifier.valid)

        # Also check that the actual classifier is created in storage.
        storage = get_storage_class()()
        self.assertTrue(storage.exists(
            settings.ROBOT_MODEL_FILE_PATTERN.format(pk=latest_classifier.pk)))

        # And that the val results are stored.
        self.assertTrue(storage.exists(
            settings.ROBOT_MODEL_VALRESULT_PATTERN.format(
                pk=latest_classifier.pk)))

        # Check that the point-counts in val_res is equal to val_data.
        val_res = ValResults.load(job_msg.tasks[0].valresult_loc)
        val_labels = job_msg.tasks[0].val_labels
        self.assertEqual(len(val_res.gt),
                         len(val_labels) * val_labels.samples_per_image)

    def test_train_second_classifier(self):
        """
        Train a second valid classifier in a source which already has a valid
        classifier.
        """
        def mock_train_msg_1(
                self_, acc, pc_accs, ref_accs, runtime):
            self_.acc = 0.5
            self_.pc_accs = pc_accs
            self_.ref_accs = ref_accs
            self_.runtime = runtime

        def mock_train_msg_2(
                self_, acc, pc_accs, ref_accs, runtime):
            self_.acc = (0.5*settings.NEW_CLASSIFIER_IMPROVEMENT_TH) + 0.001
            self_.pc_accs = [0.5]
            self_.ref_accs = ref_accs
            self_.runtime = runtime

        # Train one classifier.
        self.upload_images_for_training(
            train_image_count=spacer_config.MIN_TRAINIMAGES, val_image_count=1)
        collect_all_jobs()
        self.submit_classifier_with_filename_based_valset(self.source.id)
        # Collect classifier. Use mock to specify a particular accuracy.
        with mock.patch(
                'spacer.messages.TrainClassifierReturnMsg.__init__',
                mock_train_msg_1):
            collect_all_jobs()

        clf_1 = self.source.get_latest_robot()

        # Upload enough additional images for the next training to happen.
        old_image_count = spacer_config.MIN_TRAINIMAGES + 1
        new_image_count = math.ceil(
            old_image_count*settings.NEW_CLASSIFIER_TRAIN_TH)
        added_image_count = new_image_count - old_image_count
        self.upload_images_for_training(
            train_image_count=added_image_count, val_image_count=0)
        # Collect extracted features.
        collect_all_jobs()

        self.submit_classifier_with_filename_based_valset(self.source.id)
        # Collect classifier. Use mock to ensure a high enough accuracy
        # improvement to consider the classifier valid.
        with mock.patch(
                'spacer.messages.TrainClassifierReturnMsg.__init__',
                mock_train_msg_2):
            collect_all_jobs()

        clf_2 = self.source.get_latest_robot()

        self.assertNotEqual(clf_1.pk, clf_2.pk, "Should have a new classifier")
        self.assertGreater(
            clf_2.nbr_train_images, clf_1.nbr_train_images,
            "Second classifier's training-image count should be greater")
        self.assertGreater(
            clf_2.accuracy, clf_1.accuracy,
            "Second classifier's accuracy should be greater")

    def test_with_dupe_points(self):
        """
        Images in the training set and validation set have two points with the
        same row/column.
        """

        # Upload annotated images with dupe points
        val_image_with_dupe_point = self.upload_image_with_dupe_points(
            'val.png', with_labels=True)
        training_image_with_dupe_point = self.upload_image_with_dupe_points(
            'train.png', with_labels=True)
        # Other annotated images to get enough for training
        self.upload_images_for_training(
            train_image_count=spacer_config.MIN_TRAINIMAGES-1,
            val_image_count=0)

        # Process feature extraction results
        collect_all_jobs()

        # Train classifier
        job_msg = self.submit_classifier_with_filename_based_valset(
            self.source.id)
        collect_all_jobs()

        # Check training data

        storage = get_storage_class()()
        train_data = job_msg.tasks[0].train_labels.data
        feature_filepath = settings.FEATURE_VECTOR_FILE_PATTERN.format(
            full_image_path=training_image_with_dupe_point.original_file.name)
        feature_location = storage.spacer_data_loc(feature_filepath)
        image_train_data = train_data[feature_location.key]
        self.assertEqual(
            len(self.rowcols_with_dupes_included), len(image_train_data),
            "Training data count should include dupe points")
        rowcols = [
            (row, col) for row, col, label in image_train_data]
        self.assertListEqual(
            self.rowcols_with_dupes_included, sorted(rowcols),
            "Training data rowcols should include dupe points")

        # Check validation data

        val_data = job_msg.tasks[0].val_labels.data
        feature_filepath = settings.FEATURE_VECTOR_FILE_PATTERN.format(
            full_image_path=val_image_with_dupe_point.original_file.name)
        feature_location = storage.spacer_data_loc(feature_filepath)
        image_val_data = val_data[feature_location.key]
        self.assertEqual(
            len(self.rowcols_with_dupes_included), len(image_val_data),
            "Validation data count should include dupe points")
        rowcols = [
            (row, col) for row, col, label in image_val_data]
        self.assertListEqual(
            self.rowcols_with_dupes_included, sorted(rowcols),
            "Validation data rowcols should include dupe points")

        # Check valresults

        val_res = ValResults.load(job_msg.tasks[0].valresult_loc)
        self.assertEqual(
            len(self.rowcols_with_dupes_included), len(val_res.gt),
            "Valresults count should include dupe points")

        # Check that there's a valid classifier.

        latest_classifier = self.source.get_latest_robot()
        self.assertTrue(latest_classifier.valid)


class AbortCasesTest(BaseTaskTest):
    """
    Test cases where the task or collection would abort before reaching the
    end.
    """

    def test_nonexistent_source(self):
        """Try to train a classifier for a nonexistent source ID."""
        # To get a nonexistent source ID, create a source, get its ID, then
        # delete the source.
        source = self.create_source(self.user)
        source_id = source.pk
        source.delete()

        with patch_logger('vision_backend.tasks', 'info') as log_messages:
            self.submit_classifier_with_filename_based_valset(source_id)

            log_message = "Can't find source [{}]".format(source_id)
            self.assertIn(
                log_message, log_messages,
                "Should log the appropriate message")

    def test_classification_disabled(self):
        """Try to train for a source which has classification disabled."""
        # Ensure the source is otherwise ready for training.
        self.upload_images_for_training(
            train_image_count=spacer_config.MIN_TRAINIMAGES, val_image_count=1)
        collect_all_jobs()

        # Disable classification.
        self.source.enable_robot_classifier = False
        self.source.save()

        with patch_logger('vision_backend.tasks', 'info') as log_messages:
            self.submit_classifier_with_filename_based_valset(self.source.pk)

            log_message = "Source {} [{}] don't need new classifier.".format(
                self.source.name, self.source.pk)
            self.assertIn(
                log_message, log_messages,
                "Should log the appropriate message")

    def test_below_minimum_images(self):
        """
        Try to train while below the minimum number of images needed for first
        training.
        """
        # Prepare some training images.
        self.upload_images_for_training(
            train_image_count=spacer_config.MIN_TRAINIMAGES, val_image_count=1)
        collect_all_jobs()

        # But set CoralNet's requirement 1 higher than that image count.
        min_images = spacer_config.MIN_TRAINIMAGES + 2

        with patch_logger('vision_backend.tasks', 'info') as log_messages:
            with override_settings(MIN_NBR_ANNOTATED_IMAGES=min_images):
                self.submit_classifier_with_filename_based_valset(
                    self.source.pk)

            log_message = "Source {} [{}] don't need new classifier.".format(
                self.source.name, self.source.pk)
            self.assertIn(
                log_message, log_messages,
                "Should log the appropriate message")

    def test_not_enough_train_data_since_last_classifier(self):
        """
        Try to train when there haven't been enough training images added
        since the last training.
        """
        # Train one classifier.
        self.upload_images_for_training(
            train_image_count=spacer_config.MIN_TRAINIMAGES, val_image_count=1)
        collect_all_jobs()
        self.submit_classifier_with_filename_based_valset(self.source.pk)
        collect_all_jobs()

        # Attempt to train another classifier without adding more images.
        with patch_logger('vision_backend.tasks', 'info') as log_messages:
            self.submit_classifier_with_filename_based_valset(self.source.pk)

            log_message = "Source {} [{}] don't need new classifier.".format(
                self.source.name, self.source.pk)
            self.assertIn(
                log_message, log_messages,
                "Should log the appropriate message")

    def test_classifier_deleted_before_collection(self):
        """
        Run the train task, then delete the classifier from the DB, then
        try to collect the train result.
        """
        self.upload_images_for_training(
            train_image_count=spacer_config.MIN_TRAINIMAGES, val_image_count=1)
        collect_all_jobs()
        msg = self.submit_classifier_with_filename_based_valset(self.source.pk)

        clf = self.source.get_latest_robot(only_valid=False)
        clf.delete()

        with patch_logger(
                'vision_backend.task_helpers', 'info') as log_messages:
            collect_all_jobs()

            log_message = "Classifier {} was deleted. Aborting".format(
                msg.tasks[0].job_token)
            self.assertIn(
                log_message, log_messages,
                "Should log the appropriate message")

    def test_classifier_not_valid(self):
        """
        Run the train task, then collect the classifier and find that it's
        not enough of an improvement over the previous.
        """
        def mock_train_msg(
                self_, acc, pc_accs, ref_accs, runtime):
            self_.acc = 0.6
            self_.pc_accs = [0.5]
            self_.ref_accs = ref_accs
            self_.runtime = runtime

        # Train one classifier.
        self.upload_images_for_training(
            train_image_count=spacer_config.MIN_TRAINIMAGES, val_image_count=1)
        collect_all_jobs()
        self.submit_classifier_with_filename_based_valset(self.source.pk)
        collect_all_jobs()

        # Upload enough additional images for the next training to happen.
        old_image_count = spacer_config.MIN_TRAINIMAGES + 1
        new_image_count = math.ceil(
            old_image_count*settings.NEW_CLASSIFIER_TRAIN_TH)
        added_image_count = new_image_count - old_image_count
        self.upload_images_for_training(
            train_image_count=added_image_count, val_image_count=0)
        collect_all_jobs()
        self.submit_classifier_with_filename_based_valset(self.source.pk)

        with patch_logger(
                'vision_backend.task_helpers', 'info') as log_messages:
            with override_settings(NEW_CLASSIFIER_IMPROVEMENT_TH=1.4):
                # Collect classifier. Use mock to specify current and previous
                # classifiers' accuracy.
                with mock.patch(
                        'spacer.messages.TrainClassifierReturnMsg.__init__',
                        mock_train_msg):
                    collect_all_jobs()

            clf = self.source.get_latest_robot(only_valid=False)
            log_message = (
                "Classifier {} [Source: {} [{}]] "
                "worse than previous. Not validated. Max previous: {:.2f}, "
                "threshold: {:.2f}, this: {:.2f}".format(
                    clf.pk, self.source, self.source.pk,
                    0.5, 0.5*1.4, 0.6))
            self.assertIn(
                log_message, log_messages,
                "Should log the appropriate message")
