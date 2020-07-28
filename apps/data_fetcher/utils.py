import base64
import csv
import os
import shutil
import json
import logging
import boto3
import requests
from botocore.exceptions import ClientError
import traceback
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, SubscriptionTracking, TrackingSettings
from django.template.loader import render_to_string
from fylesdk import FyleSDK
from fylesdk.exceptions import UnauthorizedClientError, ExpiredTokenError, InvalidTokenError
from fyle_backup_app import settings

logger = logging.getLogger('app')

EXPENSE_FUND_SOURCES = {
    "PERSONAL": "Personal Account",
    "ADVANCE": "Advance",
    "CCC": "Corporate Credit Card"
}
EXPENSE_STATES = {
    "PAYMENT_PROCESSING": "Payment Processing",
    "COMPLETE": "Complete",
    "PAYMENT_PENDING": "Payment Pending",
    "APPROVED": "Approved",
    "APPROVER_PENDING": "Approver pending",
    "DRAFT": "Draft",
    "FYLED": "Fyled",
    "PAID": "Paid"
}


class FyleSdkConnector():
    """
    Class with utils functions for FyleSDK
    """

    def __init__(self, refresh_token):
        self.refresh_token = refresh_token
        self.connection = FyleSDK(
            base_url=settings.FYLE_BASE_URL,
            client_id=settings.FYLE_CLIENT_ID,
            client_secret=settings.FYLE_CLIENT_SECRET,
            refresh_token=refresh_token,
            jobs_url=settings.FYLE_JOBS_URL
        )

    def extract_expenses(self, state, fund_source, approved_at, updated_at, spent_at, reimbursed_at, reimbursable):
        """
        Get a list of existing Expenses, that match the parameters
        :param fund_source: Multiselect foud sources
        :param updated_at: Date string in yyyy-MM-ddTHH:mm:ss.SSSZ format
        :param approved_at: Date string in yyyy-MM-ddTHH:mm:ss.SSSZ format
        :param spent_at: Date string in yyyy-MM-ddTHH:mm:ss.SSSZ format
        :param reimbursable: If filter selected - True of False
        :param reimbursed_at: Date string in yyyy-MM-ddTHH:mm:ss.SSSZ format
        :param state: state of the expense [ 'PAID' , 'DRAFT' , 'APPROVED' ,
                                            'APPROVER_PENDING' , 'COMPLETE' ]
        :return: List with dicts in Expenses schema.
        """
        count = self.connection.Expenses.count(
            state=state, fund_source=fund_source,
            approved_at=approved_at, updated_at=updated_at,
            spent_at=spent_at,reimbursed_at=reimbursed_at
        )['count']

        expenses = []

        page_size = 300
        for i in range(0, count, page_size):
            try:
                segment = self.connection.Expenses.get(
                    offset=i, limit=page_size,
                    state=state, fund_source=fund_source,
                    approved_at=approved_at,
                    updated_at=updated_at, spent_at=spent_at,
                    reimbursed_at=reimbursed_at
                )

            except (UnauthorizedClientError, ExpiredTokenError, InvalidTokenError):
                self.connection = FyleSDK(
                    base_url=settings.FYLE_BASE_URL,
                    client_id=settings.FYLE_CLIENT_ID,
                    client_secret=settings.FYLE_CLIENT_SECRET,
                    refresh_token=self.refresh_token,
                    jobs_url=settings.FYLE_JOBS_URL
                )
                segment = self.connection.Expenses.get(
                    offset=i, limit=page_size,
                    state=state, fund_source=fund_source,
                    approved_at=approved_at,
                    updated_at=updated_at, spent_at=spent_at,
                    reimbursed_at=reimbursed_at
                )
            expenses = expenses + segment['data']

        if reimbursable:
            reimbursable = True if reimbursable == 'True' else False
            expenses = filter(
                lambda expense: expense['reimbursable'] == reimbursable, expenses)
        return expenses

    def extract_attachments(self, expense_id):
        """
        Get all the file attachments associated with an Expense.
        :param expense_id: Unique ID to find an Expense.
        :return: List with dicts in Attachments schema.
        """
        try:
            attachment = self.connection.Expenses.get_attachments(expense_id)
        except (UnauthorizedClientError, ExpiredTokenError, InvalidTokenError):
            self.connection = FyleSDK(
                base_url=settings.FYLE_BASE_URL,
                client_id=settings.FYLE_CLIENT_ID,
                client_secret=settings.FYLE_CLIENT_SECRET,
                refresh_token=self.refresh_token,
                jobs_url=settings.FYLE_JOBS_URL
            )
            attachment = self.connection.Expenses.get_attachments(expense_id)
        return attachment

    def extract_employee_details(self):
        """
        Extract fyle profile details of user
        """
        employee_data = self.connection.Employees.get_my_profile()
        return employee_data.get('data')

    def upload_file_to_aws(self, file_path):
        """
        Upload file to AWS S3 using FyleSDk
        :param file_path: Location to the file
        return: [file_id, file_url]
        """
        fyle_connection = self.connection

        content_type = 'application/zip'
        file_data = open(file_path, 'rb').read()

        file_obj = fyle_connection.Files.post(file_path)
        upload_url = fyle_connection.Files.create_upload_url(file_obj['id'])[
            'url']
        fyle_connection.Files.upload_file_to_aws(
            content_type, file_data, upload_url)
        response = fyle_connection.Files.create_download_url(file_obj['id'])

        val = {}
        val['fyle_file_id'] = file_obj['id']
        val['file_url'] = response['url']

        return val


class AWSS3():
    """
    Class to handle attachments on S3
    """
    def __init__(self):
        self.s3 = boto3.resource('s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        self.client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.region = settings.S3_REGION_NAME
        self.AWS_ATTACHMENT_BUCKET = settings.AWS_ATTACHMENT_BUCKET
        self.AWS_LAMBDA_ENDPOINT = settings.AWS_LAMBDA_ENDPOINT

    def zipper(self, folder):
        """
        :param folder: Invoke AWS Lambda Function to ZIP all files in a dir
        :return: File full path relative to bucket
        """
        endpoint = self.AWS_LAMBDA_ENDPOINT
        body = {
          "bucket_name": self.AWS_ATTACHMENT_BUCKET,
          "folder": folder
        }
        headers = {
          'Content-Type': 'application/json'
        }
        requests.post(url = endpoint, headers=headers, data = json.dumps(body))
        # response = response.json()
        # s3_file_path = response['body']['file_name']
        # print(s3_file_path)
        # return s3_file_path

    def create_presigned_url(self, object_path):
        """
        Generate Signed URL for the attachment ZIPs
        :param object_path: Path to the object on S3
        :return: Signed URL
        """
        expiration = 7*24*2600

        try:
            response = self.client.generate_presigned_url('get_object',
                                    Params={'Bucket': self.AWS_ATTACHMENT_BUCKET,
                                            'Key': object_path},
                                    ExpiresIn=expiration)
            return response
        except ClientError as e:
            logging.error(e)
            return None


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

    @staticmethod
    def format_date(value):
        """
        :param date of the transaction
        :return formatted date
        """
        MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "June",
                  "July", "Aug", "Sept", "Oct", "Nov", "Dec"
                  ]
        if value:
            date, month, year = value.split("T")[0].split("-")[::-1]
            return "{} {}, {}".format(MONTHS[int(month) - 1], date, year)

    def dump_csv(self, data):
        """
        :param data: Takes existing Expenses Data, that match the parameters
        :param path: Takes the path of the file
        :return: CSV file with the list of existing Expenses
        """
        expenses = data
        data = []
        for expense in expenses:
            row = {
                'Expense ID': expense['id'],
                'Orgnization Name': expense['org_name'],
                'Employee Email': expense['employee_email'],
                'Employee Id': expense['employee_id'],
                'Cost Center': expense['cost_center_name'],
                'Reimbursable': expense['reimbursable'],
                'State': EXPENSE_STATES[expense['state']],
                'Report Number': expense['report_id'],
                'Currency': expense['currency'],
                'Amount': expense['amount'],
                'Foreign Currency': expense['foreign_currency'],
                'Amount in Foreign Currency': expense['foreign_amount'],
                'Purpose': expense['purpose'],
                'Expense Number': expense['expense_number'],
                'Fund Source': EXPENSE_FUND_SOURCES[expense['fund_source']],
                'Category Name': expense['category_name'],
                'Sub Category': expense['sub_category'],
                'Project Name': expense['project_name'],
                'Spent On': self.format_date(expense['spent_at']),
                'Created On': self.format_date(expense['created_at']),
                'Approved On': self.format_date(expense['approved_at'])
            }
            data.append(row)
        return data


def remove_items_from_tmp(dir_path):
    try:
        os.unlink(dir_path)
        shutil.rmtree(dir_path.split('.zip')[0])
    except OSError as e:
        logger.error('Error while deleting %s. Error: %s', dir_path, e)
        raise


def processSegments(response_data):
    """
    Function for breaking a large dataset into small segements
    for convinient and efficient batch processing
    """
    segments = {}
    response_data = sorted(response_data, key = lambda expense: expense['spent_at'])
    monthYear_tmp = ''

    for expense in response_data:
        value = expense['spent_at']
        date, month, year = value.split("T")[0].split("-")[::-1]
        monthYear = month+year
        if(monthYear_tmp != monthYear):
            newSegment = [expense]
        else:
            newSegment.append(expense)
        monthYear_tmp = monthYear
        segments[monthYear] = newSegment
    segment_ids = list(segments.keys())
    return [segment_ids, segments]



def processBackup(fyle_connection, download_attachments, backup, response_data):
    """
    Wrapper function for dumping backup attachments to local file
    """
    fyle_org_id = backup.fyle_org_id
    fyle_file_id = []
    name = backup.name.replace(' ', '')
    if download_attachments:
        """
        If download_attachments == True, then split the task
        into subtasks and process batches
        """
        response = processSegments(response_data)
        segment_ids, segments = response[0], response[1]
        print(segment_ids)
        backup.current_state = 'IN PROGRESS'
        backup.split_count = len(segment_ids)
        backup.save()

        now = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
        dumper = Dumper(fyle_connection, path=settings.DOWNLOAD_PATH, data=response_data, name=name,
                    fyle_org_id=fyle_org_id, download_attachments=download_attachments)
        folder_name = '{}-{}-Date--{}'.format(dumper.fyle_org_id, dumper.name, now)
        dir_name = '/tmp/'+folder_name
        os.mkdir(dir_name)

        for segment_id in segment_ids:
            expenses = segments[segment_id]
            os.mkdir(dir_name+'/'+ segment_id)
            filename = '{}-{}.csv'.format(name, segment_id)
            file_path = dir_name + '/'+ segment_id + '/' + filename
            response_data = dumper.dump_csv(expenses)
            try:
                with open(file_path, 'w') as export_file:
                    keys = response_data[0].keys()
                    dict_writer = csv.DictWriter(
                        export_file, fieldnames=keys, delimiter=',')
                    dict_writer.writeheader()
                    dict_writer.writerows(response_data)
            except (OSError, csv.Error) as e:
                logger.error('CSV dump failed for %s, Error: %s', name, e)
                raise

            s3_path = folder_name+'/'+segment_id
            AWSS3().s3.Bucket(settings.AWS_ATTACHMENT_BUCKET).put_object(
                Key=s3_path+'/'+filename, Body=open(file_path, 'rb'))
            os.unlink(file_path)

            expense_ids = [(i.get('id'))
                           for i in expenses if i['has_attachments'] is True]
            if not expense_ids:
                pass
            else:
                logger.info(
                    '%s Expense(s) have attachment(s) . Downloading now.', len(expenses))

                for expense_id in expense_ids:
                    try:
                        attachment = fyle_connection.extract_attachments(expense_id)
                        attachment_data = attachment['data']
                        attachment_content = [item.get('content')
                                              for item in attachment_data]

                        if attachment['data']:
                            attachment = attachment['data'][0]
                            attachment['expense_id'] = expense_id
                            attachment_names = [item.get('filename')
                                                for item in attachment_data]

                            for index, img_data in enumerate(attachment_content):
                                img_data = (attachment_content[index])                               
                                AWSS3().s3.Bucket(settings.AWS_ATTACHMENT_BUCKET).put_object(
                                    Key=s3_path+'/'+attachment_names[index]
                                    , Body=img_data)
                                    
                    except Exception as e:
                        logger.error('Attachment dump failed for %s, Error: %s',
                                     attachment_names[index], e.response)
            AWSS3().zipper(s3_path)
            # fyle_file_id.append(zip_path)
            # backup.fyle_file_id = json.dumps(fyle_file_id)
            # backup.save()

    else:
        """
        If attachment download == false, then use the old
         method to create CSV
        """
        backup.split_count = 1
        backup.save()
        now = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
        dumper = Dumper(fyle_connection, path=settings.DOWNLOAD_PATH, data=response_data, name=name,
                    fyle_org_id=fyle_org_id, download_attachments=download_attachments)
        folder_name = '{}-{}-Date--{}'.format(dumper.fyle_org_id, dumper.name, now)
        response_data = dumper.dump_csv(response_data)
        dir_name = '/tmp/'+folder_name
        os.mkdir(dir_name)
        filename = '/{0}.csv'.format(name)
        file_path = dir_name + filename
        print("Folder Name: "+folder_name)
        try:
            with open(file_path, 'w') as export_file:
                keys = response_data[0].keys()
                dict_writer = csv.DictWriter(
                    export_file, fieldnames=keys, delimiter=',')
                dict_writer.writeheader()
                dict_writer.writerows(response_data)
        except (OSError, csv.Error) as e:
            logger.error('CSV dump failed for %s, Error: %s', name, e)
            raise
        AWSS3().s3.Bucket(settings.AWS_ATTACHMENT_BUCKET).put_object(
                Key=folder_name+filename, Body=open(file_path, 'rb'))
        os.unlink(file_path)
        print("Sent Path:"+folder_name)
        AWSS3().zipper(folder_name)
        # fyle_file_id.append(zip_path)

    # backup.fyle_file_id = json.dumps(fyle_file_id)
    # backup.current_state = 'READY'
    # backup.save()
    return backup


def send_email(from_email, to_email, subject, content):
    """
    Send an email notification
    :param from_email: email_id of sender
    :param to_email: email_id of recipient
    :param subject: subject for the email
    :param content: email body
    """
    try:
        message = Mail(from_email=from_email,
                       to_emails=to_email,
                       subject=subject,
                       html_content=content)
        sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        tracking_settings = TrackingSettings()
        tracking_settings.subscription_tracking = SubscriptionTracking(
            enable=False)
        message.tracking_settings = tracking_settings
        sg_client.send(message)
    except Exception as e:
        error = traceback.format_exc()
        logger.error('Email sending failed due to: %s', error)
        logger.error(e.body)


def notify_user(fyle_connection, download_url, object_type):
    """
    Get a presigned URL and mail it to user
    :param fyle_connection: fyle SDK connection
    :param download_url: signed URL name
    :param object_type: business object type eg: expenses
    """
    try:
        user_data = fyle_connection.extract_employee_details()
        email_to = user_data.get('employee_email')
        subject = 'The {0} backup you requested from Fyle\
                   is ready for download'.format(object_type.capitalize())
        content = render_to_string('email_body.html', {'link': download_url})
        send_email(settings.SENDER_EMAIL_ID, email_to, subject, content)
        print('Signed Download URL: ', download_url)

    except Exception as e:
        logger.error('Error while notifying user due to %s', e)
        raise


def fetch_and_notify_expenses(backup):
    """
    Fetch expenses matching the filters, upload to cloud,
    notify user via email
    :param backup: backup object for which expense needs to be procesed
    :return : False for errored cases, True otherwise
    """
    backup_id = backup.id
    filters = json.loads(backup.filters)
    download_attachments = filters.get('download_attachments')
    refresh_token = backup.fyle_refresh_token
    fyle_connection = FyleSdkConnector(refresh_token)
    logger.info('Going to fetch data for backup_id: %s', backup_id)
    response_data = fyle_connection.extract_expenses(state=filters.get('state'),
                                                     fund_source=filters.get(
                                                         'fund_source'),
                                                     approved_at=filters.get(
                                                         'approved_at'),
                                                     updated_at=filters.get(
                                                         'updated_at'),
                                                     spent_at=filters.get(
                                                         'spent_at'),
                                                     reimbursed_at=filters.get(
                                                         'reimbursed_at'),
                                                     reimbursable=filters.get('reimbursable'))
    if not response_data:
        logger.info('No data found for backup_id: %s', backup_id)
        backup.current_state = 'NO DATA FOUND'
        backup.save()
        return True

    logger.info('Going to dump data to file for backup_id: %s', backup_id)

    try:
        backup.fyle_file_id = []
        backup.save()
        backup = processBackup(fyle_connection, download_attachments, backup, response_data)
        backup.current_state = 'READY'
        backup.save()        
        # Remove the files from local machine
        
        return True
    except Exception as e:
        backup.current_state = 'FAILED'
        backup.save()
        error = traceback.format_exc()
        logger.error(
            'Backup process failed for bkp_id: %s . Error: %s , Traceback: %s', backup_id, e, error)
        return False
