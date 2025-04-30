

from models import Theme

def get_theme(theme_id):
    """Retrieve theme data by ID."""
    theme = Theme.query.get(theme_id)
    return theme.__dict__ if theme else Theme.query.get('professional').__dict__

def generate_theme_css(theme):
    """Generate CSS custom properties from theme data."""
   
    css = ":root {\n"
    for key, value in theme["colors"].items():
        css += f"  --{key}: {value};\n"
    for key, value in theme["typography"].items():
        css += f"  --{key.replace('_', '-')}: {value};\n"
    css += "}\n"
    return css