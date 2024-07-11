import os
import logging
from dotenv import load_dotenv
import requests
import json

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()





def call_foundation_model(system_msg, user_msg, max_tokens=3):
    logger.info("Executing Foundational API call.")
    dbtoken = os.getenv('DATABRICKS_TOKEN')
    db_workspace = os.environ.get('DATABRICKS_HOST')
    endpoint_url = f"{db_workspace}/serving-endpoints/databricks-dbrx-instruct/invocations"

    messages = [
        {
        "role": "system",
        "content": system_msg
        },
        {
        "role": "user",
        "content": user_msg
        }
    ]

    payload = {"messages": messages, 'max_tokens': max_tokens}
    headers = {"Content-Type": "application/json"}
    logger.info("Payload: %s", payload)
    response = requests.post(endpoint_url, headers=headers, json=payload, auth=("token", dbtoken))
    logger.info(f"Response Text: %s", response.text)
    return json.loads(response.content.decode('utf-8'))


    
    return response.get('output')

