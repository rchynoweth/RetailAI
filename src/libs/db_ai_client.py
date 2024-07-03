import requests
import json
from dotenv import load_dotenv
import os
import logging


# Load environment variables from .env file
load_dotenv()

class DBAIClient():
    """Databricks AI Client that assists with holding state and interactions with a foundational model.
    """

    def __init__(self, system_message):
        # Set class variables 
        self.dbtoken = os.environ.get('DATABRICKS_TOKEN')
        self.db_workspace = os.environ.get('DATABRICKS_WORKSPACE')
        self.bot_name = "Retail AI"
        self.system_message = system_message
        self.endpoint_url = f"https://{self.db_workspace}/serving-endpoints/databricks-dbrx-instruct/invocations"
        self.ittm_api_endpoint = os.environ.get('ITTM_ENDPOINT') 
        
        # configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()
        
        # set messages for chat history
        self.reset_messages()


    def send_chat(self, max_tokens=None):
        """Sends chat messages to Model Endpoint

        Returns:
            dict: AI Response content
        """
        payload = {"messages": self.messages, "max_tokens": max_tokens}
        headers = {"Content-Type": "application/json"}
        self.logger.info("Payload: %s", payload)
        response = requests.post(self.endpoint_url, headers=headers, json=payload, auth=("token", self.dbtoken), timeout=600)
        self.logger.info("Response Text: %s", response.text)
        return json.loads(response.content.decode('utf-8'))


    def add_message(self, role, msg):
        """Adds a message to the messages list as a dictionary. 

        Args:
            role (str): Either 'assistant' or 'user' representing the actors role in the conversation.  
            msg (str): The message to send to the AI
        """
        assert role in ['assistant', 'user'], "Error - Role must be 'user' or 'assistant' "
        message = {
            "role": role,
            "content": msg
        }
        self.messages.append(message)
        self.logger.info("Chat Messages: %s", self.messages)

    def edit_system_message(self, msg, reset = False):
        """Allows edits to the system message. This is typically used to pass additional environment information that may have changed. 

        Args:
            msg (str): The message to append to the system message.
            reset (bool, optional): If true will reset the system message to the default value allowing us to erase any additional information provided to the AI. Defaults to False.
        """
        self.messages[0]['content'] += f"{msg}. "
        if reset: 
            self.messages[0]['content'] = self.system_message

    def reset_messages(self):
        """Resets AI messages to the default system prompt with no user/assistant entries. 
        """
        self.messages = [
            {
            "role": "system",
            "content": self.system_message
            }
        ]


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