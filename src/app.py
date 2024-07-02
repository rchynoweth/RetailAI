import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import logging 
from libs.db_ai_client import DBAIClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

db_ai_client = DBAIClient()
db_ai_client.reset_messages()

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Application layout
app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(html.H1("RetailChat AI"), className="text-center mb-4")),
        dbc.Row(
            dbc.Col(
                html.Div(
                    id="chat-history",
                    style={"width": "100%", "height": "300px", "overflowY": "scroll", "border": "1px solid #ccc", "padding": "10px"},
                ),
                className="mb-4",
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Input(
                        id="input-message",
                        type="text",
                        placeholder="Type your message here...",
                        style={"width": "100%"},
                        n_submit=0,
                    ),
                    width=10,
                ),
                dbc.Col(
                    dbc.Button(
                        "Send", id="send-button", color="primary", className="w-100"
                    ),
                    width=2,
                ),
            ],
            className="mb-2",
        ),
        dcc.Upload(
            id='upload-file',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select File')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin-top': '10px'
                # 'margin': '10px'
            },
            # Allow multiple files to be uploaded
            multiple=False
        ),
        dcc.Store(id="store-chat-history", data=[]),
    ],
    fluid=True,
)


# Callback to update chat history when the send button is clicked or Enter key is pressed
@app.callback(
    Output("store-chat-history", "data"),
    [Input("send-button", "n_clicks"), Input("input-message", "n_submit")],
    [State("input-message", "value"), State("store-chat-history", "data")],
)
def update_chat(n_clicks, n_submit, new_message, chat_history):
    logger.info("Updating the Chat. ")
    if (n_clicks is None or n_clicks == 0) and (n_submit is None or n_submit == 0):
        return chat_history

    if new_message is None or new_message.strip() == "":
        return chat_history
    
    # Add the user message to the client chat
    db_ai_client.add_message('user', new_message)

    chat_history = chat_history or []
    chat_history.append({"sender": "user", "text": new_message})

    bot_message = get_bot_response()
    chat_history.append({"sender": "bot", "text": bot_message})

    return chat_history

# Callback to render the chat history
@app.callback(Output("chat-history", "children"), [Input("store-chat-history", "data")])
def display_chat(chat_history):
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
def clear_input(n_clicks, n_submit):
    logger.info("Clearing the user input text box.")
    return ""


def get_bot_response():
    logger.info("Getting AI Response")
    response = db_ai_client.send_chat()
    bot_response = response.get('choices')[0].get('message').get('content')
    db_ai_client.add_message('assistant', bot_response)
    return bot_response 



# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
