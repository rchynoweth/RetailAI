# Databricks notebook source
# MAGIC %md The purpose of this notebook is to extract descriptions from images as part of  with the Product Description Generation solution accelerator.  This notebook was developed on a **Databricks ML 14.3 LTS GPU-enabled** cluster with Standard_NC24ads_A100_v4. 

# COMMAND ----------

# MAGIC %md ##Introduction
# MAGIC
# MAGIC In this notebook, we will generate basic descriptions for each of the images read in the prior notebook.  These descriptions will serve as a critical input to our final noteobook.

# COMMAND ----------

# MAGIC %pip install transformers
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# data_path = "/Volumes/rac_demo_catalog/productcopy_demo/ecomm_product_images/"
# catalog_name = 'rac_demo_catalog'
# schema_name = 'productcopy_demo'
dbutils.widgets.text('data_path', '')
dbutils.widgets.text('catalog_name', '')
dbutils.widgets.text('schema_name', '')

data_path = dbutils.widgets.get('data_path')
catalog_name = dbutils.widgets.get('catalog_name')
schema_name = dbutils.widgets.get('schema_name')

# COMMAND ----------

spark.sql(f"use catalog {catalog_name}")
spark.sql(f"use schema {schema_name}")

# COMMAND ----------

from transformers import InstructBlipProcessor, InstructBlipForConditionalGeneration
from transformers.generation import GenerationConfig
from io import BytesIO
from PIL import Image
import torch

import pandas as pd
from typing import Iterator
import os

from pyspark.sql.functions import *

import mlflow
import mlflow.pyfunc
from mlflow.models.signature import infer_signature

mlflow.set_registry_uri('databricks-uc')

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Image to Text Process 
# MAGIC
# MAGIC We will then install the Salesforce/instructblip-flan-t5-xl model which has been trained with image and text description data to associate image structures with text:
# MAGIC
# MAGIC

# COMMAND ----------

cnt = spark.sql(f""" 
          select * 
          from {catalog_name}.information_schema.tables
          where table_catalog = '{catalog_name}' and table_schema = '{schema_name}' and table_name = 'product_images'
          limit 10
          """).count()

if cnt > 0:
  # read jpg image files
  images = (
    spark
      .read
      .format("binaryFile") # read file contents as binary
      .option("recursiveFileLookup", "true") # recursive navigation of folder structures
      .option("pathGlobFilter", "*.jpg") # read only files with jpg extension
      .load(f"{data_path}/data") # starting point for accessing files
    )

  # write images to persisted table
  _ = (
    images
      .write
      .mode("overwrite")
      .format("delta")
      .saveAsTable("product_images")
  )

# display data in table
display(
  spark
    .read
    .table("product_images")
    .limit(10)
    )

# COMMAND ----------

image = (
  spark.read
    .table('product_images')
    .select('path','content')
    .limit(1)
).collect()[0]

image

# COMMAND ----------

# Load the appropriate model from transformers into context. We also need to tell it what kind of device to use.
model = InstructBlipForConditionalGeneration.from_pretrained("Salesforce/instructblip-flan-t5-xl")
processor = InstructBlipProcessor.from_pretrained("Salesforce/instructblip-flan-t5-xl", load_in_8bit=True, cache_dir='processor_cache')

# COMMAND ----------

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

# COMMAND ----------

# Function to accept the binary contents of an image and extract from it a text description

def get_description(img):
  "Convert an image binary and generate a description"
  image = Image.open(BytesIO(img)) # This loads the image from the binary type into a format the model understands.

  # Additional prompt engineering represents one of the easiest areas to experiment with the underlying model behavior.
  prompt = "Describe the image using tags from the fashion industry? Mention style and type. Please be concise"
  inputs = processor(images=image, text=prompt, return_tensors="pt").to(device)

  gen_conf = GenerationConfig.from_model_config(model.config)

  # Model parameters can be tuned as desired.
  outputs = model.generate(
          **inputs,
          do_sample=True,
          num_beams=5,
          max_length=256,
          min_length=1,
          top_p=0.9,
          repetition_penalty=1.5,
          length_penalty=1.0,
          temperature=1,
          generation_config=gen_conf
  )
  # We need to decode the outputs from the model back to a string format.
  generated_text = processor.batch_decode(outputs, skip_special_tokens=True)[0].strip()
  return(generated_text)

# COMMAND ----------

# get description
description = get_description(image[1])

# # print discription and display image
# print(
#   Image.open(BytesIO(image['content']))
#   )
print(description)

# COMMAND ----------

# MAGIC %md 
# MAGIC ## Package solution for Model Serving

# COMMAND ----------

class ImageToTextModel(mlflow.pyfunc.PythonModel):

  def load_context(self, context): 
    from transformers import InstructBlipProcessor, InstructBlipForConditionalGeneration
    from transformers.generation import GenerationConfig
    import torch

    model = InstructBlipForConditionalGeneration.from_pretrained("Salesforce/instructblip-flan-t5-xl")
    processor = InstructBlipProcessor.from_pretrained("Salesforce/instructblip-flan-t5-xl", load_in_8bit=True, cache_dir=context.artifacts["processor"], local_files_only=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)


  def predict(self, context, model_input, prompt="Describe the image using tags from the fashion industry? Mention style and type. Please be concise."):
    """Convert an image binary and generate a description"""

    from PIL import Image
    from io import BytesIO
    import base64
    import requests
    import warnings
    print(f"---------------- Model Input: {model_input}",flush=True)
    print(f"---------------- Model Type: {type(model_input)}", flush=True)

    img = model_input["content"][0] # get the encoded image
    print(f"---------------- Get individual row", flush=True)

    decoded_img_data = base64.b64decode(img)
    print(f"---------------- Data decoded", flush=True)
    image = Image.open(BytesIO(decoded_img_data))
    print(f"---------------- Image Loaded", flush=True)

    # Additional prompt engineering represents one of the easiest areas to experiment with the underlying model behavior.
    inputs = processor(images=image, text=prompt, return_tensors="pt").to(device)
    print(f"---------------- Inputs set", flush=True)

    model.to('cuda')
    gen_conf = GenerationConfig.from_model_config(model.config)
    gen_conf.cache_implementation='dynamic'
    gen_conf.output_logits = False
    print(f"---------------- Created Config", flush=True)

    try :
      # Model parameters can be tuned as desired.
      outputs = model.generate(
        **inputs,
        do_sample=False,
        num_beams=5,
        max_length=256,
        min_length=1,
        top_p=0.9,
        repetition_penalty=1.5,
        length_penalty=1.0,
        temperature=1,
        generation_config=gen_conf,
      )
      print(f"---------------- Outputs set")
      generated_text = processor.batch_decode(outputs, skip_special_tokens=True)[0].strip()
      print(f"---------------- Generated Text", flush=True)
      return(generated_text)
    except Exception as e:
      print(f"------------ An exception occurred: {str(e)}", flush=True)
      return str(e)




# COMMAND ----------

# maybe add an evaluation table here to compare the different descriptions. "MLflow Evaluation" for reference code. 

# COMMAND ----------

reqs = ["torch==2.0.1","transformers==4.38.1", "cloudpickle==2.0.0","accelerate>=0.25.0","torchvision==0.15.2","optimum==1.17.1"]
content_list = ["This is image data as a string"]
pdf = pd.DataFrame({'content': content_list})
api_output = "This is an image description"

# Log the model
with mlflow.start_run(run_name = "rac_image_to_text_model"):
  model_name = 'rac_image_to_text_model'
  run = mlflow.active_run()
  signature = infer_signature(pdf, api_output, None)
  mlflow.pyfunc.log_model(
      artifact_path=model_name,
      python_model=ImageToTextModel(),
      artifacts={'processor': './processor_cache'},
      signature=signature, 
      pip_requirements=reqs
  )


    
  model_uri = f'runs:/{run.info.run_id}/{model_name}'
  reg = mlflow.register_model(model_uri=model_uri, name="rac_demo_catalog.productcopy_demo.rac_image_to_text_model", await_registration_for=600) 
    

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deploy to Model Serving 

# COMMAND ----------

from mlflow.deployments import get_deploy_client

client = get_deploy_client("databricks")

# COMMAND ----------

model_name = "rac_image_to_text_model"
full_model_name = f"{catalog_name}.{schema_name}.{model_name}"
model_version = reg.version
endpoint_name = "rac_image_endpoint"

# COMMAND ----------

try: 
  client.get_endpoint(endpoint=endpoint_name)
  endpoint_exists = True
except:
  endpoint_exists = False

# COMMAND ----------

endpoint_config = {
          "served_entities": [
              {
                  "name": f"{model_name}-{model_version}",
                  "entity_name": full_model_name,
                  "entity_version": model_version,
                  "workload_size": "Small",
                  "workload_type": "GPU_LARGE",
                  "scale_to_zero_enabled": False,
              }
          ],
          "auto_capture_config": {
              "catalog_name": catalog_name,
              "schema_name": schema_name,
              "table_name_prefix": model_name,
          },
          "traffic_config": {
              "routes": [
                  {
                      "served_model_name": f"{model_name}-{model_version}",
                      "traffic_percentage": 100,
                  }
              ]
          },
      }

# COMMAND ----------

if endpoint_exists == False:
  endpoint = client.create_endpoint(
      name=endpoint_name,
      config=endpoint_config,
  )
else :
  del endpoint_config['auto_capture_config']
  endpoint = client.update_endpoint(
    endpoint=endpoint_name,
    config=endpoint_config,
    )

# COMMAND ----------

