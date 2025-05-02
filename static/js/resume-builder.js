
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
  const toggleExamples = document.getElementById("toggle-examples");
  const examplesContainer = document.getElementById("examples-container");
  const exampleTabs = document.querySelectorAll(".example-tab");
  const exampleContents = document.querySelectorAll(".example-content");
  const useExampleBtns = document.querySelectorAll(".use-example-btn");
  
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
  
  // Toggle Examples
  if (toggleExamples && examplesContainer) {
    toggleExamples.addEventListener("click", function() {
      const isExpanded = this.getAttribute("aria-expanded") === "true";
      
      if (isExpanded) {
        examplesContainer.classList.add("collapse");
        this.setAttribute("aria-expanded", "false");
      } else {
        examplesContainer.classList.remove("collapse");
        this.setAttribute("aria-expanded", "true");
      }
    });
  }
  
  // Example Tabs
  if (exampleTabs) {
    exampleTabs.forEach(tab => {
      tab.addEventListener("click", function() {
        // Remove active class from all tabs and contents
        exampleTabs.forEach(t => t.classList.remove("active"));
        exampleContents.forEach(c => c.classList.remove("active"));
        
        // Add active class to the clicked tab
        this.classList.add("active");
        
        // Show the corresponding content
        const exampleType = this.dataset.example;
        document.getElementById(`example-${exampleType}`).classList.add("active");
      });
    });
  }
  
  // Use Example buttons
  if (useExampleBtns) {
    useExampleBtns.forEach(btn => {
      btn.addEventListener("click", function() {
        const exampleType = this.dataset.example;
        const exampleContent = document.getElementById(`example-${exampleType}`).querySelector("p").textContent;
        
        // Confirm before overwriting existing content
        if (summaryTextarea.value.trim() && !confirm("This will replace your current summary. Continue?")) {
          return;
        }
        
        // Apply the example text
        summaryTextarea.value = exampleContent;
        summaryTextarea.dispatchEvent(new Event('input'));
        
        // Trigger autosave
        const event = new Event('change', { bubbles: true });
        summaryTextarea.dispatchEvent(event);
        
        // Close examples container
        examplesContainer.classList.add("collapse");
        toggleExamples.setAttribute("aria-expanded", "false");
        
        // Show confirmation message
        showTooltip(summaryTextarea, "Example applied! Customize it to match your experience.");
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

// Initialize Everything
document.addEventListener("DOMContentLoaded", () => {
  // Initialize everything
  initPanels();
  initStyles();
  initSkillsManager();
  initAISkillsIntegration();
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


