import logging
from io import StringIO

import base64

from prophet import Prophet
import pandas as pd
import plotly.express as px

from langchain.tools import BaseTool
from sklearn.metrics import mean_squared_error, mean_absolute_error
from math import sqrt



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


class ForecastTool():
# class ForecastTool(BaseTool):
    name = "Forecast Generation Tool"
    description = "use this tool to generate forecasts. "

    def run(input_bytes: str):
        """Generates a forecast and image to display 

        Args:
            input_bytes (str): String representation of bytes. 

        Returns:
            tuple: The first index is a pandas dataframe or results and the second index is an image. 
        """
        logger.info("Generating Forecast.")
        # Decode the base64 string
        data = base64.b64decode(input_bytes).decode('utf-8')
        # Convert the decoded string to a file-like object
        string_io = StringIO(data)
        pdf = pd.read_csv(string_io, parse_dates=['ds'])

        logger.info("PDF Types: %s", pdf.dtypes)

        model = Prophet(interval_width=0.85)
        model.fit(pdf)

        # create a forecast and keep historical values with a join
        future_pd = model.make_future_dataframe(periods=30, freq='D', include_history=True)

        # Generate forecast
        forecast_pd = model.predict(future_pd)
        output_df = pd.merge(forecast_pd, pdf, on='ds', how='left')

        # Resetting index to keep 'ds' as a column
        output_df.rename(columns={'ds': 'Date'}, inplace=True)

        # generate a forecast image
        logger.info("Generating image.")
        forecast_image = px.line(output_df, x='Date', y=['y', 'yhat','yhat_upper', 'yhat_lower'])    

        return output_df, forecast_image
    
    def evaluate_forecasts(pdf):
        """
        Forecast evaluation function. Generates MAE, RMSE, MSE metrics. 
        """
        evaluation_pd = pdf[pdf['y'].notnull()]
        
        # calulate evaluation metrics
        mae = round(mean_absolute_error( evaluation_pd['y'], evaluation_pd['yhat'] ), 4)
        mse = round(mean_squared_error( evaluation_pd['y'], evaluation_pd['yhat'] ), 4)
        rmse = round(sqrt( mse ), 4)

        # Get trend alerts
        yhat_above_upper = pdf[pdf['y'] > pdf['yhat_upper']]
        yhat_below_lower = pdf[pdf['y'] < pdf['yhat_lower']]
        num_upper_alerts = str(len(yhat_above_upper))
        num_lower_alerts = str(len(yhat_below_lower))
        
        # assemble result set
        # results = {'training_date':[training_date], 'workspace_id':[workspace_id], 'sku':[sku], 'mae':[mae], 'mse':[mse], 'rmse':[rmse]}
        results = f"The forecast has been generated and displayed. Here is some information for the LLM. We have observed that there are {num_upper_alerts} occurences where the y value was above the upper threshold (yhat_upper) and {num_lower_alerts} occurrences where the y value was below the lower threshold (yhat_lower). Here are evaluation metrics for the forecast. Mean Average Error:{mae}, Mean Squared Error: {mse}, Root Mean Squared Error: {rmse}"
        return results
