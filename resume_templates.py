
RESUME_TEMPLATES = {
    "standard": {
        "template_id": 1,
        "name": "Standard",
        "description": "Clean and professional template suitable for most industries",
        "preview_image": "templates/standard.png",
        "css_class": "template-standard",
        "color": "#3b82f6",  # Blue
        "font_family": "Helvetica",
        "supports_photo": True
    },
    "modern": {
        "template_id": 2,
        "name": "Modern",
        "description": "Sleek, contemporary design with accent colors",
        "preview_image": "templates/modern.png",
        "css_class": "template-modern",
        "color": "#10b981",  # Green
        "font_family": "Helvetica",
        "supports_photo": True
    },
    "minimal": {
        "template_id": 3,
        "name": "Minimal",
        "description": "Simple, minimalistic design focusing on content",
        "preview_image": "templates/minimal.png",
        "css_class": "template-minimal",
        "color": "#4b5563",  # Gray
        "font_family": "Helvetica",
        "supports_photo": False
    },
    "executive": {
        "template_id": 4,
        "name": "Executive",
        "description": "Traditional format ideal for senior positions",
        "preview_image": "templates/executive.png",
        "css_class": "template-executive",
        "color": "#1e40af",  # Dark Blue
        "font_family": "Times-Roman",
        "supports_photo": True
    },
    "creative": {
        "template_id": 5,
        "name": "Creative",
        "description": "Bold design for creative industries and portfolios",
        "preview_image": "templates/creative.png",
        "css_class": "template-creative",
        "color": "#ec4899",  # Pink
        "font_family": "Helvetica",
        "supports_photo": True
    },
    "technical": {
        "template_id": 6,
        "name": "Technical",
        "description": "Structured layout optimized for technical roles and skills",
        "preview_image": "templates/technical.png",
        "css_class": "template-technical",
        "color": "#6366f1",  # Indigo
        "font_family": "Helvetica",
        "supports_photo": False
    }
}

# Template feature information
TEMPLATE_FEATURES = {
    "standard": {
        "layout": "Traditional single-column layout",
        "header": "Centered contact information",
        "sections": "Clearly defined sections with blue headings",
        "best_for": "Most professional fields and experience levels"
    },
    "modern": {
        "layout": "Two-column layout with sidebar",
        "header": "Left-aligned with accent color",
        "sections": "Clean section dividers with subtle color accents",
        "best_for": "Technology, marketing, and design roles"
    },
    "minimal": {
        "layout": "Streamlined single-column layout",
        "header": "Compact header with minimal styling",
        "sections": "No dividers, focuses on content spacing",
        "best_for": "Academic positions and research roles"
    },
    "executive": {
        "layout": "Formal single-column layout with wider margins",
        "header": "Centered name with traditional styling",
        "sections": "Underlined section headings",
        "best_for": "Senior management, C-suite, and legal professions"
    },
    "creative": {
        "layout": "Dynamic layout with asymmetric elements",
        "header": "Bold name display with accent colors",
        "sections": "Creative section styling with visual elements",
        "best_for": "Design, arts, and media positions"
    },
    "technical": {
        "layout": "Structured layout with emphasis on skills section",
        "header": "Compact header with optional GitHub/portfolio links",
        "sections": "Technical skills given visual prominence",
        "best_for": "Software engineering, data science, and IT roles"
    }
}
def get_template_info(template_id):
    """Get detailed information about a specific template."""
    template = RESUME_TEMPLATES.get(template_id, RESUME_TEMPLATES["standard"])
    features = TEMPLATE_FEATURES.get(template_id, TEMPLATE_FEATURES["standard"])
    
    return {
        **template,
        "features": features
    }

def get_all_templates():
    """Return all templates with their features."""
    result = {}
    for template_id, template in RESUME_TEMPLATES.items():
        result[template_id] = {
            **template,
            "features": TEMPLATE_FEATURES.get(template_id, {})
        }
    return result