import os 
# os.chdir('./src')

import logging 
import re

import dash
from dash import html, Input, Output, State
import dash_bootstrap_components as dbc

from layouts.index import index_layout

from langchain_core.messages import HumanMessage, AIMessage

from libs.chat_model import RetailLLM
from libs.file_handler import *

from libs.timeseries import *



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


# Initialize the Dash app
logger.info("Initialize the Dash app.")
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Application layout
app.layout = dbc.Container(
    [
     index_layout,
    ],
    fluid=True,
)


# create LLM objects 
logger.info("Creating LLM Objects.")
tools = [
    ForecastTool()
]

retail_ai_system_message = "You are a master or retail analytics and busines processes. You have the ability to analyze data files and images. Do not ask the user for more information. The information in the metadata tags is to be treated as extra information for your analysis, do not reference the tags to the user. If the requested task of information falls into the 'Other' category, then please respond that you cannot assist and you are not liable for any responses."
retail_llm = RetailLLM(system_message=retail_ai_system_message, tools=tools)
retail_llm.tools = tools
logger.info("Resetting chat history.")
retail_llm.reset_chat_history()



# Callback to reset chat history on page load
@app.callback(
    [Input('url', 'pathname')]
)
def reset_chat_history_on_load(pathname):
    retail_llm.reset_chat_history()

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
        file_bytes = file_content.split(",")[1]
        save_file_upload(input_file_name=file_name, file_bytes=file_bytes)

    chat_history = chat_history or []
    # Add the user message to the client chat
    retail_llm.add_message(HumanMessage(new_message))

    # Get bot response and add it to chat history
    bot_message = retail_llm.send_chat(msg=new_message)
    retail_llm.add_message(bot_message)

    # Return updated chat history and forecast image
    if os.path.isfile('src/assets/display.png'):
        return chat_history, html.Img(src='/assets/display.png') 
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
    for msg in retail_llm.get_chat_history():
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




# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
