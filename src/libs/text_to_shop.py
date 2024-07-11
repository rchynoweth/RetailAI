from dotenv import load_dotenv
import logging
import os 

from langchain.tools import BaseTool
import libs.cart as cart
import libs.db_sql as dbsql
from libs.foundation_api import call_foundation_model


load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


class Text2ShopTool(BaseTool):
    name = "Text to shop Tool"
    description = "use this tool to help customers shop for items. They will likely provide items they want to buy or purchase or want. "

    # def _to_args_and_kwargs(self, tool_input: Union[str, Dict]) -> Tuple[Tuple, Dict]:
    #     return (), {}

    def _run(self, product_name, quantity):
        """Searches available products based on user input and returns the available product that can be added to the cart. 

        Args:
            product_name (str): The product the user requested. 
            qty (str): The number of units that the user is asking for. 

        Returns:
            str: The Name as listed in the catalog
        """
        logger.info("Searching products for %s", product_name)

        product_table_name = "rac_demo_catalog.rac_demo_db.product_catalog"
        try:
            qty = quantity.get('title') 
        except: 
            qty = quantity

        try: 
            prd_name = product_name.get('title') 
        except:
            prd_name = product_name

        qty = 1 if qty is None else qty

        # get the item that the user requested and add it to the cart. 
        qry = f"""
            select name, id, description, company_name
            from {product_table_name}
            order by ai_similarity(name, '{prd_name}') desc
            limit 1
            """
        
        vector_qry = f"""
            select name, id, description, company_name
            from {product_table_name}
            order by ai_similarity(name, '{prd_name}') desc
            limit 1
            """
        
        results = dbsql.execute_query(query=qry)
        out = [{'name': r.name, 'id': r.id, 'description': r.description, 'company_name': r.company_name, 'quantity': qty } for r in results]
        cart.add_item(out[0])

        rec_item = call_foundation_model(
            system_msg="You are going to recieve user input information from another conversation related to items they are purchasing. Please recommend a single additional item they may be interested in. You should respond with a single word and do not use punctuation. Provide only a product name and nothing else.",
            user_msg=f"The user is requesting to purchase the following prd_name. Please recommend a product we can upsell and only produce a 1 to 2 words. No punctuation."
        ).get('choices')[0].get('message').get('content').split(" ")[0].replace("\n", "")
        logger.info("Raw Recommendation: %s", rec_item)
        

        recommendation_query = f"""
            select name
            from {product_table_name}
            order by ai_similarity(name, '{rec_item}') desc
            limit 3
        """
        product_recommendations = dbsql.execute_query(query=recommendation_query)
        recs = [{'name': r.name } for r in product_recommendations]



        tool_response = f"""
        We have automatically added the following to the customer's cart: {out}. \n
        Please recommend the following items: {recs}
        """

        return tool_response



