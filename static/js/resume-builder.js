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
};

const templateConfigs = {
  classic: {
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
    `
  },
  
  cards: {
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

  // Initialize professional enhancements
  initializeEnhancements();

  // Save button handler with enhanced feedback
  if (elements.saveButton) {
    elements.saveButton.addEventListener('click', enhancedSaveResume);
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

  // Enhanced tooltip handlers
  elements.tooltipContainers.forEach(container => {
    const tooltip = container.querySelector('.btn-tooltip');
    if (tooltip) {
      container.addEventListener('mouseenter', () => {
        tooltip.style.opacity = '1';
        tooltip.style.visibility = 'visible';
        tooltip.style.transform = 'translateY(-50%) translateX(8px)';
      });
      container.addEventListener('mouseleave', () => {
        tooltip.style.opacity = '0';
        tooltip.style.visibility = 'hidden';
        tooltip.style.transform = 'translateY(-50%) translateX(0)';
      });
    }
  });

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
      elements.templatesPanel.classList.remove('active');
    }
  });

  // Enhanced add button handlers
  document.querySelectorAll(selectors.addButtons).forEach(btn => {
    if (btn.id.startsWith('add-')) {
      const type = btn.id.replace('add-', '').replace('-btn', '');
      btn.addEventListener('click', () => {
        if (type === 'skills') addNewTag(btn);
        else if (type !== 'summary') addNewItem(btn, type);
      });
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

  // Enhanced input change handler with professional debouncing
  document.addEventListener('input', debounce((e) => {
    if (e.target.getAttribute('contenteditable') === 'true') {
      state.hasUnsavedChanges = true;
      clearTimeout(state.autoSaveTimeout);
      state.autoSaveTimeout = setTimeout(enhancedAutoSave, 1500);
      showAutoSaveIndicator();
    }
  }, 100));

  // Enhanced unload warning
  window.addEventListener('beforeunload', (e) => {
    if (state.hasUnsavedChanges) {
      e.preventDefault();
      e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
      return e.returnValue;
    }
  });

  // Enhanced iframe loading with loading overlay
  if (elements.iframe) {
    showIframeLoading('Loading resume preview...');
    elements.iframe.addEventListener('load', () => {
      const iframeDoc = elements.iframe.contentDocument || elements.iframe.contentWindow.document;
      setupIframeListeners(iframeDoc);
      hideIframeLoading();
    });
  }

  // Initial auto-save with delay
  setTimeout(enhancedAutoSave, 3000);

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
      
      // Also initialize iframe content if it exists
      const iframe = document.querySelector('#preview-iframe');
      if (iframe) {
        iframe.addEventListener('load', () => {
          const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
          if (iframeDoc) {
            initializeIframeBullets(iframeDoc);
          }
        });
      }
    }, 500);
});

// Main function to add new bullet points
function addNewBulletPoint(promptElement) {
  const descriptionContainer = promptElement.parentElement;
  const dutiesList = descriptionContainer.querySelector('.duties-list');
  
  // Create new list item
  const newBullet = document.createElement('li');
  newBullet.contentEditable = true;
  newBullet.className = 'new-bullet';
  
  // Add delete button to the bullet
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'bullet-delete';
  deleteBtn.innerHTML = '×';
  deleteBtn.title = 'Delete this point';
  deleteBtn.onclick = (e) => {
    e.stopPropagation();
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
  state.autoSaveTimeout = setTimeout(enhancedAutoSave, 1500);
  
  return newBullet;
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
    state.autoSaveTimeout = setTimeout(enhancedAutoSave, 1500);
    
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
    if (e.key === 'Backspace' && bulletElement.textContent.trim() === '') {
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
  });
  
  // Handle input changes for auto-save
  bulletElement.addEventListener('input', () => {
    state.hasUnsavedChanges = true;
    clearTimeout(state.autoSaveTimeout);
    state.autoSaveTimeout = setTimeout(enhancedAutoSave, 1500);
  });
  
  // Handle focus events
  bulletElement.addEventListener('focus', () => {
    bulletElement.style.outline = 'none';
  });
  
  // Handle blur to clean up empty bullets
  bulletElement.addEventListener('blur', () => {
    // Remove bullet if it's empty and not the only one
    const dutiesList = bulletElement.parentElement;
    const bullets = dutiesList.querySelectorAll('li');
    
    if (bulletElement.textContent.trim() === '' && bullets.length > 1) {
      setTimeout(() => {
        if (document.activeElement !== bulletElement) {
          deleteBulletPoint(bulletElement);
        }
      }, 100);
    }
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
// Helper function to add bullet from existing data
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
  deleteBtn.onclick = (e) => {
    e.stopPropagation();
    deleteBulletPoint(bullet);
  };
  
  bullet.appendChild(deleteBtn);
  setupBulletEventListeners(bullet);
  dutiesList.appendChild(bullet);
  
  return bullet;
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

function initializeEnhancements() {
  // Add professional styles if not exists
  if (!document.querySelector('#professional-enhancements-styles')) {
    const enhancementStyles = document.createElement('style');
    enhancementStyles.id = 'professional-enhancements-styles';
    enhancementStyles.textContent = `
      /* Enhanced floating controls */
      .floating-controls-left .float-control-btn {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
      }
      
      .floating-controls-left .float-control-btn::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
        transition: left 0.5s;
      }
      
      .floating-controls-left .float-control-btn:hover::before {
        left: 100%;
      }
      
      .floating-controls-left .float-control-btn:hover {
        transform: translateY(-4px) scale(1.05);
        box-shadow: 0 12px 40px rgba(79, 70, 229, 0.3);
      }

      /* Enhanced tooltips */
      .btn-tooltip {
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
      }

      /* Enhanced template panel */
      .slide-panel {
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      }

      .template-label {
        transition: all 0.3s ease;
      }

      .template-label:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
      }

      .template-overlay {
        transition: all 0.3s ease;
      }

      .template-label:hover .template-overlay {
        opacity: 1;
      }

      .template-label:hover .template-thumbnail {
        transform: scale(1.1);
      }

      /* Enhanced AI modal */
      .ai-modal {
        transition: all 0.3s ease;
      }

      .ai-modal-content {
        transition: transform 0.3s ease;
      }

      .ai-feature-card {
        transition: all 0.3s ease;
      }

      .ai-feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(79, 70, 229, 0.15);
      }

      /* Enhanced save button */
      .save-button {
        transition: all 0.3s ease;
      }

      .save-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(16, 185, 129, 0.4);
      }

      .save-button.saving {
        background: linear-gradient(135deg, #6B7280, #4B5563);
        cursor: not-allowed;
      }

      .save-button.saving i {
        animation: spin 1s linear infinite;
      }

      /* Loading overlay for iframe */
      .iframe-loading-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 500;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        border-radius: 20px;
      }

      .iframe-loading-overlay.active {
        opacity: 1;
        visibility: visible;
      }

      .loading-spinner {
        width: 60px;
        height: 60px;
        border: 4px solid rgba(79, 70, 229, 0.2);
        border-top: 4px solid #4F46E5;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
      }

      .loading-text {
        color: #4F46E5;
        font-size: 16px;
        font-weight: 600;
        text-align: center;
      }

      .loading-subtext {
        color: #6B7280;
        font-size: 14px;
        margin-top: 8px;
        text-align: center;
      }

      /* Auto-save indicator */
      .auto-save-indicator {
        position: fixed;
        bottom: 20px;
        left: 20px;
        background: rgba(79, 70, 229, 0.9);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .auto-save-indicator.show {
        opacity: 1;
        transform: translateY(0);
      }

      .auto-save-indicator.success {
        background: rgba(16, 185, 129, 0.9);
      }

      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }

      @keyframes bounce-in {
        0% { transform: scale(0.3); opacity: 0; }
        50% { transform: scale(1.05); }
        70% { transform: scale(0.9); }
        100% { transform: scale(1); opacity: 1; }
      }

      .bounce-in {
        animation: bounce-in 0.6s ease-out;
      }
    `;
    document.head.appendChild(enhancementStyles);
  }

  // Create iframe loading overlay if it doesn't exist
  if (!document.querySelector('.iframe-loading-overlay')) {
    const previewContainer = document.querySelector('.resume-preview-container');
    if (previewContainer) {
      const loadingOverlay = document.createElement('div');
      loadingOverlay.className = 'iframe-loading-overlay';
      loadingOverlay.innerHTML = `
        <div class="loading-spinner"></div>
        <div class="loading-text">Loading your resume...</div>
        <div class="loading-subtext">Please wait while we prepare your preview</div>
      `;
      previewContainer.appendChild(loadingOverlay);
    }
  }
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
function addNewSection(button, sectionType) {
  console.log('Adding new section:', sectionType);

  addNewItem(button, sectionType);
}
function deleteItem(item) {
  showEnhancedConfirmModal({
    title: 'Delete Item',
    message: 'Are you sure you want to delete this item?',
    details: 'This action cannot be undone.',
    confirmText: 'Delete',
    confirmStyle: 'danger',
    icon: 'fas fa-exclamation-triangle'
  }).then(confirmed => {
    if (confirmed) {
      item.style.transition = 'all 0.3s ease';
      item.style.opacity = '0';
      item.style.transform = 'scale(0.8)';
      setTimeout(() => {
        item.remove();
        state.hasUnsavedChanges = true;
        enhancedAutoSave();
        showEnhancedNotification('Item deleted successfully', 'success');
      }, 300);
    }
  });
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

function showAutoSaveIndicator() {
  let indicator = document.querySelector('.auto-save-indicator');
  if (!indicator) {
    indicator = document.createElement('div');
    indicator.className = 'auto-save-indicator';
    indicator.innerHTML = `
      <div style="width: 12px; height: 12px; border: 2px solid rgba(255, 255, 255, 0.3); border-top: 2px solid white; border-radius: 50%; animation: spin 1s linear infinite;"></div>
      <span>Auto-saving...</span>
    `;
    document.body.appendChild(indicator);
  }
  
  indicator.classList.remove('success');
  indicator.classList.add('show');
  
  setTimeout(() => {
    if (indicator.classList.contains('show')) {
      indicator.innerHTML = `
        <i class="fas fa-check"></i>
        <span>Auto-saved</span>
      `;
      indicator.classList.add('success');
      
      setTimeout(() => {
        indicator.classList.remove('show');
      }, 1500);
    }
  }, 1000);
}

async function enhancedSaveResume() {
  const saveButton = document.querySelector('#save-resume-btn');
  if (!saveButton) return;

  if (!state.hasUnsavedChanges) {
    showEnhancedNotification('✅ Resume is already up to date!', 'success');
    return;
  }

  saveButton.classList.add('saving');
  saveButton.querySelector('span').textContent = 'Saving...';
  
  try {
    await saveResumeData();
    saveButton.classList.remove('saving');
    saveButton.querySelector('span').textContent = 'Save Changes';
    showEnhancedNotification('✅ Resume saved successfully!', 'success');
  } catch (error) {
    saveButton.classList.remove('saving');
    saveButton.querySelector('span').textContent = 'Save Changes';
    showEnhancedNotification('❌ Failed to save resume. Please try again.', 'error');
  }
}

async function enhancedAutoSave() {
  if (state.isGeneratingContent) return;
  
  try {
    await saveResumeData();
  } catch (error) {
    console.error('Auto-save failed:', error);
    showEnhancedNotification('Auto-save failed. Please save manually.', 'warning');
  }
}

function handleKeyboardShortcuts(e) {
  // Ctrl/Cmd + S to save
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    enhancedSaveResume();
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
    setTimeout(() => n.remove(), 300);
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
    border-left: 4px solid ${colors[type]};
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
  `;
  
  notification.innerHTML = `
    <div style="padding: 20px; display: flex; align-items: flex-start; gap: 16px;">
      <div style="
        width: 24px; height: 24px; background: ${colors[type]}; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;
      ">
        <i class="${icons[type]}" style="color: white; font-size: 12px;"></i>
      </div>
      <div style="flex: 1; min-width: 0;">
        <div style="color: #1F2937; font-size: 15px; line-height: 1.5; font-weight: 600; word-wrap: break-word; margin-bottom: 4px;">
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

function setupIframeListeners(iframeDoc) {
  iframeDoc.querySelectorAll('.section-tag').forEach(addTagEventListeners);
  iframeDoc.querySelectorAll('.section-item').forEach(addItemEventListeners);
  
  // Initialize bullet points in iframe
  initializeIframeBullets(iframeDoc);
  
  // Add event listeners for iframe buttons
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
  
  iframeDoc.addEventListener('input', () => {
    state.hasUnsavedChanges = true;
    clearTimeout(state.autoSaveTimeout);
    state.autoSaveTimeout = setTimeout(enhancedAutoSave, 3000);
  });
}

function showSaveStatus(message, isError = false) {
  showEnhancedNotification(message, isError ? 'error' : 'success');
}

async function saveResumeData() {
  const saveButton = document.querySelector('#save-resume-btn');
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
  const resumeId = document.querySelector('.resume-builder')?.dataset.resumeId;
  const iframe = document.querySelector('#preview-iframe');

  if (!resumeId) {
    showEnhancedNotification('Error: Resume ID not found', 'error');
    return false;
  }

  if (!iframe || !iframe.contentDocument) {
    showEnhancedNotification('Error: Cannot access resume content', 'error');
    return false;
  }

  try {
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    const resumeContent = collectResumeData(iframeDoc);
    
    // Validate data before sending
    if (!resumeContent || !resumeContent.sections) {
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
      showEnhancedNotification('✅ Resume saved successfully!', 'success');
      return true;
    } else {
      throw new Error(data.message || 'Server returned error');
    }
    
  } catch (error) {
    console.error('Error saving resume:', error);
    showEnhancedNotification(`❌ Save failed: ${error.message}`, 'error');
    return false;
  }
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

function addTagEventListeners(tag) {
  const deleteBtn = tag.querySelector('.tag-delete');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async () => {
      // Add enhanced delete animation
      tag.style.transition = 'all 0.3s ease';
      tag.style.opacity = '0';
      tag.style.transform = 'scale(0.8)';
      
      setTimeout(() => {
        tag.remove();
        state.hasUnsavedChanges = true;
        enhancedAutoSave();
        showEnhancedNotification('Tag removed successfully', 'success');
      }, 300);
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
    await enhancedAutoSave();
    showEnhancedNotification(`✨ "${tagName}" added successfully!`, 'success');
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

function getCurrentTemplateName() {
  // First try to get from meta tag
  const metaTemplate = document.querySelector('meta[name="template"]');
  let templateName = metaTemplate ? metaTemplate.getAttribute('content') : null;
  
  // If not found, try to get from selected radio button
  if (!templateName) {
    const selectedRadio = document.querySelector('input[name="template"]:checked');
    templateName = selectedRadio ? selectedRadio.value : 'classic';
  }
  
  return templateName;
}


// Update the addNewItem function to use correct container finding:
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
    enhancedAutoSave();
    
    showEnhancedNotification(`✨ New ${type} added successfully!`, 'success');
    
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
  
  // Add delete functionality for the entire item
  const deleteBtn = item.querySelector('.item-btn.delete');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', () => deleteItem(item));
  }
  
  // Setup item event listeners
  addItemEventListeners(item);
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