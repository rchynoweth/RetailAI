# RetailAI
RetailAI is a solution that encapsulates and demonstrates the capabilities of [Compound AI Systems](https://bair.berkeley.edu/blog/2024/02/18/compound-ai-systems/). 



## Install and Run Application 

You will need to have the following `.env` file to connect to Databricks from your local desktop. 
```
DATABRICKS_TOKEN=<PAT TOKEN>
DATABRICKS_WORKSPACE=<Databricks Workspace URL> #adb-<workspaceid>.<##>.azuredatabricks.net
WAREHOUSE_HTTP_PATH=<SQL Warehouse Path> # /sql/1.0/warehouses/<ID>
DATABRICKS_CATALOG=<data catalog>
DATABRICKS_SCHEMA=<data schema>
ITTM_ENDPOINT=<image to text api endpoint on Databricks model serving>
```


To run the application locally please execute the following commands. 
```
# Create environment 
conda create -n productcopy python=3.10

conda activate productcopy

# install requirements 
pip install -r requirements.txt

# change working directory and run application
cd productcopy

python run_app.py
```
