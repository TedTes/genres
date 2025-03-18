from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, FrameBreak, PageBreak, BaseDocTemplate, Image
from reportlab.lib.units import inch, mm
from io import BytesIO
import json
import os
import copy

from base_resume_template import BaseResumeTemplate
from classic_one_column_document import ClassicOneColumnDocument
from classic_one_column_template import ClassicOneColumnTemplate
from minimal_resume_document import MinimalResumeDocument
from minimal_template import MinimalTemplate
from modern_two_column_document import ModernTwoColumnDocument
from modern_two_column_template import ModernTwoColumnTemplate
from resume_data_validator import ResumeDataValidator
from resume_document_base import ResumeDocumentBase
from resume_template_registry import ResumeTemplateRegistry
from section_processor import SectionProcessor

def load_template_config(config_file):
    """Load template configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading template config {config_file}: {e}")
        return {}


def get_sample_data():
    """Get standard sample data for previews"""
    return {
        'contact': {
            'name': 'John Smith',
            'title': 'Senior Software Engineer',
            'email': 'john.smith@example.com',
            'phone': '(555) 123-4567',
            'location': 'San Francisco, CA'
        },
        'experience': [
            {
                'title': 'Senior Software Engineer',
                'company': 'Tech Innovations Inc.',
                'startDate': 'Jan 2020',
                'current': True,
                'description': 'Led development of cloud-based applications using AWS\nImplemented CI/CD pipelines resulting in 40% faster deployments\nMentored junior developers and conducted code reviews'
            },
            {
                'title': 'Software Developer',
                'company': 'Data Systems LLC',
                'startDate': 'Mar 2017',
                'endDate': 'Dec 2019',
                'description': 'Developed RESTful APIs using Node.js and Express\nOptimized database queries improving performance by 30%\nCollaborated with UX team to implement responsive frontend'
            }
        ],
        'education': [
            {
                'degree': 'Master of Science in Computer Science',
                'school': 'Stanford University',
                'year': '2017'
            },
            {
                'degree': 'Bachelor of Science in Software Engineering',
                'school': 'University of California, Berkeley',
                'year': '2015'
            }
        ],
        'skills': 'JavaScript, Python, React, Node.js, AWS, Docker, Kubernetes, CI/CD, Git, Agile Methodologies',
        'languages': 'English (Native), Spanish (Intermediate), French (Basic)',
        'certifications': 'AWS Certified Solutions Architect, Google Cloud Professional Developer'
    }


def create_resume(template_id, user_data, output_path=None):
    """Factory function to create a resume using a specific template"""
    # Get template from registry
    template_info = template_registry.get_template(template_id)
    template_class = template_info['class']
    template_metadata = template_info['metadata']
    
    # Create template instance
    template = template_class(user_data, template_metadata)
    
    # Generate resume
    return template.generate(output_path)


def customize_template(template_id, options):
    """Update template with custom options"""
    template = template_registry.get_template(template_id)
    
    # Apply customizations to template metadata
    for key, value in options.items():
        if key == 'colors':
            # Update colors
            for color_key, color_value in value.items():
                template['metadata']['colors'][color_key] = color_value
        elif key == 'fonts':
            # Update fonts
            for font_key, font_value in value.items():
                template['metadata']['fonts'][font_key] = font_value
        elif key == 'margins':
            # Update margins
            for margin_key, margin_value in value.items():
                template['metadata']['margins'][margin_key] = margin_value
        else:
            # General metadata update
            template['metadata'][key] = value
    
    return template_id


def generate_preview(template_id, sample_data=None):
    """Generate a preview image of the template"""
    # Use a standard sample data if none provided
    if sample_data is None:
        sample_data = get_sample_data()
    
    # Generate a PDF first
    pdf_buffer = create_resume(template_id, sample_data)
    
    # In a real implementation, you would convert the PDF to an image here
    # using a library like pdf2image, Pillow, or a cloud service
    # For now, we'll just return the PDF buffer
    return pdf_buffer


def generate_resume(template_id, user_data, custom_options=None, output_path=None):
    """Generate a resume PDF with the specified template and options"""
    try:
        # Validate and normalize data
        ResumeDataValidator.validate(user_data)
        normalized_data = ResumeDataValidator.normalize(user_data)
        
        # Apply any custom options to the template
        if custom_options:
            customize_template(template_id, custom_options)
        
        # Generate the resume
        return create_resume(template_id, normalized_data, output_path)
    except Exception as e:
        print(f"Error generating resume: {e}")
        raise


# Create template configurations
modern_two_column_config = {
    "colors": {
        "primary": [0.1, 0.4, 0.7],  # Blue
        "secondary": [0.2, 0.2, 0.2]  # Dark gray
    },
    "fonts": {
        "name": {"family": "Helvetica-Bold", "size": 26},
        "heading": {"family": "Helvetica-Bold", "size": 14},
        "normal": {"family": "Helvetica", "size": 10}
    },
    "margins": {
        "left": 0.5,
        "right": 0.5,
        "top": 0.5,
        "bottom": 0.5
    },
    "layout": "two-column",
    "header_height": 1.5
}

classic_one_column_config = {
    "colors": {
        "primary": [0.0, 0.0, 0.0],  # Black
        "secondary": [0.4, 0.4, 0.4]  # Gray
    },
    "fonts": {
        "name": {"family": "Times-Bold", "size": 20},
        "heading": {"family": "Times-Bold", "size": 14},
        "normal": {"family": "Times-Roman", "size": 10}
    },
    "margins": {
        "left": 1.0,
        "right": 1.0,
        "top": 1.0,
        "bottom": 1.0
    },
    "layout": "one-column",
    "header_height": 2.0
}

minimal_config = {
    "colors": {
        "primary": [0.5, 0.5, 0.5],  # Gray
        "secondary": [0.2, 0.2, 0.2],  # Dark gray 
        "background": [0.95, 0.95, 0.95]  # Light gray for sidebar
    },
    "fonts": {
        "name": {"family": "Helvetica-Bold", "size": 20},
        "heading": {"family": "Helvetica-Bold", "size": 12},
        "normal": {"family": "Helvetica", "size": 9}
    },
    "margins": {
        "left": 0.4,
        "right": 0.4,
        "top": 0.5,
        "bottom": 0.5
    },
    "layout": "sidebar",
    "sidebar_width": 0.3
}
# Examples of additional professional template styles:


# Initialize template registry
template_registry = ResumeTemplateRegistry()
# Executive Template
# template_registry.register_template(
#     'executive-premium', 
#     ExecutiveTemplate,
#     {
#         "colors": {
#             "primary": [0.2, 0.2, 0.4],  # Navy blue
#             "secondary": [0.6, 0.3, 0.1]  # Copper accent
#         },
#         "fonts": {
#             "name": {"family": "Times-Bold", "size": 24},
#             "heading": {"family": "Times-Bold", "size": 16},
#             "normal": {"family": "Times-Roman", "size": 11}
#         },
#         "layout": "executive",
#         "paper": "letter",
#         "margins": {"top": 0.75, "bottom": 0.75, "left": 1.0, "right": 1.0}
#     }
# )

# Creative Modern
# template_registry.register_template(
#     'creative-modern', 
#     CreativeTemplate,
#     {
#         "colors": {
#             "primary": [0.2, 0.5, 0.7],  # Blue
#             "secondary": [0.7, 0.3, 0.5],  # Magenta
#             "tertiary": [0.9, 0.7, 0.2]   # Gold
#         },
#         "fonts": {
#             "name": {"family": "Helvetica-Bold", "size": 30},
#             "heading": {"family": "Helvetica-Bold", "size": 14},
#             "normal": {"family": "Helvetica", "size": 10}
#         },
#         "layout": "asymmetric",
#         "graphic_elements": True
#     }
# )

# Register templates
template_registry.register_template(
    'modern-two-column', 
    ModernTwoColumnTemplate,
    modern_two_column_config
)

template_registry.register_template(
    'classic-one-column', 
    ClassicOneColumnTemplate,
    classic_one_column_config
)

template_registry.register_template(
    'minimal-sidebar', 
    MinimalTemplate,
    minimal_config
)


def test_resume_system():
    """Test the resume template system"""
    import os
    
    # Test with sample data
    sample_data = get_sample_data()
    
    # Test each template
    for template_id in ['modern-two-column', 'classic-one-column', 'minimal-sidebar']:
        # Generate resume with default options
        output_file = f"{template_id.replace('-', '_')}_resume.pdf"
        
        try:
            with open(output_file, 'wb') as f:
                generate_resume(template_id, sample_data, output_path=f)
            
            # Check if file was created
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✅ Successfully generated {template_id} resume: {output_file} ({file_size} bytes)")
            else:
                print(f"❌ Failed to generate {template_id} resume")
        except Exception as e:
            print(f"❌ Error generating {template_id} resume: {str(e)}")
    
    # Test template customization
    try:
        # Customize the modern template with different colors
        custom_options = {
            "colors": {
                "primary": [0.2, 0.6, 0.3]  # Green instead of blue
            },
            "fonts": {
                "heading": {"family": "Helvetica-Bold", "size": 16}  # Larger headings
            }
        }
        
        output_file = "custom_modern_resume.pdf"
        with open(output_file, 'wb') as f:
            generate_resume('modern-two-column', sample_data, custom_options, f)
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ Successfully generated customized resume: {output_file} ({file_size} bytes)")
        else:
            print(f"❌ Failed to generate customized resume")
    except Exception as e:
        print(f"❌ Error generating customized resume: {str(e)}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    test_resume_system()