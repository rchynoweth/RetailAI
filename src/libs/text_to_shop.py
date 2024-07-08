import requests
import json
from dotenv import load_dotenv
import logging
import os 
from typing import Union, Dict, Tuple
import base64
from databricks import sql 



from langchain.tools import BaseTool



load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


class Text2ShopTool(BaseTool):
    name = "Text to shop Tool"
    description = "use this tool shop for items when a user requests it."

    def _to_args_and_kwargs(self, tool_input: Union[str, Dict]) -> Tuple[Tuple, Dict]:
        return (), {}

    def _run(self, product_name):
        """Searches available products based on user input and returns the available product that can be added to the cart. 

        Args:
            product_name (str): The user's inputted product that they are looking for. 

        Returns:
            str: The Name as listed in the catalog
        """
        logger.info("Searching products for %s", product_name)

        product_table_name = "rac_demo_catalog.rac_demo_db.groceries"

        # title = product_name.get('title')

        qry = f"""
            select name, id, description
            from {product_table_name}
            order by ai_similarity(name, '{product_name}') desc
            limit 1
            """
        
        logger.info("Executing Similarity Query - %s", qry)

        results = execute_query(query=qry)

        out = [{'product_name': r.product_name, 'manufacturer': r.manufacturer, 'price': r.price, 'description': r.description} for r in results]

        return out


def execute_query(query):
    dbtoken = os.getenv('DATABRICKS_TOKEN')
    server_hostname = os.getenv('DATABRICKS_WORKSPACE')
    http_path = os.getenv('WAREHOUSE_HTTP_PATH')

    with sql.connect(server_hostname=server_hostname, 
                    http_path=http_path, 
                    access_token=dbtoken) as connection:
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

    return result