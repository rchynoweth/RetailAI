import os
import glob
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
from libs.product_description import *
from libs.text_to_shop import *
import libs.cart as cart



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# remove old asset files
assets_dir = './src/assets/*'
files = glob.glob(assets_dir)
for f in files:
    os.remove(f)


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
    ForecastTool(),
    ProductDescriptionTool(),
    Text2ShopTool(),
]

retail_ai_system_message = "You are a master or retail analytics and busines processes. You have the ability to analyze data files and images. Do not ask the user for more information. The information in the metadata tags is to be treated as extra information for your analysis, do not reference the tags to the user. If the requested task of information falls into the 'Other' category, then please respond that you cannot assist and you are not liable for any responses. Provide detailed and robust answers in the chat."
retail_llm = RetailLLM(system_message=retail_ai_system_message, tools=tools)
retail_llm.tools = tools
logger.info("Resetting chat history.")
retail_llm.reset_chat_history()



# Callback to reset some objects on the page. 
# We do not retain session upon refresh for the demo
@app.callback(
    [Input('url', 'pathname')]
)
def reset_on_load(_):
    """Resets 'session' objects whenever the web page is refreshed. 
    """
    retail_llm.reset_chat_history()
    cart.empty_cart()
    


# Callback to update chat history when the send button is clicked or Enter key is pressed
# main orchestrator of events 
@app.callback(
    [Output("store-chat-history", "data"), Output("output-image", "children")],
    [Input("send-button", "n_clicks"), Input("input-message", "n_submit")],
    [State("input-message", "value"), State("store-chat-history", "data"), State('upload-file', 'filename'), State('upload-file', 'contents')],
)
def update_chat(n_clicks, n_submit, new_message, chat_history, file_name, file_content):
    """_summary_

    Args:
        n_clicks (int): number of clicks on the submit button
        n_submit (int): number of times the user has hit enter
        new_message (str): the most recent input from the user
        chat_history (list): the total chat history
        file_name (str): the name of the file that is uploaded 
        file_content (str): the bytes of the file stored as a string

    Returns:
        tuple: returns the chat history and the image to display if there is one. 
    """
    logger.info("Updating the Chat.")

    # if a file is uploaded then we want to move it to the tmp location for processing in tools
    if file_content is not None:
        logger.info("Saving uploaded file.")
        file_bytes = file_content.split(",")[1]
        save_file_upload(input_file_name=file_name, file_bytes=file_bytes)

    # Do nothing if there is no valid text input from the user
    display_check = ((n_clicks is None or n_clicks == 0) and (n_submit is None or n_submit == 0)) or (new_message is None or new_message.strip() == "")
    if display_check:
        return chat_history, None

    # Add the user message to the client chat
    chat_history = chat_history or []
    retail_llm.add_message(HumanMessage(new_message))

    # Get bot response and add it to chat history
    bot_message = retail_llm.send_chat(msg=new_message)
    retail_llm.add_message(AIMessage(bot_message))

    logger.info("Cart: %s", cart.cart_items)

    # Return updated chat history and image if there was a file uploaded. 
    # the only time we display an image is if the user provides a file (image or data)
    if file_content is not None:
        image_list = os.listdir('./src/assets')
        image_list.sort()
        latest_image = image_list[-1]
        logger.info("Display Image %s", latest_image)
        return chat_history, html.Img(src=f'/assets/{latest_image}') 
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
    # we can use this tags to provide additional information to the LLM without the user knowing
    # i.e. system prompt engineering
    pattern = r'<metadata>.*?</metadata>'

    # loop through the stored chat history in the llm class object and display with different colors
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



@app.callback(
    [Output("cart-contents", "children"), Output("store-show-cart", "data")],
    [Input("cart-button", "n_clicks")],
    [State("store-show-cart", "data"), State("store-cart", "data")]
)
def toggle_cart(n_clicks, show_cart, _):
    """Displays or hides the contents of the user's cart. 

    Args:
        n_clicks (int): Number of times the 'view cart' button was clicked.
        show_cart (bool): whether or not to display the car in the side bar. 

    Returns:
        _type_: _description_
    """
    logger.info("Displaying Cart Contents.")
    if n_clicks is None:
        logger.info("Cart Clicks is None")
        return "", show_cart
    
    if cart.cart_items != []:
        cart_items = [
            html.Div(
                [
                    html.H5(f"Product: {item['name']}"),
                    html.P(f"Quantity: {item['quantity']}"),
                    html.P(f"Description: {item['description']}"),
                    html.P(f"Company: {item['company_name']}"),
                    html.Hr()
                ]
            ) for item in cart.cart_items
        ]
        return cart_items, show_cart
    else:
        return "", show_cart



# Run the app in debug mode
if __name__ == "__main__":
    app.run_server(debug=True)
