// Global state and utilities
const state = {
  autoSaveTimeout: null,
  hasUnsavedChanges: false,
};

// DOM element selectors and event handlers
const selectors = {
  saveButton: '#save-resume-btn',
  iframe: '#preview-iframe',
  templateButton: '.float-control-btn[data-panel="templates-panel"]',
  templatesPanel: '#templates-panel',
  closePanelButtons: '.panel-close',
  aiButton: '#ai-assistant-btn',
  aiModal: '#ai-assistant-modal',
  aiModalClose: '.ai-modal-close',
  tooltipContainers: '.tooltip-container',
  addButtons: '.add-item-btn, .add-tag-btn',
  sectionTags: '.section-tag',
  sectionItems: '.section-item',
};

document.addEventListener('DOMContentLoaded', () => {
  const root = document.documentElement;
  const elements = {
    saveButton: document.querySelector(selectors.saveButton),
    iframe: document.querySelector(selectors.iframe),
    templateButton: document.querySelector(selectors.templateButton),
    templatesPanel: document.querySelector(selectors.templatesPanel),
    closePanelButtons: document.querySelectorAll(selectors.closePanelButtons),
    aiButton: document.querySelector(selectors.aiButton),
    aiModal: document.querySelector(selectors.aiModal),
    aiModalClose: document.querySelector(selectors.aiModalClose),
    tooltipContainers: document.querySelectorAll(selectors.tooltipContainers),
  };

  // Save button handler
  if (elements.saveButton) {
    elements.saveButton.addEventListener('click', saveResume);
  }

  // AI modal handlers
  if (elements.aiButton && elements.aiModal && elements.aiModalClose) {
    elements.aiButton.addEventListener('click', () => {
      if (elements.templatesPanel?.classList.contains('active')) {
        elements.templatesPanel.classList.remove('active');
      }
      elements.aiModal.classList.add('active');
    });

    elements.aiModalClose.addEventListener('click', () => {
      elements.aiModal.classList.remove('active');
    });

    elements.aiModal.addEventListener('click', (e) => {
      if (e.target === elements.aiModal) {
        elements.aiModal.classList.remove('active');
      }
    });
  }

  // Template panel toggle
  if (elements.templateButton && elements.templatesPanel) {
    elements.templateButton.addEventListener('click', () => {
      if (elements.aiModal?.classList.contains('active')) {
        elements.aiModal.classList.remove('active');
      }
      elements.templatesPanel.classList.toggle('active');
    });
  }

  // Tooltip handlers
  elements.tooltipContainers.forEach(container => {
    const tooltip = container.querySelector('.btn-tooltip');
    if (tooltip) {
      container.addEventListener('mouseenter', () => {
        tooltip.style.opacity = '1';
        tooltip.style.visibility = 'visible';
      });
      container.addEventListener('mouseleave', () => {
        tooltip.style.opacity = '0';
        tooltip.style.visibility = 'hidden';
      });
    }
  });

  // Close panels
  elements.closePanelButtons.forEach(button => {
    button.addEventListener('click', () => {
      const panelId = button.getAttribute('data-panel');
      const panel = document.getElementById(panelId);
      if (panel) panel.classList.remove('active');
    });
  });

  // Close panel when clicking outside
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.slide-panel') && !e.target.closest('.float-control-btn') && 
        elements.templatesPanel?.classList.contains('active')) {
      elements.templatesPanel.classList.remove('active');
    }
  });

  // Add button handlers
  document.querySelectorAll(selectors.addButtons).forEach(btn => {
    if (btn.id.startsWith('add-')) {
      const type = btn.id.replace('add-', '').replace('-btn', '');
      btn.addEventListener('click', () => {
        if (type === 'skills') addNewTag(btn);
        else if (type !== 'summary') addNewItem(btn, type);
      });
    }
  });

  // Existing tag and item event listeners
  document.querySelectorAll(selectors.sectionTags).forEach(addTagEventListeners);
  document.querySelectorAll(selectors.sectionItems).forEach(addItemEventListeners);

  // File drop handlers
  document.addEventListener('dragover', (e) => e.preventDefault());
  document.addEventListener('drop', (e) => {
    e.preventDefault();
    alert('File uploads will be supported in a future version.');
  });

  // Input change handler with debouncing
  document.addEventListener('input', debounce((e) => {
    if (e.target.getAttribute('contenteditable') === 'true') {
      state.hasUnsavedChanges = true;
      clearTimeout(state.autoSaveTimeout);
      state.autoSaveTimeout = setTimeout(autoSave, 1500);
    }
  }, 100));

  // Warn before unload
  window.addEventListener('beforeunload', (e) => {
    if (state.hasUnsavedChanges) {
      e.preventDefault();
      e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
      return e.returnValue;
    }
  });

  // Export functions globally
  window.addItemEventListeners = addItemEventListeners;
  window.addTagEventListeners = addTagEventListeners;
  window.addNewTag = addNewTag;
  window.addNewItem = addNewItem;
  window.autoSave = autoSave;

  // Initial auto-save
  setTimeout(autoSave, 3000);

  // Setup iframe listeners
  if (elements.iframe) {
    elements.iframe.addEventListener('load', () => {
      const iframeDoc = elements.iframe.contentDocument || elements.iframe.contentWindow.document;
      setupIframeListeners(iframeDoc);
    });
  }



  // Add PDF preview button handler
  const previewPdfButton = document.querySelector('#preview-pdf-btn');
  if (previewPdfButton) {
    previewPdfButton.addEventListener('click', async () => {
      const resumeId = document.querySelector('.resume-builder')?.dataset.resumeId;
      if (!resumeId) {
        showNotification('Error: Resume ID not found', 'error');
        return;
      }

      // Create and show modal
      const modal = Object.assign(document.createElement('div'), {
        className: 'modal',
        innerHTML: `
          <div class="modal-content">
            <h3>PDF Preview</h3>
            <iframe id="pdf-preview-iframe" style="width: 100%; height: 500px; border: none;"></iframe>
            <button class="btn btn-outline" id="close-preview-btn">Close</button>
          </div>
        `
      });
      document.body.appendChild(modal);

      // Fetch and display preview
      try {
        const response = await fetch(`/api/v1/resume/${resumeId}/preview`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
        const htmlContent = await response.text();
        const previewIframe = modal.querySelector('#pdf-preview-iframe');
        previewIframe.srcdoc = htmlContent;
      } catch (error) {
        showNotification('Error loading PDF preview', 'error');
        document.body.removeChild(modal);
      }

      // Close modal
      modal.querySelector('#close-preview-btn').addEventListener('click', () => {
        document.body.removeChild(modal);
      });
    });
  }
});

// Iframe-specific event setup
function setupIframeListeners(iframeDoc) {
  iframeDoc.querySelectorAll('.section-tag').forEach(addTagEventListeners);
  iframeDoc.addEventListener('input', () => {
    state.hasUnsavedChanges = true;
    clearTimeout(state.autoSaveTimeout);
    state.autoSaveTimeout = setTimeout(autoSave, 3000);
  });
}

// Utility functions
function showSaveStatus(message, isError = false) {
  const saveStatus = document.getElementById('save-status');
  if (saveStatus) {
    saveStatus.textContent = message;
    saveStatus.classList.add('show');
    if (isError) saveStatus.classList.add('error');
    else saveStatus.classList.remove('error');
    setTimeout(() => saveStatus.classList.remove('show'), 3000);
  }
}

async function saveResume() {
  if (!state.hasUnsavedChanges) return;
  const saveButton = window.parent.document.querySelector('#save-resume-btn');
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
  const resumeId = window.parent.document.querySelector('.resume-builder')?.dataset.resumeId;
  const iframe = window.parent.document.querySelector('#preview-iframe');

  if (!saveButton || !resumeId || !iframe) return;
  saveButton.classList.add('saving');

  try {
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    const resumeContent = collectResumeData(iframeDoc);

    await fetch(`/api/v1/resume/${resumeId}/save-data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
      body: JSON.stringify({ resume_data: resumeContent }),
    })
      .then(response => response.json())
      .then(data => {
        saveButton.classList.remove('saving');
        showSaveStatus(data.success ? 'Changes saved successfully!' : 'Error saving changes. Please try again.', true);
        if (data.success) state.hasUnsavedChanges = false;
      })
      .catch(error => {
        console.error('Error saving resume:', error);
        saveButton.classList.remove('saving');
        showSaveStatus('Error saving changes. Please try again.', true);
      });
  } catch (error) {
    console.error('Error collecting resume data:', error);
    saveButton.classList.remove('saving');
    showSaveStatus('Error accessing resume content. Please try again.', true);
  }
}

function collectResumeData(iframeDoc) {
  const resumeData = { contact: {}, sections: [], bio: { name: '', title: '' } };

  resumeData.bio.name = iframeDoc.querySelector('.name')?.textContent || '';
  resumeData.bio.title = iframeDoc.querySelector('.title')?.textContent || '';

  iframeDoc.querySelectorAll('.contact-item').forEach(item => {
    const iconClass = item.querySelector('.contact-icon')?.className;
    const content = item.querySelector('.contact-content')?.textContent;
    if (iconClass && content) {
      const match = iconClass.match(/fa-(\w+)/);
      if (match) resumeData.contact[match[1] === 'envelope' ? 'email' : match[1]] = content;
    }
  });

  // Define known section types
  const knownSectionTypes = [
    'experience', 'education', 'skills', 'summary', 'certification', 
    'project', 'volunteer', 'award', 'publication', 'language'
  ];

  iframeDoc.querySelectorAll('.resume-section').forEach(section => {

    let sectionType = 'custom'; // Default type
    

    if (section.dataset.sectionType) {
      sectionType = section.dataset.sectionType;
    } else {
      // Fall back to class name detection
      const classList = section.className.split(' ');
      
      // Check each class against known section types
      for (const className of classList) {
        const match = className.match(/^(\w+)-section$/);
        if (match && match[1] && knownSectionTypes.includes(match[1])) {
          sectionType = match[1];
          break;
        }
      }
      
      // If  didn't find a known type, try to extract any type from class
      if (sectionType === 'custom') {
        for (const className of classList) {
          const match = className.match(/^(\w+)-section$/);
          if (match && match[1] && match[1] !== 'resume') {
            sectionType = match[1];
            break;
          }
        }
      }
    }

    const sectionTitle = section.querySelector('.section-title')?.textContent.trim();
    const sectionData = { type: sectionType, title: sectionTitle, display: 'list', content: '', items: [] };

    if (section.querySelector('.section-content')) {
      sectionData.display = 'text';
      sectionData.content = section.querySelector('.section-content')?.textContent || '';
    } else if (section.querySelector('.section-container')) {
      sectionData.display = 'tags';
      sectionData.items = Array.from(section.querySelectorAll('.section-tag')).map(tag =>
        tag.textContent.trim().replace(/\s*✓\s*/, '').replace(/\s*×\s*/, '').trim()
      );
    } else {
      sectionData.display = 'list';
      sectionData.items = Array.from(section.querySelectorAll('.section-item')).map(item => {
        const itemData = {};
        
        itemData.id = item.dataset.itemId || `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        item.dataset.itemId = itemData.id;

        item.querySelectorAll('[class^="section-"], [class*=" section-"]').forEach(el => {
          const classes = el.className.split(' ');
          classes.forEach(className => {
            if (className.startsWith('section-')) {
              let key = className.replace('section-', '').replace(/-/g, '_');
              if (sectionType === 'certification' && key === 'degree') key = 'name';
              if (sectionType === 'certification' && key === 'school') key = 'issuer';
              if (sectionType === 'experience' && key === 'date') key = 'duration';
              itemData[key] = (key === 'description' || key === 'duties')
                ? (el.querySelector('.section-duties')
                  ? Array.from(el.querySelectorAll('li')).map(li => li.textContent.trim()).join('\n')
                  : el.textContent.trim())
                : el.textContent.trim();
            }
          });
        });
     
        return itemData;
      });
    }

    resumeData.sections.push(sectionData);
  });

  return resumeData;
}

function addTagEventListeners(tag) {
  const deleteBtn = tag.querySelector('.tag-delete');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async () => {
      tag.remove();
      state.hasUnsavedChanges = true;
      await autoSave();
    });
  }
}

async function addNewTag(button) {
  const tagName = prompt('Enter item name:');
  if (tagName) {
    const tagsContainer = button.parentElement;
    const newTag = Object.assign(document.createElement('span'), {
      className: 'section-tag',
      innerHTML: `<i class="fas fa-check"></i>${tagName}<i class="fas fa-times tag-delete"></i>`,
    });
    tagsContainer.insertBefore(newTag, button);
    addTagEventListeners(newTag);
    state.hasUnsavedChanges = true;
    await autoSave();
  }
}



function addItemEventListeners(item) {
  
  console.log('Item listener initialized');

  const deleteBtn = item.querySelector('.item-btn.delete');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const itemId = item.dataset.itemId || item.id?.replace('item-', '');
   

      if (!confirm('Are you sure you want to delete this item?')) return;

      const sectionType = item.closest('.resume-section')?.dataset.sectionType;
      if (!sectionType) {
        console.error('Section type not found');
        showNotification('Error: Section type not found', 'error');
        return;
      }

      const resumeContainer = document.querySelector('.resume-builder') || (window.parent?.document?.querySelector('.resume-builder'));
      const resumeId = resumeContainer?.dataset.resumeId;
      if (!resumeId) {
        console.error('Resume ID not found');
        showNotification('Error: Resume ID not found', 'error');
        return;
      }

      if (!itemId) {
        console.error('Item ID not found');
        showNotification('Error: Item ID not found', 'error');
        return;
      }

      try {
        const response = await fetch(`/api/v1/resume/${resumeId}/section/${sectionType}/item/${itemId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '',
          },
        });

        const data = await response.json();
        if (response.ok) {
          item.remove();
          showNotification('Item deleted successfully', 'success');
        } else {
          showNotification(`Failed to delete item: ${data.message || 'Unknown error'}`, 'error');
        }
      } catch (error) {
        console.error('Delete error:', error);
        showNotification('Error deleting item', 'error');
      }
    });
  }
}

// Debounce utility
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
      <div class="notification-content">
        <div class="notification-message">${message}</div>
        <button class="notification-close">&times;</button>
      </div>
    `;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
      notification.classList.add('show');
    }, 10);
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
    
    // Close button functionality
    notification.querySelector('.notification-close').addEventListener('click', () => {
      notification.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    });
}



// Enhanced Add New Item Function with Animations and Professional UX
function addNewItem(button, type) {
  const section = button.parentElement;
  const newItem = document.createElement('div');
  newItem.className = 'section-item new-item-animation';
  
  const uniqueId = generateUniqueId();
  newItem.dataset.itemId = uniqueId;
  newItem.id = `item-${uniqueId}`;
  
  // Professional loading state for button
  const originalButtonContent = button.innerHTML;
  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
  button.disabled = true;
  
  // Enhanced item templates with professional structure
  const templates = {
    experience: {
      icon: 'fas fa-briefcase',
      fields: [
        { key: 'job_title', label: 'Job Title', icon: 'fas fa-chevron-right', placeholder: 'e.g., Senior Software Engineer' },
        { key: 'company', label: 'Company Name', icon: 'fas fa-building', placeholder: 'e.g., Tech Solutions Inc.' },
        { key: 'duration', label: 'Duration', icon: 'fas fa-calendar-alt', placeholder: 'e.g., Jan 2023 - Present' },
        { key: 'description', label: 'Description', type: 'list', placeholder: 'Key responsibilities and achievements', 
          defaultItems: [
            'Led cross-functional teams to deliver high-impact projects',
            'Implemented innovative solutions that improved efficiency by X%',
            'Collaborated with stakeholders to define requirements and deliverables',
            'Mentored junior team members and facilitated knowledge sharing'
          ]
        }
      ]
    },
    education: {
      icon: 'fas fa-graduation-cap',
      fields: [
        { key: 'degree', label: 'Degree', icon: 'fas fa-graduation-cap', placeholder: 'e.g., Bachelor of Science in Computer Science' },
        { key: 'school', label: 'Institution', icon: 'fas fa-university', placeholder: 'e.g., University of Technology' },
        { key: 'date', label: 'Year', icon: 'fas fa-calendar-alt', placeholder: 'e.g., 2020 - 2024' },
        { key: 'description', label: 'Details', placeholder: 'GPA, honors, relevant coursework, activities' }
      ]
    },
    certification: {
      icon: 'fas fa-award',
      fields: [
        { key: 'degree', label: 'Certification', icon: 'fas fa-award', placeholder: 'e.g., AWS Certified Solutions Architect' },
        { key: 'school', label: 'Issuer', icon: 'fas fa-building', placeholder: 'e.g., Amazon Web Services' },
        { key: 'date', label: 'Date Obtained', icon: 'fas fa-calendar-alt', placeholder: 'e.g., March 2024' },
        { key: 'description', label: 'Details', placeholder: 'Credential ID, validation URL, or additional notes' }
      ]
    },
    project: {
      icon: 'fas fa-folder-open',
      fields: [
        { key: 'degree', label: 'Project Name', icon: 'fas fa-folder-open', placeholder: 'e.g., E-commerce Platform Redesign' },
        { key: 'school', label: 'Link/URL', icon: 'fas fa-link', placeholder: 'e.g., github.com/username/project (optional)' },
        { key: 'date', label: 'Completion Date', icon: 'fas fa-calendar-alt', placeholder: 'e.g., June 2024' },
        { key: 'description', label: 'Description', type: 'list', placeholder: 'Project details and technologies used',
          defaultItems: [
            'Developed full-stack application using modern technologies',
            'Implemented responsive design and optimized user experience',
            'Integrated third-party APIs and payment processing',
            'Achieved measurable improvements in performance metrics'
          ]
        }
      ]
    },
    volunteer: {
      icon: 'fas fa-hands-helping',
      fields: [
        { key: 'degree', label: 'Role', icon: 'fas fa-hands-helping', placeholder: 'e.g., Community Outreach Coordinator' },
        { key: 'school', label: 'Organization', icon: 'fas fa-building', placeholder: 'e.g., Local Food Bank' },
        { key: 'date', label: 'Duration', icon: 'fas fa-calendar-alt', placeholder: 'e.g., 2023 - Present' },
        { key: 'description', label: 'Impact', type: 'list', placeholder: 'Your contributions and achievements',
          defaultItems: [
            'Organized community events serving 200+ families monthly',
            'Recruited and trained 15+ volunteers for various programs',
            'Developed partnerships with local businesses and organizations'
          ]
        }
      ]
    },
    award: {
      icon: 'fas fa-trophy',
      fields: [
        { key: 'degree', label: 'Award Name', icon: 'fas fa-trophy', placeholder: 'e.g., Employee of the Year' },
        { key: 'school', label: 'Awarding Body', icon: 'fas fa-building', placeholder: 'e.g., Tech Solutions Inc.' },
        { key: 'date', label: 'Date Received', icon: 'fas fa-calendar-alt', placeholder: 'e.g., December 2023' },
        { key: 'description', label: 'Significance', placeholder: 'Recognition criteria and your achievements' }
      ]
    },
    publication: {
      icon: 'fas fa-book',
      fields: [
        { key: 'degree', label: 'Title', icon: 'fas fa-book', placeholder: 'e.g., Machine Learning in Healthcare' },
        { key: 'school', label: 'Publisher/Journal', icon: 'fas fa-newspaper', placeholder: 'e.g., IEEE Transactions' },
        { key: 'date', label: 'Publication Date', icon: 'fas fa-calendar-alt', placeholder: 'e.g., August 2024' },
        { key: 'description', label: 'Abstract/Summary', placeholder: 'Brief description of your contribution and findings' }
      ]
    },
    language: {
      icon: 'fas fa-language',
      fields: [
        { key: 'degree', label: 'Language', icon: 'fas fa-language', placeholder: 'e.g., Spanish' },
        { key: 'school', label: 'Proficiency', icon: 'fas fa-star', placeholder: 'e.g., Native, Fluent, Conversational, Basic' }
      ]
    }
  };

  const template = templates[type] || templates.experience;
  
  // Build enhanced HTML with professional styling
  let itemHTML = `
    <div class="item-actions" style="opacity: 0; transition: opacity 0.3s ease;">
      <button class="item-btn delete enhanced-delete-btn" title="Delete this ${type}" data-item-type="${type}">
        <i class="fas fa-trash"></i>
      </button>
      <button class="item-btn duplicate enhanced-duplicate-btn" title="Duplicate this ${type}" data-item-type="${type}">
        <i class="fas fa-copy"></i>
      </button>
    </div>
    <div class="item-content">
  `;

  template.fields.forEach(field => {
    if (field.type === 'list') {
      itemHTML += `
        <div class="section-${field.key.replace('_', '-')} enhanced-field" contenteditable="true" data-key="${field.key}" data-field-type="list">
          <div class="field-header">
            <i class="${field.icon}"></i>
            <span class="field-label">${field.label}</span>
          </div>
          <ul class="section-duties enhanced-duties">
            ${field.defaultItems.map(item => `<li class="duty-item">${item}</li>`).join('')}
          </ul>
          <div class="field-actions">
            <button class="add-duty-btn" type="button">
              <i class="fas fa-plus"></i> Add bullet point
            </button>
          </div>
        </div>
      `;
    } else {
      itemHTML += `
        <div class="section-${field.key.replace('_', '-')} enhanced-field" contenteditable="true" data-key="${field.key}" data-placeholder="${field.placeholder}">
          <div class="field-header">
            <i class="${field.icon}"></i>
            <span class="field-label">${field.label}</span>
          </div>
          <div class="field-content" data-placeholder="${field.placeholder}">
            <span class="placeholder-text">${field.placeholder}</span>
          </div>
        </div>
      `;
    }
  });

  itemHTML += '</div>';
  newItem.innerHTML = itemHTML;
  
  // Add professional styling and animations
  newItem.style.cssText = `
    opacity: 0;
    transform: translateY(20px) scale(0.95);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    background: linear-gradient(135deg, rgba(79, 70, 229, 0.02), rgba(16, 185, 129, 0.02));
    border: 2px solid rgba(79, 70, 229, 0.1);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
  `;

  // Add enhancement CSS if not exists
  if (!document.querySelector('#item-enhancement-styles')) {
    const enhancementStyles = document.createElement('style');
    enhancementStyles.id = 'item-enhancement-styles';
    enhancementStyles.textContent = `
      .enhanced-field {
        margin-bottom: 16px;
        border-radius: 8px;
        transition: all 0.2s ease;
        position: relative;
      }
      
      .enhanced-field:hover {
        background: rgba(79, 70, 229, 0.05);
      }
      
      .field-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        color: #4F46E5;
        margin-bottom: 8px;
        font-size: 14px;
      }
      
      .field-content {
        min-height: 40px;
        padding: 12px;
        border: 2px dashed transparent;
        border-radius: 6px;
        transition: all 0.2s ease;
        cursor: text;
      }
      
      .field-content:hover {
        border-color: rgba(79, 70, 229, 0.3);
        background: rgba(79, 70, 229, 0.05);
      }
      
      .field-content:focus-within {
        border-color: #4F46E5;
        background: rgba(79, 70, 229, 0.1);
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
      }
      
      .placeholder-text {
        color: #9CA3AF;
        font-style: italic;
        pointer-events: none;
      }
      
      .enhanced-duties {
        list-style: none;
        padding: 0;
        margin: 8px 0;
      }
      
      .duty-item {
        padding: 8px 12px;
        margin: 4px 0;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 6px;
        border-left: 3px solid #4F46E5;
        transition: all 0.2s ease;
        cursor: text;
        position: relative;
      }
      
      .duty-item:hover {
        background: rgba(79, 70, 229, 0.1);
        transform: translateX(2px);
      }
      
      .duty-item:focus {
        outline: 2px solid #4F46E5;
        background: rgba(79, 70, 229, 0.1);
      }
      
      .add-duty-btn {
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.1), rgba(16, 185, 129, 0.1));
        border: 1px dashed #4F46E5;
        color: #4F46E5;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 12px;
        font-weight: 500;
        transition: all 0.2s ease;
        margin-top: 8px;
      }
      
      .add-duty-btn:hover {
        background: linear-gradient(135deg, #4F46E5, #10B981);
        color: white;
        border-color: #4F46E5;
        transform: translateY(-1px);
      }
      
      .enhanced-delete-btn {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.1));
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
      }
      
      .enhanced-delete-btn:hover {
        background: linear-gradient(135deg, #EF4444, #DC2626);
        color: white;
        transform: scale(1.1);
      }
      
      .enhanced-duplicate-btn {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1));
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
      }
      
      .enhanced-duplicate-btn:hover {
        background: linear-gradient(135deg, #10B981, #059669);
        color: white;
        transform: scale(1.1);
      }
      
      .item-btn {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.2s ease;
        margin-left: 8px;
      }
      
      .item-actions {
        position: absolute;
        top: 16px;
        right: 16px;
        display: flex;
        gap: 4px;
        z-index: 10;
      }
      
      .section-item:hover .item-actions {
        opacity: 1 !important;
      }
      
      .new-item-animation {
        animation: slideInFromRight 0.5s cubic-bezier(0.4, 0, 0.2, 1);
      }
      
      @keyframes slideInFromRight {
        from {
          opacity: 0;
          transform: translateX(100%) scale(0.8);
        }
        to {
          opacity: 1;
          transform: translateX(0) scale(1);
        }
      }
    `;
    document.head.appendChild(enhancementStyles);
  }

  // Insert with professional timing
  section.insertBefore(newItem, button);

  // Animate in with staggered effect
  setTimeout(() => {
    newItem.style.opacity = '1';
    newItem.style.transform = 'translateY(0) scale(1)';
    
    // Restore button
    setTimeout(() => {
      button.innerHTML = originalButtonContent;
      button.disabled = false;
    }, 200);
    
    // Show actions after main animation
    setTimeout(() => {
      const actions = newItem.querySelector('.item-actions');
      if (actions) actions.style.opacity = '1';
    }, 300);
    
    // Focus first field
    setTimeout(() => {
      const firstField = newItem.querySelector('.field-content');
      if (firstField) {
        firstField.focus();
        selectPlaceholderText(firstField);
      }
    }, 500);
  }, 100);

  // Add enhanced event listeners
  addEnhancedItemEventListeners(newItem);
  
  // Mark as changed and auto-save
  state.hasUnsavedChanges = true;
  autoSave();
  
  // Show success notification
  showNotification(`✨ New ${type} added successfully!`, 'success');
  
  return newItem;
}

// Enhanced Item Event Listeners with Professional Interactions
function addEnhancedItemEventListeners(item) {
  console.log('Enhanced item listeners initialized');

  // Enhanced delete button with confirmation modal
  const deleteBtn = item.querySelector('.enhanced-delete-btn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const itemType = deleteBtn.dataset.itemType || 'item';
      const itemTitle = item.querySelector('[data-key="job_title"], [data-key="degree"]')?.textContent.trim() || `this ${itemType}`;
      
      // Professional confirmation modal
      const confirmed = await showEnhancedConfirmModal({
        title: `Delete ${itemType.charAt(0).toUpperCase() + itemType.slice(1)}`,
        message: `Are you sure you want to delete "${itemTitle}"?`,
        details: 'This action cannot be undone.',
        confirmText: 'Delete',
        confirmStyle: 'danger',
        icon: 'fas fa-exclamation-triangle'
      });
      
      if (!confirmed) return;

      // Add professional delete animation
      addProfessionalDeleteAnimation(item);
      
      const itemId = item.dataset.itemId || item.id?.replace('item-', '');
      const sectionType = item.closest('.resume-section')?.dataset.sectionType;
      const resumeContainer = document.querySelector('.resume-builder') || 
                             window.parent?.document?.querySelector('.resume-builder');
      const resumeId = resumeContainer?.dataset.resumeId;

      if (!sectionType || !resumeId || !itemId) {
        console.error('Missing data:', { sectionType, resumeId, itemId });
        setTimeout(() => {
          item.remove();
          state.hasUnsavedChanges = true;
          autoSave();
          showNotification('Item removed locally', 'warning');
        }, 300);
        return;
      }

      try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                         window.parent?.document?.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        
        const response = await fetch(`/api/v1/resume/${resumeId}/section/${sectionType}/item/${itemId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
        });

        if (response.ok) {
          setTimeout(() => {
            item.remove();
            state.hasUnsavedChanges = true;
            autoSave();
            showNotification(`${itemType.charAt(0).toUpperCase() + itemType.slice(1)} deleted successfully`, 'success');
          }, 300);
        } else {
          const data = await response.json();
          showNotification(`Failed to delete: ${data.message || 'Server error'}`, 'error');
          resetDeleteAnimation(item);
        }
      } catch (error) {
        console.error('Delete error:', error);
        setTimeout(() => {
          item.remove();
          state.hasUnsavedChanges = true;
          autoSave();
          showNotification('Item removed (network error)', 'warning');
        }, 300);
      }
    });
  }

  // Enhanced duplicate button
  const duplicateBtn = item.querySelector('.enhanced-duplicate-btn');
  if (duplicateBtn) {
    duplicateBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const itemType = duplicateBtn.dataset.itemType || 'item';
      duplicateItemProfessionally(item, itemType);
    });
  }

  // Enhanced field interactions
  item.querySelectorAll('.field-content').forEach(field => {
    setupEnhancedFieldBehavior(field);
  });

  // Enhanced duty list interactions
  item.querySelectorAll('.add-duty-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      addNewDutyItem(btn);
    });
  });

  // Enhanced duties editing
  item.querySelectorAll('.duty-item').forEach(duty => {
    setupDutyItemBehavior(duty);
  });
}

// Enhanced Auto-Save with Professional Feedback
async function autoSave() {
  if (state.isGeneratingContent) return;
  
  console.log('🔄 Auto-saving resume...');
  clearTimeout(state.autoSaveTimeout);
  
  // Create professional saving indicator
  const savingIndicator = createProfessionalSavingIndicator();
  document.body.appendChild(savingIndicator);
  
  try {
    await saveResume();
    
    // Update indicator to success
    updateSavingIndicator(savingIndicator, 'success', '✅ Auto-saved successfully');
    
  } catch (error) {
    console.error('Auto-save failed:', error);
    updateSavingIndicator(savingIndicator, 'error', '❌ Auto-save failed');
    showNotification('Auto-save failed. Please save manually.', 'warning');
  }
  
  // Remove indicator after delay
  setTimeout(() => {
    removeProfessionalSavingIndicator(savingIndicator);
  }, 2000);
}

// Helper Functions for Professional UX

function createProfessionalSavingIndicator() {
  const indicator = document.createElement('div');
  indicator.className = 'professional-saving-indicator';
  indicator.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: linear-gradient(135deg, rgba(79, 70, 229, 0.95), rgba(99, 102, 241, 0.95));
    color: white;
    padding: 12px 20px;
    border-radius: 25px;
    box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4);
    font-size: 14px;
    font-weight: 500;
    backdrop-filter: blur(10px);
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 10px;
    border: 1px solid rgba(255, 255, 255, 0.2);
  `;
  
  indicator.innerHTML = `
    <div class="indicator-spinner" style="
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top: 2px solid white;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    "></div>
    <span class="indicator-text">Saving changes...</span>
  `;
  
  setTimeout(() => {
    indicator.style.opacity = '1';
    indicator.style.transform = 'translateY(0)';
  }, 10);
  
  return indicator;
}

function updateSavingIndicator(indicator, type, message) {
  const text = indicator.querySelector('.indicator-text');
  const spinner = indicator.querySelector('.indicator-spinner');
  
  if (type === 'success') {
    indicator.style.background = 'linear-gradient(135deg, rgba(16, 185, 129, 0.95), rgba(5, 150, 105, 0.95))';
    indicator.style.boxShadow = '0 8px 25px rgba(16, 185, 129, 0.4)';
    spinner.style.display = 'none';
    text.textContent = message;
  } else if (type === 'error') {
    indicator.style.background = 'linear-gradient(135deg, rgba(239, 68, 68, 0.95), rgba(220, 38, 38, 0.95))';
    indicator.style.boxShadow = '0 8px 25px rgba(239, 68, 68, 0.4)';
    spinner.style.display = 'none';
    text.textContent = message;
  }
}

function removeProfessionalSavingIndicator(indicator) {
  if (!indicator || !indicator.parentNode) return;
  
  indicator.style.opacity = '0';
  indicator.style.transform = 'translateY(20px)';
  setTimeout(() => {
    if (indicator.parentNode) {
      indicator.parentNode.removeChild(indicator);
    }
  }, 300);
}

function addProfessionalDeleteAnimation(item) {
  item.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
  item.style.opacity = '0.5';
  item.style.transform = 'scale(0.95) translateX(-10px)';
  item.style.filter = 'blur(1px)';
}

function resetDeleteAnimation(item) {
  item.style.opacity = '1';
  item.style.transform = 'scale(1) translateX(0)';
  item.style.filter = 'none';
}

function setupEnhancedFieldBehavior(field) {
  const placeholder = field.dataset.placeholder;
  
  field.addEventListener('focus', function() {
    const placeholderSpan = this.querySelector('.placeholder-text');
    if (placeholderSpan) {
      placeholderSpan.style.display = 'none';
    }
    this.style.borderColor = '#4F46E5';
    this.style.background = 'rgba(79, 70, 229, 0.1)';
  });
  
  field.addEventListener('blur', function() {
    if (!this.textContent.trim()) {
      const placeholderSpan = this.querySelector('.placeholder-text');
      if (placeholderSpan) {
        placeholderSpan.style.display = 'block';
      }
    }
    this.style.borderColor = 'transparent';
    this.style.background = '';
  });
  
  field.addEventListener('input', function() {
    const placeholderSpan = this.querySelector('.placeholder-text');
    if (placeholderSpan) {
      placeholderSpan.style.display = this.textContent.trim() ? 'none' : 'block';
    }
    state.hasUnsavedChanges = true;
  });
}

function duplicateItemProfessionally(originalItem, itemType) {
  const section = originalItem.parentElement;
  const addButton = section.querySelector('.add-item-btn');
  
  if (addButton) {
    showNotification(`Duplicating ${itemType}...`, 'info');
    
    // Create new item using existing function
    const newItem = addNewItem(addButton, itemType);
    
    // Copy data from original item
    setTimeout(() => {
      const originalFields = originalItem.querySelectorAll('[data-key]');
      const newFields = newItem.querySelectorAll('[data-key]');
      
      originalFields.forEach((originalField, index) => {
        const newField = newFields[index];
        if (newField && originalField.textContent.trim()) {
          newField.textContent = originalField.textContent;
          const placeholderSpan = newField.querySelector('.placeholder-text');
          if (placeholderSpan) {
            placeholderSpan.style.display = 'none';
          }
        }
      });
      
      showNotification(`${itemType.charAt(0).toUpperCase() + itemType.slice(1)} duplicated successfully!`, 'success');
    }, 200);
  }
}

function selectPlaceholderText(element) {
  const placeholderSpan = element.querySelector('.placeholder-text');
  if (placeholderSpan) {
    const range = document.createRange();
    range.selectNodeContents(placeholderSpan);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }
}

function generateUniqueId() {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Enhanced Confirmation Modal
async function showEnhancedConfirmModal({ title, message, details, confirmText = 'Confirm', confirmStyle = 'primary', icon = 'fas fa-question-circle' }) {
  return new Promise((resolve) => {
    const modal = document.createElement('div');
    modal.className = 'enhanced-confirm-modal';
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(8px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 2000;
      opacity: 0;
      transition: opacity 0.3s ease;
    `;
    
    const styleMap = {
      primary: { bg: '#4F46E5', shadow: 'rgba(79, 70, 229, 0.4)' },
      danger: { bg: '#EF4444', shadow: 'rgba(239, 68, 68, 0.4)' },
      success: { bg: '#10B981', shadow: 'rgba(16, 185, 129, 0.4)' }
    };
    
    const style = styleMap[confirmStyle] || styleMap.primary;
    
    modal.innerHTML = `
      <div class="modal-content" style="
        background: white;
        border-radius: 20px;
        padding: 32px;
        width: 90%;
        max-width: 440px;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
        transform: scale(0.9);
        transition: transform 0.3s ease;
        text-align: center;
      ">
        <div style="
          width: 64px;
          height: 64px;
          background: ${style.bg};
          border-radius: 50%;
          margin: 0 auto 24px;
          box-shadow: 0 8px 25px ${style.shadow};
        ">
          <i class="${icon}" style="color: white; font-size: 28px;"></i>
        </div>
        
        <h3 style="
          margin: 0 0 12px 0;
          color: #1F2937;
          font-size: 24px;
          font-weight: 700;
        ">${title}</h3>
        
        <p style="
          margin: 0 0 8px 0;
          color: #374151;
          font-size: 16px;
          line-height: 1.5;
        ">${message}</p>
        
        ${details ? `<p style="
          margin: 0 0 32px 0;
          color: #6B7280;
          font-size: 14px;
          line-height: 1.4;
        ">${details}</p>` : '<div style="margin-bottom: 32px;"></div>'}
        
        <div class="modal-actions" style="
          display: flex;
          gap: 12px;
          justify-content: center;
        ">
          <button class="btn-cancel" style="
            background: #F3F4F6;
            border: 2px solid #E5E7EB;
            color: #374151;
            padding: 12px 24px;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s ease;
            min-width: 100px;
          ">Cancel</button>
          <button class="btn-confirm" style="
            background: linear-gradient(135deg, ${style.bg}, ${style.bg}dd);
            border: 2px solid ${style.bg};
            color: white;
            padding: 12px 24px;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s ease;
            min-width: 100px;
            box-shadow: 0 4px 12px ${style.shadow};
          ">${confirmText}</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Animate in
    setTimeout(() => {
      modal.style.opacity = '1';
      const content = modal.querySelector('.modal-content');
      content.style.transform = 'scale(1)';
    }, 10);
    
    // Add enhanced hover effects
    const cancelBtn = modal.querySelector('.btn-cancel');
    const confirmBtn = modal.querySelector('.btn-confirm');
    
    cancelBtn.addEventListener('mouseenter', () => {
      cancelBtn.style.background = '#E5E7EB';
      cancelBtn.style.transform = 'translateY(-2px)';
      cancelBtn.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
    });
    
    cancelBtn.addEventListener('mouseleave', () => {
      cancelBtn.style.background = '#F3F4F6';
      cancelBtn.style.transform = '';
      cancelBtn.style.boxShadow = '';
    });
    
    confirmBtn.addEventListener('mouseenter', () => {
      confirmBtn.style.transform = 'translateY(-2px)';
      confirmBtn.style.boxShadow = `0 8px 25px ${style.shadow}`;
    });
    
    confirmBtn.addEventListener('mouseleave', () => {
      confirmBtn.style.transform = '';
      confirmBtn.style.boxShadow = `0 4px 12px ${style.shadow}`;
    });
    
    // Event listeners
    const closeModal = (confirmed = false) => {
      modal.style.opacity = '0';
      const content = modal.querySelector('.modal-content');
      content.style.transform = 'scale(0.9)';
      setTimeout(() => {
        document.body.removeChild(modal);
        resolve(confirmed);
      }, 300);
    };
    
    cancelBtn.addEventListener('click', () => closeModal(false));
    confirmBtn.addEventListener('click', () => closeModal(true));
    
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal(false);
    });
    
    // Enhanced keyboard handling
    const handleKeydown = (e) => {
      if (e.key === 'Escape') {
        document.removeEventListener('keydown', handleKeydown);
        closeModal(false);
      } else if (e.key === 'Enter') {
        document.removeEventListener('keydown', handleKeydown);
        closeModal(true);
      }
    };
    
    document.addEventListener('keydown', handleKeydown);
  });
}

// Enhanced Duty Item Management
function addNewDutyItem(button) {
  const dutiesList = button.parentElement.previousElementSibling;
  const newDuty = document.createElement('li');
  newDuty.className = 'duty-item';
  newDuty.contentEditable = 'true';
  newDuty.style.cssText = `
    opacity: 0;
    transform: translateX(-20px);
    transition: all 0.3s ease;
  `;
  newDuty.textContent = 'Click to add your achievement or responsibility';
  
  dutiesList.appendChild(newDuty);
  setupDutyItemBehavior(newDuty);
  
  // Animate in
  setTimeout(() => {
    newDuty.style.opacity = '1';
    newDuty.style.transform = 'translateX(0)';
    
    // Focus and select text
    setTimeout(() => {
      newDuty.focus();
      const range = document.createRange();
      range.selectNodeContents(newDuty);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    }, 100);
  }, 10);
  
  // Add delete button
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'duty-delete-btn';
  deleteBtn.innerHTML = '<i class="fas fa-times"></i>';
  deleteBtn.style.cssText = `
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #EF4444;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 10px;
    display: none;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
  `;
  
  deleteBtn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    newDuty.style.opacity = '0';
    newDuty.style.transform = 'translateX(-20px)';
    setTimeout(() => {
      newDuty.remove();
      state.hasUnsavedChanges = true;
    }, 200);
  });
  
  newDuty.style.position = 'relative';
  newDuty.appendChild(deleteBtn);
  
  // Show delete button on hover
  newDuty.addEventListener('mouseenter', () => {
    deleteBtn.style.display = 'flex';
  });
  
  newDuty.addEventListener('mouseleave', () => {
    deleteBtn.style.display = 'none';
  });
  
  state.hasUnsavedChanges = true;
  showNotification('✨ New bullet point added', 'info');
}

function setupDutyItemBehavior(duty) {
  duty.addEventListener('focus', function() {
    this.style.background = 'rgba(79, 70, 229, 0.1)';
    this.style.borderLeftColor = '#10B981';
  });
  
  duty.addEventListener('blur', function() {
    this.style.background = 'rgba(255, 255, 255, 0.8)';
    this.style.borderLeftColor = '#4F46E5';
    
    // Remove if empty
    if (!this.textContent.trim()) {
      this.style.opacity = '0';
      setTimeout(() => this.remove(), 200);
    }
  });
  
  duty.addEventListener('input', function() {
    state.hasUnsavedChanges = true;
  });
  
  duty.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      // Create new duty item
      const addBtn = this.closest('.enhanced-field').querySelector('.add-duty-btn');
      if (addBtn) {
        addNewDutyItem(addBtn);
      }
    } else if (e.key === 'Backspace' && !this.textContent.trim()) {
      e.preventDefault();
      const prevDuty = this.previousElementSibling;
      this.remove();
      if (prevDuty) {
        prevDuty.focus();
        // Place cursor at end
        const range = document.createRange();
        const sel = window.getSelection();
        range.setStart(prevDuty, prevDuty.childNodes.length);
        range.collapse(true);
        sel.removeAllRanges();
        sel.addRange(range);
      }
    }
  });
}

// Enhanced notification system integration
function showNotification(message, type = 'info') {
  // Remove existing notifications
  const existingNotifications = document.querySelectorAll('.enhanced-notification');
  existingNotifications.forEach(notification => {
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  });
  
  const notification = document.createElement('div');
  notification.className = `enhanced-notification ${type}`;
  
  const iconMap = {
    success: 'fas fa-check-circle',
    error: 'fas fa-exclamation-circle',
    warning: 'fas fa-exclamation-triangle',
    info: 'fas fa-info-circle'
  };
  
  const colorMap = {
    success: '#10B981',
    error: '#EF4444',
    warning: '#F59E0B',
    info: '#3B82F6'
  };
  
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 2000;
    max-width: 400px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(15px);
    border-radius: 16px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    border-left: 4px solid ${colorMap[type]};
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
  `;
  
  notification.innerHTML = `
    <div style="
      padding: 20px;
      display: flex;
      align-items: flex-start;
      gap: 16px;
    ">
      <div style="
        width: 24px;
        height: 24px;
        background: ${colorMap[type]};
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 2px;
      ">
        <i class="${iconMap[type]}" style="
          color: white;
          font-size: 12px;
        "></i>
      </div>
      <div style="
        flex: 1;
        min-width: 0;
      ">
        <div style="
          color: #1F2937;
          font-size: 15px;
          line-height: 1.5;
          font-weight: 600;
          word-wrap: break-word;
          margin-bottom: 4px;
        ">${message}</div>
        <div style="
          color: #6B7280;
          font-size: 12px;
          font-weight: 500;
        ">Just now</div>
      </div>
      <button class="notification-close" style="
        background: none;
        border: none;
        color: #9CA3AF;
        cursor: pointer;
        font-size: 18px;
        padding: 4px;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
        transition: all 0.2s ease;
        flex-shrink: 0;
      ">&times;</button>
    </div>
  `;
  
  document.body.appendChild(notification);
  
  // Show with enhanced animation
  setTimeout(() => {
    notification.style.opacity = '1';
    notification.style.transform = 'translateX(0)';
  }, 10);
  
  // Auto-hide with progress bar
  const progressBar = document.createElement('div');
  progressBar.style.cssText = `
    position: absolute;
    bottom: 0;
    left: 0;
    height: 3px;
    background: ${colorMap[type]};
    width: 100%;
    transform-origin: left;
    animation: progressShrink 4s linear;
  `;
  notification.appendChild(progressBar);
  
  // Add progress animation
  if (!document.querySelector('#notification-progress-styles')) {
    const progressStyles = document.createElement('style');
    progressStyles.id = 'notification-progress-styles';
    progressStyles.textContent = `
      @keyframes progressShrink {
        from { transform: scaleX(1); }
        to { transform: scaleX(0); }
      }
    `;
    document.head.appendChild(progressStyles);
  }
  
  const autoHideTimeout = setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 400);
  }, 4000);
  
  // Enhanced close button
  const closeBtn = notification.querySelector('.notification-close');
  closeBtn.addEventListener('click', () => {
    clearTimeout(autoHideTimeout);
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 400);
  });
  
  closeBtn.addEventListener('mouseenter', () => {
    closeBtn.style.background = '#F3F4F6';
    closeBtn.style.color = '#374151';
    closeBtn.style.transform = 'scale(1.1)';
  });
  
  closeBtn.addEventListener('mouseleave', () => {
    closeBtn.style.background = 'none';
    closeBtn.style.color = '#9CA3AF';
    closeBtn.style.transform = 'scale(1)';
  });
  
  // Pause auto-hide on hover
  notification.addEventListener('mouseenter', () => {
    clearTimeout(autoHideTimeout);
    progressBar.style.animationPlayState = 'paused';
  });
  
  notification.addEventListener('mouseleave', () => {
    progressBar.style.animationPlayState = 'running';
    setTimeout(() => {
      notification.style.opacity = '0';
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 400);
    }, 2000);
  });
}

// Export the enhanced functions
window.addNewItem = addNewItem;
window.addEnhancedItemEventListeners = addEnhancedItemEventListeners;
window.autoSave = autoSave;