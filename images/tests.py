import os
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from guardian.shortcuts import get_objects_for_user
from images.model_utils import PointGen
from images.models import Source, Image
from images.tasks import PreprocessImages, MakeFeatures, Classify, addLabelsToFeatures, trainRobot
from lib.test_utils import ClientTest, BaseTest, MediaTestComponent, ProcessingTestComponent


class SourceAboutTest(ClientTest):
    """
    Test the About Sources page.
    """
    def test_source_about(self):
        response = self.client.get(reverse('source_about'))
        self.assertStatusOK(response)


class SourceListTestWithSources(ClientTest):
    """
    Test the source list page when there's at least one source.
    """

    fixtures = ['test_users.yaml', 'test_sources.yaml']
    source_member_roles = [
        ('public1', 'user2', Source.PermTypes.ADMIN.code),
        ('public1', 'user4', Source.PermTypes.EDIT.code),
        ('private1', 'user3', Source.PermTypes.ADMIN.code),
        ('private1', 'user4', Source.PermTypes.VIEW.code),
    ]

    def source_list_as_user(self, username, password,
                            num_your_sources_predicted,
                            num_other_public_sources_predicted):
        """
        Test the source_list page as a certain user.
        If username is None, then the test is done while logged out.
        """
        # Sign in
        user = None
        if username is not None:
            user = User.objects.get(username=username)
            self.client.login(username=username, password=password)

        response = self.client.get(reverse('source_list'))

        if user is None or num_your_sources_predicted == 0:
            # Redirects to source_about page
            self.assertRedirects(response, reverse('source_about'))

            # 2 public sources
            response = self.client.get(reverse('source_list'), follow=True)
            public_sources = response.context['public_sources']
            self.assertEqual(len(public_sources), 2)
            for source in public_sources:
                self.assertEqual(source.visibility, Source.VisibilityTypes.PUBLIC)
        else:
            # Goes to source_list page
            self.assertStatusOK(response)
            your_sources_predicted = get_objects_for_user(user, Source.PermTypes.VIEW.fullCode)

            # Sources this user is a member of
            your_sources = response.context['your_sources']
            self.assertEqual(len(your_sources), num_your_sources_predicted)
            for source_dict in your_sources:
                source = Source.objects.get(pk=source_dict['id'])
                self.assertTrue(source in your_sources_predicted)
                self.assertEqual(source.get_member_role(user), source_dict['your_role'])

            # Public sources this user isn't a member of
            other_public_sources = response.context['other_public_sources']
            self.assertEqual(len(other_public_sources), num_other_public_sources_predicted)
            for source in other_public_sources:
                self.assertFalse(source in your_sources_predicted)
                self.assertEqual(source.visibility, Source.VisibilityTypes.PUBLIC)

        self.client.logout()

    def test_source_list(self):
        self.source_list_as_user(
            None, None,
            num_your_sources_predicted=0, num_other_public_sources_predicted=2,
        )
        self.source_list_as_user(
            'user2', 'secret',
            num_your_sources_predicted=1, num_other_public_sources_predicted=1,
        )
        self.source_list_as_user(
            'user3', 'secret',
            num_your_sources_predicted=1, num_other_public_sources_predicted=2,
        )
        self.source_list_as_user(
            'user4', 'secret',
            num_your_sources_predicted=2, num_other_public_sources_predicted=1,
        )
        self.source_list_as_user(
            'user5', 'secret',
            num_your_sources_predicted=0, num_other_public_sources_predicted=2,
        )
        self.source_list_as_user(
            'superuser_user', 'secret',
            num_your_sources_predicted=4, num_other_public_sources_predicted=0,
        )


class SourceListTestWithoutSources(ClientTest):
    """
    Test the source list page when there are no sources on the entire site.
    (A corner case to be sure, but testable material nonetheless.)
    """

    fixtures = ['test_users.yaml']

    def source_list_as_user(self, username, password):
        """
        Test the source_list page as a certain user.
        If username is None, then the test is done while logged out.
        """
        if username is not None:
            self.client.login(username=username, password=password)

        # Redirect to source_about
        response = self.client.get(reverse('source_list'))
        self.assertRedirects(response, reverse('source_about'))

        # 0 public sources
        response = self.client.get(reverse('source_list'), follow=True)
        self.assertEqual(len(response.context['public_sources']), 0)

        self.client.logout()

    def test_source_list(self):
        self.source_list_as_user(None, None)
        self.source_list_as_user('user2', 'secret')


class SourceNewTest(ClientTest):
    """
    Test the New Source page.
    """
    fixtures = ['test_users.yaml']

    def test_source_new_permissions(self):
        """
        Test that certain users are able to access the
        page, and that certain other users are denied.
        """
        self.login_required_page_test(
            protected_url=reverse('source_new'),
            username='user2',
            password='secret',
        )

    def test_source_new_success(self):
        """
        Successful creation of a new source.
        """
        self.client.login(username='user2', password='secret')
        response = self.client.get(reverse('source_new'))
        self.assertStatusOK(response)

        response = self.client.post(reverse('source_new'), dict(
            name='Test Source',
            visibility=Source.VisibilityTypes.PRIVATE,
            point_generation_type=PointGen.Types.SIMPLE,
            simple_number_of_points=200,
            image_height_in_cm=50,
            min_x=0,
            max_x=100,
            min_y=0,
            max_y=100,
        ))
        # TODO: Check that the source_main context reflects the source info.
        self.assertRedirects(response, reverse('source_main',
            kwargs={
                'source_id': Source.objects.latest('create_date').pk
            }
        ))

    # TODO: Test other successful and unsuccessful inputs for the
    # new source form.


class SourceEditTest(ClientTest):
    """
    Test the Edit Source page.
    """
    fixtures = ['test_users.yaml', 'test_sources.yaml']
    source_member_roles = [
        ('public1', 'user2', Source.PermTypes.ADMIN.code),
        ('public1', 'user4', Source.PermTypes.EDIT.code),
        ('private1', 'user3', Source.PermTypes.ADMIN.code),
        ('private1', 'user4', Source.PermTypes.VIEW.code),
    ]

    def setUp(self):
        super(SourceEditTest, self).setUp()
        self.source_id = Source.objects.get(name='public1').pk

    def test_source_edit_permissions(self):
        """
        Test that certain users are able to access the
        page, and that certain other users are denied.
        """
        self.permission_required_page_test(
            protected_url=reverse('source_edit', kwargs={'source_id': self.source_id}),
            denied_users=[dict(username='user3', password='secret')],
            accepted_users=[dict(username='user2', password='secret')],
        )

    def test_source_edit_success(self):
        """
        Successful edit of an existing source.
        """
        self.client.login(username='user2', password='secret')
        response = self.client.post(reverse('source_edit', kwargs={'source_id': self.source_id}), dict(
            name='Test Source',
            visibility=Source.VisibilityTypes.PRIVATE,
            point_generation_type=PointGen.Types.SIMPLE,
            simple_number_of_points=200,
            image_height_in_cm=50,
            min_x=0,
            max_x=100,
            min_y=0,
            max_y=100,
        ))
        # TODO: Check that the source_main context reflects the source edits.
        self.assertRedirects(response, reverse('source_main',
            kwargs={'source_id': self.source_id}
        ))

    # TODO: Test other successful and unsuccessful inputs for the
    # edit source form.


class ImageUploadTest(ClientTest):
    """
    Test the image upload page.
    """
    extra_components = [MediaTestComponent]
    fixtures = ['test_users.yaml', 'test_sources.yaml']
    source_member_roles = [
        ('public1', 'user2', Source.PermTypes.ADMIN.code),
    ]

    def setUp(self):
        super(ImageUploadTest, self).setUp()
        self.source_id = Source.objects.get(name='public1').pk

#    def assertSourceImageCount(self, expected_count):
#        self.assertEqual(Image.objects.filter(source=Source.objects.get(pk=self.source_id)).count(), expected_count)

    def upload_images_test(self, filenames, expect_success=True,
                           expected_new_images=None, **options):
        """
        Unlike ClientTest's upload_image method,
        this method includes assert statements, the ability to upload
        multiple images, and the ability to specify alternate options
        in the upload form.
        """
        if isinstance(filenames, basestring):
            filenames = [filenames]

        old_source_image_count = Image.objects.filter(source=Source.objects.get(pk=self.source_id)).count()

        self.client.login(username='user2', password='secret')

        files_to_upload = []
        for filename in filenames:
            sample_uploadable_path = os.path.join(settings.SAMPLE_UPLOADABLES_ROOT, 'data', filename)
            f = open(sample_uploadable_path, 'rb')
            files_to_upload.append(f)

        post_dict = dict(
            files=files_to_upload,
            skip_or_replace_duplicates='skip',
            specify_metadata='filenames',
        )
        post_dict.update(options)

        response = self.client.post(reverse('image_upload', kwargs={'source_id': self.source_id}), post_dict)
        for uploaded_file in files_to_upload:
            uploaded_file.close()

        self.assertStatusOK(response)

        new_source_image_count = Image.objects.filter(source=Source.objects.get(pk=self.source_id)).count()

        # TODO: If it's not None, use the parameter expected_new_images
        # when checking the source image count, to accommodate
        # the possibility of skipping or replacing images.
        #
        # TODO: Accommodate partial successes (some uploaded, some not)?

        if expect_success:
            self.assertEqual(len(response.context['uploadedImages']), len(filenames))
            self.assertEqual(new_source_image_count, len(filenames) + old_source_image_count)
        else:
            self.assertEqual(len(response.context['uploadedImages']), 0)
            self.assertEqual(new_source_image_count, old_source_image_count)

        # TODO: Test that the correct message(s) and error(s) were displayed?

        return response

#    def single_image_test(self, filenames, expect_success=True):
#        """
#        Test a single image upload.
#        Call this method only once per unit test, since it checks for
#        0 or 1 images existing in the source to determine success or failure.
#        """
#        response = self.upload_images_test(self.source_id, [filename], expect_success)
#        if expect_success:
#            self.assertImageCount(1)
#        else:
#            self.assertImageCount(0)


    def test_valid_png(self):
        """ .png created using the PIL. """
        self.upload_images_test('001_2012-05-01_color-grid-001.png')

    def test_unloadable_corrupt_png_1(self):
        """ .png with some bytes swapped around.
        PIL load() would get IOError: broken data stream when reading image file """
        self.upload_images_test('001_2012-05-01_color-grid-001_png-corrupt-unloadable-1.png',
                                expect_success=False)

    def test_unloadable_corrupt_png_2(self):
        """ .png with some bytes deleted from the end.
        PIL load() would get IndexError: string index out of range """
        self.upload_images_test('001_2012-05-01_color-grid-001_png-corrupt-unloadable-2.png',
                                expect_success=False)

    def test_unopenable_corrupt_png(self):
        """ .png with some bytes deleted near the beginning.
        PIL open() would get IOError: cannot identify image file """
        self.upload_images_test('001_2012-05-01_color-grid-001_png-corrupt-unopenable.png',
                                expect_success=False)

    def test_valid_jpg(self):
        """ .jpg created using the PIL. """
        self.upload_images_test('001_2012-05-01_color-grid-001_jpg-valid.jpg')

    def test_unloadable_corrupt_jpg(self):
        """ .jpg with bytes deleted from the end.
        PIL load() would get IOError: image file is truncated (4 bytes not processed) """
        self.upload_images_test('001_2012-05-01_color-grid-001_jpg-corrupt-unloadable.jpg',
                                expect_success=False)

    def test_unopenable_corrupt_jpg(self):
        """ .jpg with bytes deleted near the beginning.
        PIL open() would get IOError: cannot identify image file """
        self.upload_images_test('001_2012-05-01_color-grid-001_jpg-corrupt-unopenable.jpg',
                                expect_success=False)

    def test_non_image(self):
        """ .txt in UTF-8 created using Notepad++. """
        self.upload_images_test('sample_text_file.txt',
                                expect_success=False)

    # Multi-file upload tests.

    def test_multiple_valid(self):
        self.upload_images_test(['001_2012-05-01_color-grid-001.png',
                                 '002_2012-05-29_color-grid-001_large.png'])

    def test_multiple_invalid(self):
        self.upload_images_test(['001_2012-05-01_color-grid-001_jpg-corrupt-unloadable.jpg',
                                 '001_2012-05-01_color-grid-001_png-corrupt-unopenable.png'],
                                expect_success=False)

    def test_valid_and_non_image(self):
        self.upload_images_test(['001_2012-05-01_color-grid-001.png',
                                 'sample_text_file.txt'],
                                expect_success=False)

    def test_valid_and_unopenable_image(self):
        self.upload_images_test(['001_2012-05-01_color-grid-001.png',
                                 '001_2012-05-01_color-grid-001_png-corrupt-unopenable.png'],
                                expect_success=False)

    def test_valid_and_unloadable_image(self):
        self.upload_images_test(['001_2012-05-01_color-grid-001.png',
                                 '001_2012-05-01_color-grid-001_jpg-corrupt-unloadable.jpg'],
                                expect_success=False)

    # The order of the files in the list actually matters, because the
    # FileInput class validates only the last item of the list (and we
    # want to make sure we don't have this behavior).

    def test_non_image_and_valid(self):
        self.upload_images_test(['sample_text_file.txt',
                                 '001_2012-05-01_color-grid-001.png'],
                                expect_success=False)

    def test_unopenable_image_and_valid(self):
        self.upload_images_test(['001_2012-05-01_color-grid-001_jpg-corrupt-unopenable.jpg',
                                 '001_2012-05-01_color-grid-001.png'],
                                expect_success=False)

    def test_unloadable_image_and_valid(self):
        self.upload_images_test(['001_2012-05-01_color-grid-001_png-corrupt-unloadable-1.png',
                                 '001_2012-05-01_color-grid-001.png'],
                                expect_success=False)

    # TODO: Test uploading a nonexistent file (i.e. filling the file field with
    # a nonexistent filename).  However, this will probably have to be done
    # with a Selenium test.

    def test_no_images_specified(self):
        self.upload_images_test([],
                                expect_success=False)

    # TODO: Add more image upload tests:
    # invalid filename formats, different options, etc.


class ImageViewTest(ClientTest):
    """
    Test the image view page.
    This is an abstract class that doesn't actually have any tests.
    """
    extra_components = [MediaTestComponent]
    fixtures = ['test_users.yaml', 'test_sources.yaml']
    source_member_roles = [
        ('public1', 'user2', Source.PermTypes.ADMIN.code),
    ]

    def setUp(self):
        super(ImageViewTest, self).setUp()
        self.source_id = Source.objects.get(name='public1').pk

    def view_page_with_image(self, image_file):
        self.client.login(username='user2', password='secret')

        self.image_id = self.upload_image(self.source_id, image_file)

        response = self.client.get(reverse('image_detail', kwargs={'image_id': self.image_id}))
        self.assertStatusOK(response)

        # Try fetching the page a second time, to make sure thumbnail
        # generation doesn't go nuts.
        response = self.client.get(reverse('image_detail', kwargs={'image_id': self.image_id}))
        self.assertStatusOK(response)

        # TODO: Add more checks.

    def test_view_page_with_small_image(self):
        self.view_page_with_image('001_2012-05-01_color-grid-001.png')

    def test_view_page_with_large_image(self):
        self.view_page_with_image('002_2012-05-29_color-grid-001_large.png')


class ImageProcessingTaskTest(ClientTest):
    """
    Test the image processing tasks' logic with respect to
    database interfacing, preparation for subsequent tasks,
    and final results.

    Don't explicitly check for certain input/output files.
    Simply check that running task n prepares for task n+1
    in a sequence of tasks.
    """
    extra_components = [MediaTestComponent, ProcessingTestComponent]
    fixtures = ['test_users.yaml', 'test_sources.yaml']
    source_member_roles = [
        ('public1', 'user2', Source.PermTypes.ADMIN.code),
    ]

    def setUp(self):
        super(ImageProcessingTaskTest, self).setUp()
        self.source_id = Source.objects.get(name='public1').pk

        self.client.login(username='user2', password='secret')

        self.image_id = self.upload_image(self.source_id, '001_2012-05-01_color-grid-001.png')

    def test_preprocess_task(self):
        # The uploaded image should start out not preprocessed.
        # Otherwise, we need to change the setup code so that
        # the prepared image has preprocessed == False.
        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, False)

        # Run task, attempt 1.
        result = PreprocessImages.delay(self.image_id)
        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())

        # Should be preprocessed, and process_date should be set
        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, True)
        process_date = Image.objects.get(pk=self.image_id).process_date
        self.assertNotEqual(process_date, None)

        # Run task, attempt 2.
        result = PreprocessImages.delay(self.image_id)
        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())

        # Should have exited without re-doing the preprocess
        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, True)
        # process_date should have stayed the same
        self.assertEqual(Image.objects.get(pk=self.image_id).process_date, process_date)

    def test_make_features_task(self):
        # Preprocess the image first.
        result = PreprocessImages.delay(self.image_id)
        self.assertTrue(result.successful())
        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, True)

        # Sanity check: features have not been made yet
        self.assertEqual(Image.objects.get(pk=self.image_id).status.featuresExtracted, False)

        # Run task, attempt 1.
        result = MakeFeatures.delay(self.image_id)
        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())

        # Should have extracted features
        self.assertEqual(Image.objects.get(pk=self.image_id).status.featuresExtracted, True)

        # Run task, attempt 2.
        result = MakeFeatures.delay(self.image_id)
        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())

        # Should have exited without re-doing the feature making
        # TODO: Check file ctime/mtime to check that it wasn't redone?
        self.assertEqual(Image.objects.get(pk=self.image_id).status.featuresExtracted, True)

#    def test_add_feature_labels_task(self):
#        # Preprocess and feature-extract first.
#        result = PreprocessImages.delay(self.image_id)
#        self.assertTrue(result.successful())
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, True)
#        result = MakeFeatures.delay(self.image_id)
#        self.assertTrue(result.successful())
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.featuresExtracted, True)
#
#        # TODO: The image needs to be human annotated first.
#
#        # Sanity check: haven't added labels to features yet
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.featureFileHasHumanLabels, False)
#
#        # Run task, attempt 1.
#        result = addLabelsToFeatures.delay(self.image_id)
#        # Check that the task didn't encounter an exception
#        self.assertTrue(result.successful())
#
#        # Should have added labels to features
#        # TODO: Check file ctime/mtime to check that the file was changed
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.featureFileHasHumanLabels, True)
#
#        # Run task, attempt 2.
#        result = addLabelsToFeatures.delay(self.image_id)
#        # Check that the task didn't encounter an exception
#        self.assertTrue(result.successful())
#
#        # Should have exited without re-doing label adding
#        # TODO: Check file ctime/mtime to check that it wasn't redone?
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.featureFileHasHumanLabels, True)
#
#    def test_train_robot_task(self):
#        # TODO
#        #trainRobot
#        pass
#
#    def test_classify_task(self):
#        # Preprocess and feature-extract first.
#        result = PreprocessImages.delay(self.image_id)
#        self.assertTrue(result.successful())
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, True)
#        result = MakeFeatures.delay(self.image_id)
#        self.assertTrue(result.successful())
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.featuresExtracted, True)
#
#        # TODO: Do other preparation tasks.
#
#        # Sanity check: not classified yet
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.annotatedByRobot, False)
#
#        # Run task, attempt 1.
#        result = Classify.delay(self.image_id)
#        # Check that the task didn't encounter an exception
#        self.assertTrue(result.successful())
#
#        # Should have classified the image
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.annotatedByRobot, True)
#
#        # Run task, attempt 2.
#        result = Classify.delay(self.image_id)
#        # Check that the task didn't encounter an exception
#        self.assertTrue(result.successful())
#
#        # Should have exited without re-doing the classification
#        # TODO: Check file ctime/mtime to check that it wasn't redone?
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.annotatedByRobot, True)