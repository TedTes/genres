let autoSaveTimeout;
let hasUnsavedChanges = false;
document.addEventListener('DOMContentLoaded', function() {
  // Theme color changer
  const root = document.documentElement;
  

  const templateButton = document.querySelector('.float-control-btn[data-panel="templates-panel"]');
  const templatesPanel = document.getElementById('templates-panel');
  const closePanelButtons = document.querySelectorAll('.panel-close');

  const aiButton = document.getElementById('ai-assistant-btn');
  const aiModal = document.getElementById('ai-assistant-modal');
  const aiModalClose = document.querySelector('.ai-modal-close');

  const saveButton = document.getElementById('save-resume-btn');
  const iframe = document.getElementById('preview-iframe');

  if(saveButton) {
    // Save button click handler
    saveButton.addEventListener('click', function() {
      saveResume();
    });
  }

  if(iframe) {
      // Listen for content changes in iframe
    
      iframe.addEventListener('load', function() {
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        
        // Listen for input events inside the iframe
        iframeDoc.addEventListener('input', function() {
            hasUnsavedChanges = true;
            
            // Clear any existing auto-save timeout
            clearTimeout(autoSaveTimeout);
            
            // Set auto-save timeout
            autoSaveTimeout = setTimeout(() => {
                saveResume();
            }, 30000); // Auto-save after 30 seconds of inactivity
        });
    });
  }
  // Setup AI modal if elements exist
  if (aiButton && aiModal && aiModalClose) {
    // Open AI modal and close templates panel if open
    aiButton.addEventListener('click', function() {
        if (templatesPanel && templatesPanel.classList.contains('active')) {
            templatesPanel.classList.remove('active');
        }
        aiModal.classList.add('active');
    });
    
    // Close AI modal
    aiModalClose.addEventListener('click', function() {
        aiModal.classList.remove('active');
    });
    
    // Close AI modal when clicking outside
    aiModal.addEventListener('click', function(e) {
        if (e.target === aiModal) {
            aiModal.classList.remove('active');
        }
    });
  }
  // Toggle templates panel when clicking the template button
  if (templateButton && templatesPanel) {
      templateButton.addEventListener('click', function() {
        if (aiModal && aiModal.classList.contains('active')) {
          aiModal.classList.remove('active');
      }
          templatesPanel.classList.toggle('active');
      });
  }

  const tooltipContainers = document.querySelectorAll('.tooltip-container');
  tooltipContainers.forEach(container => {
      const tooltip = container.querySelector('.btn-tooltip');
      if (tooltip) {
          // Show tooltip on hover
          container.addEventListener('mouseenter', function() {
              tooltip.style.opacity = '1';
              tooltip.style.visibility = 'visible';
          });
          
          // Hide tooltip when mouse leaves
          container.addEventListener('mouseleave', function() {
              tooltip.style.opacity = '0';
              tooltip.style.visibility = 'hidden';
          });
      }
  });
     // Close panel buttons
  closePanelButtons.forEach(button => {
      button.addEventListener('click', function() {
          const panelId = this.getAttribute('data-panel');
          const panel = document.getElementById(panelId);
          if (panel) {
              panel.classList.remove('active');
          }
      });
  });

 // Close panel when clicking outside
 document.addEventListener('click', function(e) {
  if (!e.target.closest('.slide-panel') && 
      !e.target.closest('.float-control-btn') && 
      templatesPanel.classList.contains('active')) {
      templatesPanel.classList.remove('active');
  }
});

  // Add event listeners to all "Add" buttons
  document.querySelectorAll('.add-item-btn, .add-tag-btn').forEach(btn => {
    if (btn.id.startsWith('add-')) {
      const type = btn.id.replace('add-', '').replace('-btn', '');
      if (type === 'skills') {
        btn.addEventListener('click', function() {
          addNewTag(this);
        });
      } else if (type !== 'summary') {
        btn.addEventListener('click', function() {
          addNewItem(this, type);
        });
      }
    }
  });

  // Add event listeners to delete buttons for existing tags

  document.querySelectorAll('.section-tag').forEach(addTagEventListeners);

  // Add event listeners to existing items
  document.querySelectorAll('.section-item').forEach(addItemEventListeners);



  // Handle dropping files
  document.addEventListener('dragover', function(e) {
    e.preventDefault();
  });
  document.addEventListener('drop', function(e) {
    e.preventDefault();
    alert('File uploads will be supported in a future version.');
  });

  // Listen for input changes and save
  document.addEventListener('input', function(e) {
    if (e.target.getAttribute('contenteditable') === 'true') {
      clearTimeout(window.autoSaveTimeout);
      window.autoSaveTimeout = setTimeout(autoSave, 1500);
    }
  });

  

    // Warn before leaving with unsaved changes
    window.addEventListener('beforeunload', function(e) {
      if (hasUnsavedChanges) {
          e.preventDefault();
          e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
          return e.returnValue;
      }
  });
  // Export these functions for global use
  window.addItemEventListeners = addItemEventListeners;
  window.addTagEventListeners = addTagEventListeners;
  window.addNewTag = addNewTag;
  window.addNewItem = addNewItem;
  window.autoSave = autoSave;

  // Initial auto-save
  setTimeout(autoSave, 3000);
});

// Function to show save status message
function showSaveStatus(message, isError = false) {
  const saveStatus = document.getElementById('save-status');
    saveStatus.textContent = message;
    saveStatus.classList.add('show');
    
    if (isError) {
        saveStatus.classList.add('error');
    } else {
        saveStatus.classList.remove('error');
    }
    
    setTimeout(() => {
        saveStatus.classList.remove('show');
    }, 3000);
}

// Function to save resume changes
function saveResume() {

  // const saveButton = document.getElementById('save-resume-btn');
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
  const resumeId = document.querySelector('.resume-builder').dataset.resumeId;


    if (!hasUnsavedChanges) return;
    
    saveButton.classList.add('saving');
    
    // Get content from iframe
    const iframe = document.getElementById('preview-iframe');
    let resumeContent;
    
    try {
        // Try to get all editable content from the iframe
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        
        // Collect resume data from the iframe
        resumeContent = collectResumeData(iframeDoc);
        
        // AJAX request to save the resume
        fetch(`/resume/${resumeId}/save-data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ resume_data: resumeContent })
        })
        .then(response => response.json())
        .then(data => {
            saveButton.classList.remove('saving');
            
            if (data.success) {
                showSaveStatus('Changes saved successfully!');
                hasUnsavedChanges = false;
            } else {
                showSaveStatus('Error saving changes. Please try again.', true);
            }
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

    // Function to collect resume data from iframe document
function collectResumeData(iframeDoc) {
      // TODO: adjust with resume structure
      const resumeData = {
          contact: {},
          sections: []
      };
      
      // Collect name and title
      resumeData.name = iframeDoc.querySelector('.name')?.textContent || '';
      resumeData.title = iframeDoc.querySelector('.title')?.textContent || '';
      
      // Collect contact information
      const contactItems = iframeDoc.querySelectorAll('.contact-item');
      contactItems.forEach(item => {
          const icon = item.querySelector('.contact-icon')?.className.match(/fa-(\w+)/)?.[1];
          const content = item.querySelector('.contact-content')?.textContent;
          if (icon && content) {
              resumeData.contact[icon] = content;
          }
      });
      
      // Collect sections
      const sections = iframeDoc.querySelectorAll('.resume-section');
      sections.forEach(section => {
          const sectionType = section.className.match(/(\w+)-section/)?.[1];
          const sectionTitle = section.querySelector('.section-title')?.textContent.trim();
          const sectionData = { type: sectionType, title: sectionTitle, content: '' };
          
          if (section.querySelector('.section-content')) {
              sectionData.content = section.querySelector('.section-content')?.innerHTML || '';
          } else if (section.querySelector('.section-container')) {
              sectionData.items = Array.from(section.querySelectorAll('.section-tag')).map(tag => 
                  tag.textContent.trim().replace(/^\s*[✓✔]\s*|\s*[×✖]\s*$/g, '')
              );
          } else {
              sectionData.items = Array.from(section.querySelectorAll('.section-item')).map(item => {
                  const itemData = {};
                  item.querySelectorAll('[class^="section-"]').forEach(el => {
                      const key = el.className.replace('section-', '').replace('-', '_');
                      itemData[key] = el.textContent.trim();
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
    deleteBtn.addEventListener('click', function() {
      tag.remove();
      autoSave();
    });
  }
}

function autoSave() {
  console.log('Auto-saving resume...');
  const savedIndicator = document.createElement('div');
  savedIndicator.style.position = 'fixed';
  savedIndicator.style.bottom = '20px';
  savedIndicator.style.left = '20px';
  savedIndicator.style.backgroundColor = 'var(--success)';
  savedIndicator.style.color = 'white';
  savedIndicator.style.padding = '10px 20px';
  savedIndicator.style.borderRadius = '4px';
  savedIndicator.style.boxShadow = 'var(--shadow-md)';
  savedIndicator.style.opacity = '0';
  savedIndicator.style.transition = 'opacity 0.3s';
  savedIndicator.innerHTML = '<i class="fas fa-check"></i> Changes saved';
  document.body.appendChild(savedIndicator);
  setTimeout(() => {
    savedIndicator.style.opacity = '1';
    setTimeout(() => {
      savedIndicator.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(savedIndicator);
      }, 300);
    }, 2000);
  }, 100);
}
  // Add new tag
function addNewTag(button) {
    const tagName = prompt('Enter item name:');
    if (tagName) {
      const tagsContainer = button.parentElement;
      const newTag = document.createElement('span');
      newTag.className = 'section-tag';
      newTag.innerHTML = `
        <i class="fas fa-check"></i>
        ${tagName}
        <i class="fas fa-times tag-delete"></i>
      `;
      tagsContainer.insertBefore(newTag, button);
      addTagEventListeners(newTag);
      autoSave();
    }
  }


    // Add item event listeners
function addItemEventListeners(item) {
      const moveUpBtn = item.querySelector('.move-up');
      const moveDownBtn = item.querySelector('.move-down');
      const deleteBtn = item.querySelector('.delete');
      if (moveUpBtn) {
        moveUpBtn.addEventListener('click', function() {
          const prevItem = item.previousElementSibling;
          if (prevItem && !prevItem.classList.contains('add-item-btn') && prevItem.classList.contains('section-item')) {
            item.parentNode.insertBefore(item, prevItem);
            autoSave();
          }
        });
      }
      if (moveDownBtn) {
        moveDownBtn.addEventListener('click', function() {
          const nextItem = item.nextElementSibling;
          if (nextItem && !nextItem.classList.contains('add-item-btn')) {
            item.parentNode.insertBefore(nextItem, item);
            autoSave();
          }
        });
      }
      if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
          if (confirm('Are you sure you want to delete this item?')) {
            item.remove();
            autoSave();
          }
        });
      }
    }

  // Add new item
  function addNewItem(button, type) {
    const section = button.parentElement;
    const newItem = document.createElement('div');
    newItem.className = 'section-item';
    let itemHTML = `
      <div class="item-actions">
        <button class="item-btn move-up" title="Move Up"><i class="fas fa-arrow-up"></i></button>
        <button class="item-btn move-down" title="Move Down"><i class="fas fa-arrow-down"></i></button>
        <button class="item-btn delete" title="Delete"><i class="fas fa-trash"></i></button>
      </div>
    `;
    switch(type) {
      case 'experience':
        itemHTML += `
          <div class="section-job-title" contenteditable="true">
            <i class="fas fa-chevron-right"></i>
            Job Title
          </div>
          <div class="section-company" contenteditable="true">
            <i class="fas fa-building"></i>
            Company Name
          </div>
          <div class="section-date" contenteditable="true">
            <i class="fas fa-calendar-alt"></i>
            Start Date - End Date
          </div>
          <div class="section-description" contenteditable="true">
            <ul class="section-duties">
              <li>Add your responsibilities and achievements here...</li>
              <li>Use bullet points to highlight your accomplishments...</li>
              <li>Include metrics and results where possible (e.g., "Increased sales by 20%")</li>
              <li>Focus on achievements rather than just duties</li>
            </ul>
          </div>
        `;
        break;
      case 'education':
        itemHTML += `
          <div class="section-degree" contenteditable="true">
            <i class="fas fa-chevron-right"></i>
            Degree / Certification
          </div>
          <div class="section-school" contenteditable="true">
            <i class="fas fa-university"></i>
            Institution Name
          </div>
          <div class="section-date" contenteditable="true">
            <i class="fas fa-calendar-alt"></i>
            Start Year - End Year
          </div>
          <div class="section-description" contenteditable="true">
            Add details about your educational achievements, relevant coursework, honors, extracurricular activities, or GPA if notable.
          </div>
        `;
        break;
      case 'certification':
        itemHTML += `
          <div class="section-degree" contenteditable="true">
            <i class="fas fa-award"></i>
            Certification Name
          </div>
          <div class="section-school" contenteditable="true">
            <i class="fas fa-building"></i>
            Issuing Organization
          </div>
          <div class="section-date" contenteditable="true">
            <i class="fas fa-calendar-alt"></i>
            Year Obtained (and expiration if applicable)
          </div>
          <div class="section-description" contenteditable="true">
            Include additional details about the certification, such as skills validated or special achievements.
          </div>
        `;
        break;
      case 'project':
        itemHTML += `
          <div class="section-degree" contenteditable="true">
            <i class="fas fa-folder-open"></i>
            Project Name
          </div>
          <div class="section-school" contenteditable="true">
            <i class="fas fa-link"></i>
            Project URL (if available)
          </div>
          <div class="section-date" contenteditable="true">
            <i class="fas fa-calendar-alt"></i>
            Completion Date / Duration
          </div>
          <div class="section-description" contenteditable="true">
            <ul class="section-duties">
              <li>Describe the purpose and scope of the project</li>
              <li>List technologies, tools, and methodologies used</li>
              <li>Explain your specific role and contributions</li>
              <li>Highlight outcomes, impact, or key achievements</li>
            </ul>
          </div>
        `;
        break;
      case 'volunteer':
        itemHTML += `
          <div class="section-degree" contenteditable="true">
            <i class="fas fa-hands-helping"></i>
            Volunteer Position
          </div>
          <div class="section-school" contenteditable="true">
            <i class="fas fa-building"></i>
            Organization
          </div>
          <div class="section-date" contenteditable="true">
            <i class="fas fa-calendar-alt"></i>
            Start Date - End Date
          </div>
          <div class="section-description" contenteditable="true">
            <ul class="section-duties">
              <li>Describe your volunteer contributions and responsibilities</li>
              <li>Highlight any leadership roles or special projects</li>
              <li>Include skills developed or utilized</li>
            </ul>
          </div>
        `;
        break;
      case 'award':
        itemHTML += `
          <div class="section-degree" contenteditable="true">
            <i class="fas fa-trophy"></i>
            Award/Recognition Name
          </div>
          <div class="section-school" contenteditable="true">
            <i class="fas fa-building"></i>
            Awarding Organization
          </div>
          <div class="section-date" contenteditable="true">
            <i class="fas fa-calendar-alt"></i>
            Date Received
          </div>
          <div class="section-description" contenteditable="true">
            Describe the significance of this award, what it recognizes, and why you received it. Include any relevant context like competition size or selection criteria.
          </div>
        `;
        break;
      case 'publication':
        itemHTML += `
          <div class="section-degree" contenteditable="true">
            <i class="fas fa-book"></i>
            Publication Title
          </div>
          <div class="section-school" contenteditable="true">
            <i class="fas fa-newspaper"></i>
            Publisher/Journal
          </div>
          <div class="section-date" contenteditable="true">
            <i class="fas fa-calendar-alt"></i>
            Publication Date
          </div>
          <div class="section-description" contenteditable="true">
            Briefly describe the publication, your contribution, and its significance. Include co-authors if applicable and any important details about reach or impact.
          </div>
        `;
        break;
      case 'language':
        itemHTML += `
          <div class="section-degree" contenteditable="true">
            <i class="fas fa-language"></i>
            Language Name
          </div>
          <div class="section-school" contenteditable="true">
            <i class="fas fa-star"></i>
            Proficiency Level (e.g., Fluent, Native, Intermediate)
          </div>
        `;
        break;
      default:
        const sectionTitle = section.querySelector('.section-title').textContent.trim().toLowerCase();
        if (sectionTitle.includes('volunteer')) {
          return addNewItem(button, 'volunteer');
        } else if (sectionTitle.includes('award') || sectionTitle.includes('honor')) {
          return addNewItem(button, 'award');
        } else if (sectionTitle.includes('publication') || sectionTitle.includes('research')) {
          return addNewItem(button, 'publication');
        } else if (sectionTitle.includes('language')) {
          return addNewItem(button, 'language');
        } else if (sectionTitle.includes('project')) {
          return addNewItem(button, 'project');
        } else {
          itemHTML += `
            <div class="section-degree" contenteditable="true">
              <i class="fas fa-chevron-right"></i>
              Item Title
            </div>
            <div class="section-school" contenteditable="true">
              <i class="fas fa-building"></i>
              Organization / Entity
            </div>
            <div class="section-date" contenteditable="true">
              <i class="fas fa-calendar-alt"></i>
              Relevant Date
            </div>
            <div class="section-description" contenteditable="true">
              Add details here to describe this item...
            </div>
          `;
        }
    }
    newItem.innerHTML = itemHTML;
    section.insertBefore(newItem, button);
    addItemEventListeners(newItem);
    autoSave();
  }
