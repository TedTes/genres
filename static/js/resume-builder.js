const state = {
  autoSaveTimeout: null,
  hasUnsavedChanges: false,
  isGeneratingContent: false,
  currentTemplate: null
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
  previewContainer: ".resume-preview-container",
  previewButton: '.float-control-btn[data-action="toggle-preview"]'
};

const templateConfigs = {
  classic: {
    summary: `
      <div class="section-item" data-section="summary">
        <div class="section-summary" contenteditable="true" data-field="summary" placeholder="Write a compelling professional summary that highlights your key qualifications, experience, and career objectives..."></div>
      </div>
    `,
    experience: `
      <div class="section-item" data-section="experience">
        <div class="item-actions">
          <button class="item-btn delete" title="Delete experience">
            <i class="fas fa-trash"></i>
          </button>
        </div>
        <div class="section-job-title" contenteditable="true" data-field="job_title" placeholder="Job Title"></div>
        <div class="section-company" contenteditable="true" data-field="company" placeholder="Company Name"></div>
        <div class="section-duration" contenteditable="true" data-field="duration" placeholder="Date Range"></div>
        <div class="section-description" data-field="description">
          <ul class="duties-list"></ul>
          <div class="add-bullet-prompt" onclick="addNewBulletPoint(this)">
            <i class="fas fa-plus"></i>
            <span>Click to add responsibility</span>
          </div>
        </div>
      </div>
    `,
    education: `
      <div class="section-item" data-section="education">
        <div class="item-actions">
          <button class="item-btn delete" title="Delete education">
            <i class="fas fa-trash"></i>
          </button>
        </div>
        <div class="section-degree" contenteditable="true" data-field="degree" placeholder="Degree"></div>
        <div class="section-school" contenteditable="true" data-field="school" placeholder="School Name"></div>
        <div class="section-date" contenteditable="true" data-field="date" placeholder="Year"></div>
      </div>
    `,
    certification: `
      <div class="section-item" data-section="certification">
        <div class="item-actions">
          <button class="item-btn delete" title="Delete certification">
            <i class="fas fa-trash"></i>
          </button>
        </div>
        <div class="section-name" contenteditable="true" data-field="name" placeholder="Certification Name"></div>
        <div class="section-issuer" contenteditable="true" data-field="issuer" placeholder="Issuing Organization"></div>
        <div class="section-date" contenteditable="true" data-field="date" placeholder="Year"></div>
      </div>
    `,
    project: `
      <div class="section-item" data-section="project">
        <div class="item-actions">
          <button class="item-btn delete" title="Delete project">
            <i class="fas fa-trash"></i>
          </button>
        </div>
        <div class="section-name" contenteditable="true" data-field="name" placeholder="Project Name"></div>
        <div class="section-date" contenteditable="true" data-field="date" placeholder="Year"></div>
        <div class="section-description" data-field="description">
          <ul class="duties-list"></ul>
          <div class="add-bullet-prompt" onclick="addNewBulletPoint(this)">
            <i class="fas fa-plus"></i>
            <span>Click to add project detail</span>
          </div>
        </div>
      </div>
    `,
    skills: `
    <div class="section-container" data-section-type="skills">
      <button class="add-tag-btn" data-section="skills" data-type="skills">
        <i class="fas fa-plus"></i> Add Skill
      </button>
    </div>`
  },
  
  cards: {
    summary: `
      <div class="card summary-card section-item" data-section="summary">
        <div class="card-header">
          <h3 class="card-title">Professional Summary</h3>
        </div>
        <div class="section-summary" contenteditable="true" data-field="summary" placeholder="Write a compelling professional summary that showcases your expertise and career goals..."></div>
      </div>
    `,
    experience: `
      <div class="card exp-card section-item" data-section="experience">
        <div class="card-header">
          <div class="section-job-title" contenteditable="true" data-field="job_title" placeholder="Job Title"></div>
          <div class="section-duration" contenteditable="true" data-field="duration" placeholder="Date Range"></div>
        </div>
        <div class="section-company" contenteditable="true" data-field="company" placeholder="Company Name"></div>
        <div class="section-description" data-field="description">
          <ul class="duties-list"></ul>
          <div class="add-bullet-prompt" onclick="addNewBulletPoint(this)">
            <i class="fas fa-plus"></i>
            <span>Click to add responsibility</span>
          </div>
        </div>
      </div>
    `,
    education: `
      <div class="card edu-card section-item" data-section="education">
        <div class="section-degree" contenteditable="true" data-field="degree" placeholder="Degree"></div>
        <div class="section-school" contenteditable="true" data-field="school" placeholder="School Name"></div>
        <div class="section-date" contenteditable="true" data-field="year" placeholder="Year"></div>
      </div>
    `
  }
};

const templateLoaders = {
  classic: {
    loader: classicTemplateLoader,
    initialize: classicInitialize
  }
};

document.addEventListener('click', (e) => {
  // Handle template selection via radio buttons with loading
  if (e.target.matches('input[name="template"]')) {
    const templateId = e.target.value;
    const templateName = e.target.closest('.template-option').querySelector('.template-name')?.textContent;
    
    if (templateId && templateConfigs[templateId]) {
      handleTemplateSelection(templateId, templateName);
    }
  }
  
  // Enhanced template label clicks
  if (e.target.closest('.template-label')) {
    const label = e.target.closest('.template-label');
    const templateId = label.dataset.templateId;
    const radio = document.querySelector(`#template-${templateId}`);
    
    if (radio && !radio.checked) {
      radio.checked = true;
      radio.dispatchEvent(new Event('click'));
    }
  }
  
  // Enhanced select button clicks with loading
  if (e.target.classList.contains('select-btn')) {
    e.preventDefault();
    handleTemplateSelectButton(e.target);
  }

  // Handle AI feature cards
  if (e.target.closest('.ai-feature-card')) {
    const action = e.target.closest('.ai-feature-card').dataset.action;
    handleAIFeature(action);
  }
});
document.addEventListener('DOMContentLoaded', () => {
  if(window == window.top) {
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
      previewButton : document.querySelector(selectors.previewButton),
      previewContainer : document.querySelector(selectors.previewContainer)
    };
    const closePanel = () => {
      if (elements.templatesPanel?.classList.contains('active')) {
        elements.templatesPanel.classList.remove('active');
      }
    };
      if (elements.iframe) {
        window.addEventListener('blur', () => {
          setTimeout(() => {
            if (document.activeElement === elements.iframe && elements.templatesPanel?.classList.contains('active')) {
              closePanel();
            }
          }, 100);
        });
        elements.iframe.addEventListener('load', () => {
          let templateId = state.currentTemplate || getCurrentTemplateName();
         templateId = templateId.split("_")[1];
          if (templateLoaders[templateId]) {
            templateLoaders[templateId].loader(elements.iframe.contentDocument);
            templateLoaders[templateId].initialize(elements.iframe.contentDocument);
          }
          setupIframeListeners(elements.iframe.contentDocument);
        });
      }
    // Save button handler with enhanced feedback
    if (elements.saveButton) {
      elements.saveButton.addEventListener('click', () => {
        updateSaveButtonState('saving');
        saveResumeData({ showNotifications: true, isAutoSave: false });
      });
    }

    if(elements.previewButton) {
      elements.previewButton.addEventListener('click', () => { 
       
        if (elements.iframe && elements.previewContainer) {
          togglePreviewMode(elements.previewButton,elements.iframe, elements.previewContainer);
        }
      });
    }

    // Enhanced template meta tag handling
    const selectedRadio = document.querySelector('input[name="template"]:checked');
    if (selectedRadio) {
      const templateId = selectedRadio.value;
      state.currentTemplate = templateId;
      updateTemplateMetaTag(templateId);
    }
  
    // Enhanced AI modal handlers with animations
    if (elements.aiButton && elements.aiModal && elements.aiModalClose) {
      elements.aiButton.addEventListener('click', () => {
        if (elements.templatesPanel?.classList.contains('active')) {
          elements.templatesPanel.classList.remove('active');
        }
        openAIModalWithAnimation();
      });
  
      elements.aiModalClose.addEventListener('click', () => {
        closeAIModalWithAnimation();
      });
  
      elements.aiModal.addEventListener('click', (e) => {
        if (e.target === elements.aiModal) {
          closeAIModalWithAnimation();
        }
      });
    }
  
    // Enhanced template panel toggle with loading
    if (elements.templateButton && elements.templatesPanel) {
      elements.templateButton.addEventListener('click', () => {
        if (elements.aiModal?.classList.contains('active')) {
          closeAIModalWithAnimation();
        }
        toggleTemplatePanelWithAnimation();
      });
    }

  
    // Enhanced close panels
    elements.closePanelButtons.forEach(button => {
      button.addEventListener('click', () => {
        const panelId = button.getAttribute('data-panel');
        const panel = document.getElementById(panelId);
        if (panel) {
          panel.classList.remove('active');
          // Add exit animation
          panel.style.transform = 'translateX(-100%)';
          setTimeout(() => {
            panel.style.transform = '';
          }, 300);
        }
      });
    });
  
    // Enhanced outside click handling
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.slide-panel') && !e.target.closest('.float-control-btn') && 
          elements.templatesPanel?.classList.contains('active')) {
            closePanel();
      }
    });
  
    document.addEventListener('click', (e) => {
      // Handle empty state "Add Section" buttons
      if (e.target.closest('.add-section-btn')) {
        const button = e.target.closest('.add-section-btn');
        const sectionType = button.dataset.section;
        console.log('Adding section:', sectionType);
        addNewSection(button, sectionType);
      }
      
      // Handle "Add Item" buttons with data-section attribute
      if (e.target.closest('.add-item-btn[data-section]')) {
        const button = e.target.closest('.add-item-btn');
        const sectionType = button.dataset.section;
        console.log('Adding item:', sectionType);
        addNewItem(button, sectionType);
      }
    });
  
    // Existing tag and item event listeners
    document.querySelectorAll(selectors.sectionTags).forEach(addTagEventListeners);
    document.querySelectorAll(selectors.sectionItems).forEach(addItemEventListeners);
  
    // Enhanced file drop handlers
    document.addEventListener('dragover', (e) => e.preventDefault());
    document.addEventListener('drop', (e) => {
      e.preventDefault();
      showEnhancedNotification('📁 File uploads will be supported in a future version.', 'info');
    });
  
 
  
    // Enhanced unload warning
    window.addEventListener('beforeunload', (e) => {
      if (state.hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return e.returnValue;
      }
    });

  
  
    // Initial auto-save with delay
    setTimeout(saveResumeData, 3000,{ showNotifications: false, isAutoSave: true });
  
    // Enhanced PDF preview handler
    const previewPdfButton = document.querySelector('#preview-pdf-btn');
    if (previewPdfButton) {
      previewPdfButton.addEventListener('click', handlePDFPreview);
    }
  
    // Add keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
  
      // Initialize bullet points for existing content
      setTimeout(() => {
        initializeExistingBullets();
        
     
      }, 500);
  }
 
});
  
function togglePreviewMode(button, iframe, container) {
  const isFullscreen = container?.classList?.contains('fullscreen-preview');
  
  if (isFullscreen) {
      // Exit preview - restore original editing iframe
      container.classList.remove('fullscreen-preview');
      button.querySelector('.btn-tooltip').textContent = 'Preview Resume';
      button.querySelector('i').className = 'fas fa-eye';
      
      // Restore original iframe src (with editing)
      const resumeId = iframe.getAttribute('resume_id');
      iframe.src = `/api/v1/resume/${resumeId}/render`; // Original editing version
      
      showEnhancedNotification('✅ Exited preview mode', 'success');
  } else {
      // Enter preview - load clean preview content
      container.classList.add('fullscreen-preview');
      button.querySelector('.btn-tooltip').textContent = 'Exit Preview';
      button.querySelector('i').className = 'fas fa-eye-slash';
      
      // Switch iframe to preview endpoint
      const resumeId = iframe.getAttribute('resume_id');
      iframe.src = `/api/v1/resume/${resumeId}/preview`;
      showEnhancedNotification('👁️ Entered preview mode', 'success');
  }
}
function setupIframeListeners(iframeDoc) {
  iframeDoc.querySelectorAll('.section-tag').forEach(addTagEventListeners);
  iframeDoc.querySelectorAll('.section-item').forEach(addItemEventListeners);
  
  // Initialize bullet points in iframe
  initializeIframeBullets(iframeDoc);
  
  if(!iframeDoc.hasInputListener) {
    iframeDoc.addEventListener('click', (e) => {
      if (e.target.closest('.add-section-btn')) {
        const button = e.target.closest('.add-section-btn');
        const sectionType = button.dataset.section;
        window.parent.addNewSection(button, sectionType);
      }
      
      if (e.target.closest('.add-item-btn[data-section]')) {
        const button = e.target.closest('.add-item-btn');
        const sectionType = button.dataset.section;
        window.parent.addNewItem(button, sectionType);
      }
    });
  }
  iframeDoc.addEventListener('input', debounce((e) => {
    if (e.target.getAttribute('contenteditable') === 'true') {
      state.hasUnsavedChanges = true;
      updateSaveButtonState('unsaved');
      clearTimeout(state.autoSaveTimeout);
      state.autoSaveTimeout = setTimeout(saveResumeData, 1500, { showNotifications: false, isAutoSave: true });
    }
  }, 100));
}
function classicInitialize(iframeDoc) {
  console.log("Iframe: Initializing classic template event listeners");

  iframeDoc.querySelectorAll('[contenteditable="true"]').forEach(field => {
    field.addEventListener('focus', () => {
      field.style.outline = '2px solid #007bff';
      field.style.backgroundColor = '#f8f9fa';
      field.style.padding = '2px';
    });
    field.addEventListener('blur', () => {
      field.style.outline = 'none';
      field.style.backgroundColor = 'transparent';
      field.style.padding = '0';
    });
  });

  iframeDoc.querySelectorAll('.section-job-title, .section-company, .section-duration, .section-degree, .section-school, .section-date, .section-name, .section-issuer').forEach(field => {
    field.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        field.blur();
      }
    });
  });

  iframeDoc.querySelectorAll('.section-item').forEach(item => {
    item.addEventListener('mouseenter', () => {
      item.style.backgroundColor = '#f1f3f5';
      item.style.transition = 'background-color 0.2s ease';
    });
    item.addEventListener('mouseleave', () => {
      item.style.backgroundColor = 'transparent';
    });
    item.setAttribute('tabindex', '0');
    item.addEventListener('keydown', (e) => {
      if ((e.key === 'Enter' || e.key === ' ') && e.target === item) {
        e.preventDefault();
        const firstEditable = item.querySelector('[contenteditable="true"]');
        if (firstEditable) {
          firstEditable.focus();
        }
      }
    });
  });

  iframeDoc.addEventListener('click', (e) => {
    if (e.target.closest('.add-tag-btn')) {
      const button = e.target.closest('.add-tag-btn');
      const sectionType = button.getAttribute('data-section');
      if (sectionType === 'skills' || sectionType === 'technical-skills' || sectionType === 'soft-skills') {
        e.preventDefault();
        e.stopPropagation();
        window.parent.addNewSkillTag(button);
      }
    }

    if (e.target.classList.contains('tag-delete')) {
      const tag = e.target.closest('.section-tag');
      if (tag && tag.closest('[data-section-type="skills"]')) {
        e.preventDefault();
        e.stopPropagation();
        window.parent.deleteSkillTag(e.target);
      }
    }

    if (e.target.closest('.section-tag') && !e.target.classList.contains('tag-delete')) {
      const tag = e.target.closest('.section-tag');
      if (tag && tag.closest('[data-section-type="skills"]')) {
        window.parent.editSkillTag(tag);
      }
    }
  });
}
function classicTemplateLoader(iframeDoc) {
  console.log("Iframe: Loading classic template");
  initializeIframeBullets(iframeDoc);
  iframeDoc.querySelectorAll('.section-item').forEach(item => {
    item.classList.add('classic-item');
  });
}
function cardTemplateLoader() {

}


function addNewBulletPoint(promptElement) {
  const descriptionContainer = promptElement.parentElement;
  const dutiesList = descriptionContainer.querySelector('.duties-list');
  
  // Create new list item
  const newBullet = document.createElement('li');
  newBullet.contentEditable = true;
  newBullet.className = 'new-bullet';
  newBullet.innerHTML = '&nbsp;';
  // Add delete button to the bullet
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'bullet-delete';
  deleteBtn.innerHTML = '×';
  deleteBtn.title = 'Delete this point';
  deleteBtn.contentEditable = false;
  deleteBtn.onclick = (e) => {
    e.stopPropagation();
    e.preventDefault();
    deleteBulletPoint(newBullet);
  };
  
  newBullet.appendChild(deleteBtn);
  
  // Add event listeners for bullet editing
  setupBulletEventListeners(newBullet);
  
  // Add to list
  dutiesList.appendChild(newBullet);
  
  // Focus the new bullet for immediate editing
  newBullet.focus();
  
  // Remove animation class after animation completes
  setTimeout(() => {
    newBullet.classList.remove('new-bullet');
  }, 300);
  
  // Mark as changed for auto-save
  state.hasUnsavedChanges = true;
  clearTimeout(state.autoSaveTimeout);
 state.autoSaveTimeout = setTimeout(saveResumeData, 1500,{ showNotifications: false, isAutoSave: true });
  
  return newBullet;
}
// Main function to add new bullet points
function addBulletFromData(dutiesList, bulletText) {
  if (!bulletText || !bulletText.trim()) return;
  
  const bullet = document.createElement('li');
  bullet.contentEditable = true;
  bullet.textContent = bulletText.trim();
  
  // Add delete button
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'bullet-delete';
  deleteBtn.innerHTML = '×';
  deleteBtn.title = 'Delete this point';
  deleteBtn.contentEditable = false; 
  deleteBtn.onclick = (e) => {
    e.stopPropagation();
    e.preventDefault();
    deleteBulletPoint(bullet);
  };
  
  bullet.appendChild(deleteBtn);

  const textNode = document.createTextNode(bulletText.trim());
  bullet.insertBefore(textNode, deleteBtn);
  
  setupBulletEventListeners(bullet);
  dutiesList.appendChild(bullet);
  
  return bullet;
}
// Function to delete individual bullet points
function deleteBulletPoint(bulletElement) {
  // Add fade-out animation
  bulletElement.style.transition = 'all 0.3s ease';
  bulletElement.style.opacity = '0';
  bulletElement.style.transform = 'translateX(-20px)';
  
  setTimeout(() => {
    bulletElement.remove();
    
    // Mark as changed for auto-save
    state.hasUnsavedChanges = true;
    clearTimeout(state.autoSaveTimeout);
    state.autoSaveTimeout = setTimeout(saveResumeData, 1500,{ showNotifications: false, isAutoSave: true });
    
    showEnhancedNotification('Bullet point removed', 'success');
  }, 300);
}
// Setup event listeners for bullet points
function setupBulletEventListeners(bulletElement) {
  // Handle Enter key to add new bullet
  bulletElement.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      
      // If current bullet is empty, don't add new one
      if (bulletElement.textContent.trim() === '') {
        return;
      }
      
      // Find the prompt element and add new bullet
      const descriptionContainer = bulletElement.closest('.section-description');
      const promptElement = descriptionContainer.querySelector('.add-bullet-prompt');
      const newBullet = addNewBulletPoint(promptElement);
      
      // Focus the new bullet
      setTimeout(() => {
        newBullet.focus();
      }, 50);
    }
    
    // Handle Backspace on empty bullet to delete it
    if (e.key === 'Backspace') {
      // Get text content excluding the delete button
      const deleteBtn = bulletElement.querySelector('.bullet-delete');
      const textContent = deleteBtn ? 
        bulletElement.textContent.replace(deleteBtn.textContent, '').trim() : 
        bulletElement.textContent.trim();
      
      if (textContent === '') {
        e.preventDefault();
        
        const dutiesList = bulletElement.parentElement;
        const bullets = Array.from(dutiesList.children);
        const currentIndex = bullets.indexOf(bulletElement);
        
        // Focus previous bullet if exists
        if (currentIndex > 0) {
          const prevBullet = bullets[currentIndex - 1];
          prevBullet.focus();
          // Move cursor to end of previous bullet
          const range = document.createRange();
          const selection = window.getSelection();
          range.selectNodeContents(prevBullet);
          range.collapse(false);
          selection.removeAllRanges();
          selection.addRange(range);
        }
        
        deleteBulletPoint(bulletElement);
      }
    }
  });
  
  // Handle input changes for auto-save
  bulletElement.addEventListener('input', () => {
    state.hasUnsavedChanges = true;
    clearTimeout(state.autoSaveTimeout);
    state.autoSaveTimeout = setTimeout(saveResumeData, 1500, { showNotifications: false, isAutoSave: true });
  });
  
  // Handle focus events
  bulletElement.addEventListener('focus', () => {
    bulletElement.style.outline = 'none';
  });
}

// Function to populate existing bullets when loading data
function populateBulletPoints(descriptionElement, bulletData) {
  const dutiesList = descriptionElement.querySelector('.duties-list');
  const promptElement = descriptionElement.querySelector('.add-bullet-prompt');
  
  if (!dutiesList) {
    console.warn('No duties list found in description element');
    return;
  }
  
  // Clear existing bullets
  dutiesList.innerHTML = '';
  
  let bulletsToAdd = [];
  
  if (Array.isArray(bulletData)) {
    // Data is already an array
    bulletsToAdd = bulletData.filter(item => item && item.trim());
  } else if (typeof bulletData === 'string' && bulletData.trim()) {
    // Data is a string - split by newlines
    bulletsToAdd = bulletData.split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0);
  }
  
  // Add bullets to the list
  bulletsToAdd.forEach(bulletText => {
    addBulletFromData(dutiesList, bulletText);
  });
  
  // Ensure prompt element exists and is functional
  if (!promptElement) {
    const newPrompt = document.createElement('div');
    newPrompt.className = 'add-bullet-prompt';
    newPrompt.onclick = () => addNewBulletPoint(newPrompt);
    newPrompt.innerHTML = '<i class="fas fa-plus"></i><span>Click to add detail</span>';
    descriptionElement.appendChild(newPrompt);
  }
}
// Function to collect bullet point data for saving
function collectBulletData(descriptionElement) {
  const bullets = descriptionElement.querySelectorAll('.duties-list li');
  const bulletTexts = [];
  
  bullets.forEach(bullet => {
    let text = bullet.textContent || '';
    
    // Remove delete button text (×) and clean up
    text = text.replace(/×$/, '').trim();
    
    // Only include non-empty bullets
    if (text && text.length > 0) {
      bulletTexts.push(text);
    }
  });
  
  return bulletTexts.length > 0 ? bulletTexts.join('\n') : '';
}
// Initialize existing bullet points when page loads
function initializeExistingBullets() {
  // Find all existing section descriptions with bullet lists
  document.querySelectorAll('.section-description').forEach(descriptionElement => {
    const dutiesList = descriptionElement.querySelector('.duties-list');
    if (dutiesList) {
      // Setup event listeners for existing bullets
      dutiesList.querySelectorAll('li').forEach(bullet => {
        setupBulletEventListeners(bullet);
        
        // Add delete button if it doesn't exist
        if (!bullet.querySelector('.bullet-delete')) {
          const deleteBtn = document.createElement('button');
          deleteBtn.className = 'bullet-delete';
          deleteBtn.innerHTML = '×';
          deleteBtn.title = 'Delete this point';
          deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteBulletPoint(bullet);
          };
          bullet.appendChild(deleteBtn);
        }
      });
    }
  });
}
function addNewSection(button, sectionType) {
  console.log('Adding new section:', sectionType);

  addNewItem(button, sectionType);
}

function addTagEventListeners(tag) {
  const deleteBtn = tag.querySelector('.tag-delete');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      // Check if this is a skills tag for special handling
      if (tag.closest('[data-section-type="skills"]')) {
        deleteSkillTag(deleteBtn);
      } else {
        // Original delete logic for other tags
        tag.style.transition = 'all 0.3s ease';
        tag.style.opacity = '0';
        tag.style.transform = 'scale(0.8)';
        
        setTimeout(() => {
          tag.remove();
          state.hasUnsavedChanges = true;
          saveResumeData({ showNotifications: false, isAutoSave: true });
          showEnhancedNotification('Tag removed successfully', 'success');
        }, 300);
      }
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
    
    // Add entrance animation
    newTag.style.cssText = `
      opacity: 0;
      transform: scale(0.8);
      transition: all 0.3s ease;
    `;
    
    tagsContainer.insertBefore(newTag, button);
    addTagEventListeners(newTag);
    
    // Animate in
    setTimeout(() => {
      newTag.style.opacity = '1';
      newTag.style.transform = 'scale(1)';
    }, 10);
    
    state.hasUnsavedChanges = true;
    saveResumeData({ showNotifications: false, isAutoSave: true });
  }
}

function addItemEventListeners(item) {
  console.log('Enhanced item listener initialized');

  const deleteBtn = item.querySelector('.item-btn.delete');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const itemId = item.dataset.itemId || item.id?.replace('item-', '');

      // Enhanced confirmation
      const confirmed = await showEnhancedConfirmModal({
        title: 'Delete Item',
        message: 'Are you sure you want to delete this item?',
        details: 'This action cannot be undone.',
        confirmText: 'Delete',
        confirmStyle: 'danger',
        icon: 'fas fa-exclamation-triangle'
      });

      if (!confirmed) return;

      const sectionType = item.closest('.resume-section')?.dataset.sectionType;
      if (!sectionType) {
        console.error('Section type not found');
        showEnhancedNotification('Error: Section type not found', 'error');
        return;
      }

      const resumeContainer = document.querySelector('.resume-builder') || (window.parent?.document?.querySelector('.resume-builder'));
      const resumeId = resumeContainer?.dataset.resumeId;
      if (!resumeId) {
        console.error('Resume ID not found');
        showEnhancedNotification('Error: Resume ID not found', 'error');
        return;
      }

      if (!itemId) {
        console.error('Item ID not found');
        showEnhancedNotification('Error: Item ID not found', 'error');
        return;
      }

      // Add professional delete animation
      item.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
      item.style.opacity = '0.5';
      item.style.transform = 'scale(0.95) translateX(-10px)';
      item.style.filter = 'blur(1px)';

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
          setTimeout(() => {
            item.remove();
            showEnhancedNotification('Item deleted successfully', 'success');
          }, 300);
        } else {
          // Reset animation on error
          item.style.opacity = '1';
          item.style.transform = 'scale(1) translateX(0)';
          item.style.filter = 'none';
          showEnhancedNotification(`Failed to delete item: ${data.message || 'Unknown error'}`, 'error');
        }
      } catch (error) {
        console.error('Delete error:', error);
        showEnhancedNotification('Error deleting item', 'error');
        // Reset animation on error
        item.style.opacity = '1';
        item.style.transform = 'scale(1) translateX(0)';
        item.style.filter = 'none';
      }
    });
  }
}
function addNewItem(button, type) {
  if (button.dataset.adding === 'true') {
    return;
  }
  button.dataset.adding = 'true';
  
  const originalButtonContent = button.innerHTML;
  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
  button.disabled = true;
  
  try {
    const currentTemplateName = getCurrentTemplateName();
    const templateConfig = templateConfigs[currentTemplateName];

    if (!templateConfig || !templateConfig[type]) {
      throw new Error(`No template configuration found for ${currentTemplateName}.${type}`);
    }
    
    // Determine target document
    const targetDoc = window !== window.parent ? document : getIframeDocument() || document;
    
    // Create new item
    const newItem = createItemElement(type, templateConfig[type]);
    
    // Find or create section container
    let container = findSectionContainer(targetDoc, type);
    
    if (!container) {
      // Create new section if none exists
      container = createNewSection(targetDoc, type);
    }
    
    // Insert item
    insertItemWithAnimation(container, newItem, button);
    
    // Setup editing
    makeItemEditable(newItem);
    
    state.hasUnsavedChanges = true;
    saveResumeData({ showNotifications: false, isAutoSave: true });
    
  } catch (error) {
    console.error('Error adding new item:', error);
    showEnhancedNotification(`❌ Failed to add ${type}: ${error.message}`, 'error');
  } finally {
    setTimeout(() => {
      button.innerHTML = originalButtonContent;
      button.disabled = false;
      button.dataset.adding = 'false';
    }, 500);
  }
}


function createItemElement(type, templateHTML) {
  const uniqueId = generateUniqueId();
  const wrapper = document.createElement('div');
  
  wrapper.innerHTML = templateHTML;
  const newItem = wrapper.firstElementChild;
  
  newItem.dataset.itemId = uniqueId;
  newItem.dataset.sectionType = type;
  newItem.id = `item-${uniqueId}`;
  
  // Setup bullet points if this item has description field
  const descriptionField = newItem.querySelector('.section-description');
  if (descriptionField) {
    handleDescriptionField(descriptionField);
  }
  
  return newItem;
}

function findSectionContainer(doc, sectionType) {
  // First try to find existing section
  let container = doc.querySelector(`.${sectionType}-section`);
  
  if (container) {
    return container;
  }
  
  // If no section exists, try to find empty state container
  container = doc.querySelector(`#${sectionType}-container`);
  
  if (container && container.classList.contains('empty')) {
    // Convert empty state to actual section
    const section = doc.createElement('section');
    section.className = `resume-section ${sectionType}-section`;
    section.setAttribute('data-section-type', sectionType);
    
    // Add section title
    const title = doc.createElement('h2');
    title.className = 'section-title';
    title.contentEditable = true;
    title.innerHTML = `<i class="fas fa-${getSectionIcon(sectionType)}"></i>${getSectionDisplayName(sectionType)}`;
    section.appendChild(title);
    
    // Replace empty container with section
    container.parentNode.replaceChild(section, container);
    return section;
  }
  
  return null;
}

function removeEmptyState(container) {
  if (container.classList.contains('empty')) {
    container.classList.remove('empty');
    
    // Remove empty state content (add buttons, placeholder text)
    const emptyContent = container.querySelector('.add-section-btn, .empty-placeholder');
    if (emptyContent) {
      emptyContent.remove();
    }
  }
}

function insertItemWithAnimation(container, newItem, button) {
  // Add entrance animation
  newItem.style.cssText += `
    opacity: 0;
    transform: translateY(20px) scale(0.95);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  `;
  
  // Insert before the add button, or at the end
  if (button && container.contains(button)) {
    container.insertBefore(newItem, button);
  } else {
    container.appendChild(newItem);
  }
  
  // Trigger animation
  setTimeout(() => {
    newItem.style.opacity = '1';
    newItem.style.transform = 'translateY(0) scale(1)';
  }, 50);
}

function makeItemEditable(item) {
  // Make all data-field elements editable
  item.querySelectorAll('[data-field]').forEach(field => {
    if (!field.hasAttribute('contenteditable') && !field.classList.contains('section-description')) {
      field.contentEditable = true;
    }
    
    // Special handling for description fields with bullet lists
    if (field.dataset.field === 'description') {
      handleDescriptionField(field);
    }
    
    // Add placeholder behavior for simple fields
    if (field.hasAttribute('placeholder')) {
      handlePlaceholderField(field);
    }
  });
  // Setup item event listeners
  addItemEventListeners(item);
}

// function to create a section if it doesn't exist
function createNewSection(doc, sectionType) {
  const section = doc.createElement('section');
  section.className = `resume-section ${sectionType}-section`;
  section.setAttribute('data-section-type', sectionType);
  
  const title = doc.createElement('h2');
  title.className = 'section-title';
  title.contentEditable = true;
  title.innerHTML = `<i class="fas fa-${getSectionIcon(sectionType)}"></i>${getSectionDisplayName(sectionType)}`;
  
  section.appendChild(title);
  
  // Find a good place to insert the section
  const lastSection = doc.querySelector('.resume-section:last-of-type');
  if (lastSection) {
    lastSection.parentNode.insertBefore(section, lastSection.nextSibling);
  } else {
    const header = doc.querySelector('.resume-header');
    if (header) {
      header.parentNode.insertBefore(section, header.nextSibling);
    } else {
      doc.body.appendChild(section);
    }
  }
  
  return section;
}
// function to handle description input with list formatting
function handleDescriptionInput(e) {
  const field = e.target;
  const text = field.textContent;
  
  // If user types bullet points manually, convert to proper list
  if (text.includes('•') || text.includes('-') || text.includes('*')) {
    const lines = text.split('\n').filter(line => line.trim());
    if (lines.length > 1) {
      const ul = document.createElement('ul');
      ul.className = 'duties-list';
      
      lines.forEach(line => {
        const cleanLine = line.replace(/^[•\-*]\s*/, '').trim();
        if (cleanLine) {
          const li = document.createElement('li');
          li.textContent = cleanLine;
          li.contentEditable = true;
          ul.appendChild(li);
        }
      });
      
      field.innerHTML = '';
      field.appendChild(ul);
    }
  }
}

// function to initialize bullets in iframe
function initializeIframeBullets(iframeDoc) {
  // Make addNewBulletPoint available in iframe context
  iframeDoc.defaultView.addNewBulletPoint = addNewBulletPoint;
  
  // Initialize existing bullets in iframe
  iframeDoc.querySelectorAll('.section-description').forEach(descriptionElement => {
    const dutiesList = descriptionElement.querySelector('.duties-list');
    if (dutiesList) {
      dutiesList.querySelectorAll('li').forEach(bullet => {
        setupBulletEventListeners(bullet);
        
        // Add delete button if missing
        if (!bullet.querySelector('.bullet-delete')) {
          const deleteBtn = iframeDoc.createElement('button');
          deleteBtn.className = 'bullet-delete';
          deleteBtn.innerHTML = '×';
          deleteBtn.title = 'Delete this point';
          deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteBulletPoint(bullet);
          };
          bullet.appendChild(deleteBtn);
        }
      });
    }
  });
}

function handleDescriptionField(descriptionField) {
  const dutiesList = descriptionField.querySelector('.duties-list');
  const promptElement = descriptionField.querySelector('.add-bullet-prompt');
  
  if (dutiesList) {
    // Initialize existing bullets
    dutiesList.querySelectorAll('li').forEach(bullet => {
      setupBulletEventListeners(bullet);
      
      // Add delete button if missing
      if (!bullet.querySelector('.bullet-delete')) {
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'bullet-delete';
        deleteBtn.innerHTML = '×';
        deleteBtn.title = 'Delete this point';
        deleteBtn.onclick = (e) => {
          e.stopPropagation();
          deleteBulletPoint(bullet);
        };
        bullet.appendChild(deleteBtn);
      }
    });
  }
  
  // Ensure prompt element has correct onclick
  if (promptElement && !promptElement.onclick) {
    promptElement.onclick = () => addNewBulletPoint(promptElement);
  }
}

function handlePlaceholderField(field) {
  // Focus event - clear placeholder styling
  field.addEventListener('focus', () => {
    field.classList.remove('placeholder');
  });
  
  // Blur event - add placeholder styling if empty
  field.addEventListener('blur', () => {
    if (field.textContent.trim() === '') {
      field.classList.add('placeholder');
    }
  });
  
  // Input event - remove placeholder styling when typing
  field.addEventListener('input', () => {
    if (field.textContent.trim() !== '') {
      field.classList.remove('placeholder');
    }
  });
  
  // Initial state
  if (field.textContent.trim() === '') {
    field.classList.add('placeholder');
  }
}

// Helper function to populate existing section
function populateExistingSection(sectionElement, sectionData) {
  // Clear existing items
  const existingItems = sectionElement.querySelectorAll('.section-item');
  existingItems.forEach(item => item.remove());
  
  // Add new items based on data
  if (sectionData.items && Array.isArray(sectionData.items)) {
    const templateConfig = templateConfigs[getCurrentTemplateName()];
    const addButton = sectionElement.querySelector('.add-item-btn');
    
    sectionData.items.forEach(itemData => {
      if (templateConfig && templateConfig[sectionData.type]) {
        const itemElement = createItemElement(sectionData.type, templateConfig[sectionData.type]);
        populateItemFromData(itemElement, itemData);
        
        // Insert before add button if it exists
        if (addButton) {
          sectionElement.insertBefore(itemElement, addButton);
        } else {
          sectionElement.appendChild(itemElement);
        }
      }
    });
  }
}

function createAndPopulateSection(sectionData) {
  const newSection = createSectionFromData(sectionData);
  
  // Find appropriate place to insert
  const lastSection = document.querySelector('.resume-section:last-of-type');
  if (lastSection) {
    lastSection.parentNode.insertBefore(newSection, lastSection.nextSibling);
  } else {
    const header = document.querySelector('.resume-header');
    if (header) {
      header.parentNode.insertBefore(newSection, header.nextSibling);
    }
  }
}
async function addNewSkillTag(button) {
  const skillName = prompt('Enter skill name:');
  if (!skillName || !skillName.trim()) return;
  
  const trimmedSkill = skillName.trim();
  const tagsContainer = button.parentElement;
  
  // Check for duplicates
  const existingTags = Array.from(tagsContainer.querySelectorAll('.section-tag'));
  const isDuplicate = existingTags.some(tag => {
    const tagText = tag.textContent.replace(/\s*✓\s*/, '').replace(/\s*×\s*/, '').trim();
    return tagText.toLowerCase() === trimmedSkill.toLowerCase();
  });
  
  if (isDuplicate) {
    showEnhancedNotification('This skill already exists!', 'warning');
    return;
  }
  
  const newTag = document.createElement('span');
  newTag.className = 'section-tag';
  newTag.innerHTML = `
    <i class="fas fa-check"></i>
    ${trimmedSkill}
    <i class="fas fa-times tag-delete"></i>
  `;
  
  // Add entrance animation
  newTag.style.cssText = `
    opacity: 0;
    transform: scale(0.8);
    transition: all 0.3s ease;
  `;
  
  tagsContainer.insertBefore(newTag, button);
  addTagEventListeners(newTag);
  
  // Animate in
  setTimeout(() => {
    newTag.style.opacity = '1';
    newTag.style.transform = 'scale(1)';
  }, 10);
  
  state.hasUnsavedChanges = true;
  await saveResumeData({ showNotifications: false, isAutoSave: true })
  showEnhancedNotification(`✅ Added skill: ${trimmedSkill}`, 'success');
}
async function editSkillTag(tag) {
  const currentSkill = tag.textContent.replace(/\s*✓\s*/, '').replace(/\s*×\s*/, '').trim();
  const newSkill = prompt('Edit skill name:', currentSkill);
  if (!newSkill || !newSkill.trim() || newSkill.trim() === currentSkill) return;

  const trimmedSkill = newSkill.trim();
  const tagsContainer = tag.parentElement;

  // Check for duplicates
  const existingTags = Array.from(tagsContainer.querySelectorAll('.section-tag'));
  const isDuplicate = existingTags.some(otherTag => {
    if (otherTag === tag) return false;
    const tagText = otherTag.textContent.replace(/\s*✓\s*/, '').replace(/\s*×\s*/, '').trim();
    return tagText.toLowerCase() === trimmedSkill.toLowerCase();
  });

  if (isDuplicate) {
    showEnhancedNotification('This skill already exists!', 'warning');
    return;
  }

  // Update tag content
  tag.innerHTML = `
    <i class="fas fa-check"></i>
    ${trimmedSkill}
    <i class="fas fa-times tag-delete"></i>
  `;

  // Re-attach event listeners
  window.addTagEventListeners(tag);

  // Trigger auto-save
  state.hasUnsavedChanges = true;
  await saveResumeData({ showNotifications: false, isAutoSave: true });
  showEnhancedNotification(`✅ Updated skill to: ${trimmedSkill}`, 'success');
}
async function deleteSkillTag(deleteBtn) {
  const tag = deleteBtn.closest('.section-tag');
  if (!tag) return;
  
  const skillName = tag.textContent.replace(/\s*✓\s*/, '').replace(/\s*×\s*/, '').trim();
  
  // Add enhanced delete animation
  tag.style.transition = 'all 0.3s ease';
  tag.style.opacity = '0';
  tag.style.transform = 'scale(0.8)';
  
  setTimeout(async () => {
    tag.remove();
    state.hasUnsavedChanges = true;
    await saveResumeData({ showNotifications: false, isAutoSave: true })
    showEnhancedNotification(`Removed skill: ${skillName}`, 'success');
  }, 300);
}

function getCurrentTemplateName() {

  // First try to get from meta tag
  const metaTemplate = document.querySelector('meta[name="template"]');
  let templateName = metaTemplate ? metaTemplate.getAttribute('content').split("_")[1] : null;

  // If not found, try to get from selected radio button
  if (!templateName) {
    const selectedRadio = document.querySelector('input[name="template"]:checked');
    templateName = selectedRadio ? selectedRadio.value.split('_')[1] : 'classic';
  }

  return templateName;
}

function handleTemplateSelection(templateId, templateName) {
  showIframeLoading(`Applying ${templateName || templateId} template...`);
  state.currentTemplate = templateId;
  updateTemplateMetaTag(templateId);
  
  // Simulate template loading
  setTimeout(() => {
    hideIframeLoading();
    showEnhancedNotification(`✨ ${templateName || templateId} template applied successfully!`, 'success');
    state.hasUnsavedChanges = true;
  }, 1500);
}

function handleTemplateSelectButton(button) {
  const templateOption = button.closest('.template-option');
  const radio = templateOption.querySelector('input[name="template"]');
  
  if (radio) {
    radio.checked = true;
    
    // Add loading state to button
    const originalText = button.textContent;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    button.disabled = true;
    
    setTimeout(() => {
      // Trigger the form submission
      const form = document.getElementById('template-form');
      if (form) {
        form.submit();
      }
    }, 500);
  }
}

function handleAIFeature(action) {
  const features = {
    'enhance-bullets': 'Enhancing your experience bullets with AI...',
    'suggest-skills': 'Analyzing your profile for skill suggestions...',
    'ats-scan': 'Running ATS compatibility scan...',
    'grammar-check': 'Checking grammar and style...'
  };

  const message = features[action] || 'Processing AI request...';
  showIframeLoading(message, 'AI is analyzing your resume content');
  
  // Simulate AI processing
  setTimeout(() => {
    hideIframeLoading();
    showEnhancedNotification('✅ AI analysis complete! Check your resume for improvements.', 'success');
  }, 3000);
  
  closeAIModalWithAnimation();
}

function openAIModalWithAnimation() {
  const aiModal = document.querySelector('#ai-assistant-modal');
  const content = aiModal.querySelector('.ai-modal-content');
  
  aiModal.classList.add('active');
  content.classList.add('bounce-in');
  
  setTimeout(() => {
    content.classList.remove('bounce-in');
  }, 600);
}

function closeAIModalWithAnimation() {
  const aiModal = document.querySelector('#ai-assistant-modal');
  aiModal.classList.remove('active');
}

function toggleTemplatePanelWithAnimation() {
  const templatesPanel = document.querySelector('#templates-panel');
  templatesPanel.classList.toggle('active');
}


function showIframeLoading(message = 'Loading...', subtext = 'Please wait while we process your request') {
  const loadingOverlay = document.querySelector('.iframe-loading-overlay');
  if (loadingOverlay) {
    loadingOverlay.querySelector('.loading-text').textContent = message;
    loadingOverlay.querySelector('.loading-subtext').textContent = subtext;
    loadingOverlay.classList.add('active');
  }
}

function hideIframeLoading() {
  const loadingOverlay = document.querySelector('.iframe-loading-overlay');
  if (loadingOverlay) {
    loadingOverlay.classList.remove('active');
  }
}

function updateTemplateMetaTag(templateId) {
  let metaTemplate = document.querySelector('meta[name="template"]');
  if (!metaTemplate) {
    metaTemplate = document.createElement('meta');
    metaTemplate.setAttribute('name', 'template');
    document.head.appendChild(metaTemplate);
  }
  metaTemplate.setAttribute('content', templateId);
}

async function saveResumeData(options = {}) {
  console.log("saving resume data");
  console.log(options);
  const { 
    showNotifications = true, 
    isAutoSave = false 
  } = options;
  
  // Check if content generation is in progress
  if (state.isGeneratingContent) return false;

  try {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    // const resumeId = document.querySelector('.resume-header')?.dataset.resumeId;
 
    const iframe = document.querySelector("#preview-iframe");
    const resumeId = iframe.getAttribute("resume_id");

    // Enhanced error handling with indicator management
    if (!resumeId) {
      if (showNotifications) {
        showEnhancedNotification('Error: Resume ID not found', 'error');
      }
      if (isAutoSave) {
        hideAutoSaveIndicator();
      }
      return false;
    }
    
    if (!iframe || !iframe.contentDocument) {
      if (showNotifications) {
        showEnhancedNotification('Error: Cannot access resume content', 'error');
      }
      if (isAutoSave) {
        hideAutoSaveIndicator();
      }
      return false;
    }

    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    const resumeContent = collectResumeData(iframeDoc);
    
    // Enhanced data validation with indicator management
    if (!resumeContent || !resumeContent.sections) {
      if (isAutoSave) {
        hideAutoSaveIndicator();
      }
      throw new Error('Invalid resume data collected');
    }

    const response = await fetch(`/api/v1/resume/${resumeId}/save-data`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json', 
        'X-CSRFToken': csrfToken 
      },
      body: JSON.stringify({ 
        resume_data: resumeContent,
        timestamp: new Date().toISOString()
      }),
    });

    const data = await response.json();
    
    if (response.ok && data.success) {
      state.hasUnsavedChanges = false;
      
      updateSaveButtonState('saved');
    
      return true;
    } else {

      throw new Error(data.message || 'Server returned error');
    }
    
  } catch (error) {
    console.error(isAutoSave ? 'Auto-save failed:' : 'Error saving resume:', error);
    
    // Show notification for manual save or if requested
    if (showNotifications && !isAutoSave) {
      showEnhancedNotification(`❌ Save failed: ${error.message}`, 'error');
    }
    
    return false;
  }
}


function handleKeyboardShortcuts(e) {
  // Ctrl/Cmd + S to save
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    saveResumeData({ showNotifications: false, isAutoSave: true });
  }
  
  // Escape to close modals/panels
  if (e.key === 'Escape') {
    const aiModal = document.querySelector('#ai-assistant-modal');
    const templatesPanel = document.querySelector('#templates-panel');
    
    if (aiModal?.classList.contains('active')) {
      closeAIModalWithAnimation();
    }
    if (templatesPanel?.classList.contains('active')) {
      templatesPanel.classList.remove('active');
    }
  }
}

async function handlePDFPreview() {
  const resumeId = document.querySelector('.resume-builder')?.dataset.resumeId;
  if (!resumeId) {
    showEnhancedNotification('Error: Resume ID not found', 'error');
    return;
  }

  showEnhancedNotification('📄 Preparing PDF preview...', 'info');

  const modal = document.createElement('div');
  modal.className = 'enhanced-pdf-modal';
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
  
  modal.innerHTML = `
    <div class="modal-content" style="
      background: white;
      border-radius: 20px;
      width: 90%;
      max-width: 900px;
      height: 80vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transform: scale(0.9);
      transition: transform 0.3s ease;
    ">
      <div style="
        background: linear-gradient(135deg, #4F46E5, #7C3AED);
        color: white;
        padding: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      ">
        <h3 style="margin: 0; font-size: 18px; font-weight: 700;">📄 PDF Preview</h3>
        <button id="close-preview-btn" style="
          background: rgba(255, 255, 255, 0.2);
          border: none;
          color: white;
          width: 32px;
          height: 32px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 18px;
        ">&times;</button>
      </div>
      <iframe id="pdf-preview-iframe" style="flex: 1; border: none;"></iframe>
    </div>
  `;
  
  document.body.appendChild(modal);

  // Animate in
  setTimeout(() => {
    modal.style.opacity = '1';
    modal.querySelector('.modal-content').style.transform = 'scale(1)';
  }, 10);

  // Fetch and display preview
  try {
    const response = await fetch(`/api/v1/resume/${resumeId}/preview`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    const htmlContent = await response.text();
    const previewIframe = modal.querySelector('#pdf-preview-iframe');
    previewIframe.srcdoc = htmlContent;
    showEnhancedNotification('✅ PDF preview loaded successfully!', 'success');
  } catch (error) {
    showEnhancedNotification('Error loading PDF preview', 'error');
    document.body.removeChild(modal);
  }

  // Close modal handler
  const closeModal = () => {
    modal.style.opacity = '0';
    modal.querySelector('.modal-content').style.transform = 'scale(0.9)';
    setTimeout(() => {
      document.body.removeChild(modal);
    }, 300);
  };

  modal.querySelector('#close-preview-btn').addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });
}

function showEnhancedNotification(message, type = 'info') {
  const existing = document.querySelectorAll('.enhanced-notification');
  existing.forEach(n => {
    n.style.opacity = '0';
    n.style.transform = 'translateX(100%)';
    n.remove();
  });
  
  const notification = document.createElement('div');
  notification.className = `enhanced-notification notification ${type}`;
  
  const icons = {
    success: 'fas fa-check-circle',
    error: 'fas fa-exclamation-circle',
    warning: 'fas fa-exclamation-triangle',
    info: 'fas fa-info-circle'
  };
  
  const colors = {
    success: '#10B981',
    error: '#EF4444',
    warning: '#F59E0B',
    info: '#3B82F6'
  };
  
  
  
  notification.innerHTML = `
    <div style="padding: 20px; display: flex; align-items: flex-start; gap: 16px;">
      <div style="
        width: 24px; height: 24px; background: ${colors[type]}; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;
      ">
        <i class="${icons[type]}" style="color: white; font-size: 12px;"></i>
      </div>
      <div style="flex: 1; min-width: 0; overflow: hidden;">
        <div style="color: #1F2937; font-size: 15px; line-height: 1.5; font-weight: 600; word-wrap: break-word; margin-bottom: 4px; overflow-wrap: break-word;">
          ${message}
        </div>
        <div style="color: #6B7280; font-size: 12px; font-weight: 500;">Just now</div>
      </div>
      <button class="notification-close" style="
        background: none; border: none; color: #9CA3AF; cursor: pointer; font-size: 18px;
        padding: 4px; width: 28px; height: 28px; display: flex; align-items: center;
        justify-content: center; border-radius: 6px; transition: all 0.2s ease; flex-shrink: 0;
      ">&times;</button>
    </div>
  `;
  
  document.body.appendChild(notification);
  
  // Show with animation
  setTimeout(() => {
    notification.style.opacity = '1';
    notification.style.transform = 'translateX(0)';
  }, 10);
  
  // Auto-hide
  const autoHide = setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => notification.remove(), 400);
  }, 4000);
  
  // Close button
  notification.querySelector('.notification-close').addEventListener('click', () => {
    clearTimeout(autoHide);
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => notification.remove(), 400);
  });
}
// Function to load and populate resume data
function loadResumeData(resumeData) {
  if (!resumeData) {
    console.warn('No resume data provided');
    return;
  }
  
  // Populate bio data
  if (resumeData.bio) {
    const nameElement = document.querySelector('.name');
    const titleElement = document.querySelector('.title');
    
    if (nameElement && resumeData.bio.name) {
      nameElement.textContent = resumeData.bio.name;
    }
    if (titleElement && resumeData.bio.title) {
      titleElement.textContent = resumeData.bio.title;
    }
  }
  
  // Populate contact data
  if (resumeData.contact) {
    Object.keys(resumeData.contact).forEach(contactType => {
      const contactElement = document.querySelector(`[data-field="${contactType}"]`);
      if (contactElement) {
        contactElement.textContent = resumeData.contact[contactType];
      }
    });
  }
  
  // Populate sections
  if (resumeData.sections && Array.isArray(resumeData.sections)) {
    resumeData.sections.forEach(sectionData => {
      const existingSection = document.querySelector(`.${sectionData.type}-section`);
      
      if (existingSection) {
        populateExistingSection(existingSection, sectionData);
      } else {
        createAndPopulateSection(sectionData);
      }
    });
  }
  
}
function collectResumeData(iframeDoc) {
  const resumeData = { contact: {}, sections: [], bio: { name: '', title: '' } };

  // Collect bio data
  resumeData.bio.name = iframeDoc.querySelector('.name')?.textContent.trim() || '';
  resumeData.bio.title = iframeDoc.querySelector('.title')?.textContent.trim() || '';

  // Collect contact info
  iframeDoc.querySelectorAll('.contact-item').forEach(item => {
    const iconClass = item.querySelector('.contact-icon')?.className;
    const content = item.querySelector('.contact-content')?.textContent.trim();
    if (iconClass && content) {
      const match = iconClass.match(/fa-(\w+)/);
      if (match) {
        const key = match[1] === 'envelope' ? 'email' : 
                   match[1] === 'map-marker-alt' ? 'location' : 
                   match[1] === 'linkedin-in' ? 'linkedin' : match[1];
        resumeData.contact[key] = content;
      }
    }
  });

  // Define known section types
  const knownSectionTypes = [
    'experience', 'education', 'skills', 'summary', 'certification', 
    'project', 'volunteer', 'award', 'publication', 'language'
  ];

  iframeDoc.querySelectorAll('.resume-section').forEach(section => {
    let sectionType = 'custom';
    
    // Determine section type
    if (section.dataset.sectionType) {
      sectionType = section.dataset.sectionType;
    } else {
      const classList = section.className.split(' ');
      for (const className of classList) {
        const match = className.match(/^(\w+)-section$/);
        if (match && match[1] && knownSectionTypes.includes(match[1])) {
          sectionType = match[1];
          break;
        }
      }
    }

    const sectionTitle = section.querySelector('.section-title')?.textContent.trim().replace(/[^\w\s]/g, '').trim();
    const sectionData = { 
      type: sectionType, 
      title: sectionTitle, 
      display: 'list', 
      content: '', 
      items: [] 
    };

    // Handle different section types
    if (section.querySelector('.section-content')) {
      sectionData.display = 'text';
      sectionData.content = section.querySelector('.section-content')?.textContent.trim() || '';
    } else if (section.querySelector('.section-container')) {
      sectionData.display = 'tags';
      sectionData.items = Array.from(section.querySelectorAll('.section-tag')).map(tag => {
        // Clean up tag text (remove icons and extra spaces)
        let tagText = tag.textContent || '';
        tagText = tagText.replace(/\s*✓\s*/, '').replace(/\s*×\s*/, '').trim();
        return tagText;
      }).filter(text => text.length > 0);
    } else {
      // List items
      sectionData.display = 'list';
      sectionData.items = Array.from(section.querySelectorAll('.section-item')).map(item => {
        const itemData = {};
        
        // Ensure item has an ID
        itemData.id = item.dataset.itemId || generateUniqueId();
        item.dataset.itemId = itemData.id;

        // Collect field data
        item.querySelectorAll('[data-field]').forEach(field => {
          const fieldName = field.dataset.field;
          let fieldValue = '';
          
          if (fieldName === 'description' && field.querySelector('.duties-list')) {
            // Handle bullet point descriptions
            fieldValue = collectBulletData(field);
          } else {
            // Handle regular text fields
            fieldValue = field.textContent.trim();
          }
          
          // Map field names for different section types
          let mappedFieldName = fieldName;
          if (sectionType === 'certification') {
            if (fieldName === 'degree') mappedFieldName = 'name';
            if (fieldName === 'school') mappedFieldName = 'issuer';
          }
          if (sectionType === 'experience' && fieldName === 'date') {
            mappedFieldName = 'duration';
          }
          
          itemData[mappedFieldName] = fieldValue;
        });

        return itemData;
      });
    }

    // Only add section if it has content
    if (sectionData.content || sectionData.items.length > 0) {
      resumeData.sections.push(sectionData);
    }
  });
  return resumeData;
}


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
          display: flex;
          align-items: center;
          justify-content: center;
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
    
    modal.querySelector('.btn-cancel').addEventListener('click', () => closeModal(false));
    modal.querySelector('.btn-confirm').addEventListener('click', () => closeModal(true));
    
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal(false);
    });
    
    // Keyboard handling
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

// Debounce utility
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

function getIframeDocument() {
  const iframe = document.getElementById('preview-iframe');
  return iframe?.contentDocument || iframe?.contentWindow?.document;
}

function generateUniqueId() {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Helper function to get section icons
function getSectionIcon(sectionType) {
  const icons = {
    'summary': 'user',
    'experience': 'briefcase',
    'education': 'graduation-cap',
    'skills': 'cogs',
    'certification': 'certificate',
    'project': 'code',
    'volunteer': 'hands-helping',
    'award': 'trophy',
    'publication': 'book',
    'language': 'language'
  };
  return icons[sectionType] || 'star';
}

// Helper function to get section display names
function getSectionDisplayName(sectionType) {
  const names = {
    'summary': 'Professional Summary',
    'experience': 'Professional Experience',
    'education': 'Education',
    'skills': 'Skills',
    'certification': 'Certifications',
    'project': 'Projects',
    'volunteer': 'Volunteer Experience',
    'award': 'Awards',
    'publication': 'Publications',
    'language': 'Languages'
  };
  return names[sectionType] || sectionType.charAt(0).toUpperCase() + sectionType.slice(1);
}

function hideAutoSaveIndicator() {
  let indicator = document.querySelector('.auto-save-indicator');
  if (indicator) {
    indicator.classList.remove('show', 'success');
  }
}

function updateSaveButtonState(state) {
  const saveButton = document.querySelector('#save-resume-btn');
  const buttonText = saveButton.querySelector('span');
  const buttonIcon = saveButton.querySelector('i');
  
  if (!saveButton) return;
  
  // Remove all state classes
  saveButton.classList.remove('saving', 'saved');
  
  switch(state) {
    case 'saving':
      saveButton.classList.add('saving');
      saveButton.disabled = true;
      buttonText.textContent = 'Saving';
      buttonIcon.className = 'fas fa-spinner';
      break;
      
    case 'saved':
      saveButton.classList.add('saved');
      saveButton.disabled = false;
      buttonText.textContent = 'Saved';
      buttonIcon.className = 'fas fa-check';
      
      // Reset to normal after 2 seconds
      setTimeout(() => {
        saveButton.classList.remove('saved');
        buttonText.textContent = 'Save';
        buttonIcon.className = 'fas fa-save';
      }, 2000);
      break;
      
    case 'unsaved':
      saveButton.disabled = false;
      buttonText.textContent = 'Save';
      buttonIcon.className = 'fas fa-save';
      break;
  }
}
// Export enhanced functions globally
window.handleDescriptionField = handleDescriptionField;
window.handlePlaceholderField = handlePlaceholderField;
window.initializeIframeBullets = initializeIframeBullets;
window.addNewBulletPoint = addNewBulletPoint;
window.deleteBulletPoint = deleteBulletPoint;
window.initializeExistingBullets = initializeExistingBullets;

window.collectResumeData = collectResumeData;
window.collectBulletData = collectBulletData;
window.populateBulletPoints = populateBulletPoints;
window.addBulletFromData = addBulletFromData;
window.saveResumeData = saveResumeData;
window.loadResumeData = loadResumeData;
window.populateExistingSection = populateExistingSection;
window.createAndPopulateSection = createAndPopulateSection;


window.addItemEventListeners = addItemEventListeners;
window.addTagEventListeners = addTagEventListeners;
window.addNewTag = addNewTag;
window.addNewItem = addNewItem;

window.addNewSkillTag = addNewSkillTag;
window.deleteSkillTag = deleteSkillTag;
window.editSkillTag = editSkillTag;