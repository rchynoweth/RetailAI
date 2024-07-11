import requests
import json
from dotenv import load_dotenv
import logging
import os 




load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def image_to_text_extract(data):
    # data = {'dataframe_records': [{'content': content}] }
    itt_endpoint = os.getenv("ITT_ENDPOINT")
    dbtoken = os.getenv('DATABRICKS_TOKEN')

    # Make the POST request
    response = requests.post(
        itt_endpoint,
        auth=("token", dbtoken),
        headers={"Content-Type": "application/json"},
        json=data
    )
    return json.loads(response.content.decode('utf-8'))
