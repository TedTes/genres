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
});

// Iframe-specific event setup
function setupIframeListeners(iframeDoc) {
  iframeDoc.addEventListener('click', (e) => {
    const deleteBtn = e.target.closest('.item-btn.delete');
    if (deleteBtn) {
      e.preventDefault();
      e.stopPropagation();
      const item = deleteBtn.closest('.section-item');
      if (item && confirm('Are you sure you want to delete this item?')) {
        item.remove();
        state.hasUnsavedChanges = true;
        autoSave();
      }
    }
  });

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

function saveResume() {
  if (!state.hasUnsavedChanges) return;

  const saveButton = document.querySelector('#save-resume-btn');
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
  const resumeId = document.querySelector('.resume-builder')?.dataset.resumeId;
  const iframe = document.querySelector('#preview-iframe');

  if (!saveButton || !resumeId || !iframe) return;

  saveButton.classList.add('saving');

  try {
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    const resumeContent = collectResumeData(iframeDoc);

    fetch(`/api/v1/resume/${resumeId}/save-data`, {
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

  iframeDoc.querySelectorAll('.resume-section').forEach(section => {
    const sectionType = section.className.match(/(\w+)-section/)?.[1];
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
    deleteBtn.addEventListener('click', () => {
      tag.remove();
      state.hasUnsavedChanges = true;
      autoSave();
    });
  }
}

function autoSave() {
  console.log('Auto-saving resume...');
  state.hasUnsavedChanges = true;
  const savedIndicator = Object.assign(document.createElement('div'), {
    style: `position: fixed; bottom: 20px; left: 20px; background-color: var(--success); 
            color: white; padding: 10px 20px; border-radius: 4px; box-shadow: var(--shadow-md); 
            opacity: 0; transition: opacity 0.3s`,
    innerHTML: '<i class="fas fa-check"></i> Changes saved',
  });
  document.body.appendChild(savedIndicator);

  clearTimeout(state.autoSaveTimeout);
  state.autoSaveTimeout = setTimeout(saveResume, 1500);

  const saveStatus = document.getElementById('save-status');
  if (saveStatus) showSaveStatus('Changes saved', false);

  setTimeout(() => {
    savedIndicator.style.opacity = '1';
    setTimeout(() => {
      savedIndicator.style.opacity = '0';
      setTimeout(() => document.body.removeChild(savedIndicator), 300);
    }, 2000);
  }, 100);
}

function addNewTag(button) {
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
    autoSave();
  }
}

function addNewItem(button, type) {
  const section = button.parentElement;
  const newItem = document.createElement('div');
  newItem.className = 'section-item';
  
  const uniqueId = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  newItem.dataset.itemId = uniqueId; // Fixed line
  newItem.id = `item-${uniqueId}`;
  let itemHTML = '<div class="item-actions"><button class="item-btn delete" title="Delete"><i class="fas fa-trash"></i></button></div>';

  switch (type) {
    case 'experience':
      itemHTML += `
        <div class="section-job-title" contenteditable="true"><i class="fas fa-chevron-right"></i>Job Title</div>
        <div class="section-company" contenteditable="true"><i class="fas fa-building"></i>Company Name</div>
        <div class="section-date" contenteditable="true"><i class="fas fa-calendar-alt"></i>Start Date - End Date</div>
        <div class="section-description" contenteditable="true"><ul class="section-duties"><li>Add your responsibilities...</li><li>Use bullet points...</li><li>Include metrics...</li><li>Focus on achievements...</li></ul></div>`;
      break;
    case 'education':
      itemHTML += `
        <div class="section-degree" contenteditable="true"><i class="fas fa-chevron-right"></i>Degree / Certification</div>
        <div class="section-school" contenteditable="true"><i class="fas fa-university"></i>Institution Name</div>
        <div class="section-date" contenteditable="true"><i class="fas fa-calendar-alt"></i>Start Year - End Year</div>
        <div class="section-description" contenteditable="true">Add details about achievements...</div>`;
      break;
    case 'certification':
      itemHTML += `
        <div class="section-degree" contenteditable="true"><i class="fas fa-award"></i>Certification Name</div>
        <div class="section-school" contenteditable="true"><i class="fas fa-building"></i>Issuing Organization</div>
        <div class="section-date" contenteditable="true"><i class="fas fa-calendar-alt"></i>Year Obtained</div>
        <div class="section-description" contenteditable="true">Include additional details...</div>`;
      break;
    case 'project':
      itemHTML += `
        <div class="section-degree" contenteditable="true"><i class="fas fa-folder-open"></i>Project Name</div>
        <div class="section-school" contenteditable="true"><i class="fas fa-link"></i>Project URL</div>
        <div class="section-date" contenteditable="true"><i class="fas fa-calendar-alt"></i>Completion Date</div>
        <div class="section-description" contenteditable="true"><ul class="section-duties"><li>Describe purpose...</li><li>List technologies...</li><li>Explain role...</li><li>Highlight outcomes...</li></ul></div>`;
      break;
    case 'volunteer':
      itemHTML += `
        <div class="section-degree" contenteditable="true"><i class="fas fa-hands-helping"></i>Volunteer Position</div>
        <div class="section-school" contenteditable="true"><i class="fas fa-building"></i>Organization</div>
        <div class="section-date" contenteditable="true"><i class="fas fa-calendar-alt"></i>Start Date - End Date</div>
        <div class="section-description" contenteditable="true"><ul class="section-duties"><li>Describe contributions...</li><li>Highlight leadership...</li><li>Include skills...</li></ul></div>`;
      break;
    case 'award':
      itemHTML += `
        <div class="section-degree" contenteditable="true"><i class="fas fa-trophy"></i>Award Name</div>
        <div class="section-school" contenteditable="true"><i class="fas fa-building"></i>Awarding Organization</div>
        <div class="section-date" contenteditable="true"><i class="fas fa-calendar-alt"></i>Date Received</div>
        <div class="section-description" contenteditable="true">Describe significance...</div>`;
      break;
    case 'publication':
      itemHTML += `
        <div class="section-degree" contenteditable="true"><i class="fas fa-book"></i>Publication Title</div>
        <div class="section-school" contenteditable="true"><i class="fas fa-newspaper"></i>Publisher</div>
        <div class="section-date" contenteditable="true"><i class="fas fa-calendar-alt"></i>Publication Date</div>
        <div class="section-description" contenteditable="true">Describe contribution...</div>`;
      break;
    case 'language':
      itemHTML += `
        <div class="section-degree" contenteditable="true"><i class="fas fa-language"></i>Language Name</div>
        <div class="section-school" contenteditable="true"><i class="fas fa-star"></i>Proficiency Level</div>`;
      break;
    default:
      const sectionTitle = section.querySelector('.section-title')?.textContent.trim().toLowerCase();
      if (sectionTitle?.includes('volunteer')) return addNewItem(button, 'volunteer');
      if (sectionTitle?.includes('award') || sectionTitle?.includes('honor')) return addNewItem(button, 'award');
      if (sectionTitle?.includes('publication') || sectionTitle?.includes('research')) return addNewItem(button, 'publication');
      if (sectionTitle?.includes('language')) return addNewItem(button, 'language');
      if (sectionTitle?.includes('project')) return addNewItem(button, 'project');
      itemHTML += `
        <div class="section-degree" contenteditable="true"><i class="fas fa-chevron-right"></i>Item Title</div>
        <div class="section-school" contenteditable="true"><i class="fas fa-building"></i>Organization</div>
        <div class="section-date" contenteditable="true"><i class="fas fa-calendar-alt"></i>Relevant Date</div>
        <div class="section-description" contenteditable="true">Add details...</div>`;
  }

  newItem.innerHTML = itemHTML;
  section.insertBefore(newItem, button);
  console.log("from item")
  console.log(newItem);
  addItemEventListeners(newItem);
  state.hasUnsavedChanges = true;
  autoSave();
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