from dash import html, dcc
import dash_bootstrap_components as dbc


# Sidebar layout
sidebar = html.Div(
    [
        html.H6("Databricks", className="display-7"),
        html.Hr(),
        html.Button("View Cart", id="cart-button", className="btn btn-primary mb-2"),
        html.Div(id="cart-contents")
    ],
    style={
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "16rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    }
)

# Main content layout
main_content = html.Div(
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
            },
            multiple=False
        ),
        html.Div(id='output-image', style={'width': '100%', 'display': 'inline-block', 'textAlign': 'center', 'margin-top': '10px'}),
        dcc.Store(id="store-chat-history", data=[], storage_type='session'),
        html.Div(id='page-load-trigger', style={'display': 'none'}),
        dcc.Location(id='url', refresh=False),
    ]
)

index_layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(sidebar, width=2),
                dbc.Col(main_content, width=10),
            ]
        ),
        dcc.Store(id="store-cart", data=[]),
        dcc.Store(id="store-show-cart", data=False),
    ]
)
