
from models import Layout

def get_layout(layout_id):
    layout = Layout.query.get(layout_id)
    return layout.__dict__ if layout else Layout.query.get('classic').__dict__