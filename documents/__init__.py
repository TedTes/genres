# documents/__init__.py
from pathlib import Path
import os
import logging

# Setup package structure
ROOT_DIR = Path(__file__).parent
CONFIG_DIR = ROOT_DIR / "templates" / "config"

# Ensure important directories exist
os.makedirs(ROOT_DIR / "core", exist_ok=True)
os.makedirs(ROOT_DIR / "templates" / "classic_one_column", exist_ok=True)
os.makedirs(ROOT_DIR / "utils", exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import core modules
try:
    from documents.core.base_resume_template import BaseResumeTemplate
    from documents.core.resume_document_base import ResumeDocumentBase
    from documents.core.resume_data_validator import ResumeDataValidator
    from documents.core.section_processor import SectionProcessor
except ImportError as e:
    logger.error(f"Error importing core modules: {e}")

# Import template classes
try:
    from documents.templates.classic_one_column.document import ClassicOneColumnDocument
    from documents.templates.classic_one_column.template import ClassicOneColumnTemplate
    
    # Try to import other templates if available
    try:
        from documents.templates.modern_two_column.document import ModernTwoColumnDocument
        from documents.templates.modern_two_column.template import ModernTwoColumnTemplate
    except ImportError:
        logger.warning("Modern two-column template not available")
    
    try:
        from documents.templates.minimal_sidebar.document import MinimalResumeDocument
        from documents.templates.minimal_sidebar.template import MinimalTemplate
    except ImportError:
        logger.warning("Minimal sidebar template not available")
        
except ImportError as e:
    logger.error(f"Error importing template modules: {e}")

# Import utility classes
try:
    from documents.utils.template_registry import TemplateRegistry
    from documents.utils.document_generator import ResumeDocumentGenerator
except ImportError as e:
    logger.error(f"Error importing utility modules: {e}")

logger.info("Documents package initialized")