from dash import html, dcc
import dash_bootstrap_components as dbc


index_layout = html.Div(
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
        html.Div(id='output-image', style={'width': '100%', 'display': 'inline-block', 'textAlign': 'center', 'margin-top': '10px'}),
# dcc.Graph(id='graph-content'),
        dcc.Store(id="store-chat-history", data=[]),
    ]
)