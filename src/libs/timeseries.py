import logging
from typing import Union, Dict, Tuple
from prophet import Prophet
import pandas as pd
import plotly.express as px
import plotly.io as pio
import libs.file_handler as fh
from langchain.tools import BaseTool
from sklearn.metrics import mean_squared_error, mean_absolute_error
from math import sqrt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()



class ForecastTool(BaseTool):
    name = "Forecast Generation Tool"
    description = "use this tool to generate forecasts. "

    # def _to_args_and_kwargs(self, tool_input: Union[str, Dict]) -> Tuple[Tuple, Dict]:
    #     return (), {}

    def _run(self, frequency):
        """Generates a forecast and image to display 

        Args:
            frequency (str): The frequency of which to produce forecasts. It should be daily, weekly, or monthly.  

        Returns:
            str: returns a text description of the forecast. The image of the forecast is saved to the assets folder for display. 
        """
        freq = 'D' if frequency.lower() == 'daily' else 'D'
        logger.info("Generating Forecast - %s")
        # file was uploaded and saved to this location
        pdf = pd.read_csv('/tmp/data.csv', parse_dates=['ds'])

        logger.info("PDF Types: %s", pdf.dtypes)

        model = Prophet(interval_width=0.85)
        model.fit(pdf)

        # create a forecast and keep historical values with a join
        future_pd = model.make_future_dataframe(periods=30, freq=freq, include_history=True)

        # Generate forecast
        forecast_pd = model.predict(future_pd)
        output_df = pd.merge(forecast_pd, pdf, on='ds', how='left')

        # Resetting index to keep 'ds' as a column
        output_df.rename(columns={'ds': 'Date'}, inplace=True)

        # generate a forecast image
        logger.info("Generating image.")
        forecast_image = px.line(output_df, x='Date', y=['y', 'yhat','yhat_upper', 'yhat_lower'])
        img_path = f"src/assets/display_{fh.get_current_timestamp()}.png"
        pio.write_image(forecast_image, img_path)

        return evaluate_forecasts(output_df)



    def _arun(self):
        return NotImplementedError
    
    
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
    results = f"The forecast has been generated. We have observed that there are {num_upper_alerts} occurences where the y value was above the upper threshold (yhat_upper) and {num_lower_alerts} occurrences where the y value was below the lower threshold (yhat_lower). Here are evaluation metrics for the forecast. Mean Average Error:{mae}, Mean Squared Error: {mse}, Root Mean Squared Error: {rmse}"
    return results

