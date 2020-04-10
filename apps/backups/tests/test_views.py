from django.test import TestCase
from django.contrib.messages import get_messages

from apps.user.models import UserProfile
from apps.backups.models import ObjectLookup

from fyle_backup_app import settings


class BackupsViewTest(TestCase):
    """
    Test cases for Backups view
    """

    def setUp(self):
        """
        Setup sample data for testing
        """
        UserProfile.objects.create_user(email="user1@test.com", password="foo",
                                        refresh_token=settings.TEST_REFRESH_TOKEN,
                                        fyle_org_id=settings.TEST_FYLE_ORG_ID)
        ObjectLookup.objects.create(name='expenses')
        self.client.login(email='user1@test.com', password='foo')

    def test_create_backup_failed(self):
        # name is missing, so form validation should fail
        post_data = {'approved_at_lte': [''], 'updated_at_gte': [''], 'updated_at_lte': [''],
                     'download_attachments': ['on'], 'object_type': ['expenses'],
                     'data_format': ['CSV']}
        response = self.client.post('/main/backups/', post_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Something went wrong. Please try again!')

    def test_create_backup_success(self):
        post_data = {'name': ['test'], 'approved_at_gte': [''], 'approved_at_lte': [''],
                     'updated_at_gte': [''], 'updated_at_lte': [''],
                     'download_attachments': ['on'], 'object_type': ['expenses'],
                     'data_format': ['CSV']}
        response = self.client.post('/main/backups/', post_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertNotEqual(str(messages[0]), 'Something went wrong. Please try again!')

