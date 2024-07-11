from dotenv import load_dotenv
import logging
import os 
from databricks import sql 


load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def execute_query(query):
    logger.info("Executing SQL Query: %s", query)
    dbtoken = os.getenv('DATABRICKS_TOKEN')
    server_hostname = os.getenv('DATABRICKS_HOST').replace("https://", "")
    http_path = os.getenv('WAREHOUSE_HTTP_PATH')

    with sql.connect(server_hostname=server_hostname, 
                    http_path=http_path, 
                    access_token=dbtoken) as connection:
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

    return result