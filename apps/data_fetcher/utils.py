import base64
import csv
import os
import shutil
import logging
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from fylesdk import FyleSDK
from fyle_backup_app import settings

logger = logging.getLogger('app')


class FyleSdkConnector():
    """
    Class with utils functions for FyleSDK
    """
    def __init__(self, refresh_token):
        self.connection = FyleSDK(
            base_url=settings.BASE_URL,
            client_id=settings.CLIENT_ID,
            client_secret=settings.CLIENT_SECRET,
            refresh_token=refresh_token
        )

    def extract_expenses(self, state, approved_at, updated_at):
        """
        Get a list of existing Expenses, that match the parameters
        :param updated_at: Date string in yyyy-MM-ddTHH:mm:ss.SSSZ format
        :param approved_at: Date string in yyyy-MM-ddTHH:mm:ss.SSSZ format
        :param state: state of the expense [ 'PAID' , 'DRAFT' , 'APPROVED' ,
                                            'APPROVER_PENDING' , 'COMPLETE' ]
        :return: List with dicts in Expenses schema.
        """
        expenses = self.connection.Expenses.get_all(state=state, approved_at=approved_at,
                                                    updated_at=updated_at)
        return expenses

    def extract_attachments(self, expense_id):
        """
        Get all the file attachments associated with an Expense.
        :param expense_id: Unique ID to find an Expense.
        :return: List with dicts in Attachments schema.
        """
        attachment = self.connection.Expenses.get_attachments(expense_id)
        return attachment

    def extract_employee_details(self):
        """
        Extract fyle profile details of user
        """
        employee_data = self.connection.Employees.get_my_profile()
        return employee_data.get('data')


class CloudStorage():
    """
    Utility class for fcloud file upload
    """
    def __init__(self, provider=None):
        """
        :param provider: cloud provider, awss3 by default
        """
        if provider is None:
            provider = settings.CLOUD_STORAGE_PROVIDER
        self.provider = provider

    def s3_upload_file(self, path, fyle_org_id):
        """
        Upload a file to AWS S3
        :param path: path to find the local file
        /tmp/ormsDa8NCYdL-sample1-Date--17-03-2020-16:19:22.zip
        :param fyle_org_id: fyle org_id of the user
        :return: True if uploaded False otherwise
        """
        file_name = path
        object_name = fyle_org_id +'/'+ path.split('/')[2]
        s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        try:
            s3_client.upload_file(file_name, settings.S3_BUCKET_NAME, object_name)
        except ClientError as e:
            logging.error('Error while uploading to s3 for oject %s. Error: %s', object_name, e)
            raise

    def upload(self, path, fyle_org_id):
        """
        Factory method to upload file to cloud storage
        :param path: path to find the local file
        :param fyle_org_id: fyle org_id of the user
        """
        if self.provider == 'awss3':
            return self.s3_upload_file(path, fyle_org_id)
        raise NotImplementedError

    @staticmethod
    def create_presigned_url(object_name):
        """Generate a presigned URL to share an S3 object

        :param object_name: string - s3 object name
        :return: Presigned URL as string. If error, returns None.
        """
        s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                 region_name=settings.S3_REGION_NAME)
        try:
            response = s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': settings.S3_BUCKET_NAME,
                                                                'Key': object_name},
                                                        ExpiresIn=settings.PRESIGNED_URL_EXPIRY)
        except ClientError as e:
            logging.error('Presigned url creation failure for object: %s. Error: %s',
                          object_name, e)
            raise
        return response


class Dumper():
    """
    Used to Dump the expenses data into a CSV or JSON file
    """
    def __init__(self, fyle_connection, **kwargs):
        """
        :param fyle_connection: connection to fyle through FyleSDK
        :param path: path to find the local file
        :param data: List of dicts containing expense data
        :param fyle_org_id: string
        :param name: backup name
        :param download_attachments: string 'True'/'False'
        """
        self.connection = fyle_connection
        self.path = kwargs.get('path')
        self.data = kwargs.get('data')
        self.fyle_org_id = kwargs.get('fyle_org_id')
        self.name = kwargs.get('name')
        self.download_attachments = kwargs.get('download_attachments')

    def dump_csv(self, dir_name):
        """
        :param data: Takes existing Expenses Data, that match the parameters
        :param path: Takes the path of the file
        :return: CSV file with the list of existing Expenses
        """
        data = self.data
        filename = dir_name + '/{0}.csv'.format(self.name)
        try:
            with open(filename, 'w') as export_file:
                keys = data[0].keys()
                dict_writer = csv.DictWriter(export_file, fieldnames=keys, delimiter=',')
                dict_writer.writeheader()
                dict_writer.writerows(data)
        except (OSError, csv.Error) as e:
            logger.error('CSV dump failed for %s, Error: %s', self.name, e)
            raise

    def dump_attachments(self, dir_name):
        """
        :param data: Takes existing Expenses Data, that match the parameters
        :param path: Takes the path of the file
        :return:  Expenses Attachments
        """
        fyle_connection = self.connection
        expense_ids = [(i.get('id')) for i in self.data if i['has_attachments'] is True]
        if not expense_ids:
            logger.error('No attachments found for: %s', dir_name)
            return
        logger.info('%s Expense(s) have attachment(s)', len(expense_ids))
        logger.info('Downloading now')

        for expense_id in expense_ids:
            attachment = fyle_connection.extract_attachments(expense_id)
            attachment_data = attachment['data']
            attachment_content = [item.get('content') for item in attachment_data]

            if attachment['data']:
                attachment = attachment['data'][0]
                attachment['expense_id'] = expense_id
                attachment_names = [item.get('filename') for item in attachment_data]

                for index, img_data in enumerate(attachment_content):
                    img_data = (attachment_content[index])
                    try:
                        with open(dir_name + '/' + expense_id + '_' +
                                  attachment_names[index], "wb") as fh:
                            logger.info(' Downloading %s_%s', expense_id, attachment_names[index])
                            fh.write(base64.b64decode(img_data))
                            logger.info('%s_%s Download completed', expense_id,
                                        attachment_names[index])
                    except (OSError, csv.Error) as e:
                        logger.error('CSV dump failed for %s, Error: %s', dir_name, e)
                        raise

    def dump_data(self):
        """
        Wrapper function for dumping backup to local file
        """
        try:
            now = datetime.now().strftime("%d-%m-%Y-%H:%M:%S")
            dir_name = self.path + '{}-{}-Date--{}'.format(self.fyle_org_id, self.name, now)
            os.mkdir(dir_name)
            self.dump_csv(dir_name)
            if self.download_attachments == 'on':
                logger.info('Going to download attachment for backup: %s', self.name)
                self.dump_attachments(dir_name)
            shutil.make_archive(dir_name, 'zip', dir_name)
            logger.info('Archive file created at %s for ', dir_name)
            return dir_name+'.zip'
        except Exception as e:
            logger.error('Error in dump_data() : %s', e)
            raise


def send_email(from_email, to_email, subject, content):
    """
    Send an email notification
    :param from_email: email_id of sender
    :param to_email: email_id of recipient
    :param subject: subject for the email
    :param content: email body
    """
    try:
        message = Mail(
                        from_email=from_email,
                        to_emails=to_email,
                        subject=subject,
                        html_content=content)
        sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        sg_client.send(message)
    except Exception as e:
        logger.error('Email sending failed due to: %s',e)
        raise

def notify_user(fyle_connection, file_path, fyle_org_id, object_type):
    """
    Get a presigned URL and mail it to user
    """
    try:
        object_name = fyle_org_id +'/'+ file_path
        presigned_url = CloudStorage().create_presigned_url(object_name)
        user_data = fyle_connection.extract_employee_details()
        email_to = user_data.get('employee_email')
        subject = 'The {0} Backup you requested from Fyle is ready for download'.format(object_type)
        send_email(settings.SENDER_EMAIL_ID, email_to, subject, presigned_url)
    except Exception as e:
        logger.error(e)
        raise
