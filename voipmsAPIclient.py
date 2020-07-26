import os
import json
import boto3
from urllib.parse import urlencode
from urllib import request

class EmailHandler:
    default_subject = 'Elevators/Phones offline'
    default_body = """Offline Elevators/Phones: {}"""
    default_body_html = """<html>
            <head></head>
            <body>
            <h1>Offline Elevators/Phones</h1>
            <p> {}
            </body>
            </html>
    """
    default_recipient = 'juan@eljach.com'

    @classmethod
    def send(cls, body_payload):
        client = boto3.client('ses',region_name='us-east-1')
        parsed_body_payload = '.\n'.join([str(x) for x in body_payload])
        try:
            #Provide the contents of the email.
            response = client.send_email(
                Destination={
                    'ToAddresses': [
                        cls.default_recipient,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': 'UTF-8',
                            'Data': cls.default_body_html.format(parsed_body_payload),
                        },
                        'Text': {
                            'Charset': 'UTF-8',
                            'Data': cls.default_body.format(parsed_body_payload),
                        },
                    },
                    'Subject': {
                        'Charset': 'UTF-8',
                        'Data': cls.default_subject,
                    },
                },
                Source='juan@eljach.com',
                # If you are not using a configuration set, comment or delete the
                # following line
                #ConfigurationSetName=CONFIGURATION_SET,
            )
        # Display an error if something goes wrong.	
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])



class APIManager:
    voip_user = 'USERNAME'
    voip_api_password = os.environ.get('password')
    base_url = 'https://voip.ms/api/v1/rest.php?api_username={}&api_password={}&'.format(voip_user, voip_api_password)

    def _get(self, payload):
        url = self.base_url + urlencode(payload)
        response = request.urlopen(url)
        return json.loads(response.read())

    def get_register_status(self, account_id):
        payload = {
            'method' : 'getRegistrationStatus',
            'account' : account_id
        }
        return self._get(payload)

    def get_subaccounts(self):
        payload = {
            'method' : 'getSubAccounts'
        }
        return self._get(payload)

    def find_offline(self):
        offline = list()
        sub_accounts = self.get_subaccounts()['accounts']
        if len(sub_accounts) < 1:
            raise Exception("No data received from Voipms")
        
        for sub_account in sub_accounts:
            sub_account_id = sub_account.get('account')
            assert sub_account_id
            sub_account_desc = sub_account.get('description', 'N/A')
            if self.get_register_status(sub_account_id)['registered'] == 'no':
                offline.append(sub_account_desc)

        EmailHandler.send(offline)
        return True



        

        

        
