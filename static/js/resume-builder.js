// Enhanced Global state and utilities
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

  // Export enhanced functions globally
  window.addItemEventListeners = addItemEventListeners;
  window.addTagEventListeners = addTagEventListeners;
  window.addNewTag = addNewTag;
  window.addNewItem = addNewItem;
  window.autoSave = enhancedAutoSave;

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
});

// Enhanced template selection handler with loading feedback
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

// Enhanced Professional Functions

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
    await saveResume();
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
    await saveResume();
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

  // Create enhanced modal
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
  // Remove existing notifications
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

// Keep all existing functions but enhance them
function setupIframeListeners(iframeDoc) {
  iframeDoc.querySelectorAll('.section-tag').forEach(addTagEventListeners);
  iframeDoc.addEventListener('input', () => {
    state.hasUnsavedChanges = true;
    clearTimeout(state.autoSaveTimeout);
    state.autoSaveTimeout = setTimeout(enhancedAutoSave, 3000);
  });
}

function showSaveStatus(message, isError = false) {
  showEnhancedNotification(message, isError ? 'error' : 'success');
}

// Keep all your existing functions with enhancements
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
        showSaveStatus(data.success ? 'Changes saved successfully!' : 'Error saving changes. Please try again.', !data.success);
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
      
      // If didn't find a known type, try to extract any type from class
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

// Enhanced confirmation modal
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

function showNotification(message, type) {
  showEnhancedNotification(message, type);
}

function getCurrentTemplate() {
  // First try to get from meta tag
  const metaTemplate = document.querySelector('meta[name="template"]');
  let templateName = metaTemplate ? metaTemplate.getAttribute('content') : null;
  
  // If not found, try to get from selected radio button
  if (!templateName) {
    const selectedRadio = document.querySelector('input[name="template"]:checked');
    templateName = selectedRadio ? selectedRadio.value : 'classic';
  }
  
  return templateConfigs[templateName] || templateConfigs.classic;
}

// Template configurations for different resume styles
const templateConfigs = {
  classic: {
    name: 'classic',
    itemStructure: {
      experience: [
        { key: 'job_title', icon: 'fas fa-chevron-right', placeholder: 'e.g., Senior Software Engineer' },
        { key: 'company', icon: 'fas fa-building', placeholder: 'e.g., Tech Solutions Inc.' },
        { key: 'duration', icon: 'fas fa-calendar-alt', placeholder: 'e.g., Jan 2023 - Present' },
        { 
          key: 'description', 
          type: 'list', 
          icon: 'fas fa-list',
          placeholder: 'Key responsibilities and achievements',
          defaultItems: [
            'Led cross-functional teams to deliver high-impact projects',
            'Implemented innovative solutions that improved efficiency',
            'Collaborated with stakeholders to define requirements'
          ]
        }
      ],
      education: [
        { key: 'degree', icon: 'fas fa-graduation-cap', placeholder: 'e.g., Bachelor of Computer Science' },
        { key: 'school', icon: 'fas fa-university', placeholder: 'e.g., University of Technology' },
        { key: 'date', icon: 'fas fa-calendar-alt', placeholder: 'e.g., 2020 - 2024' },
        { key: 'description', placeholder: 'GPA, honors, relevant coursework' }
      ]
    }
  }
  // ... other templates can be added here
};

// Map section types to their display names
const sectionTypeMap = {
  experience: 'Experience',
  education: 'Education', 
  certification: 'Certification',
  project: 'Project',
  volunteer: 'Volunteer',
  award: 'Award',
  publication: 'Publication',
  language: 'Language'
};

// Enhanced Add New Item Function with your existing template structure
function addNewItem(button, type) {
  if (button.dataset.adding === 'true') {
    return; // Prevent duplicate calls
  }
  button.dataset.adding = 'true';
  
  const section = button.parentElement;
  const newItem = document.createElement('div');
  newItem.className = 'section-item';
  
  const uniqueId = generateUniqueId();
  newItem.dataset.itemId = uniqueId;
  newItem.id = `item-${uniqueId}`;
  
  // Professional loading state for button
  const originalButtonContent = button.innerHTML;
  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
  button.disabled = true;
  
  // Get current template configuration
  const currentTemplate = getCurrentTemplate();
  const templateStructure = currentTemplate.itemStructure[type];

  if (!templateStructure) {
    console.warn(`No template structure found for type: ${type}`);
    // Restore button state
    button.innerHTML = originalButtonContent;
    button.disabled = false;
    button.dataset.adding = 'false';
    return;
  }

  // Build template from current configuration
  const template = {
    icon: templateStructure[0]?.icon || 'fas fa-star',
    fields: templateStructure.map(field => ({
      ...field,
      label: field.key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
    }))
  };
  
  // Build enhanced HTML with professional styling
  let itemHTML = `
    <div class="item-actions" style="opacity: 0; transition: opacity 0.3s ease;">
      <button class="item-btn delete" title="Delete this ${type}" data-item-type="${type}">
        <i class="fas fa-trash"></i>
      </button>
    </div>
    <div class="item-content">
  `;

  template.fields.forEach(field => {
    if (field.type === 'list') {
      itemHTML += `
        <div class="section-${field.key.replace('_', '-')}" contenteditable="false" data-key="${field.key}">
          ${field.icon ? `<i class="${field.icon}"></i>` : ''}
          <ul class="section-duties">
            ${(field.defaultItems || ['Click to add your achievement']).map(item => 
              `<li class="duty-item" contenteditable="true">${item}</li>`
            ).join('')}
          </ul>
        </div>
      `;
    } else {
      itemHTML += `
        <div class="section-${field.key.replace('_', '-')}" contenteditable="true" data-key="${field.key}">
          ${field.icon ? `<i class="${field.icon}"></i>` : ''}
          ${field.placeholder}
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
  }, 100);

  // Add enhanced event listeners
  addItemEventListeners(newItem);
  
  // Mark as changed and auto-save
  state.hasUnsavedChanges = true;
  enhancedAutoSave();
  
  // Show success notification
  showEnhancedNotification(`✨ New ${type} added successfully!`, 'success');
  setTimeout(() => {
    button.dataset.adding = 'false';
  }, 1000);
  return newItem;
}

function generateUniqueId() {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}