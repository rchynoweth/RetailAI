import logging
from io import StringIO

import base64

from prophet import Prophet
import pandas as pd
import plotly.express as px


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def generate_forecast(input_bytes):
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




