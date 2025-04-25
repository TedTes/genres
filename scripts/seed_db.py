from app import app, db
from models import Theme, Layout

with app.app_context():
    # Clear existing data (optional)
    db.session.query(Theme).delete()
    db.session.query(Layout).delete()

    # Insert themes
    professional = Theme(
        id='professional',
        name='Professional',
        colors={
            'primary': '#2c3e50',
            'secondary': '#3498db',
            'text': '#ffffff',
            'text_light': '#cccccc',
            'background': '#000000',
            'accent': '#e74c3c',
            'border': '#dddddd'
        },
        typography={
            'font_family': "'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif",
            'heading_family': "'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif",
            'base_size': '14px',
            'line_height': '1.6',
            'heading_weight': '600'
        }
    )
    modern = Theme(
        id='modern',
        name='Modern',
        colors={
            'primary': '#1a3c34',
            'secondary': '#f4a261',
            'text': '#222222',
            'text_light': '#555555',
            'background': '#f5f6f5',
            'accent': '#e76f51',
            'border': '#cccccc'
        },
        typography={
            'font_family': "'Roboto', 'Helvetica Neue', Helvetica, Arial, sans-serif",
            'heading_family': "'Roboto', 'Helvetica Neue', Helvetica, Arial, sans-serif",
            'base_size': '15px',
            'line_height': '1.7',
            'heading_weight': '700'
        }
    )
    db.session.add_all([professional, modern])

    # Insert layouts
    classic = Layout(
        id='classic',
        name='Classic',
        description='Traditional single-column layout',
        template='classic.html',
        css_file='css/layouts/classic.css'
    )
    db.session.add(classic)

    db.session.commit()
    print("Database seeded successfully!")