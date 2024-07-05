# RetailAI
RetailAI is a solution that encapsulates and demonstrates the capabilities of [Compound AI Systems](https://bair.berkeley.edu/blog/2024/02/18/compound-ai-systems/). 



## Install and Run Application 

You will need to have the following `.env` file to connect to Databricks from your local desktop. 
```
DATABRICKS_TOKEN=<PAT TOKEN>
DATABRICKS_HOST=<Databricks Workspace URL> #adb-<workspaceid>.<##>.azuredatabricks.net
WAREHOUSE_HTTP_PATH=<SQL Warehouse Path> # /sql/1.0/warehouses/<ID>
DATABRICKS_CATALOG=<data catalog>
DATABRICKS_SCHEMA=<data schema>
ITTM_ENDPOINT=<image to text api endpoint on Databricks model serving>
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
<video src="https://www.youtube.com/watch?v=z8s0S9FLTrw" controls="controls" style="max-width: 730px;"></video>
</div>
