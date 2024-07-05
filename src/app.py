# import os 
# os.chdir('./src')

import logging 
import re

import dash
from dash import html, Input, Output, State, dcc
import dash_bootstrap_components as dbc

from layouts.index import index_layout

from langchain_core.messages import HumanMessage, AIMessage


from libs.chat_model import RetailLLM
from libs.file_handler import *

from libs.timeseries import *



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

tools = [
    ForecastTool()
]

retail_ai_system_message = "You are a master or retail analytics and busines processes. You have the ability to analyze data files and images. Do not ask the user for more information. The information in the metadata tags is to be treated as extra information for your analysis, do not reference the tags to the user. Do not attempt to do the skill, just provide a summary of the action. You possess the following skills and assume that you have the all required information to take action. "
for t in tools:
    retail_ai_system_message += f"Name: {t.name} | Descrption: {t.description}\n"

retail_ai_system_message += " If the requested task of information falls into the 'Other' category, then please respond that you cannot assist and you are not liable for any responses."
retail_llm = RetailLLM(system_message=retail_ai_system_message)
retail_llm.tools = tools
retail_llm.reset_chat_history()
chat_history = []

ai_intent_system_message = "The following tools are available. Please select one based on the message history provided. Please assume all required information is provided and select a tool by responding only with the name. "
for t in retail_llm.tools:
    ai_intent_system_message += f"Name: {t.name} | Descrption: {t.description}\n"

ai_intent_classifier = RetailLLM(system_message=ai_intent_system_message)


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
    [Input("send-button", "n_clicks"), Input("input-message", "n_submit")],
    [State("input-message", "value"), State("store-chat-history", "data"), State('upload-file', 'filename'), State('upload-file', 'contents')],
)
def update_chat(n_clicks, n_submit, new_message, chat_history, file_name, file_content):
    logger.info("Updating the Chat.")

    # Do nothing if there is no valid text input from the user
    display_check = ((n_clicks is None or n_clicks == 0) and (n_submit is None or n_submit == 0)) or (new_message is None or new_message.strip() == "")
    if display_check:
        return chat_history, None
    

    if file_content is not None:
        metadata, img = determine_intent(chat_history=chat_history, file_content=file_content)
    else : 
        metadata, img = determine_intent(chat_history=chat_history, file_content=None)

    msg = new_message + f"<metadata>Please use the following in summarization. {metadata}</metadata>" if metadata is not None else new_message
    # Add the user message to the client chat
    retail_llm.add_message(HumanMessage(msg))

    # Get bot response and add it to chat history
    bot_message = retail_llm.send_chat()
    retail_llm.add_message(bot_message)


    # Return updated chat history and forecast image
    if img is not None:
        return chat_history, dcc.Graph(id='graph-content', figure=img)
    else :
        return chat_history, None


# Callback to render the chat history
@app.callback(Output("chat-history", "children"),
              [Input("store-chat-history", "data")])
def display_chat(_):
    """Displays the chat history between the user and the assistant. 

    Args:
        chat_history (list): List of dictionaries with alternating assistant and user text. 

    Returns:
        list: List of dictionaries containing user and assistant chat messages
    """
    logger.info("Displaying the chat")
    # Define the regular expression pattern to match the metadata tags and their content
    pattern = r'<metadata>.*?</metadata>'
    
    messages = []
    for msg in retail_llm.chat_history:
        if isinstance(msg, HumanMessage):
            messages.append(html.Div(re.sub(pattern, '', msg.content, flags=re.DOTALL) , style={"background-color": "#dff0d8", "padding": "5px", "border-radius": "5px", "margin-bottom": "5px", "white-space": "pre-wrap"}))
        elif isinstance(msg, AIMessage):
            messages.append(html.Div(re.sub(pattern, '', msg.content, flags=re.DOTALL), style={"background-color": "#f2dede", "padding": "5px", "border-radius": "5px", "margin-bottom": "5px", "white-space": "pre-wrap"}))
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


# def handle_file(file_content=None, file_name=""):
#     # Check file type validity
#     if not check_file_type(file_name=file_name)[0]:
#         return None
#     # Check if a file was uploaded
#     elif file_content is not None:
#         file_bytes = file_content.split(",")[1]
#         logger.info("File Contents: %s | %s", file_bytes[:10], file_name)
#         retail_llm.edit_system_message("", True)
        



#     return None


def determine_intent(chat_history, file_content):
    # ask the AI which action to take based on chat history
    # may need to change system prompt
    ai_intent_classifier.add_message(HumanMessage(str(chat_history)))
    user_intent = ai_intent_classifier.send_chat().content.replace("'","")
    logger.info("---------> INTENT CLASSIFICATION: '%s'", user_intent)
    ai_intent_classifier.reset_chat_history()
    assert user_intent in ['Forecast Generation Tool', 'Product Description Generation', 'Other', '', None]
    
    if user_intent == "Forecast Generation Tool" and file_content is not None:
        # Generate forecast and image
        file_bytes = file_content.split(",")[1]
        forecast, forecast_image = ForecastTool.run(input_bytes=file_bytes) 
        return_metadata = ForecastTool.evaluate_forecasts(forecast)
        # Convert figure to HTML representation
        # forecast_image = dcc.Graph(figure=fig)
        logger.info("%s", forecast.head(5))
        return return_metadata, forecast_image
    elif user_intent == "Product Description Generation":
        return True
    elif user_intent == "Text to Shop":
        return True 
    else :
        return "No skill selected.", None


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
