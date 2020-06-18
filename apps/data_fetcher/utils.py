import base64
import csv
import os
import shutil
import json
import logging
import traceback
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, SubscriptionTracking, TrackingSettings
from django.template.loader import render_to_string
from fylesdk import FyleSDK
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
        self.connection = FyleSDK(
            base_url=settings.FYLE_BASE_URL,
            client_id=settings.FYLE_CLIENT_ID,
            client_secret=settings.FYLE_CLIENT_SECRET,
            refresh_token=refresh_token,
            jobs_url=settings.FYLE_JOBS_URL
        )

    def extract_expenses(self, state, fund_source, approved_at, updated_at, spent_at, reimbursed_at):
        """
        Get a list of existing Expenses, that match the parameters
        :param updated_at: Date string in yyyy-MM-ddTHH:mm:ss.SSSZ format
        :param approved_at: Date string in yyyy-MM-ddTHH:mm:ss.SSSZ format
        :param spent_at: Date string in yyyy-MM-ddTHH:mm:ss.SSSZ format
        :param reimbursed_at: Date string in yyyy-MM-ddTHH:mm:ss.SSSZ format
        :param state: state of the expense [ 'PAID' , 'DRAFT' , 'APPROVED' ,
                                            'APPROVER_PENDING' , 'COMPLETE' ]
        :return: List with dicts in Expenses schema.
        """
        expenses = self.connection.Expenses.get_all(state=state, fund_source=fund_source, 
                                                    approved_at=approved_at,
                                                    updated_at=updated_at, spent_at=spent_at,
                                                    reimbursed_at=reimbursed_at)        
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

    def dump_csv(self, dir_name, reimbursable):
        """
        :param data: Takes existing Expenses Data, that match the parameters
        :param path: Takes the path of the file
        :param reimbursable: Reimbursable Filter on Expenses
        :return: CSV file with the list of existing Expenses
        """
        reimbursable = bool(reimbursable)
        expenses = self.data
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
            if reimbursable!='':
                if reimbursable == expense['reimbursable']:
                    data.append(row)
            else:
                data.append(row)
        filename = dir_name + '/{0}.csv'.format(self.name)
        try:
            with open(filename, 'w') as export_file:
                keys = data[0].keys()
                dict_writer = csv.DictWriter(
                    export_file, fieldnames=keys, delimiter=',')
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
        expense_ids = [(i.get('id'))
                       for i in self.data if i['has_attachments'] is True]
        if not expense_ids:
            logger.error('No attachments found for: %s', dir_name)
            return
        logger.info(
            '%s Expense(s) have attachment(s) . Downloading now.', len(expense_ids))

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
                        with open(dir_name + '/' + expense_id + '_' +
                                  attachment_names[index], "wb") as fh:
                            fh.write(base64.b64decode(img_data))
                            # logger.info('%s_%s Download completed', expense_id,
                            #              attachment_names[index])
            except Exception as e:
                logger.error('Attachment dump failed for %s, Error: %s',
                             attachment_names[index], e)

    def dump_data(self, reimbursable):
        """
        Wrapper function for dumping backup to local file
        """
        try:
            now = datetime.now().strftime("%d-%m-%Y-%H:%M:%S")
            dir_name = self.path + \
                '{}-{}-Date--{}'.format(self.fyle_org_id, self.name, now)
            os.mkdir(dir_name)
            self.dump_csv(dir_name, reimbursable)
            if self.download_attachments is True:
                logger.info(
                    'Going to download attachment for backup: %s', self.name)
                self.dump_attachments(dir_name)
            logger.info('Attachment dump finished for %s', self.name)
            shutil.make_archive(dir_name, 'zip', dir_name)
            logger.info('Archive file created at %s for %s',
                        dir_name, self.name)
            return dir_name+'.zip'
        except Exception as e:
            logger.error('Error in dump_data() : %s', e)
            raise


def remove_items_from_tmp(dir_path):
    try:
        os.unlink(dir_path)
        shutil.rmtree(dir_path.split('.zip')[0])
    except OSError as e:
        logger.error('Error while deleting %s. Error: %s', dir_path, e)
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
        message = Mail(from_email=from_email,
                       to_emails=to_email,
                       subject=subject,
                       html_content=content)
        sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        tracking_settings = TrackingSettings()
        tracking_settings.subscription_tracking = SubscriptionTracking(enable=False)
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
    reimbursable = filters.get('reimbursable')
    refresh_token = backup.fyle_refresh_token
    fyle_org_id = backup.fyle_org_id
    name = backup.name.replace(' ', '')
    fyle_connection = FyleSdkConnector(refresh_token)
    logger.info('Going to fetch data for backup_id: %s', backup_id)
    response_data = fyle_connection.extract_expenses(state=filters.get('state'),
                                                     fund_source=filters.get('fund_source'),
                                                     approved_at=filters.get(
                                                         'approved_at'),
                                                     updated_at=filters.get('updated_at'),
                                                     spent_at=filters.get('spent_at'),
                                                     reimbursed_at=filters.get('reimbursed_at'))
    if not response_data:
        logger.info('No data found for backup_id: %s', backup_id)
        backup.current_state = 'NO DATA FOUND'
        backup.save()
        return True

    logger.info('Going to dump data to file for backup_id: %s', backup_id)
    dumper = Dumper(fyle_connection, path=settings.DOWNLOAD_PATH, data=response_data, name=name,
                    fyle_org_id=fyle_org_id, download_attachments=download_attachments)
    try:
        file_path = dumper.dump_data(reimbursable)
        logger.info('Download Successful for backup_id: %s', backup_id)

        response = fyle_connection.upload_file_to_aws(file_path)

        logger.info('Cloud upload Successful for backup_id: %s', backup_id)

        # Get a secure URL for this backup and mail it to user
        notify_user(fyle_connection, response['file_url'], 'expense')

        backup.fyle_file_id = response['fyle_file_id']
        backup.current_state = 'READY'
        backup.save()
        # Remove the files from local machine
        remove_items_from_tmp(file_path)
        return True
    except Exception as e:
        backup.current_state = 'FAILED'
        backup.save()
        error = traceback.format_exc()
        logger.error(
            'Backup process failed for bkp_id: %s . Error: %s , Traceback: %s', backup_id, e, error)
        return False
