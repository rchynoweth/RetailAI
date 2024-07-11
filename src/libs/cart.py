# Small module to make a user cart work for the demo
# a simple list of dictionaries should suffice
# example: [{'name': r.name, 'id': r.id, 'description': r.description, 'company_name': r.company_name }]


global cart_items 
cart_items = []


def add_item(item):
    # global cart_items
    cart_items.append(item)


def empty_cart():
    # global cart_items 
    global cart_items
    cart_items = []
