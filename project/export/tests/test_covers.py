# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import resolve_url

from export.tests.utils import BaseExportTest
from labels.models import LocalLabel
from lib.tests.utils import BasePermissionTest


class PermissionTest(BasePermissionTest):

    def test_annotations_private_source(self):
        url = resolve_url(
            'export_image_covers', self.private_source.pk)
        self.assertPermissionDenied(url, None)
        self.assertPermissionDenied(url, self.user_outsider)
        self.assertPermissionGranted(url, self.user_viewer)
        self.assertPermissionGranted(url, self.user_editor)
        self.assertPermissionGranted(url, self.user_admin)

    def test_annotations_public_source(self):
        url = resolve_url(
            'export_image_covers', self.public_source.pk)
        self.assertPermissionGranted(url, None)
        self.assertPermissionGranted(url, self.user_outsider)
        self.assertPermissionGranted(url, self.user_viewer)
        self.assertPermissionGranted(url, self.user_editor)
        self.assertPermissionGranted(url, self.user_admin)


class ImageSetTest(BaseExportTest):
    """Test image covers export to CSV for different kinds of image subsets."""

    @classmethod
    def setUpTestData(cls):
        super(ImageSetTest, cls).setUpTestData()

        cls.user = cls.create_user()
        cls.source = cls.create_source(
            cls.user,
            min_x=0, max_x=100, min_y=0, max_y=100, simple_number_of_points=5)
        labels = cls.create_labels(cls.user, ['A', 'B'], 'GroupA')
        cls.create_labelset(cls.user, cls.source, labels)

    def test_all_images_single(self):
        """Export for 1 out of 1 images."""
        self.img1 = self.upload_image(
            self.user, self.source, dict(filename='1.jpg'))
        self.add_annotations(self.user, self.img1, {
            1: 'A', 2: 'B', 3: 'A', 4: 'B', 5: 'A'})

        post_data = self.default_search_params.copy()
        response = self.export_image_covers(post_data)

        expected_lines = [
            'Name,Annotation status,Annotation area,A,B',
            '1.jpg,Confirmed,X: 0 - 100% / Y: 0 - 100%,60.000,40.000',
        ]
        self.assert_csv_content_equal(response.content, expected_lines)

    def test_all_images_multiple(self):
        """Export for 1 out of 1 images."""
        self.img1 = self.upload_image(
            self.user, self.source, dict(filename='1.jpg'))
        self.img2 = self.upload_image(
            self.user, self.source, dict(filename='2.jpg'))
        self.img3 = self.upload_image(
            self.user, self.source, dict(filename='3.jpg'))
        self.add_annotations(self.user, self.img1, {
            1: 'A', 2: 'B', 3: 'A', 4: 'B', 5: 'A'})
        self.add_annotations(self.user, self.img2, {
            1: 'A', 2: 'B', 3: 'B', 4: 'B', 5: 'B'})
        self.add_annotations(self.user, self.img3, {
            1: 'A', 2: 'A', 3: 'A', 4: 'A', 5: 'A'})

        post_data = self.default_search_params.copy()
        response = self.export_image_covers(post_data)

        expected_lines = [
            'Name,Annotation status,Annotation area,A,B',
            '1.jpg,Confirmed,X: 0 - 100% / Y: 0 - 100%,60.000,40.000',
            '2.jpg,Confirmed,X: 0 - 100% / Y: 0 - 100%,20.000,80.000',
            '3.jpg,Confirmed,X: 0 - 100% / Y: 0 - 100%,100.000,0.000',
        ]
        self.assert_csv_content_equal(response.content, expected_lines)

    def test_image_subset_by_metadata(self):
        """Export for some, but not all, images."""
        self.img1 = self.upload_image(
            self.user, self.source, dict(filename='1.jpg'))
        self.img2 = self.upload_image(
            self.user, self.source, dict(filename='2.jpg'))
        self.img3 = self.upload_image(
            self.user, self.source, dict(filename='3.jpg'))
        self.add_annotations(self.user, self.img1, {
            1: 'A', 2: 'B', 3: 'A', 4: 'B', 5: 'A'})
        self.add_annotations(self.user, self.img2, {
            1: 'A', 2: 'B', 3: 'B', 4: 'B', 5: 'B'})
        self.add_annotations(self.user, self.img3, {
            1: 'A', 2: 'A', 3: 'A', 4: 'A', 5: 'A'})
        self.img1.metadata.aux1 = 'X'
        self.img1.metadata.save()
        self.img2.metadata.aux1 = 'Y'
        self.img2.metadata.save()
        self.img3.metadata.aux1 = 'X'
        self.img3.metadata.save()

        post_data = self.default_search_params.copy()
        post_data['aux1'] = 'X'
        response = self.export_image_covers(post_data)

        expected_lines = [
            'Name,Annotation status,Annotation area,A,B',
            '1.jpg,Confirmed,X: 0 - 100% / Y: 0 - 100%,60.000,40.000',
            '3.jpg,Confirmed,X: 0 - 100% / Y: 0 - 100%,100.000,0.000',
        ]
        self.assert_csv_content_equal(response.content, expected_lines)

    def test_image_empty_set(self):
        """Export for 0 images."""
        self.img1 = self.upload_image(
            self.user, self.source, dict(filename='1.jpg'))
        self.add_annotations(self.user, self.img1, {
            1: 'A', 2: 'B', 3: 'A', 4: 'B', 5: 'A'})

        post_data = self.default_search_params.copy()
        post_data['image_name'] = '5.jpg'
        response = self.export_image_covers(post_data)

        expected_lines = [
            'Name,Annotation status,Annotation area,A,B',
        ]
        self.assert_csv_content_equal(response.content, expected_lines)


class ColumnOrderTest(BaseExportTest):
    """Test column order in the exported covers CSV."""

    @classmethod
    def setUpTestData(cls):
        super(ColumnOrderTest, cls).setUpTestData()

        cls.user = cls.create_user()
        cls.source = cls.create_source(
            cls.user,
            min_x=0, max_x=100, min_y=0, max_y=100, simple_number_of_points=5)
        labels = cls.create_labels(cls.user, ['A', 'B', 'C'], 'GroupA')
        cls.create_labelset(cls.user, cls.source, labels)

        # Custom codes; ordering by these codes gives a different order from
        # ordering by name or default code
        local_a = LocalLabel.objects.get(
            labelset=cls.source.labelset, code='A')
        local_a.code = '2'
        local_a.save()
        local_b = LocalLabel.objects.get(
            labelset=cls.source.labelset, code='B')
        local_b.code = '1'
        local_b.save()
        local_c = LocalLabel.objects.get(
            labelset=cls.source.labelset, code='C')
        local_c.code = '3'
        local_c.save()

    def test(self):
        self.img1 = self.upload_image(
            self.user, self.source, dict(filename='1.jpg'))
        self.add_annotations(self.user, self.img1, {
            1: '3', 2: '1', 3: '2', 4: '1', 5: '3'})

        post_data = self.default_search_params.copy()
        response = self.export_image_covers(post_data)

        # Columns should be ordered by LocalLabel short code
        expected_lines = [
            'Name,Annotation status,Annotation area,1,2,3',
            '1.jpg,Confirmed,X: 0 - 100% / Y: 0 - 100%,40.000,20.000,40.000',
        ]
        self.assert_csv_content_equal(
            response.content.decode('utf-8'), expected_lines)


class UnicodeTest(BaseExportTest):
    """Test that non-ASCII characters don't cause problems."""

    @classmethod
    def setUpTestData(cls):
        super(UnicodeTest, cls).setUpTestData()

        cls.user = cls.create_user()
        cls.source = cls.create_source(
            cls.user,
            min_x=0, max_x=100, min_y=0, max_y=100, simple_number_of_points=5)
        labels = cls.create_labels(cls.user, ['い'], 'GroupA')
        cls.create_labelset(cls.user, cls.source, labels)

    def test(self):
        self.img1 = self.upload_image(
            self.user, self.source, dict(filename='あ.jpg'))
        self.add_annotations(self.user, self.img1, {
            1: 'い', 2: 'い', 3: 'い', 4: 'い', 5: 'い'})

        post_data = self.default_search_params.copy()
        response = self.export_image_covers(post_data)

        expected_lines = [
            'Name,Annotation status,Annotation area,い',
            'あ.jpg,Confirmed,X: 0 - 100% / Y: 0 - 100%,100.000',
        ]
        self.assert_csv_content_equal(
            response.content.decode('utf-8'), expected_lines)
