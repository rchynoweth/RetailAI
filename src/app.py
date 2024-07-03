import logging 

import dash
from dash import html, Input, Output, State, dcc
import dash_bootstrap_components as dbc

from layouts.index import index_layout

from libs.db_ai_client import DBAIClient
from libs.file_handler import *

from libs.timeseries import *


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

retail_ai_system_message = "You are a master or retail analytics and busines processes. If the user asks you to do something you will categorize it as one of the following in your response: Time Series Forecasting, Product Image Description Generation, or Other. Users have the ability to upload csv and image files for processing and you do have the ability to view images and data files. If the requested task of information falls into the 'Other' category, then please respond that you cannot assist and you are not liable for any responses. "
db_ai_client = DBAIClient(system_message=retail_ai_system_message)
ai_intent_system_message = "Behave like a multi-classification machine learning model where you predict one of the following based on user intent: 'Time Series Forecasting', 'Product Description Generation', or 'Other'. You are limited to only those categories and do not say anything else. Do not use more than 3 words. If the user changes their intent then you should predict the latest intent. "
ai_intent_classifier = DBAIClient(system_message=ai_intent_system_message)
db_ai_client.reset_messages()

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Application layout
app.layout = dbc.Container(
    [
     index_layout
    ],
    fluid=True,
)


# Callback to update chat history when the send button is clicked or Enter key is pressed
@app.callback(
    [Output("store-chat-history", "data"), Output("output-image", "children")],
    [Input("send-button", "n_clicks"), Input("input-message", "n_submit"), Input('upload-file', 'contents')],
    [State("input-message", "value"), State("store-chat-history", "data"), State('upload-file', 'filename')],
)
def update_chat(n_clicks, n_submit, file_content, new_message, chat_history, file_name):
    logger.info("Updating the Chat.")
    forecast_image = None 

    # Check if a file was uploaded
    if file_content is not None:
        file_bytes = file_content.split(",")[1]
        logger.info("File Contents: %s | %s", file_bytes[:10], file_name)
        db_ai_client.edit_system_message("", True)
        
        # Generate forecast and image
        forecast, forecast_image = generate_forecast(file_bytes)
        # Convert figure to HTML representation
        # forecast_image = dcc.Graph(figure=fig)
        logger.info("%s", forecast.head(5))

        # Check file type validity
        if not check_file_type(file_name=file_name)[0]:
            chat_history.append({"sender": "bot", "text": check_file_type(file_name=file_name)[1]})
            return chat_history, None

    # Do nothing if there is no valid text input from the user
    display_check = ((n_clicks is None or n_clicks == 0) and (n_submit is None or n_submit == 0)) or (new_message is None or new_message.strip() == "")
    if display_check:
        return chat_history, None
    
    # Add the user message to the client chat
    db_ai_client.add_message('user', new_message)
    # chat_history = chat_history or []
    chat_history.append({"sender": "user", "text": new_message})

    determine_intent(chat_history=chat_history, file_content=file_bytes)

    # Get bot response and add it to chat history
    bot_message = get_bot_response()
    chat_history.append({"sender": "bot", "text": bot_message})

    # Return updated chat history and forecast image
    if forecast_image is not None:
        return chat_history, dcc.Graph(id='graph-content', figure=forecast_image)
    else :
        return chat_history, None


# Callback to render the chat history
@app.callback(Output("chat-history", "children"), [Input("store-chat-history", "data")])
def display_chat(chat_history):
    """Displays the chat history between the user and the assistant. 

    Args:
        chat_history (list): List of dictionaries with alternating assistant and user text. 

    Returns:
        list: List of dictionaries containing user and assistant chat messages
    """
    logger.info("Displaying the chat")
    messages = []
    for msg in chat_history:
        if msg["sender"] == "user":
            messages.append(html.Div(msg["text"], style={"background-color": "#dff0d8", "padding": "5px", "border-radius": "5px", "margin-bottom": "5px"}))
        else:
            messages.append(html.Div(msg["text"], style={"background-color": "#f2dede", "padding": "5px", "border-radius": "5px", "margin-bottom": "5px"}))
    return messages


# Callback to clear the input field after sending the message
@app.callback(
    Output("input-message", "value"),
    [Input("send-button", "n_clicks"), Input("input-message", "n_submit")],
)
def clear_input(_, __):
    """Clears the user input box when submitted. 

    Returns:
        str: Returns empty string to reset the input box to nothing. 
    """
    logger.info("Clearing the user input text box.")
    return ""



def get_bot_response():
    """Calls the AI API to get the response message from the LLM

    Returns:
        str: Bot's response based on chat history. 
    """
    logger.info("Getting AI Response")
    # call the API
    response = db_ai_client.send_chat()
    # get the bot response 
    bot_response = response.get('choices')[0].get('message').get('content')
    # save the bot response to the object for chat tracking
    db_ai_client.add_message('assistant', bot_response)
    # return the response for display
    return bot_response 


def determine_intent(chat_history, file_content):
    # ask the AI which action to take based on chat history
    # may need to change system prompt
    action = ""
    message = f"What is the users intent based on the following message history? {chat_history}"
    ai_intent_classifier.add_message('user', msg=message)
    user_intent = ai_intent_classifier.send_chat(max_tokens=5).get('choices')[0].get('message').get('content').strip().replace("'", "").replace(".","")
    logger.info("---------> INTENT CLASSIFICATION: %s", user_intent)
    assert user_intent in ['Time Series Forecasting', 'Product Description Generation', 'Other', '', None]
    
    if action == "Time Series Forecast":
        return True
    elif action == "Product Description Generation":
        return True
    elif action == "Text to Shop":
        return True 
    else :
        ai_intent_classifier.reset_messages()
        return False


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
