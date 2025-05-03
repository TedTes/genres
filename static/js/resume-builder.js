
// Initialize Template Selection
const initTemplates = () => {
  const templateForm = document.getElementById("template-form");
  const templateOptions = document.querySelectorAll('.template-option input[type="radio"]');
  const resumeId = document.querySelector(".resume-builder").dataset.resumeId;
  const previewContainer = document.querySelector(".preview-container");
  
  // Store the current template ID
  let currentTemplate = document.querySelector('.template-option input[type="radio"]:checked')?.value || '';
  
  templateOptions.forEach(option => {
    option.addEventListener("change", function() {
      const templateId = this.value;
      if (templateId === currentTemplate) return; // Don't update if same template
      
      // Show loading indicator
      const previewContent = document.getElementById("dynamic-preview-content");
      if (previewContent) {
        const loadingOverlay = document.createElement("div");
        loadingOverlay.className = "preview-loading-overlay";
        loadingOverlay.innerHTML = `
          <div class="loading-spinner"></div>
          <div class="loading-text">Updating template...</div>
        `;
        previewContent.parentNode.insertBefore(loadingOverlay, previewContent);
      }
      
      currentTemplate = templateId;
      
      // Update the UI to reflect the new template
      updateTemplatePreview(templateId);
      
      // Send AJAX request to update template
      const formData = new FormData();
      formData.append('template', templateId);
      formData.append('csrf_token', document.querySelector('input[name="csrf_token"]').value);
      
      // Update the URL to match the correct endpoint
      const updateUrl = `http://localhost:5000/resume/${resumeId}/update-template`;
      
      fetch(updateUrl, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(response => {
        // If the server doesn't return JSON, we can still consider it a success
        if (response.ok) {
          return { success: true };
        }
        return response.json();
      })
      .then(data => {
        if (data.success) {
          // Remove loading overlay
          document.querySelector(".preview-loading-overlay")?.remove();
          
          // Refresh the preview with the new template
          // updatePreview();
          
          // Show success feedback
          showFeedback(templateForm, "success", "Template updated!");
        } else {
          document.querySelector(".preview-loading-overlay")?.remove();
          showFeedback(templateForm, "error", data.error || "Error updating template");
        }
      })
      .catch(error => {
        console.error("Error updating template:", error);
        document.querySelector(".preview-loading-overlay")?.remove();
        showFeedback(templateForm, "error", "Error updating template");
      });
    });
  });
  
  // Function to update the preview with the new template
  function updateTemplatePreview(templateId) {
    // First, update class on preview container to reflect template
    if (!previewContainer) return;
    
    // Remove any existing template classes
    const classes = previewContainer.className.split(' ');
    const templateClasses = classes.filter(cls => cls.startsWith('template-'));
    templateClasses.forEach(cls => previewContainer.classList.remove(cls));
    
    // Add new template class
    previewContainer.classList.add(`template-${templateId}`);
  }
};
// Global state
let experiences = [];
let educations = [];
let skills = [];
let additionalSections = {};

// Utility: Debounce function to limit frequent updates
const debounce = (func, wait) => {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

// Utility: Show feedback messages
const showFeedback = (element, type, message) => {
  const feedbackClass = `${type}-feedback`;
  let feedback = element.parentElement.querySelector(`.${feedbackClass}`);

  if (!feedback) {
    feedback = document.createElement("div");
    feedback.className = feedbackClass;
    element.parentElement.appendChild(feedback);
  }

  feedback.textContent = message;
  feedback.style.opacity = "1";

  setTimeout(() => {
    feedback.style.opacity = "0";
    setTimeout(() => {
      if (feedback.parentNode) {
        feedback.parentNode.removeChild(feedback);
      }
    }, 300);
  }, 2000);
};

// Initialize Panels (Sidebar and Slide-Out Panels)
const initPanels = () => {
  const floatControlBtns = document.querySelectorAll(".float-control-btn[data-panel]");
  const panelCloseBtns = document.querySelectorAll(".panel-close");
  const slidePanels = document.querySelectorAll(".slide-panel");
  const sidebarToggleBtn = document.getElementById("sidebar-toggle");
  const sidebar = document.querySelector(".floating-controls-left");
  const previewToggleBtn = document.getElementById("preview-toggle");
  const container = document.querySelector(".resume-builder-container");

  // Handle sidebar toggle for mobile
  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
      
      if (sidebar.classList.contains("collapsed")) {
        sidebarToggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
        container.classList.add("sidebar-collapsed");
      } else {
        sidebarToggleBtn.innerHTML = '<i class="fas fa-times"></i>';
        container.classList.remove("sidebar-collapsed");
      }
    });
  }

  // Initialize sidebar state for mobile
  if (window.innerWidth <= 768) {
    sidebar.classList.add("collapsed");
    container.classList.add("sidebar-collapsed");
  } else {
    sidebar.classList.remove("collapsed");
    // container.classList.remove("sidebar-collapsed");
  }

  // Toggle panels
  floatControlBtns.forEach((btn) => {
    btn.addEventListener("click", function () {
      const panelId = this.dataset.panel;
      const panel = document.getElementById(panelId);

      // Close other panels
      slidePanels.forEach((p) => {
        if (p.id !== panelId) {
          p.classList.remove("active");
          document
            .querySelector(`.float-control-btn[data-panel="${p.id}"]`)
            ?.classList.remove("active");
        }
      });

      // Toggle current panel
      panel.classList.toggle("active");
      this.classList.toggle("active", panel.classList.contains("active"));

      // Adjust container
      const anyPanelActive = Array.from(slidePanels).some((p) =>
        p.classList.contains("active")
      );
      
      if (anyPanelActive) {
        container.classList.add("expanded");
      } else {
        container.classList.remove("expanded");
      }
    });
  });

  // Close panels
  panelCloseBtns.forEach((btn) => {
    btn.addEventListener("click", function () {
      const panelId = this.closest(".slide-panel").id;
      const panel = document.getElementById(panelId);
      panel.classList.remove("active");

      const controlBtn = document.querySelector(
        `.float-control-btn[data-panel="${panelId}"]`
      );
      if (controlBtn) controlBtn.classList.remove("active");

      const anyPanelActive = Array.from(slidePanels).some((p) =>
        p.classList.contains("active")
      );
      if (!anyPanelActive) {
        document
          .querySelector(".resume-builder-container")
          .classList.remove("expanded");
      }
    });
  });

  // Toggle preview size
  if (previewToggleBtn) {
    previewToggleBtn.addEventListener("click", () => {
      const container = document.querySelector(".resume-builder-container");
      const isFullScreen = container.classList.contains("preview-fullscreen");

      if (isFullScreen) {
        container.classList.remove("preview-fullscreen");
        previewToggleBtn.innerHTML = '<i class="fas fa-expand"></i>';
        previewToggleBtn.title = "Expand Preview";
      } else {
        container.classList.add("preview-fullscreen");
        previewToggleBtn.innerHTML = '<i class="fas fa-compress"></i>';
        previewToggleBtn.title = "Collapse Preview";
      }
    });
  }

  // Add info icon for current template
  const templateInfoBtn = document.createElement("div");
  templateInfoBtn.className = "tooltip-container";
  templateInfoBtn.innerHTML = `
    <button class="float-control-btn" title="Current Template Info">
      <i class="fas fa-info-circle"></i>
    </button>
    <div class="btn-tooltip">View current template</div>
  `;
  if (sidebar) {
    sidebar.appendChild(templateInfoBtn);
  }

  templateInfoBtn.addEventListener("click", () => {
    const selectedTemplate = document.querySelector(
      '.template-option input[type="radio"]:checked'
    );
    const templateName = selectedTemplate
      ? selectedTemplate.nextElementSibling.querySelector(".template-name")
          .textContent
      : "No template selected";
    alert(`Current Template: ${templateName}`);
  });

  // Handle click outside to close sidebar on mobile
  document.addEventListener("click", (event) => {
    const isClickInsideSidebar = sidebar.contains(event.target);
    const isClickInsideSidebarToggle = sidebarToggleBtn && sidebarToggleBtn.contains(event.target);
    
    if (window.innerWidth <= 768 && !isClickInsideSidebar && !isClickInsideSidebarToggle && !sidebar.classList.contains("collapsed")) {
      sidebar.classList.add("collapsed");
      container.classList.add("sidebar-collapsed");
      if (sidebarToggleBtn) {
        sidebarToggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
      }
    }
  });
};

// Initialize Collapsible Sections
const initCollapsibleSections = () => {
  const sectionHeaders = document.querySelectorAll(".section-header.collapsible");

  sectionHeaders.forEach((header) => {
    header.addEventListener("click", function () {
      const section = this.closest(".resume-section-collapsible");
      section.classList.toggle("active");

      const chevron = this.querySelector(".fa-chevron-down");
      if (section.classList.contains("active")) {
        chevron.style.transform = "rotate(180deg)";
      } else {
        chevron.style.transform = "rotate(0deg)";
      }
    });
  });

  // Open first section by default
  const firstSection = document.querySelector(".resume-section-collapsible");
  if (firstSection) {
    firstSection.classList.add("active");
    const chevron = firstSection.querySelector(".fa-chevron-down");
    if (chevron) chevron.style.transform = "rotate(180deg)";
  }
};

const initSectionOptions = () => {
  const sectionOptions = document.querySelectorAll(".section-option");
  
  sectionOptions.forEach(option => {
    option.addEventListener("click", function() {
      const sectionType = this.dataset.section;
      // Implement section addition logic here
      console.log(`Adding section: ${sectionType}`);
      
      // Show temporary feedback
      const feedback = document.createElement("div");
      feedback.className = "success-feedback";
      feedback.textContent = `${sectionType} section added!`;
      feedback.style.opacity = "1";
      this.appendChild(feedback);
      
      setTimeout(() => {
        feedback.style.opacity = "0";
        setTimeout(() => {
          if (feedback.parentNode) {
            feedback.parentNode.removeChild(feedback);
          }
        }, 300);
      }, 2000);
      
      // Actual implementation would add the new section to the UI
      // and manage the data structure
    });
  });
};
// Setup Auto Resize Inputs
const setupAutoResizeInputs = () => {
  document.querySelectorAll(".auto-resize").forEach((input) => {
    input.addEventListener("input", function () {
      if (!this.dataset.hasOwnProperty("originalWidth")) {
        this.dataset.originalWidth = this.style.width || "";
        this.dataset.originalMinWidth = this.style.minWidth || "";
      }

      const span = document.createElement("span");
      span.style.position = "absolute";
      span.style.left = "-9999px";
      span.style.fontSize = window.getComputedStyle(this).fontSize;
      span.style.fontFamily = window.getComputedStyle(this).fontFamily;
      span.style.whiteSpace = "pre";
      span.textContent = this.value || this.placeholder;
      document.body.appendChild(span);

      const paddingWidth = 20;
      const newWidth = Math.min(span.offsetWidth + paddingWidth, 300);
      this.style.width = Math.max(newWidth, 80) + "px";

      document.body.removeChild(span);
    });
    input.dispatchEvent(new Event("input"));
  });
};

// Setup Auto Expand Textareas
const setupAutoExpandTextareas = () => {
  document.querySelectorAll(".auto-expand").forEach((textarea) => {
    textarea.addEventListener("input", function () {
      this.style.height = "auto";
      this.style.height = `${this.scrollHeight}px`;
    });
    textarea.dispatchEvent(new Event("input"));
  });
};

// Setup Auto Save
const setupAutoSave = () => {
  const autoSave = debounce((field, value) => {
    const resumeId = document.querySelector(".resume-builder").dataset.resumeId;
    const section = field.closest("[data-section]")?.dataset.section || 'general';

    // Simulate saving to localStorage (replace with backend API call)
    localStorage.setItem(
      `resume-${resumeId}-${section}-${field.name}`,
      value
    );
    
    // Update progress after save
    updateProgress();
  }, 800);

  document.querySelectorAll(".resume-field").forEach((field) => {
    field.addEventListener("input", () =>
      autoSave(field, field.value)
    );
    field.addEventListener("change", () =>
      autoSave(field, field.value)
    );
  });
};

//  Skills Manager
const initSkillsManager = () => {
  const skillsInput = document.getElementById("skill-input");
  const skillsList = document.getElementById("skills-list");
  const skillsHidden = document.getElementById("skills-hidden");
  const skillSuggestions = document.querySelectorAll(".skill-tag.suggested");
  const toggleSkills = document.getElementById("toggle-skills");
  const emptySkillsMessage = document.getElementById("empty-skills-message");
  
  if (!skillsInput || !skillsList || !skillsHidden) return;

  // Initialize skills from hidden input
  let skills = [];
  try {
    skills = skillsHidden.value ? JSON.parse(skillsHidden.value) : [];
  } catch (e) {
    console.error("Error parsing skills JSON:", e);
    skills = [];
  }
  
  renderSkills();

  // Add skill on Enter or comma
  skillsInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addSkill(skillsInput.value.trim());
      skillsInput.value = "";
    }
  });

  // Add skill on blur
  skillsInput.addEventListener("blur", () => {
    if (skillsInput.value.trim()) {
      addSkill(skillsInput.value.trim());
      skillsInput.value = "";
    }
  });

  // Toggle suggested skills
  if (toggleSkills) {
    toggleSkills.addEventListener("click", function () {
      const skillsContainer = document.getElementById("skills-tags-container");
      const isExpanded = this.getAttribute("aria-expanded") === "true";

      if (isExpanded) {
        skillsContainer.classList.add("collapse");
        this.setAttribute("aria-expanded", "false");
      } else {
        skillsContainer.classList.remove("collapse");
        this.setAttribute("aria-expanded", "true");
      }
    });
  }

  // Add suggested skills
  if (skillSuggestions) {
    skillSuggestions.forEach((suggestion) => {
      suggestion.addEventListener("click", function () {
        addSkill(this.dataset.skill);
        this.classList.add("added");
        
        // Visual feedback
        this.style.backgroundColor = "#d1fae5"; // Success light green
        this.style.borderColor = "#10b981"; // Success
        this.style.color = "#10b981"; // Success
        
        // Reset after a moment
        setTimeout(() => {
          this.style.backgroundColor = "";
          this.style.borderColor = "";
          this.style.color = "";
        }, 1500);
      });
    });
  }

  function addSkill(skillText) {
    if (!skillText) return;
    
    const skillsToAdd = skillText
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s && !skills.includes(s));
      
    if (skillsToAdd.length === 0) return;
    
    skills.push(...skillsToAdd);
    renderSkills();
    updateSkillsField();
    
    // Provide subtle feedback
    skillsInput.style.borderColor = "#10b981";
    setTimeout(() => {
      skillsInput.style.borderColor = "";
    }, 800);
  }

  function removeSkill(index) {
    skills.splice(index, 1);
    renderSkills();
    updateSkillsField();
  }

  function renderSkills() {
    skillsList.innerHTML = "";
    
    if (skills.length === 0) {
      skillsList.appendChild(emptySkillsMessage || createEmptyMessage());
      return;
    }
    
    skills.forEach((skill, index) => {
      const tag = document.createElement("div");
      tag.className = "skill-tag";
      tag.innerHTML = `
        <span>${skill}</span>
        <button type="button" class="remove-skill" data-index="${index}" aria-label="Remove ${skill}">×</button>
      `;
      skillsList.appendChild(tag);
    });

    document.querySelectorAll(".remove-skill").forEach((button) => {
      button.addEventListener("click", function () {
        removeSkill(parseInt(this.dataset.index));
      });
    });
  }

  function createEmptyMessage() {
    const message = document.createElement("div");
    message.className = "empty-skills-message";
    message.id = "empty-skills-message";
    message.textContent = "No skills added yet. Use the field above to add your skills.";
    return message;
  }

  function updateSkillsField() {
    skillsHidden.value = JSON.stringify(skills);
    // Trigger change event for auto-save
    const event = new Event('change', { bubbles: true });
    skillsHidden.dispatchEvent(event);
    
    // Update progress
    updateProgress();
  }
};

// Add placeholder for future AI integration
const initAISkillsIntegration = () => {
  const aiExtractBtn = document.getElementById('ai-extract-skills');
  const aiSuggestBtn = document.getElementById('ai-suggest-skills');
  
  if (!aiExtractBtn || !aiSuggestBtn) return;
  
  // Just stub functions for now that will be implemented later
  aiExtractBtn.addEventListener('click', function() {
    console.log('AI Extract Skills functionality will be implemented in future steps');
  });
  
  aiSuggestBtn.addEventListener('click', function() {
    console.log('AI Suggest Skills functionality will be implemented in future steps');
  });
};



// Initialize AI Enhancement
const initAIEnhancement = () => {
  const enhanceButtons = document.querySelectorAll(".enhance-summary");

  enhanceButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      const type = button.dataset.type;
      const summaryField = document.querySelector('textarea[name="summary"]');
      const summary = summaryField.value;

      if (!summary) {
        showFeedback(summaryField, "error", "Please enter a summary first");
        return;
      }

      button.disabled = true;
      button.classList.add("loading");

      // Simulate AI enhancement (replace with actual API call)
      setTimeout(() => {
        let enhancedSummary = summary;
        if (type === "professional") {
          enhancedSummary = enhanceProfessional(summary);
        } else if (type === "concise") {
          enhancedSummary = enhanceConcise(summary);
        } else if (type === "keywords") {
          enhancedSummary = enhanceKeywords(summary);
        }

        summaryField.value = enhancedSummary;
        showFeedback(summaryField, "success", "Summary enhanced");
        summaryField.dispatchEvent(new Event("input"));
        
        // Trigger auto-save
        const event = new Event('change', { bubbles: true });
        summaryField.dispatchEvent(event);

        button.disabled = false;
        button.classList.remove("loading");
      }, 1000);
    });
  });

  // Helper functions for AI enhancement
  function enhanceProfessional(text) {
    // Simple simulation of professional enhancement
    return text
      .replace(/I am/g, "I'm")
      .replace(/I have/g, "I've")
      .replace(/worked on/g, "delivered")
      .replace(/good/g, "exceptional")
      .replace(/made/g, "created")
      .replace(/did/g, "executed")
      .replace(/used/g, "leveraged")
      .replace(/responsible for/g, "spearheaded")
      .replace(/team player/g, "collaborative professional");
  }

  function enhanceConcise(text) {
    // Simple simulation of making text more concise
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    if (sentences.length <= 2) return text;
    return sentences.slice(0, 2).join(". ") + ".";
  }

  function enhanceKeywords(text) {
    // Simple simulation of adding keywords
    const keywords = [
      "strategic leadership",
      "cross-functional collaboration",
      "agile methodology",
      "data-driven decision making",
      "stakeholder management"
    ];
    const randomKeyword = keywords[Math.floor(Math.random() * keywords.length)];
    return `${text} Expertise in ${randomKeyword}.`;
  }
};


// Helper function to create a preview section
function createPreviewSection(title, dataAttribute, content, contentElement) {
  const section = document.createElement("div");
  section.className = "preview-section";
  
  const heading = document.createElement("h2");
  heading.textContent = title;
  section.appendChild(heading);
  
  if (contentElement) {
    section.appendChild(contentElement);
  } else if (dataAttribute) {
    const contentDiv = document.createElement(content && content.includes('<') ? "div" : "p");
    contentDiv.setAttribute("data-preview", dataAttribute);
    contentDiv.innerHTML = content;
    section.appendChild(contentDiv);
  }
  
  return section;
}

// Format description helper for experience items
function formatDescription(text) {
  if (!text) return "";
  const lines = text
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => {
      line = line.trim();
      if (
        !line.startsWith("•") &&
        !line.startsWith("-") &&
        !line.startsWith("*")
      ) {
        line = `• ${line}`;
      }
      return `<li>${line.replace(/^[•\-*]\s*/, "")}</li>`;
    });
  return lines.length ? `<ul>${lines.join("")}</ul>` : "";
}

// Update Progress Indicator
const updateProgress = () => {
  const sections = document.querySelectorAll("[data-section]");
  let totalRequiredFields = 0;
  let completedRequiredFields = 0;
  let completedSections = 0;

  sections.forEach((section) => {
    const requiredFields = section.querySelectorAll("[required]");
    totalRequiredFields += requiredFields.length;

    let sectionComplete = true;
    requiredFields.forEach((field) => {
      if (field.value.trim()) {
        completedRequiredFields++;
      } else {
        sectionComplete = false;
      }
    });

    if (sectionComplete && requiredFields.length > 0) {
      completedSections++;
      section.classList.add("complete");
    } else {
      section.classList.remove("complete");
    }

    // For sections without required fields (like skills)
    if (requiredFields.length === 0) {
      const contentFields = section.querySelectorAll("input, textarea");
      const hasContent = Array.from(contentFields).some(
        (field) => field.value.trim() !== ""
      );
      
      // For skills section, check if we have skills
      if (section.dataset.section === "skills" && skills.length > 0) {
        section.classList.add("complete");
        completedSections++;
      } else if (hasContent) {
        section.classList.add("complete");
        completedSections++;
      }
    }
  });

  // Calculate progress as a percentage
  const progressPercentage = totalRequiredFields > 0
    ? Math.round((completedRequiredFields / totalRequiredFields) * 100)
    : 0;

  // Update circular progress indicator
  const progressRingFill = document.querySelector(".progress-ring-fill");
  const progressText = document.querySelector(".progress-percentage");
  
  if (progressRingFill) {
    const circleLength = progressRingFill.getTotalLength || 100;
    // Setting the stroke dasharray to reflect the progress percentage
    progressRingFill.style.strokeDasharray = `${progressPercentage}, 100`;
  }
  
  if (progressText) {
    progressText.textContent = `${progressPercentage}%`;
  }
};
// Enhance form field behavior
const enhanceFormFields = () => {
  // Add floating label effect
  document.querySelectorAll('.form-control').forEach(field => {
    // Add event listeners for focus and blur to improve the visual feedback
    field.addEventListener('focus', function() {
      this.parentElement.classList.add('focused');
    });
    
    field.addEventListener('blur', function() {
      this.parentElement.classList.remove('focused');
      
      // Add 'filled' class if the field has a value
      if (this.value.trim()) {
        this.parentElement.classList.add('filled');
      } else {
        this.parentElement.classList.remove('filled');
      }
    });
    
    // Initialize filled state
    if (field.value.trim()) {
      field.parentElement.classList.add('filled');
    }
  });
};
const initStyles = ()=>{
  const style = document.createElement('style');
  style.textContent = `
    .preview-loading-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: rgba(255, 255, 255, 0.8);
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      z-index: 100;
      border-radius: 8px;
    }
    
    .loading-spinner {
      width: 40px;
      height: 40px;
      border: 4px solid rgba(59, 130, 246, 0.3);
      border-radius: 50%;
      border-top-color: var(--primary);
      animation: spin 1s linear infinite;
    }
    
    .loading-text {
      margin-top: 10px;
      font-size: 14px;
      color: var(--secondary);
    }
    
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
}

// Enhanced Summary Manager
const initSummaryManager = () => {
  const summaryTextarea = document.getElementById("summary-textarea");
  const charCounter = document.getElementById("summary-char-counter");
  const enhanceButtons = document.querySelectorAll(".enhance-summary");

  
  if (!summaryTextarea) return;
  
  // Initialize character counter
  const updateCharCounter = () => {
    const maxLength = parseInt(summaryTextarea.getAttribute("maxlength") || 400);
    const currentLength = summaryTextarea.value.length;
    
    charCounter.textContent = `${currentLength}/${maxLength}`;
    
    // Update visual feedback based on limit
    if (currentLength >= maxLength) {
      charCounter.classList.add("limit-reached");
      charCounter.classList.remove("limit-near");
    } else if (currentLength >= maxLength * 0.8) {
      charCounter.classList.add("limit-near");
      charCounter.classList.remove("limit-reached");
    } else {
      charCounter.classList.remove("limit-near", "limit-reached");
    }
  };
  
  // Initialize character counter if textarea exists
  if (summaryTextarea) {
    updateCharCounter();
    
    summaryTextarea.addEventListener("input", () => {
      updateCharCounter();
      
      // Auto expand height
      summaryTextarea.style.height = "auto";
      summaryTextarea.style.height = (summaryTextarea.scrollHeight) + "px";
    });
  }
  
  // AI Enhancement Buttons
  if (enhanceButtons) {
    enhanceButtons.forEach(button => {
      button.addEventListener("click", function() {
        const enhancementType = this.dataset.type;
        
        if (!summaryTextarea.value.trim()) {
          showTooltip(summaryTextarea, "Please write a summary first");
          return;
        }
        
        // Show loading state
        this.classList.add("loading");
        const originalIcon = this.innerHTML;
        this.innerHTML = '';
        
        // Simulate AI processing (replace with actual API call later)
        setTimeout(() => {
          let enhancedText = "";
          
          switch (enhancementType) {
            case "professional":
              enhancedText = enhanceProfessional(summaryTextarea.value);
              break;
            case "concise":
              enhancedText = enhanceConcise(summaryTextarea.value);
              break;
            case "keywords":
              enhancedText = enhanceKeywords(summaryTextarea.value);
              break;
            case "achievement":
              enhancedText = enhanceAchievement(summaryTextarea.value);
              break;
            default:
              enhancedText = summaryTextarea.value;
          }
          
          // Apply the enhanced text
          summaryTextarea.value = enhancedText;
          summaryTextarea.dispatchEvent(new Event('input'));
          
          // Add enhancement effect
          summaryTextarea.classList.add("enhanced");
          setTimeout(() => {
            summaryTextarea.classList.remove("enhanced");
          }, 1000);
          
          // Remove loading state
          this.classList.remove("loading");
          this.innerHTML = originalIcon;
          
          // Trigger autosave
          const event = new Event('change', { bubbles: true });
          summaryTextarea.dispatchEvent(event);
          
          // Show success message
          const enhancementName = this.closest('.enhancement-option').querySelector('h4').textContent;
          showTooltip(summaryTextarea, `Enhanced with ${enhancementName} style`);
        }, 1500);
      });
    });
  }
   

  
  // Helper function to show tooltip
  function showTooltip(element, message) {
    const tooltip = document.createElement("div");
    tooltip.className = "floating-tooltip";
    tooltip.textContent = message;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.top = `${rect.top + window.scrollY - 30}px`;
    tooltip.style.left = `${rect.left + window.scrollX + rect.width / 2}px`;
    tooltip.style.transform = "translate(-50%, -100%)";
    
    setTimeout(() => {
      tooltip.classList.add("show");
    }, 10);
    
    setTimeout(() => {
      tooltip.classList.remove("show");
      setTimeout(() => {
        document.body.removeChild(tooltip);
      }, 300);
    }, 3000);
  }
  
  // Helper functions for AI enhancement (placeholder implementations)
  function enhanceProfessional(text) {
    // Placeholder for professional enhancement
    return text
      .replace(/I am/g, "I am a")
      .replace(/I have/g, "I have")
      .replace(/worked on/g, "successfully delivered")
      .replace(/good/g, "exceptional")
      .replace(/made/g, "developed")
      .replace(/did/g, "executed")
      .replace(/used/g, "leveraged")
      .replace(/responsible for/g, "spearheaded")
      .replace(/team player/g, "collaborative professional");
  }
  
  function enhanceConcise(text) {
    // Placeholder for concise enhancement
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    if (sentences.length <= 2) return text;
    return sentences.slice(0, 2).join(". ") + ".";
  }
  
  function enhanceKeywords(text) {
    // Placeholder for keywords enhancement
    const keywords = [
      "strategic leadership",
      "cross-functional collaboration",
      "agile methodology",
      "data-driven decision making",
      "stakeholder management",
      "revenue growth",
      "process optimization"
    ];
    const randomKeyword = keywords[Math.floor(Math.random() * keywords.length)];
    return `${text} Adept at ${randomKeyword}.`;
  }
  
  function enhanceAchievement(text) {
    // Placeholder for achievement-focused enhancement
    const achievements = [
      "Increased revenue by 30% through strategic initiatives",
      "Reduced operational costs by 25% by streamlining processes",
      "Led cross-functional team that delivered project ahead of schedule",
      "Improved customer satisfaction scores from 85% to 95%",
      "Recognized with performance award for exceptional contributions"
    ];
    const randomAchievement = achievements[Math.floor(Math.random() * achievements.length)];
    
    return text + ` Achievements include: ${randomAchievement}.`;
  }
};

// Add this CSS for the tooltip
const addTooltipStyles = () => {
  const style = document.createElement('style');
  style.textContent = `
    .floating-tooltip {
      position: absolute;
      z-index: 1000;
      background-color: var(--secondary);
      color: white;
      padding: 8px 16px;
      border-radius: 4px;
      font-size: 14px;
      opacity: 0;
      transition: opacity 0.3s ease;
      pointer-events: none;
      white-space: nowrap;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .floating-tooltip::after {
      content: '';
      position: absolute;
      top: 100%;
      left: 50%;
      transform: translateX(-50%);
      border-width: 6px;
      border-style: solid;
      border-color: var(--secondary) transparent transparent transparent;
    }
    
    .floating-tooltip.show {
      opacity: 0.95;
    }
    
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
};
// Enhanced Experience Manager
const initExperienceManager = () => {
  // Elements
  const experienceTimeline = document.getElementById("experience-timeline");
  const addExperienceBtn = document.getElementById("add-experience-btn");
  const experienceFormContainer = document.getElementById("experience-form-container");
  const experienceForm = document.getElementById("experience-form");
  const experienceFormClose = document.getElementById("experience-form-close");
  const cancelExperienceBtn = document.getElementById("cancel-experience");
  const experienceFormTitle = document.getElementById("experience-form-title");
  const experienceIndex = document.getElementById("experience-index");
  const jobTitle = document.getElementById("job-title");
  const company = document.getElementById("company");
  const startDate = document.getElementById("start-date");
  const endDate = document.getElementById("end-date");
  const currentJob = document.getElementById("current-job");
  const jobDescription = document.getElementById("job-description");
  const experienceData = document.getElementById("experience-data");
  const emptyState = document.getElementById("timeline-empty-state");
  const toggleJobSkills = document.getElementById("toggle-job-skills");
  const jobSkillsContainer = document.getElementById("job-skills-container");
  const skillTags = document.querySelectorAll(".skill-tag.suggested");
  const aiEnhanceBtn = document.querySelector(".toolbar-btn.ai-enhance");
  const aiEnhancePanel = document.getElementById("ai-enhance-panel");
  const enhanceOptions = document.querySelectorAll(".enhance-option");
  const toolbarBtns = document.querySelectorAll(".toolbar-btn");
  
  if (!experienceTimeline || !addExperienceBtn || !experienceForm) return;
  
  // Experience data
  let experiences = [];
  
  // Initialize from existing data if available
  const initializeExperiences = () => {
    try {
      experiences = experienceData && experienceData.value 
        ? JSON.parse(experienceData.value) 
        : [];
    } catch (e) {
      console.error("Error parsing experience data:", e);
      experiences = [];
    }
    
    renderExperiences();
  };
  
  // Render experiences to timeline
  const renderExperiences = () => {
    // Clear the timeline
    // Keep the empty state element
    Array.from(experienceTimeline.children).forEach(child => {
      if (child.id !== "timeline-empty-state") {
        experienceTimeline.removeChild(child);
      }
    });
    
    // Toggle empty state visibility
    if (experiences.length === 0) {
      emptyState.style.display = "block";
      return;
    } else {
      emptyState.style.display = "none";
    }
    
    // Render each experience
    experiences.forEach((exp, index) => {
      const timelineItem = document.createElement("div");
      timelineItem.className = "timeline-item";
      timelineItem.dataset.index = index;
      
      // Format description as bullet points
      let descriptionHTML = "";
      if (exp.description) {
        const items = exp.description
          .split("\n")
          .filter(line => line.trim())
          .map(line => {
            // Ensure each line starts with a bullet
            const trimmed = line.trim();
            if (trimmed.startsWith("•") || trimmed.startsWith("-") || trimmed.startsWith("*")) {
              return `<li>${trimmed.substring(1).trim()}</li>`;
            } else {
              return `<li>${trimmed}</li>`;
            }
          });
        
        if (items.length) {
          descriptionHTML = `<ul>${items.join("")}</ul>`;
        }
      }
      
      // Current or past position
      const dateDisplay = exp.current 
        ? `${exp.startDate} - Present` 
        : `${exp.startDate} - ${exp.endDate}`;
      
      timelineItem.innerHTML = `
        <div class="timeline-date">${dateDisplay}</div>
        <div class="timeline-actions">
          <button type="button" class="timeline-action edit" data-index="${index}" aria-label="Edit">
            <i class="fas fa-pencil-alt"></i>
          </button>
          <button type="button" class="timeline-action delete" data-index="${index}" aria-label="Delete">
            <i class="fas fa-trash-alt"></i>
          </button>
        </div>
        <div class="timeline-content">
          <h4>${exp.title}</h4>
          <div class="timeline-company">${exp.company}</div>
          <div class="timeline-description">
            ${descriptionHTML}
          </div>
        </div>
      `;
      
      experienceTimeline.appendChild(timelineItem);
    });
    
    // Add event listeners to the action buttons
    document.querySelectorAll(".timeline-action.edit").forEach(btn => {
      btn.addEventListener("click", function() {
        const index = parseInt(this.dataset.index);
        editExperience(index);
      });
    });
    
    document.querySelectorAll(".timeline-action.delete").forEach(btn => {
      btn.addEventListener("click", function() {
        const index = parseInt(this.dataset.index);
        deleteExperience(index);
      });
    });
    
    // Update progress
    updateProgress();
  };
  
// Add experience
const addExperience = () => {
  // Reset the form
  experienceForm.reset();
  experienceIndex.value = -1;
  experienceFormTitle.textContent = "Add Work Experience";
  
  // Show the form
  experienceFormContainer.style.display = "flex";
  setTimeout(() => {
    experienceFormContainer.classList.add("active");
  }, 10);
  
  // Focus on the first input
  jobTitle.focus();
};

// Edit experience
const editExperience = (index) => {
  const experience = experiences[index];
  if (!experience) return;
  
  // Set form values
  experienceIndex.value = index;
  jobTitle.value = experience.title;
  company.value = experience.company;
  startDate.value = experience.startDate;
  
  if (experience.current) {
    currentJob.checked = true;
    endDate.value = "";
    endDate.disabled = true;
  } else {
    currentJob.checked = false;
    endDate.value = experience.endDate;
    endDate.disabled = false;
  }
  
  jobDescription.value = experience.description;
  
  // Update form title
  experienceFormTitle.textContent = "Edit Work Experience";
  
  // Show the form
  experienceFormContainer.style.display = "flex";
  setTimeout(() => {
    experienceFormContainer.classList.add("active");
  }, 10);
  
  // Expand the textarea to fit content
  jobDescription.style.height = "auto";
  jobDescription.style.height = jobDescription.scrollHeight + "px";
};

// Delete experience
const deleteExperience = (index) => {
  // Confirm before deleting
  if (confirm("Are you sure you want to delete this experience?")) {
    experiences.splice(index, 1);
    updateExperienceData();
    renderExperiences();
  }
};

// Update the hidden input with experiences data
const updateExperienceData = () => {
  experienceData.value = JSON.stringify(experiences);
  // Trigger change event for autosave
  const event = new Event('change', { bubbles: true });
  experienceData.dispatchEvent(event);
};

// Format the job description to ensure bullet points
const formatDescription = (text) => {
  if (!text) return "";
  
  return text
    .split("\n")
    .map(line => {
      const trimmed = line.trim();
      if (!trimmed) return "";
      if (trimmed.startsWith("•") || trimmed.startsWith("-") || trimmed.startsWith("*")) {
        return trimmed;
      } else {
        return `• ${trimmed}`;
      }
    })
    .filter(line => line)
    .join("\n");
};

// Handle form submission
const handleFormSubmit = (e) => {
  e.preventDefault();
  
  // Basic validation
  if (!jobTitle.value || !company.value || !startDate.value || !jobDescription.value) {
    showTooltip(experienceForm, "Please fill in all required fields");
    return;
  }
  
  const index = parseInt(experienceIndex.value);
  const isNewExperience = index === -1;
  
  // Format the description
  const formattedDescription = formatDescription(jobDescription.value);
  
  // Create experience object
  const experience = {
    title: jobTitle.value,
    company: company.value,
    startDate: startDate.value,
    endDate: currentJob.checked ? "" : endDate.value,
    current: currentJob.checked,
    description: formattedDescription
  };
  
  // Update or add the experience
  if (isNewExperience) {
    experiences.push(experience);
  } else {
    experiences[index] = experience;
  }
  
  // Update data and render
  updateExperienceData();
  renderExperiences();
  
  // Close the form
  closeForm();
  
  // Show success toast
  showTooltip(addExperienceBtn, isNewExperience ? "Experience added successfully" : "Experience updated successfully");
};

// Close the form
const closeForm = () => {
  experienceFormContainer.classList.remove("active");
  setTimeout(() => {
    experienceFormContainer.style.display = "none";
  }, 300);
};

// Initialize event listeners
const initEventListeners = () => {
  // Add experience button
  addExperienceBtn.addEventListener("click", addExperience);
  
  // Form submission
  experienceForm.addEventListener("submit", handleFormSubmit);
  
  // Close form buttons
  experienceFormClose.addEventListener("click", closeForm);
  cancelExperienceBtn.addEventListener("click", closeForm);
  
  // Current job checkbox
  currentJob.addEventListener("change", function() {
    if (this.checked) {
      endDate.value = "";
      endDate.disabled = true;
    } else {
      endDate.disabled = false;
    }
  });
  
  // Close on click outside form
  experienceFormContainer.addEventListener("click", function(e) {
    if (e.target === this) {
      closeForm();
    }
  });
  
  // Toggle job skills
  if (toggleJobSkills && jobSkillsContainer) {
    toggleJobSkills.addEventListener("click", function() {
      const isExpanded = this.getAttribute("aria-expanded") === "true";
      
      if (isExpanded) {
        jobSkillsContainer.classList.add("collapse");
        this.setAttribute("aria-expanded", "false");
      } else {
        jobSkillsContainer.classList.remove("collapse");
        this.setAttribute("aria-expanded", "true");
      }
    });
  }
  
  // Skill tag click
  if (skillTags) {
    skillTags.forEach(tag => {
      tag.addEventListener("click", function() {
        const skill = this.dataset.skill;
        // Add to job description with a bullet point
        const currentText = jobDescription.value;
        const newBullet = `• Utilized ${skill} to improve project outcomes`;
        
        if (currentText) {
          jobDescription.value = currentText + (currentText.endsWith("\n") ? "" : "\n") + newBullet + "\n";
        } else {
          jobDescription.value = newBullet + "\n";
        }
        
        // Show visual feedback
        this.classList.add("selected");
        setTimeout(() => {
          this.classList.remove("selected");
        }, 1500);
        
        // Focus and resize the textarea
        jobDescription.focus();
        jobDescription.style.height = "auto";
        jobDescription.style.height = jobDescription.scrollHeight + "px";
      });
    });
  }
  
  // AI Enhance button
  if (aiEnhanceBtn && aiEnhancePanel) {
    aiEnhanceBtn.addEventListener("click", function() {
      // Toggle the AI enhancement panel
      if (aiEnhancePanel.style.display === "none") {
        aiEnhancePanel.style.display = "block";
      } else {
        aiEnhancePanel.style.display = "none";
      }
    });
  }
  
  // Enhancement options
  if (enhanceOptions) {
    enhanceOptions.forEach(option => {
      option.addEventListener("click", function() {
        const enhanceType = this.dataset.enhance;
        
        if (!jobDescription.value.trim()) {
          showTooltip(jobDescription, "Please add job description first");
          return;
        }
        
        // Add loading effect
        this.classList.add("loading");
        const originalContent = this.innerHTML;
        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Processing...</span>';
        
        // Simulate AI processing (replace with actual API call later)
        setTimeout(() => {
          let enhancedText = "";
          
          switch (enhanceType) {
            case "achievements":
              enhancedText = enhanceWithAchievements(jobDescription.value);
              break;
            case "action-verbs":
              enhancedText = enhanceWithActionVerbs(jobDescription.value);
              break;
            case "skills":
              enhancedText = enhanceWithSkills(jobDescription.value);
              break;
            case "concise":
              enhancedText = enhanceConcise(jobDescription.value);
              break;
            default:
              enhancedText = jobDescription.value;
          }
          
          // Apply the enhanced text
          jobDescription.value = enhancedText;
          
          // Auto-resize the textarea
          jobDescription.style.height = "auto";
          jobDescription.style.height = jobDescription.scrollHeight + "px";
          
          // Reset the button
          this.classList.remove("loading");
          this.innerHTML = originalContent;
          
          // Hide the enhancement panel
          aiEnhancePanel.style.display = "none";
          
          // Show feedback
          const enhanceName = enhanceType.split('-').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
          ).join(' ');
          showTooltip(jobDescription, `Enhanced with ${enhanceName}`);
        }, 1500);
      });
    });
  }
  
  // Toolbar buttons
  if (toolbarBtns) {
    toolbarBtns.forEach(btn => {
      btn.addEventListener("click", function() {
        const action = this.dataset.action;
        
        // Skip if it's the AI enhance button (handled separately)
        if (action === "enhance") return;
        
        switch (action) {
          case "bullet":
            // Add bullet point at cursor or at end
            const cursorPos = jobDescription.selectionStart;
            const textBefore = jobDescription.value.substring(0, cursorPos);
            const textAfter = jobDescription.value.substring(cursorPos);
            
            if (cursorPos === 0 || jobDescription.value.charAt(cursorPos - 1) === '\n') {
              // Add bullet at cursor
              jobDescription.value = textBefore + "• " + textAfter;
              jobDescription.selectionStart = jobDescription.selectionEnd = cursorPos + 2;
            } else if (cursorPos === jobDescription.value.length) {
              // Add new line and bullet at end
              jobDescription.value = textBefore + "\n• ";
              jobDescription.selectionStart = jobDescription.selectionEnd = jobDescription.value.length;
            } else {
              // Add new line and bullet in the middle
              jobDescription.value = textBefore + "\n• " + textAfter;
              jobDescription.selectionStart = jobDescription.selectionEnd = cursorPos + 3;
            }
            break;
            
          case "achievement":
            // Add achievement phrase
            const achievements = [
              "resulting in ",
              "which increased ",
              "leading to ",
              "improving ",
              "reducing "
            ];
            const randomAchievement = achievements[Math.floor(Math.random() * achievements.length)];
            
            // Add at cursor or end
            const pos = jobDescription.selectionEnd;
            jobDescription.value = jobDescription.value.substring(0, pos) + 
                                 " " + randomAchievement + 
                                 jobDescription.value.substring(pos);
            jobDescription.selectionStart = jobDescription.selectionEnd = pos + randomAchievement.length + 1;
            break;
            
          case "skills":
            // Toggle skills panel
            if (toggleJobSkills) {
              const isExpanded = toggleJobSkills.getAttribute("aria-expanded") === "true";
              if (!isExpanded) {
                jobSkillsContainer.classList.remove("collapse");
                toggleJobSkills.setAttribute("aria-expanded", "true");
              }
            }
            break;
        }
        
        // Focus the textarea and update its height
        jobDescription.focus();
        jobDescription.style.height = "auto";
        jobDescription.style.height = jobDescription.scrollHeight + "px";
      });
    });
  }
  
  // Auto expand textarea on input
  jobDescription.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = this.scrollHeight + "px";
  });
};

// Enhancement helper functions (placeholders for future AI integration)
const enhanceWithAchievements = (text) => {
  // Add quantifiable achievements to bullet points
  const lines = text.split('\n');
  const achievementPhrases = [
    "resulting in a 20% increase in efficiency",
    "which improved team productivity by 15%",
    "leading to a 30% reduction in costs",
    "generating an additional $50,000 in revenue",
    "reducing project completion time by 25%",
    "increasing customer satisfaction by 40%",
    "which decreased error rates by 35%",
    "improving system performance by 50%"
  ];
  
  return lines.map(line => {
    if (!line.trim() || line.includes("resulting in") || line.includes("which improved") || 
        line.includes("leading to") || line.includes("increasing") || line.includes("reducing")) {
      return line; // Skip empty lines or lines that already have achievements
    }
    
    const randomAchievement = achievementPhrases[Math.floor(Math.random() * achievementPhrases.length)];
    return `${line.trim()}, ${randomAchievement}`;
  }).join('\n');
};

const enhanceWithActionVerbs = (text) => {
  // Replace weak verbs with strong action verbs
  const weakToStrong = {
    "worked on": "spearheaded",
    "helped": "facilitated",
    "made": "created",
    "did": "executed",
    "used": "leveraged",
    "responsible for": "led",
    "handled": "managed",
    "took care of": "orchestrated",
    "in charge of": "directed",
    "managed": "strategized"
  };
  
  let enhancedText = text;
  Object.entries(weakToStrong).forEach(([weak, strong]) => {
    const regex = new RegExp(`\\b${weak}\\b`, 'gi');
    enhancedText = enhancedText.replace(regex, strong);
  });
  
  return enhancedText;
};

const enhanceWithSkills = (text) => {
  // Add technical skills and keywords
  const techSkills = [
    "SQL", "Python", "JavaScript", "Data Analysis", 
    "Project Management", "Agile Methodology", "Strategic Planning",
    "Cross-functional Collaboration", "Cloud Computing", "Machine Learning",
    "Digital Marketing", "Financial Analysis", "UI/UX Design"
  ];
  
  const lines = text.split('\n');
  
  return lines.map((line, index) => {
    // Only add skills to some lines (not all)
    if (line.trim() && index % 2 === 0 && !lines.some(l => 
      techSkills.some(skill => l.includes(skill)))) {
      const skill = techSkills[Math.floor(Math.random() * techSkills.length)];
      if (!line.includes(skill)) {
        return `${line.trim()} using ${skill}`;
      }
    }
    return line;
  }).join('\n');
};

const enhanceConcise = (text) => {
  // Make text more concise by removing filler words
  const fillerWords = [
    "basically", "actually", "literally", "very", "really", "just",
    "quite", "simply", "that", "in order to", "I think that", "kind of",
    "sort of", "type of", "for the most part", "needless to say"
  ];
  
  let conciseText = text;
  fillerWords.forEach(word => {
    const regex = new RegExp(`\\b${word}\\b`, 'gi');
    conciseText = conciseText.replace(regex, '');
  });
  
  // Clean up double spaces
  conciseText = conciseText.replace(/\s+/g, ' ');
  
  // Restore line breaks
  conciseText = conciseText.replace(/• /g, '\n• ');
  if (!conciseText.startsWith('•')) {
    conciseText = '• ' + conciseText.trim();
  }
  
  return conciseText;
};

// Helper function to show tooltip
const showTooltip = (element, message) => {
  const tooltip = document.createElement("div");
  tooltip.className = "floating-tooltip";
  tooltip.textContent = message;
  
  document.body.appendChild(tooltip);
  
  const rect = element.getBoundingClientRect();
  tooltip.style.top = `${rect.top + window.scrollY - 30}px`;
  tooltip.style.left = `${rect.left + window.scrollX + rect.width / 2}px`;
  tooltip.style.transform = "translate(-50%, -100%)";
  
  setTimeout(() => {
    tooltip.classList.add("show");
  }, 10);
  
  setTimeout(() => {
    tooltip.classList.remove("show");
    setTimeout(() => {
      document.body.removeChild(tooltip);
    }, 300);
  }, 3000);
};

// Initialize
initializeExperiences();
initEventListeners();
};
// Education Manager
const initEducationManager = () => {
  // Elements
  const educationTimeline = document.getElementById("education-timeline");
  const addEducationBtn = document.getElementById("add-education-btn");
  const educationFormContainer = document.getElementById("education-form-container");
  const educationForm = document.getElementById("education-form");
  const educationFormClose = document.getElementById("education-form-close");
  const cancelEducationBtn = document.getElementById("cancel-education");
  const educationFormTitle = document.getElementById("education-form-title");
  const educationIndex = document.getElementById("education-index");
  const degree = document.getElementById("degree");
  const school = document.getElementById("school");
  const startYear = document.getElementById("education-start");
  const endYear = document.getElementById("education-end");
  const currentEducation = document.getElementById("current-education");
  const educationDescription = document.getElementById("education-description");
  const educationData = document.getElementById("education-data");
  const emptyState = document.getElementById("education-empty-state");
  const aiEnhanceBtn = document.querySelector("#education-form .toolbar-btn.ai-enhance");
  const aiEnhancePanel = document.getElementById("education-enhance-panel");
  const enhanceOptions = document.querySelectorAll("#education-enhance-panel .enhance-option");
  const toolbarBtns = document.querySelectorAll("#education-form .toolbar-btn");
  
  if (!educationTimeline || !addEducationBtn || !educationForm) return;
  
  // Education data
  let educations = [];
  
  // Initialize from existing data if available
  const initializeEducations = () => {
    try {
      educations = educationData && educationData.value 
        ? JSON.parse(educationData.value) 
        : [];
    } catch (e) {
      console.error("Error parsing education data:", e);
      educations = [];
    }
    
    renderEducations();
  };
  
  // Render educations to timeline
  const renderEducations = () => {
    // Clear the timeline except empty state
    Array.from(educationTimeline.children).forEach(child => {
      if (child.id !== "education-empty-state") {
        educationTimeline.removeChild(child);
      }
    });
    
    // Toggle empty state visibility
    if (educations.length === 0) {
      emptyState.style.display = "block";
      return;
    } else {
      emptyState.style.display = "none";
    }
    
    // Render each education
    educations.forEach((edu, index) => {
      const timelineItem = document.createElement("div");
      timelineItem.className = "education-timeline-item";
      timelineItem.dataset.index = index;
      
      // Format description as bullet points
      let descriptionHTML = "";
      if (edu.description) {
        const items = edu.description
          .split("\n")
          .filter(line => line.trim())
          .map(line => {
            // Ensure each line starts with a bullet
            const trimmed = line.trim();
            if (trimmed.startsWith("•") || trimmed.startsWith("-") || trimmed.startsWith("*")) {
              return `<li>${trimmed.substring(1).trim()}</li>`;
            } else {
              return `<li>${trimmed}</li>`;
            }
          });
        
        if (items.length) {
          descriptionHTML = `<ul>${items.join("")}</ul>`;
        }
      }
      
      // Current or past education
      const dateDisplay = edu.current 
        ? `${edu.startYear} - Present` 
        : `${edu.startYear} - ${edu.endYear}`;
      
      timelineItem.innerHTML = `
        <div class="education-date">${dateDisplay}</div>
        <div class="education-actions">
          <button type="button" class="education-action edit" data-index="${index}" aria-label="Edit">
            <i class="fas fa-pencil-alt"></i>
          </button>
          <button type="button" class="education-action delete" data-index="${index}" aria-label="Delete">
            <i class="fas fa-trash-alt"></i>
          </button>
        </div>
        <div class="education-content">
          <h4>${edu.degree}</h4>
          <div class="education-school">${edu.school}</div>
          <div class="education-description">
            ${descriptionHTML}
          </div>
        </div>
      `;
      
      educationTimeline.appendChild(timelineItem);
    });
    
    // Add event listeners to the action buttons
    document.querySelectorAll(".education-action.edit").forEach(btn => {
      btn.addEventListener("click", function() {
        const index = parseInt(this.dataset.index);
        editEducation(index);
      });
    });
    
    document.querySelectorAll(".education-action.delete").forEach(btn => {
      btn.addEventListener("click", function() {
        const index = parseInt(this.dataset.index);
        deleteEducation(index);
      });
    });
    
    // Update progress
    updateProgress();
  };
  
  // Add education
  const addEducation = () => {
    // Reset the form
    educationForm.reset();
    educationIndex.value = -1;
    educationFormTitle.textContent = "Add Education";
    
    // Show the form
    educationFormContainer.style.display = "flex";
    setTimeout(() => {
      educationFormContainer.classList.add("active");
    }, 10);
    
    // Focus on the first input
    degree.focus();
  };
  
  // Edit education
  const editEducation = (index) => {
    const education = educations[index];
    if (!education) return;
    
    // Set form values
    educationIndex.value = index;
    degree.value = education.degree;
    school.value = education.school;
    startYear.value = education.startYear;
    
    if (education.current) {
      currentEducation.checked = true;
      endYear.value = "";
      endYear.disabled = true;
    } else {
      currentEducation.checked = false;
      endYear.value = education.endYear;
      endYear.disabled = false;
    }
    
    educationDescription.value = education.description || '';
    
    // Update form title
    educationFormTitle.textContent = "Edit Education";
    
    // Show the form
    educationFormContainer.style.display = "flex";
    setTimeout(() => {
      educationFormContainer.classList.add("active");
    }, 10);
    
    // Expand the textarea to fit content
    educationDescription.style.height = "auto";
    educationDescription.style.height = educationDescription.scrollHeight + "px";
  };
  
  // Delete education
  const deleteEducation = (index) => {
    // Confirm before deleting
    if (confirm("Are you sure you want to delete this education entry?")) {
      educations.splice(index, 1);
      updateEducationData();
      renderEducations();
    }
  };
  
  // Update the hidden input with educations data
  const updateEducationData = () => {
    educationData.value = JSON.stringify(educations);
    // Trigger change event for autosave
    const event = new Event('change', { bubbles: true });
    educationData.dispatchEvent(event);
  };
  
  // Format the education description to ensure bullet points
  const formatDescription = (text) => {
    if (!text) return "";
    
    return text
      .split("\n")
      .map(line => {
        const trimmed = line.trim();
        if (!trimmed) return "";
        if (trimmed.startsWith("•") || trimmed.startsWith("-") || trimmed.startsWith("*")) {
          return trimmed;
        } else {
          return `• ${trimmed}`;
        }
      })
      .filter(line => line)
      .join("\n");
  };
  
  // Handle form submission
  const handleFormSubmit = (e) => {
    e.preventDefault();
    
    // Basic validation
    if (!degree.value || !school.value || !startYear.value) {
      showTooltip(educationForm, "Please fill in all required fields");
      return;
    }
    
    const index = parseInt(educationIndex.value);
    const isNewEducation = index === -1;
    
    // Format the description
    const formattedDescription = formatDescription(educationDescription.value);
    
    // Create education object
    const education = {
      degree: degree.value,
      school: school.value,
      startYear: startYear.value,
      endYear: currentEducation.checked ? "" : endYear.value,
      current: currentEducation.checked,
      description: formattedDescription
    };
    
    // Update or add the education
    if (isNewEducation) {
      educations.push(education);
    } else {
      educations[index] = education;
    }
    
    // Update data and render
    updateEducationData();
    renderEducations();
    
    // Close the form
    closeForm();
    
    // Show success toast
    showTooltip(addEducationBtn, isNewEducation ? "Education added successfully" : "Education updated successfully");
  };
  
  // Close the form
  const closeForm = () => {
    educationFormContainer.classList.remove("active");
    setTimeout(() => {
      educationFormContainer.style.display = "none";
    }, 300);
  };
  
  // Initialize event listeners
  const initEventListeners = () => {
    // Add education button
    addEducationBtn.addEventListener("click", addEducation);
    
    // Form submission
    educationForm.addEventListener("submit", handleFormSubmit);
    
    // Close form buttons
    educationFormClose.addEventListener("click", closeForm);
    cancelEducationBtn.addEventListener("click", closeForm);
    
    // Current education checkbox
    currentEducation.addEventListener("change", function() {
      if (this.checked) {
        endYear.value = "";
        endYear.disabled = true;
      } else {
        endYear.disabled = false;
      }
    });
    
    // Close on click outside form
    educationFormContainer.addEventListener("click", function(e) {
      if (e.target === this) {
        closeForm();
      }
    });
    
    // AI Enhance button
    if (aiEnhanceBtn && aiEnhancePanel) {
      aiEnhanceBtn.addEventListener("click", function() {
        // Toggle the AI enhancement panel
        if (aiEnhancePanel.style.display === "none") {
          aiEnhancePanel.style.display = "block";
        } else {
          aiEnhancePanel.style.display = "none";
        }
      });
    }
    
    // Enhancement options
    if (enhanceOptions) {
      enhanceOptions.forEach(option => {
        option.addEventListener("click", function() {
          const enhanceType = this.dataset.enhance;
          
          if (!educationDescription.value.trim() && enhanceType !== 'coursework') {
            showTooltip(educationDescription, "Please add a description first");
            return;
          }
          
          // Add loading effect
          this.classList.add("loading");
          const originalContent = this.innerHTML;
          this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Processing...</span>';
          
          // Simulate AI processing (replace with actual API call later)
          setTimeout(() => {
            let enhancedText = "";
            
            switch (enhanceType) {
              case "coursework":
                enhancedText = addRelevantCoursework(degree.value, educationDescription.value);
                break;
              case "achievements":
                enhancedText = addAcademicAchievements(educationDescription.value);
                break;
              case "concise":
                enhancedText = makeEducationConcise(educationDescription.value);
                break;
              case "format":
                enhancedText = improveEducationFormat(educationDescription.value);
                break;
              default:
                enhancedText = educationDescription.value;
            }
            
            // Apply the enhanced text
            educationDescription.value = enhancedText;
            
            // Auto-resize the textarea
            educationDescription.style.height = "auto";
            educationDescription.style.height = educationDescription.scrollHeight + "px";
            
            // Reset the button
            this.classList.remove("loading");
            this.innerHTML = originalContent;
            
            // Hide the enhancement panel
            aiEnhancePanel.style.display = "none";
            
            // Show feedback
            const enhanceName = enhanceType.split('-').map(word => 
              word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
            showTooltip(educationDescription, `Enhanced with ${enhanceName}`);
          }, 1500);
        });
      });
    }
    
    // Toolbar buttons
    if (toolbarBtns) {
      toolbarBtns.forEach(btn => {
        btn.addEventListener("click", function() {
          const action = this.dataset.action;
          
          // Skip if it's the AI enhance button (handled separately)
          if (action === "enhance") return;
          
          switch (action) {
            case "bullet":
              // Add bullet point at cursor or at end
              const cursorPos = educationDescription.selectionStart;
              const textBefore = educationDescription.value.substring(0, cursorPos);
              const textAfter = educationDescription.value.substring(cursorPos);
              
              if (cursorPos === 0 || educationDescription.value.charAt(cursorPos - 1) === '\n') {
                // Add bullet at cursor
                educationDescription.value = textBefore + "• " + textAfter;
                educationDescription.selectionStart = educationDescription.selectionEnd = cursorPos + 2;
              } else if (cursorPos === educationDescription.value.length) {
                // Add new line and bullet at end
                educationDescription.value = textBefore + "\n• ";
                educationDescription.selectionStart = educationDescription.selectionEnd = educationDescription.value.length;
              } else {
                // Add new line and bullet in the middle
                educationDescription.value = textBefore + "\n• " + textAfter;
                educationDescription.selectionStart = educationDescription.selectionEnd = cursorPos + 3;
              }
              break;
              
            case "course":
              // Add coursework template based on degree
              addCourseTemplate();
              break;
              
            case "gpa":
              // Add GPA template
              const gpaPos = educationDescription.selectionEnd;
              const gpaTemplate = "• GPA: 3.8/4.0, Dean's List";
              
              if (educationDescription.value) {
                const lastChar = educationDescription.value.slice(-1);
                educationDescription.value += (lastChar === '\n' ? '' : '\n') + gpaTemplate;
              } else {
                educationDescription.value = gpaTemplate;
              }
              
              educationDescription.selectionStart = educationDescription.selectionEnd = educationDescription.value.length;
              break;
          }
          
          // Focus the textarea and update its height
          educationDescription.focus();
          educationDescription.style.height = "auto";
          educationDescription.style.height = educationDescription.scrollHeight + "px";
        });
      });
    }
    
    // Auto expand textarea on input
    educationDescription.addEventListener("input", function() {
      this.style.height = "auto";
      this.style.height = this.scrollHeight + "px";
    });
  };
  
  // Add course template based on degree
  const addCourseTemplate = () => {
    if (!degree.value) {
      showTooltip(degree, "Please enter your degree first");
      degree.focus();
      return;
    }
    
    const degreeText = degree.value.toLowerCase();
    let courseTemplate = "• Relevant coursework: ";
    
    if (degreeText.includes("computer science") || degreeText.includes("cs")) {
      courseTemplate += "Data Structures, Algorithms, Operating Systems, Database Systems, Web Development";
    } else if (degreeText.includes("business") || degreeText.includes("mba")) {
      courseTemplate += "Financial Accounting, Marketing Management, Business Strategy, Organizational Behavior";
    } else if (degreeText.includes("engineering")) {
      courseTemplate += "Engineering Design, Thermodynamics, Fluid Mechanics, Materials Science";
    } else if (degreeText.includes("data") || degreeText.includes("analytics")) {
      courseTemplate += "Statistical Methods, Data Mining, Machine Learning, Big Data Technologies";
    } else {
      courseTemplate += "[Add your relevant courses here]";
    }
    
    // Add to description
    if (educationDescription.value) {
      const lastChar = educationDescription.value.slice(-1);
      educationDescription.value += (lastChar === '\n' ? '' : '\n') + courseTemplate;
    } else {
      educationDescription.value = courseTemplate;
    }
    
    educationDescription.selectionStart = educationDescription.selectionEnd = educationDescription.value.length;
    educationDescription.focus();
    educationDescription.style.height = "auto";
    educationDescription.style.height = educationDescription.scrollHeight + "px";
  };
  
  const addRelevantCoursework = (degreeText, currentText) => {
    // Generate relevant coursework based on degree
    const degree = degreeText.toLowerCase();
    let coursework = "";
    
    if (degree.includes("computer science") || degree.includes("cs")) {
      coursework = "• Relevant coursework: Data Structures, Algorithms, Operating Systems, Database Systems, Computer Networks, Software Engineering, Artificial Intelligence, Machine Learning";
    } else if (degree.includes("business") || degree.includes("mba")) {
      coursework = "• Relevant coursework: Financial Accounting, Marketing Management, Business Strategy, Organizational Behavior, Corporate Finance, Economics, Business Ethics";
    } else if (degree.includes("engineering")) {
      coursework = "• Relevant coursework: Engineering Mathematics, Thermodynamics, Fluid Mechanics, Materials Science, Control Systems, Engineering Design, Project Management";
    } else if (degree.includes("psychology")) {
      coursework = "• Relevant coursework: Cognitive Psychology, Developmental Psychology, Social Psychology, Research Methods, Statistics, Abnormal Psychology";
    } else if (degree.includes("data") || degree.includes("analytics")) {
      coursework = "• Relevant coursework: Statistical Methods, Data Mining, Machine Learning, Big Data Technologies, Data Visualization, Predictive Modeling";
    } else {
      coursework = "• Relevant coursework: [Add your major-specific courses here]";
    }
    
    // Add to existing content or replace
    if (currentText.trim() && !currentText.includes("Relevant coursework")) {
      return currentText + (currentText.endsWith('\n') ? '' : '\n') + coursework;
    } else if (currentText.includes("Relevant coursework")) {
      // Replace existing coursework line
      const lines = currentText.split('\n');
      const updatedLines = lines.map(line => {
        if (line.includes("Relevant coursework")) {
          return coursework;
        }
        return line;
      });
      return updatedLines.join('\n');
    } else {
      return coursework;
    }
  };
  
  const addAcademicAchievements = (currentText) => {
    // Add academic achievements
    const achievements = [
      "• Dean's List for all semesters",
      "• Graduated Magna Cum Laude",
      "• Recipient of Academic Excellence Scholarship",
      "• Selected for Honors Program",
      "• Awarded Department Recognition for Outstanding Performance",
      "• Participated in Undergraduate Research Program",
      "• Selected as Teaching Assistant for core courses"
    ];
    
    // Select 2-3 random achievements
    const numAchievements = Math.floor(Math.random() * 2) + 2; // 2-3
    const selectedAchievements = [];
    
    for (let i = 0; i < numAchievements; i++) {
      const randomIndex = Math.floor(Math.random() * achievements.length);
      selectedAchievements.push(achievements[randomIndex]);
      achievements.splice(randomIndex, 1); // Remove selected achievement
    }
    
    const achievementsText = selectedAchievements.join('\n');
    
    // Add to existing content
    if (currentText.trim()) {
      return currentText + (currentText.endsWith('\n') ? '' : '\n') + achievementsText;
    } else {
      return achievementsText;
    }
  };
  
  const makeEducationConcise = (currentText) => {
    if (!currentText.trim()) return "";
    
    // Split into lines and remove redundant/verbose content
    const lines = currentText.split('\n').filter(line => line.trim());
    
    // Filter out filler words and shorten lines
    const conciseLines = lines.map(line => {
      // Remove filler words
      let conciseLine = line
        .replace(/I was |I have been |I am |I've been /g, '')
        .replace(/was responsible for|was tasked with/g, 'handled')
        .replace(/In this program,|During my time here,|Throughout my studies,/g, '')
        .replace(/\bvery\b|\breally\b|\bquite\b|\bbasically\b|\bjust\b/g, '')
        .trim();
      
      // Ensure bullet point
      if (!conciseLine.startsWith('•') && !conciseLine.startsWith('-') && !conciseLine.startsWith('*')) {
        conciseLine = '• ' + conciseLine;
      }
      
      return conciseLine;
    });
    
    // Limit to 4-5 most important points
    const importantLines = conciseLines.slice(0, Math.min(5, conciseLines.length));
    
    return importantLines.join('\n');
  };
  
  const improveEducationFormat = (currentText) => {
    if (!currentText.trim()) return "";
    
    // Split into lines
    let lines = currentText.split('\n').filter(line => line.trim());
    
    // Make sure each line starts with a bullet point
    lines = lines.map(line => {
      line = line.trim();
      if (!line.startsWith('•') && !line.startsWith('-') && !line.startsWith('*')) {
        return '• ' + line;
      }
      return line;
    });
    
    // Organize by categories
    const categorized = {
      gpa: [],
      coursework: [],
      achievements: [],
      activities: [],
      other: []
    };
    
    lines.forEach(line => {
      const lowerLine = line.toLowerCase();
      if (lowerLine.includes('gpa') || lowerLine.includes('grade') || lowerLine.includes('cum laude')) {
        categorized.gpa.push(line);
      } else if (lowerLine.includes('course') || lowerLine.includes('class') || lowerLine.includes('studied')) {
        categorized.coursework.push(line);
      } else if (lowerLine.includes('award') || lowerLine.includes('honor') || lowerLine.includes('scholarship') || 
                lowerLine.includes('dean') || lowerLine.includes('recognition')) {
        categorized.achievements.push(line);
      } else if (lowerLine.includes('club') || lowerLine.includes('society') || 
                lowerLine.includes('association') || lowerLine.includes('volunteer') ||
                lowerLine.includes('member') || lowerLine.includes('president') ||
                lowerLine.includes('leader') || lowerLine.includes('captain')) {
        categorized.activities.push(line);
      } else {
        categorized.other.push(line);
      }
    });
    
    // Reassemble in a logical order
    const formattedLines = [
      ...categorized.gpa,
      ...categorized.coursework,
      ...categorized.achievements,
      ...categorized.activities,
      ...categorized.other
    ];
    
    return formattedLines.join('\n');
  };
  
  // Helper function to show tooltip
  const showTooltip = (element, message) => {
    const tooltip = document.createElement("div");
    tooltip.className = "floating-tooltip";
    tooltip.textContent = message;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.top = `${rect.top + window.scrollY - 30}px`;
    tooltip.style.left = `${rect.left + window.scrollX + rect.width / 2}px`;
    tooltip.style.transform = "translate(-50%, -100%)";
    
    setTimeout(() => {
      tooltip.classList.add("show");
    }, 10);
    
    setTimeout(() => {
      tooltip.classList.remove("show");
      setTimeout(() => {
        document.body.removeChild(tooltip);
      }, 300);
    }, 3000);
  };
  
  // Initialize
  initializeEducations();
  initEventListeners();
};

// Initialize Everything
document.addEventListener("DOMContentLoaded", () => {
  // Initialize everything
  initPanels();
  initStyles();
  initSkillsManager();
  initAISkillsIntegration();
  initExperienceManager();
  initSummaryManager();
  addTooltipStyles();
  initCollapsibleSections();
  setupAutoResizeInputs();
  setupAutoExpandTextareas();
  setupAutoSave();
  enhanceFormFields();
  initAIEnhancement();
  initSectionOptions();
  initTemplates(); // Add template initialization
  updateProgress();
  initEducationManager();
  // Add this to your document.addEventListener("DOMContentLoaded", ...)
const toggleAddSections = document.getElementById("toggle-add-sections");
const addSectionOptions = document.getElementById("add-section-options");

if (toggleAddSections && addSectionOptions) {
    toggleAddSections.addEventListener("click", function() {
        const isVisible = addSectionOptions.style.display !== "none";
        
        if (isVisible) {
            addSectionOptions.style.display = "none";
            this.classList.remove("active");
        } else {
            addSectionOptions.style.display = "grid";
            this.classList.add("active");
        }
    });
    
    // Set up section option handlers
    const sectionOptions = document.querySelectorAll(".section-option");
    sectionOptions.forEach(option => {
        option.addEventListener("click", function() {
            const sectionType = this.dataset.section;
            // Implement section addition logic here
            console.log(`Adding section: ${sectionType}`);
            
            // Show feedback
            showFeedback(this, "success", `${sectionType} section added!`);
            
            // Close the options panel after selection
            addSectionOptions.style.display = "none";
            toggleAddSections.classList.remove("active");
        });
    });
}

  const refreshBtn = document.getElementById("preview-refresh");
  if (refreshBtn) {
    // refreshBtn.addEventListener("click", updatePreview);
  }

  // Handle download button feedback
  const downloadBtn = document.querySelector(
    '.float-control-btn[href*="/download_resume"]'
  );
  if (downloadBtn) {
    downloadBtn.addEventListener("click", (e) => {
      e.preventDefault();
      showFeedback(downloadBtn, "success", "Downloading resume...");
      setTimeout(() => {
        window.location.href = downloadBtn.href;
      }, 1000);
    });
  }
  
  // Initialize circular progress click to show details
  const circularProgress = document.querySelector('.circular-progress');
  if (circularProgress) {
    circularProgress.addEventListener('click', () => {
      const percentage = document.querySelector('.progress-percentage').textContent;
      
      const sections = document.querySelectorAll('.resume-section-collapsible');
      const completedSections = document.querySelectorAll('.resume-section-collapsible.complete');
      
      const message = `Resume completion: ${percentage}
Completed sections: ${completedSections.length} of ${sections.length}

Click on the Edit button in the sidebar to continue building your resume.`;
      
      alert(message);
    });
  }

  // Listen for window resize to adjust sidebar visibility
  window.addEventListener('resize', () => {
    const sidebar = document.querySelector('.floating-controls-left');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const container = document.querySelector('.resume-builder-container');
    
    if (window.innerWidth <= 768) {
      sidebar.classList.add('collapsed');
      container.classList.add('sidebar-collapsed');
      if (sidebarToggle) {
        sidebarToggle.innerHTML = '<i class="fas fa-bars"></i>';
      }
    } else {
      sidebar.classList.remove('collapsed');
      container.classList.remove('sidebar-collapsed');
    }
  });
});


