# RetailAI
RetailAI is a solution that encapsulates and demonstrates the capabilities of [Compound AI Systems](https://bair.berkeley.edu/blog/2024/02/18/compound-ai-systems/). It is an agentic solution that leverages a centralized LLM and agent to correspond with the user via chat and execute a distinct skill set automatically depending on the user's request. 



## Install and Run Application 

You will need to have the following `.env` file to connect to Databricks from your local desktop. 
```
DATABRICKS_TOKEN=<PAT TOKEN>
DATABRICKS_HOST=<Databricks Workspace URL> #adb-<workspaceid>.<##>.azuredatabricks.net
WAREHOUSE_HTTP_PATH=<SQL Warehouse Path> # /sql/1.0/warehouses/<ID>
ITT_ENDPOINT=<image to text api endpoint on Databricks model serving>
```


To run the application locally please execute the following commands. 
```
# Create environment 
conda create -n retailai python=3.10

conda activate retailai

# install requirements 
pip install -r requirements.txt

# change working directory and run application
cd RetailAI

python src/app.py
```
<div style="text-align: center;">
<video src="https://github.com/rchynoweth/RetailAI/assets/79483287/a98c89e4-a678-4bd5-964e-273b8345ade0" controls="controls" style="max-width: 730px;"></video>
</div>



## Skills 

The Retail AI System possess the following skills:
- Text to shop
    - Conversational agent to shop and automatically add items to the cart 
    - LLM will complete the shopping for the user and provide personalized recommendations depending on user interactions.
    - Please note that we have hard coded datasets in the `text_to_shop.py` module that make this skill not available out of the box. 
- Time Series Forecasting
    - Upload data (daily only) and execute demand forecasting on the fly and receive prescriptive analytics and chart. 
- Recipe Shopping 
    - Provide a list of ingredients or a screenshot of a recipe list and have the LLM shop for you! 
    - LLM will complete the shopping for the user and provided personalized recommendations depending on user interactions. 
- Product Description Editor
    - Use the LLM to create and edit product descriptions! 
    - Optionally provide an image allowing the LLM to analyze the product independently. 
    - The image to text API must be deployed prior using the `deploy_image_to_text_api.py` Databricks notebook that needs to be executed on a single node A100 Databricks cluster using the ML Runtime. This notebook contains hardcoded values that may need to be altered. 







