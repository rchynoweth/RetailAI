# Databricks notebook source
# MAGIC %md ##Introduction
# MAGIC
# MAGIC In this notebook we will deploy an image to text API to Databricks GPU Model Serving. 

# COMMAND ----------

# MAGIC %pip install transformers

# COMMAND ----------

dbutils.library.restartPython()

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

# Load the appropriate model from transformers into context. We also need to tell it what kind of device to use.
model = InstructBlipForConditionalGeneration.from_pretrained("Salesforce/instructblip-flan-t5-xl")
processor = InstructBlipProcessor.from_pretrained("Salesforce/instructblip-flan-t5-xl", load_in_8bit=True, cache_dir='processor_cache')

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
    device = "cuda" if torch.cuda.is_available() else "cpu"
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
      print(f"---------------- Outputs set", flush=True)
      generated_text = processor.batch_decode(outputs, skip_special_tokens=True)[0].strip()
      print(f"---------------- Generated Text", flush=True)
      return(generated_text)
    except Exception as e:
      print(f"------------ An exception occurred: {str(e)}", flush=True)
      return str(e)




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
catalog_name = 'rac_demo_catalog'
schema_name = 'productcopy_demo'
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
  spark.sql("drop table if exists rac_demo_catalog.productcopy_demo.rac_image_to_text_model_payload")
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
