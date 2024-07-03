import os



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