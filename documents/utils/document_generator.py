from io import BytesIO
from typing import Dict, Any, Optional, Tuple, List, Union
import os
import logging
from reportlab.lib.pagesizes import A4
from pathlib import Path

logger = logging.getLogger(__name__)

class ResumeDocumentGenerator:
    """
    Unified document generator that works with the template registry to create 
    resume documents in various formats.
    """
    
    def __init__(self, template_registry):
        """
        Initialize with a template registry.
        
        Args:
            template_registry: Registry containing available templates
        """
        self.template_registry = template_registry
        self.validators = {}  # Data validators for different template types
    
    def register_validator(self, template_type: str, validator_class) -> None:
        """Register a data validator for a specific template type."""
        self.validators[template_type] = validator_class
    
    def generate_resume(self, 
                       template_id: str, 
                       user_data: Dict[str, Any], 
                       custom_options: Optional[Dict[str, Any]] = None,
                       output_path: Optional[str] = None,
                       output_format: str = 'pdf') -> Union[BytesIO, str]:
        """
        Generate a resume using the specified template and options.
        
        Args:
            template_id: ID of the template to use
            user_data: User resume data
            custom_options: Optional custom template options
            output_path: Optional path to save the output
            output_format: Output format (pdf, docx, html)
            
        Returns:
            BytesIO buffer containing the generated document or path to saved file
            
        Raises:
            ValueError: If validation fails or template not found
            RuntimeError: If document generation fails
        """
        try:
            # Get template configuration
            template_config = self.template_registry.get_template(template_id)
            template_class = template_config['class']
            document_class = template_config['document_class']
            metadata = template_config['metadata']
            
            # Apply any custom options
            if custom_options:
                # Create a customized template
                custom_id = self.template_registry.customize_template(template_id, custom_options)
                template_config = self.template_registry.get_template(custom_id)
                metadata = template_config['metadata']
            
            # Validate data if a validator is registered for this template type
            template_type = metadata.get('layout', 'standard')
            if template_type in self.validators:
                validator = self.validators[template_type]
                validated_data = validator.normalize(user_data)
                if not validator.validate(validated_data):
                    raise ValueError("Resume data validation failed")
            else:
                validated_data = user_data
            
            # Determine output handling
            buffer = None
            if not output_path:
                buffer = BytesIO()
                output_target = buffer
            else:
                # Ensure directory exists
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                output_target = output_path
            
            # Create template instance
            template = template_class(validated_data, metadata)
            
            # Handle different output formats
            if output_format.lower() == 'pdf':
                result = template.generate(output_target)
            elif output_format.lower() == 'docx':
                # For future implementation of DOCX export
                raise NotImplementedError("DOCX format not yet implemented")
            elif output_format.lower() == 'html':
                # For future implementation of HTML export
                raise NotImplementedError("HTML format not yet implemented")
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            if buffer:
                buffer.seek(0)
                return buffer
            else:
                return output_path
                
        except KeyError as e:
            error_msg = f"Missing required field in template configuration: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error generating resume: {e}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)
    
    def generate_preview(self, 
                        template_id: str, 
                        sample_data: Optional[Dict[str, Any]] = None,
                        output_format: str = 'pdf') -> BytesIO:
        """
        Generate a preview of a template with sample data.
        
        Args:
            template_id: ID of the template to preview
            sample_data: Optional sample data (uses defaults if not provided)
            output_format: Format of the preview (pdf, png)
            
        Returns:
            BytesIO buffer containing the preview
        """
        # Use default sample data if none provided
        if not sample_data:
            sample_data = self._get_sample_data()
        
        # Generate PDF first
        pdf_buffer = self.generate_resume(template_id, sample_data)
        
        if output_format.lower() == 'pdf':
            return pdf_buffer
        
        elif output_format.lower() == 'png':
            # Convert PDF to PNG for thumbnail generation
            # This would typically use a library like pdf2image, wand, or call an external service
            try:
                from pdf2image import convert_from_bytes
                
                images = convert_from_bytes(pdf_buffer.getvalue(), dpi=72)
                # Take just the first page
                if images:
                    first_page = images[0]
                    img_buffer = BytesIO()
                    first_page.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    return img_buffer
                else:
                    raise RuntimeError("Failed to convert PDF to image")
            except ImportError:
                logger.warning("pdf2image not installed, returning PDF instead")
                return pdf_buffer
        else:
            raise ValueError(f"Unsupported preview format: {output_format}")
    
    def _get_sample_data(self) -> Dict[str, Any]:
        """Get standard sample data for previews."""
        return {
            'contact': {
                'name': 'Alex Johnson',
                'title': 'Senior Software Engineer',
                'email': 'alex.johnson@example.com',
                'phone': '(555) 123-4567',
                'location': 'San Francisco, CA'
            },
            'summary': {
                'content': 'Experienced software engineer with 8+ years developing scalable applications and leading development teams. Specialized in cloud architecture and backend systems with a focus on performance optimization.'
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
    
    def get_available_formats(self) -> List[str]:
        """Returns the list of available export formats."""
        return ['pdf', 'html', 'docx']  # Add formats as they're implemented