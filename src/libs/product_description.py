import requests
import json
from dotenv import load_dotenv
import logging
import os 
from typing import Union, Dict, Tuple
import base64
import io

from langchain.tools import BaseTool
from PIL import Image
from datetime import datetime



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


class ProductDescriptionTool(BaseTool):
    name = "Product Description Tool Tool"
    description = "use this tool convert an image to text description then generate a product description based on the output and user input."

    def _to_args_and_kwargs(self, tool_input: Union[str, Dict]) -> Tuple[Tuple, Dict]:
        return (), {}

    def _run(self):
        """Generates product description

        Returns:
            str: returns a text description of the product. 
        """
        logger.info("Generating Product Description.")

        logger.info("Loading image from system.")
        # create input data from image 
        with open('/tmp/product_image.png', 'rb') as f:
            img_data = f.read()

        img_data_base64 = base64.b64encode(img_data).decode('utf-8')
        data = {'dataframe_records': [{'content': img_data_base64}], 'client_request_id':'1' }

        logger.info("Extracting text from image.")
        desc_output = image_to_text_extract(data=data)
        logger.info("Raw Image Description - %s", desc_output)

        # save image for display 
        img_path = f"src/assets/display_{get_current_timestamp()}.png"
        image = Image.open(io.BytesIO(img_data))
        image.save(img_path)
        image.close()
        logger.info("Display image saved.")

        return desc_output


def get_current_timestamp():
    # Get the current time
    now = datetime.now()
    
    # Format the current time as yyyyMMddHHmmss
    current_timestamp = now.strftime('%Y%m%d%H%M%S')
    
    return current_timestamp
