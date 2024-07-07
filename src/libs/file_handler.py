import os
import logging
import pandas as pd
from io import StringIO

import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def check_file_type(file_name):
    """Validates files uploaded are of acceptable type 

    Args:
        file_name (str): Name of the file. 

    Returns:
        Tuple: First index of the tuple is if the file type is support. The second index is a string containing the explaination. 
    """
    # Get the file extension
    _, file_extension = os.path.splitext(file_name)

    accepted_file_types = [
        '.csv',
        '.txt',
        '.png',
        '.jpg',
        '.jpeg',
    ]
    
    # Normalize the extension to lowercase
    file_extension = file_extension.lower()
    
    # Check if the file is a CSV or PNG
    if file_extension not in accepted_file_types:
        return (False, f"Error: Invalid file type: {file_extension}. Only {accepted_file_types} files are allowed.")
    else:
        return (True, f"File type {file_extension} is valid.")
    

def save_file_upload(input_file_name, file_bytes, output_file_path='/tmp'):
    _, file_extension = os.path.splitext(input_file_name)

    if file_extension == '.csv':
        logger.info("Generating Forecast.")
        # Decode the base64 string
        data = base64.b64decode(file_bytes).decode('utf-8')
        # Convert the decoded string to a file-like object
        string_io = StringIO(data)
        pdf = pd.read_csv(string_io, parse_dates=['ds'])
        pdf.to_csv(f"{output_file_path}/data.csv")