from __future__ import unicode_literals
import datetime
from django.test import override_settings
from django.urls import reverse

from images.model_utils import PointGen
from lib.tests.utils import BasePermissionTest, ClientTest


class PermissionTest(BasePermissionTest):
    """
    Test page permissions.
    """
    def test_browse_images(self):
        url = reverse('browse_images', args=[self.source.pk])
        template = 'visualization/browse_images.html'

        self.source_to_private()
        self.assertPermissionLevel(url, self.SOURCE_VIEW, template=template)
        self.source_to_public()
        self.assertPermissionLevel(url, self.SIGNED_OUT, template=template)

    # TODO: Implement and test permissions on the availability of the
    # action form's actions.


class SearchTest(ClientTest):

    @classmethod
    def setUpTestData(cls):
        super(SearchTest, cls).setUpTestData()

        cls.user = cls.create_user()
        cls.source = cls.create_source(
            cls.user,
            point_generation_type=PointGen.Types.SIMPLE,
            # Make it easy to have confirmed and partially annotated images
            simple_number_of_points=2,
        )
        labels = cls.create_labels(cls.user, ['A', 'B'], 'GroupA')
        cls.create_labelset(cls.user, cls.source, labels)

        cls.url = reverse('browse_images', args=[cls.source.pk])

        cls.imgs = [
            cls.upload_image(cls.user, cls.source) for _ in range(5)
        ]

    def submit_search(self, **kwargs):
        data = dict(
            image_form_type='search',
            aux1='', aux2='', aux3='', aux4='', aux5='',
            height_in_cm='', latitude='', longitude='', depth='',
            photographer='', framing='', balance='',
            date_filter_0='year', date_filter_1='',
            date_filter_2='', date_filter_3='',
            annotation_status='', image_name='',
        )
        data.update(**kwargs)
        response = self.client.post(self.url, data, follow=True)
        return response

    def test_page_landing(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.context['page_results'].paginator.count, 5)

    def test_default_search(self):
        self.client.force_login(self.user)
        response = self.submit_search()
        self.assertEqual(
            response.context['page_results'].paginator.count, 5)

    def test_filter_by_year(self):
        self.imgs[0].metadata.photo_date = datetime.date(2011, 12, 28)
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.photo_date = datetime.date(2012, 1, 13)
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.photo_date = datetime.date(2012, 8, 4)
        self.imgs[2].metadata.save()
        # 2 other images left with no date

        self.client.force_login(self.user)
        response = self.submit_search(date_filter_1=2012)
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_filter_by_year_none(self):
        self.imgs[0].metadata.photo_date = datetime.date(2011, 12, 28)
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.photo_date = datetime.date(2012, 1, 13)
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.photo_date = datetime.date(2013, 8, 4)
        self.imgs[2].metadata.save()
        # 2 other images left with no date

        self.client.force_login(self.user)
        response = self.submit_search(date_filter_1='(none)')
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_year_choices(self):
        self.imgs[0].metadata.photo_date = datetime.date(2011, 12, 28)
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.photo_date = datetime.date(2012, 1, 13)
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.photo_date = datetime.date(2013, 8, 4)
        self.imgs[2].metadata.save()

        self.client.force_login(self.user)
        response = self.client.get(self.url)

        search_form = response.context['image_search_form']
        year_field = search_form.fields['date_filter'].fields[1]
        year_choices = [value for value, label in year_field.choices]
        self.assertListEqual(
            year_choices,
            ['', 2011, 2012, 2013, '(none)']
        )

    def test_filter_by_date(self):
        self.imgs[0].metadata.photo_date = datetime.date(2012, 1, 12)
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.photo_date = datetime.date(2012, 1, 13)
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.photo_date = datetime.date(2012, 1, 13)
        self.imgs[2].metadata.save()
        # 2 other images left with no date

        self.client.force_login(self.user)
        response = self.submit_search(
            date_filter_0='date', date_filter_2=datetime.date(2012, 1, 13))
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_filter_by_date_range(self):
        self.imgs[0].metadata.photo_date = datetime.date(2012, 3, 9)
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.photo_date = datetime.date(2012, 3, 10)
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.photo_date = datetime.date(2012, 3, 15)
        self.imgs[2].metadata.save()
        self.imgs[3].metadata.photo_date = datetime.date(2012, 3, 20)
        self.imgs[3].metadata.save()
        self.imgs[4].metadata.photo_date = datetime.date(2012, 3, 21)
        self.imgs[4].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(
            date_filter_0='date_range',
            date_filter_3=datetime.date(2012, 3, 10),
            date_filter_4=datetime.date(2012, 3, 20))
        self.assertEqual(
            response.context['page_results'].paginator.count, 3)
        # Make sure that it's the middle three images
        self.assertSetEqual(
            {img.pk for img in response.context['page_results'].object_list},
            {self.imgs[1].pk, self.imgs[2].pk, self.imgs[3].pk})

    def test_filter_by_annotation_status_confirmed(self):
        robot = self.create_robot(self.source)
        # 2 points per image
        # confirmed, confirmed, unconfirmed, partial
        self.add_annotations(self.user, self.imgs[0], {1: 'A', 2: 'B'})
        self.add_annotations(self.user, self.imgs[1], {1: 'B', 2: 'A'})
        self.add_robot_annotations(robot, self.imgs[2])
        self.add_annotations(self.user, self.imgs[3], {1: 'B'})

        self.client.force_login(self.user)
        response = self.submit_search(annotation_status='confirmed')
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_filter_by_annotation_status_unconfirmed(self):
        robot = self.create_robot(self.source)
        # 2 points per image
        # confirmed, unconfirmed, unconfirmed, partial
        self.add_annotations(self.user, self.imgs[0], {1: 'A', 2: 'B'})
        self.add_robot_annotations(robot, self.imgs[1])
        self.add_robot_annotations(robot, self.imgs[2])
        self.add_annotations(self.user, self.imgs[3], {1: 'B'})

        self.client.force_login(self.user)
        response = self.submit_search(annotation_status='unconfirmed')
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_filter_by_annotation_status_unclassified(self):
        robot = self.create_robot(self.source)
        # 2 points per image
        # confirmed, unconfirmed, partial (counts as unclassified)
        self.add_annotations(self.user, self.imgs[0], {1: 'A', 2: 'B'})
        self.add_robot_annotations(robot, self.imgs[1])
        self.add_annotations(self.user, self.imgs[2], {1: 'B'})

        self.client.force_login(self.user)
        response = self.submit_search(annotation_status='unclassified')
        self.assertEqual(
            response.context['page_results'].paginator.count, 3)

    def test_filter_by_aux1(self):
        self.imgs[0].metadata.aux1 = 'Site1'
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.aux1 = 'Site3'
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.aux1 = 'Site3'
        self.imgs[2].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(aux1='Site3')
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_filter_by_aux1_none(self):
        self.imgs[0].metadata.aux1 = 'Site1'
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.aux1 = 'Site3'
        self.imgs[1].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(aux1='(none)')
        self.assertEqual(
            response.context['page_results'].paginator.count, 3)

    def test_aux1_choices(self):
        self.imgs[0].metadata.aux1 = 'Site1'
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.aux1 = 'Site3'
        self.imgs[1].metadata.save()

        self.client.force_login(self.user)
        response = self.client.get(self.url)

        search_form = response.context['image_search_form']
        field = search_form.fields['aux1']
        choices = [value for value, label in field.choices]
        self.assertListEqual(
            choices,
            ['', 'Site1', 'Site3', '(none)']
        )

    def test_filter_by_aux5(self):
        self.imgs[0].metadata.aux5 = 'C'
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.aux5 = 'D'
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.aux5 = 'D'
        self.imgs[2].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(aux5='D')
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_filter_by_height_cm(self):
        self.imgs[0].metadata.height_in_cm = 25
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.height_in_cm = 25
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.height_in_cm = 30
        self.imgs[2].metadata.save()
        # Source default is 50, so the other 2 images have that

        self.client.force_login(self.user)
        response = self.submit_search(height_in_cm=25)
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_filter_by_height_cm_none(self):
        self.imgs[0].metadata.height_in_cm = 25
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.height_in_cm = 25
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.height_in_cm = None
        self.imgs[2].metadata.save()
        self.imgs[3].metadata.height_in_cm = 50
        self.imgs[3].metadata.save()
        self.imgs[4].metadata.height_in_cm = 50
        self.imgs[4].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(height_in_cm='(none)')
        self.assertEqual(
            response.context['page_results'].paginator.count, 1)

    def test_height_cm_choices(self):
        self.imgs[0].metadata.height_in_cm = 25
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.height_in_cm = 30
        self.imgs[1].metadata.save()

        self.client.force_login(self.user)
        response = self.client.get(self.url)

        search_form = response.context['image_search_form']
        field = search_form.fields['height_in_cm']
        choices = [value for value, label in field.choices]
        self.assertListEqual(
            choices,
            ['', 25, 30, '(none)']
        )

    def test_filter_by_latitude(self):
        self.imgs[0].metadata.latitude = '12.34'
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.latitude = '-56.78'
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.latitude = '-56.78'
        self.imgs[2].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(latitude='-56.78')
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_filter_by_latitude_none(self):
        self.imgs[0].metadata.latitude = '12.34'
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.latitude = '-56.78'
        self.imgs[1].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(latitude='(none)')
        self.assertEqual(
            response.context['page_results'].paginator.count, 3)

    def test_filter_by_camera(self):
        self.imgs[0].metadata.camera = 'Nikon'
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.camera = 'Canon'
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.camera = 'Canon'
        self.imgs[2].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(camera='Canon')
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_filter_by_camera_none(self):
        self.imgs[0].metadata.camera = 'Nikon'
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.camera = 'Canon'
        self.imgs[1].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(camera='(none)')
        self.assertEqual(
            response.context['page_results'].paginator.count, 3)

    def test_filter_by_image_name_one_token(self):
        self.imgs[0].metadata.name = 'XYZ.jpg'
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.name = 'abcxyzdef.png'
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.name = 'xydefz.png'
        self.imgs[2].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(image_name='xyz')
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_filter_by_image_name_two_tokens(self):
        # Both search tokens must be present
        self.imgs[0].metadata.name = 'ABCXYZ.jpg'
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.name = 'xyz.abc'
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.name = 'abc.png'
        self.imgs[2].metadata.save()
        self.imgs[3].metadata.name = 'xyz.jpg'
        self.imgs[3].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(image_name='abc xyz')
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_filter_by_image_name_punctuation(self):
        # Punctuation is considered part of search tokens
        self.imgs[0].metadata.name = '1-1.png'
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.name = '1*1.png'
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.name = '2-1-1.jpg'
        self.imgs[2].metadata.save()
        self.imgs[3].metadata.name = '1-1-2.png'
        self.imgs[3].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(image_name='1-1.')
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

    def test_filter_by_multiple_fields(self):
        self.imgs[0].metadata.photo_date = datetime.date(2012, 3, 9)
        self.imgs[0].metadata.height_in_cm = 30
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.photo_date = datetime.date(2013, 3, 10)
        self.imgs[1].metadata.height_in_cm = 30
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.photo_date = datetime.date(2012, 5, 17)
        self.imgs[2].metadata.height_in_cm = 25
        self.imgs[2].metadata.save()
        self.imgs[3].metadata.photo_date = datetime.date(2013, 10, 12)
        self.imgs[3].metadata.height_in_cm = 25
        self.imgs[3].metadata.save()

        self.client.force_login(self.user)
        response = self.submit_search(date_filter_1=2013, height_in_cm=30)
        self.assertEqual(
            response.context['page_results'].paginator.count, 1)

        # Make sure that it's the correct image
        self.assertSetEqual(
            {img.pk for img in response.context['page_results'].object_list},
            {self.imgs[1].pk})

    def test_dont_show_metadata_field_if_all_blank_values(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        search_form = response.context['image_search_form']
        self.assertFalse('latitude' in search_form.fields)

    def test_dont_show_metadata_field_if_all_same_value(self):
        self.imgs[0].metadata.height_in_cm = 50
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.height_in_cm = 50
        self.imgs[1].metadata.save()
        self.imgs[2].metadata.height_in_cm = 50
        self.imgs[2].metadata.save()
        self.imgs[3].metadata.height_in_cm = 50
        self.imgs[3].metadata.save()
        self.imgs[4].metadata.height_in_cm = 50
        self.imgs[4].metadata.save()

        self.client.force_login(self.user)
        response = self.client.get(self.url)

        search_form = response.context['image_search_form']
        self.assertFalse('height_in_cm' in search_form.fields)


# Make it easy to get multiple pages of results.
@override_settings(BROWSE_DEFAULT_THUMBNAILS_PER_PAGE=3)
class ResultsAndPagesTest(ClientTest):

    @classmethod
    def setUpTestData(cls):
        super(ResultsAndPagesTest, cls).setUpTestData()

        cls.user = cls.create_user()
        cls.source = cls.create_source(cls.user)
        cls.url = reverse('browse_images', args=[cls.source.pk])

        cls.imgs = [
            cls.upload_image(cls.user, cls.source) for _ in range(10)
        ]

        cls.default_search_params = dict(
            image_form_type='search',
            aux1='', aux2='', aux3='', aux4='', aux5='',
            height_in_cm='', latitude='', longitude='', depth='',
            photographer='', framing='', balance='',
            date_filter_0='year', date_filter_1='',
            date_filter_2='', date_filter_3='',
            annotation_status='',
        )

    def test_zero_results(self):
        post_data = self.default_search_params.copy()
        post_data['date_filter_0'] = 'date'
        post_data['date_filter_2'] = datetime.date(2000, 1, 1)

        self.client.force_login(self.user)
        response = self.client.post(self.url, post_data)
        self.assertEqual(
            response.context['page_results'].paginator.count, 0)

        self.assertContains(response, "No image results.")

    def test_one_page_results(self):
        post_data = self.default_search_params.copy()
        post_data['aux1'] = 'Site1'

        self.imgs[0].metadata.aux1 = 'Site1'
        self.imgs[0].metadata.save()
        self.imgs[1].metadata.aux1 = 'Site1'
        self.imgs[1].metadata.save()

        self.client.force_login(self.user)
        response = self.client.post(self.url, post_data)
        self.assertEqual(
            response.context['page_results'].paginator.count, 2)

        # html=True is used so that extra whitespace is ignored.
        # There is a tradeoff though: The element name (span) and attributes
        # (none here) must be matched as well.
        self.assertContains(
            response, "<span>Showing 1-2 of 2</span>", html=True)
        self.assertContains(response, "<span>Page 1 of 1</span>", html=True)

    def test_multiple_pages_results(self):
        post_data = self.default_search_params.copy()
        post_data['aux1'] = ''

        self.client.force_login(self.user)
        response = self.client.post(self.url, post_data)
        self.assertEqual(
            response.context['page_results'].paginator.count, 10)

        self.assertContains(
            response, "<span>Showing 1-3 of 10</span>", html=True)
        self.assertContains(response, "<span>Page 1 of 4</span>", html=True)

    def test_page_two(self):
        post_data = self.default_search_params.copy()
        post_data['aux1'] = ''
        post_data['page'] = 2

        self.client.force_login(self.user)
        response = self.client.post(self.url, post_data)
        self.assertEqual(
            response.context['page_results'].paginator.count, 10)

        self.assertContains(
            response, "<span>Showing 4-6 of 10</span>", html=True)
        self.assertContains(response, "<span>Page 2 of 4</span>", html=True)
