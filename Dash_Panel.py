import panel as pn

pn.extension()

def hello():
    return "Hello, Panel!"

pn.serve(pn.panel(hello), port=8000, address="0.0.0.0")
