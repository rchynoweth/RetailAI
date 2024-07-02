import requests 
import json
from dotenv import load_dotenv
import os
import logging


# Load environment variables from .env file
load_dotenv()

class DBAIClient():

    def __init__(self):
        # Access an environment variable
        self.dbtoken = os.environ.get('DATABRICKS_TOKEN')
        self.db_workspace = os.environ.get('DATABRICKS_WORKSPACE')
        self.bot_name = "Retail AI"
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()
        self.endpoint_url = f"https://{self.db_workspace}/serving-endpoints/databricks-dbrx-instruct/invocations"
        self.ittm_api_endpoint = os.environ.get('ITTM_ENDPOINT') 
        self.reset_messages()


    def send_chat(self):
        payload = {"messages": self.messages}
        headers = {"Content-Type": "application/json"}
        self.logger.info(f"Payload: {payload}")
        response = requests.post(self.endpoint_url, headers=headers, json=payload, auth=("token", self.dbtoken))
        self.logger.info(f"Response Text: {response.text}")
        return json.loads(response.content.decode('utf-8'))


    def add_message(self, role, msg):
        message = {
            "role": role,
            "content": msg
        }
        self.messages.append(message)
        self.logger.info(f"Chat Messages: {self.messages}")


    def reset_messages(self):
        self.messages = [
            {
            "role": "system",
            "content": "You are a master or retail analytics and busines processes. If the user asks you to do something you will categorize it as one of the following in your response: Time Series Forecasting, Product Image Description Generation, or Other. Users have the ability to upload csv and image files for processing. If the requested task of information falls into the 'Other' category, then please respond that you cannot assist and you are not liable for any responses."
            }
        ]


    def messages_to_string(self):
        msg = ""
        for m in self.messages:
            if m.get('role') == 'system':
                continue 
            elif m.get('role') == 'user':
                msg += f"User: {m.get('content')}\n"
            elif m.get('role') == 'assistant':
                msg += f"{self.bot_name}: {m.get('content')}\n"
        
        return msg

    # def image_to_text_extract(self, content):
    #     data = {'dataframe_records': [{'content': content}] }

    #     # Make the POST request
    #     response = requests.post(
    #         self.ittm_api_endpoint,
    #         auth=("token", self.dbtoken),
    #         headers={"Content-Type": "application/json"},
    #         json=data
    #     )


    #     return json.loads(response.content.decode('utf-8'))