// AI Assistant functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize AI Assistant
    setupAIAssistant();
  });
  
  // Setup the main AI assistant
  function setupAIAssistant() {
    // Main AI assistant button
    const aiModal = document.getElementById('ai-assistant-modal');
 
   
    const atsButton = document.querySelector('.ats-score-btn');
    if(aiModal) {
      const featureCards = aiModal.querySelectorAll('.ai-feature-card');
      // Handle AI feature card clicks
      featureCards.forEach(card => {
        card.addEventListener('click', function() {
          const action = this.getAttribute('data-action');
          handleAIAction(action);
        });
      });
       // Close modal when clicking outside
    aiModal.addEventListener('click', function(e) {
      if (e.target === aiModal) {
        aiModal.classList.remove('active');
      }
    });
    }
  
    
    // Handle ATS score button
    if (atsButton) {
      atsButton.addEventListener('click', function() {
        handleAIAction('ats-scan');
      });
    }
    
   
  }
  
  // Handle AI actions
  function handleAIAction(action) {
    switch (action) {
      case 'generate-summary':
        generateSummary();
        break;
      case 'enhance-bullets':
        showEnhanceBulletsSelector();
        break;
      case 'suggest-skills':
        suggestSkills();
        break;
      case 'tailor-to-job':
        showJobDescriptionInput();
        break;
      case 'ats-scan':
        scanResumeForATS();
        break;
      case 'extract-skills':
        extractSkills();
        break;
      default:
        console.log('Unknown AI action:', action);
    }
  }
  
  // Show and update AI modal
  function showAIModal(title, content) {
    const modal = document.querySelector('.ai-modal');
    const modalTitle = document.querySelector('.ai-modal-title');
    const modalBody = document.querySelector('.ai-modal-body');
    modalTitle.textContent = title;
    modalBody.innerHTML = content;
    if (!modal.classList.contains('active')) {
      modal.classList.add('active');
    }
  }
  
  // Close AI modal
  function closeAIModal() {
    document.querySelector('.ai-modal').classList.remove('active');
  }
  
  // Show error in AI modal
  function showAIError(message) {
    showAIModal('Error', `
      <p>${message}</p>
      <div class="ai-actions">
        <button class="btn btn-outline ai-cancel">Close</button>
      </div>
    `);
    document.querySelector('.ai-cancel').addEventListener('click', closeAIModal);
  }
  
  // Call LLM API
  function callLLMAPI(endpoint, data) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    return fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify(data),
      credentials: 'same-origin'
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Network response was not ok: ${response.status}`);
      }
      return response.json();
    })
    .catch(error => {
      console.error('API call error:', error);
      return { success: false, error: error.message };
    });
  }
  
  // Collect resume content
  function collectResumeContent() {
    const resumeData = {
      name: document.querySelector('.name')?.textContent || '',
      title: document.querySelector('.title')?.textContent || '',
      contact: {},
      sections: []
    };
    
    // Collect contact information
    document.querySelectorAll('.contact-item').forEach(item => {
      const icon = item.querySelector('.contact-icon')?.className.match(/fa-(\w+)/)?.[1];
      const content = item.querySelector('.contact-content')?.textContent;
      if (icon && content) {
        resumeData.contact[icon] = content;
      }
    });
    
    // Collect sections
    document.querySelectorAll('.resume-section').forEach(section => {
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
  
  // Trigger save event
  function triggerSaveEvent(element) {
    element.dispatchEvent(new Event('input', { bubbles: true }));
  }
  
  // Generate summary
  function generateSummary() {
    const summarySection = document.querySelector('.summary-section .section-content');
    if (!summarySection) {
      showAIError('Summary section not found. Please add a summary section first.');
      return;
    }
    
    const resumeContent = collectResumeContent();
    const resumeId = 1; // Replace with actual resume ID
    
    showAIModal('Generating Professional Summary', `
      <div class="ai-loading">
        <div class="ai-spinner"></div>
        <p>Analyzing your experience and skills...</p>
      </div>
    `);
    
    callLLMAPI('/api/v1/resume/llm/generate-summary', {
      resume_id: resumeId,
      resumeContent: resumeContent
    })
    .then(response => {
      if (response.success && response.options) {
        showAIModal('Choose a Professional Summary', `
          <p>Select a summary that best represents your experience:</p>
          ${response.options.map((option, index) => `
            <div class="ai-option" data-index="${index}">
              <div class="ai-option-title">Option ${index + 1}</div>
              <div class="ai-option-content">${option}</div>
            </div>
          `).join('')}
          <div class="ai-actions">
            <button class="btn btn-outline ai-cancel">Cancel</button>
          </div>
        `);
        
        document.querySelectorAll('.ai-option').forEach(option => {
          option.addEventListener('click', function() {
            summarySection.textContent = response.options[parseInt(this.getAttribute('data-index'))];
            triggerSaveEvent(summarySection);
            closeAIModal();
          });
        });
        
        document.querySelector('.ai-cancel').addEventListener('click', closeAIModal);
      } else {
        showAIError('Could not generate summary. ' + (response.error || ''));
      }
    })
    .catch(error => {
      console.error('Error generating summary:', error);
      showAIError('Could not generate summary. Please try again.');
    });
  }
  
  // Show bullet enhancement interface
  function showEnhanceBulletsSelector() {
    const experienceSections = document.querySelectorAll('.experience-section .section-item');
    if (experienceSections.length === 0) {
      showAIError('No experience items found. Please add work experience first.');
      return;
    }
    
    let experienceOptions = '';
    experienceSections.forEach((item, index) => {
      const jobTitle = item.querySelector('.section-job-title')?.textContent.trim() || 'Position';
      const company = item.querySelector('.section-company')?.textContent.trim() || 'Company';
      experienceOptions += `
        <div class="ai-option" data-index="${index}">
          <div class="ai-option-title">${jobTitle} at ${company}</div>
          <div class="ai-option-content">Enhance this experience entry</div>
        </div>
      `;
    });
    
    showAIModal('Enhance Experience', `
      <p>Select which experience to enhance:</p>
      ${experienceOptions}
      <div class="ai-actions">
        <button class="btn btn-outline ai-cancel">Cancel</button>
      </div>
    `);
    
    document.querySelectorAll('.ai-option').forEach(option => {
      option.addEventListener('click', function() {
        const index = parseInt(this.getAttribute('data-index'));
        enhanceBullets(experienceSections[index]);
      });
    });
    
    document.querySelector('.ai-cancel').addEventListener('click', closeAIModal);
  }
  
  // Enhance bullet points
  function enhanceBullets(experienceItem) {
    const bulletsContainer = experienceItem.querySelector('.section-duties');
    if (!bulletsContainer) {
      showAIError('No bullet points found in this experience entry.');
      return;
    }
    
    const bullets = Array.from(bulletsContainer.querySelectorAll('li')).map(li => li.textContent.trim()).filter(text => text);
    if (bullets.length === 0) {
      showAIError('Please add bullet points to this experience entry first.');
      return;
    }
    
    const resumeId = 1; // Replace with actual resume ID
    const jobTitle = experienceItem.querySelector('.section-job-title')?.textContent.trim() || '';
    const company = experienceItem.querySelector('.section-company')?.textContent.trim() || '';
    
    showAIModal('Enhancing Bullet Points', `
      <div class="ai-loading">
        <div class="ai-spinner"></div>
        <p>Strengthening your bullet points...</p>
      </div>
    `);
    
    callLLMAPI('/api/v1/resume/llm/enhance-bullets', {
      resume_id: resumeId,
      bullets: bullets,
      jobTitle: jobTitle,
      company: company
    })
    .then(response => {
      if (response.success && response.enhanced) {
        showAIModal('Enhanced Bullet Points', `
          <p>Select which enhanced bullet points to use:</p>
          <div class="ai-bullets-comparison">
            ${response.enhanced.map((enhanced, i) => `
              <div class="ai-bullet-pair">
                <div class="ai-bullet-original">${bullets[i] || ''}</div>
                <div class="ai-bullet-arrow">→</div>
                <div class="ai-bullet-enhanced">${enhanced}</div>
                <label class="ai-bullet-checkbox">
                  <input type="checkbox" data-index="${i}" checked>
                  <span class="checkmark"></span>
                </label>
              </div>
            `).join('')}
          </div>
          <div class="ai-actions">
            <button class="btn btn-outline ai-cancel">Cancel</button>
            <button class="btn btn-primary ai-apply">Apply Selected</button>
          </div>
        `);
        
        document.querySelector('.ai-apply').addEventListener('click', () => {
            const selectedIndices = Array.from(document.querySelectorAll('.ai-bullet-checkbox input:checked')).map(cb => parseInt(cb.getAttribute('data-index')));
            const bulletItems = bulletsContainer.querySelectorAll('li');
            selectedIndices.forEach(index => {
              if (index < bulletItems.length) {
                bulletItems[index].textContent = response.enhanced[index];
                triggerSaveEvent(bulletItems[index]);
              } else {
                const newBullet = document.createElement('li');
                newBullet.textContent = response.enhanced[index];
                bulletsContainer.appendChild(newBullet);
                triggerSaveEvent(newBullet);
              }
            });
            closeAIModal();
          });
          
          document.querySelector('.ai-cancel').addEventListener('click', closeAIModal);
        } else {
          showAIError('Could not enhance bullet points. ' + (response.error || ''));
        }
      })
      .catch(error => {
        console.error('Error enhancing bullets:', error);
        showAIError('Could not enhance bullet points. Please try again.');
      });
    }
    
    // Suggest skills
  function suggestSkills() {
      const skillsSection = document.querySelector('.skills-section .section-container');
      if (!skillsSection) {
        showAIError('Skills section not found. Please add a skills section first.');
        return;
      }
      
      const resumeContent = collectResumeContent();
      const resumeId = 1; // Replace with actual resume ID
      
      showAIModal('Suggesting Skills', `
        <div class="ai-loading">
          <div class="ai-spinner"></div>
          <p>Analyzing your experience to suggest relevant skills...</p>
        </div>
      `);
      
      callLLMAPI('/api/v1/resume/llm/suggest-skills', {
        resume_id: resumeId,
        resumeContent: resumeContent
      })
      .then(response => {
        if (response.success && response.suggestedSkills) {
          showAIModal('Suggested Skills', `
            <p>Select skills to add to your resume:</p>
            <div class="ai-skills-grid">
              ${response.suggestedSkills.map((skill, i) => `
                <div class="ai-skill-option">
                  <input type="checkbox" class="ai-skill-checkbox" id="skill-${i}" data-skill="${skill}" checked>
                  <label for="skill-${i}">
                    <span class="ai-skill-name">${skill}</span>
                    ${response.relevance && response.relevance[i] ? `<span class="ai-skill-relevance">(${response.relevance[i]})</span>` : ''}
                  </label>
                </div>
              `).join('')}
            </div>
            <div class="ai-actions">
              <button class="btn btn-outline ai-cancel">Cancel</button>
              <button class="btn btn-primary ai-apply">Add Selected</button>
            </div>
          `);
          
          document.querySelector('.ai-apply').addEventListener('click', () => {
            const selectedSkills = Array.from(document.querySelectorAll('.ai-skill-checkbox:checked')).map(cb => cb.getAttribute('data-skill'));
            const addTagBtn = skillsSection.querySelector('.add-tag-btn');
            
            if (selectedSkills.length > 0) {
              selectedSkills.forEach(skill => {
                const existingTags = Array.from(skillsSection.querySelectorAll('.section-tag')).map(tag => 
                  tag.textContent.trim().replace(/^\s*[✓✔]\s*|\s*[×✖]\s*$/g, '')
                );
                
                // Only add if the skill doesn't already exist
                if (!existingTags.includes(skill)) {
                  const newTag = document.createElement('span');
                  newTag.className = 'section-tag';
                  newTag.innerHTML = `
                    <i class="fas fa-check"></i>
                    ${skill}
                    <i class="fas fa-times tag-delete"></i>
                  `;
                  skillsSection.insertBefore(newTag, addTagBtn);
                  
                  // Add event listener for delete button
                  const deleteBtn = newTag.querySelector('.tag-delete');
                  if (deleteBtn) {
                    deleteBtn.addEventListener('click', function() {
                      newTag.remove();
                      // Trigger save
                      document.dispatchEvent(new Event('input'));
                    });
                  }
                }
              });
              
              // Trigger save
              document.dispatchEvent(new Event('input'));
              closeAIModal();
            }
          });
          
          document.querySelector('.ai-cancel').addEventListener('click', closeAIModal);
        } else {
          showAIError('Could not suggest skills. ' + (response.error || ''));
        }
      })
      .catch(error => {
        console.error('Error suggesting skills:', error);
        showAIError('Could not suggest skills. Please try again.');
      });
    }
    
    // Extract skills from experience
  function extractSkills() {
      const skillsSection = document.querySelector('.skills-section .section-container');
      if (!skillsSection) {
        showAIError('Skills section not found. Please add a skills section first.');
        return;
      }
      
      const experienceSection = document.querySelector('.experience-section');
      if (!experienceSection) {
        showAIError('Experience section not found. Please add work experience first.');
        return;
      }
      
      const resumeContent = collectResumeContent();
      const resumeId = 1; // Replace with actual resume ID
      
      showAIModal('Extracting Skills', `
        <div class="ai-loading">
          <div class="ai-spinner"></div>
          <p>Analyzing your experience to extract relevant skills...</p>
        </div>
      `);
      
      callLLMAPI('/api/v1/resume/llm/extract-skills', {
        resume_id: resumeId,
        resumeContent: resumeContent
      })
      .then(response => {
        if (response.success && response.extractedSkills) {
          showAIModal('Extracted Skills', `
            <p>Select skills to add to your resume:</p>
            <div class="ai-skills-grid">
              ${response.extractedSkills.map((skill, i) => `
                <div class="ai-skill-option">
                  <input type="checkbox" class="ai-skill-checkbox" id="ext-skill-${i}" data-skill="${skill}" checked>
                  <label for="ext-skill-${i}">
                    <span class="ai-skill-name">${skill}</span>
                  </label>
                </div>
              `).join('')}
            </div>
            <div class="ai-actions">
              <button class="btn btn-outline ai-cancel">Cancel</button>
              <button class="btn btn-primary ai-apply">Add Selected</button>
            </div>
          `);
          
          document.querySelector('.ai-apply').addEventListener('click', () => {
            const selectedSkills = Array.from(document.querySelectorAll('.ai-skill-checkbox:checked')).map(cb => cb.getAttribute('data-skill'));
            const addTagBtn = skillsSection.querySelector('.add-tag-btn');
            
            if (selectedSkills.length > 0) {
              selectedSkills.forEach(skill => {
                const existingTags = Array.from(skillsSection.querySelectorAll('.section-tag')).map(tag => 
                  tag.textContent.trim().replace(/^\s*[✓✔]\s*|\s*[×✖]\s*$/g, '')
                );
                
                // Only add if the skill doesn't already exist
                if (!existingTags.includes(skill)) {
                  const newTag = document.createElement('span');
                  newTag.className = 'section-tag';
                  newTag.innerHTML = `
                    <i class="fas fa-check"></i>
                    ${skill}
                    <i class="fas fa-times tag-delete"></i>
                  `;
                  skillsSection.insertBefore(newTag, addTagBtn);
                  
                  // Add event listener for delete button
                  const deleteBtn = newTag.querySelector('.tag-delete');
                  if (deleteBtn) {
                    deleteBtn.addEventListener('click', function() {
                      newTag.remove();
                      // Trigger save
                      document.dispatchEvent(new Event('input'));
                    });
                  }
                }
              });
              
              // Trigger save
              document.dispatchEvent(new Event('input'));
              closeAIModal();
            }
          });
          
          document.querySelector('.ai-cancel').addEventListener('click', closeAIModal);
        } else {
          showAIError('Could not extract skills. ' + (response.error || ''));
        }
      })
      .catch(error => {
        console.error('Error extracting skills:', error);
        showAIError('Could not extract skills. Please try again.');
      });
    }
    
    // TODO : CHECKING WHERE ITS RENDERING
    // Show job description input for tailoring
  function showJobDescriptionInput() {
      showAIModal('Tailor Resume to Job Description', `
        <p>Paste the job description you're applying for:</p>
        <textarea class="ai-job-description" placeholder="Enter job description..."></textarea>
        <div class="ai-actions">
          <button class="btn btn-outline ai-cancel">Cancel</button>
          <button class="btn btn-primary ai-submit-job">Analyze & Tailor</button>
        </div>
      `);
      
      document.querySelector('.ai-submit-job').addEventListener('click', () => {
        const jobDescription = document.querySelector('.ai-job-description').value.trim();
        if (!jobDescription) {
          showAIError('Please enter a job description');
          return;
        }
        
        tailorToJobDescription(jobDescription);
      });
      
      document.querySelector('.ai-cancel').addEventListener('click', closeAIModal);
    }
    
    // Tailor resume to job description
  function tailorToJobDescription(jobDescription) {
      const resumeContent = collectResumeContent();
      const resumeId = 1; // Replace with actual resume ID
      
      showAIModal('Tailoring Resume', `
        <div class="ai-loading">
          <div class="ai-spinner"></div>
          <p>Analyzing job description and tailoring your resume...</p>
        </div>
      `);
      
      // First, get experience items to tailor
      const experienceItems = document.querySelectorAll('.experience-section .section-item');
      if (experienceItems.length === 0) {
        showAIError('No experience items found. Please add work experience first.');
        return;
      }
      
      // Collect all bullet points from all experience entries
      let allBullets = [];
      let experienceData = [];
      
      experienceItems.forEach(item => {
        const jobTitle = item.querySelector('.section-job-title')?.textContent.trim() || '';
        const company = item.querySelector('.section-company')?.textContent.trim() || '';
        
        const bulletsList = item.querySelector('.section-duties');
        if (bulletsList) {
          const bullets = Array.from(bulletsList.querySelectorAll('li')).map(li => li.textContent.trim()).filter(text => text);
          if (bullets.length > 0) {
            experienceData.push({
              item: item,
              jobTitle: jobTitle,
              company: company,
              bullets: bullets,
              bulletsList: bulletsList
            });
            allBullets = allBullets.concat(bullets);
          }
        }
      });
      
      if (experienceData.length === 0) {
        showAIError('No bullet points found in your experience entries.');
        return;
      }
      
      // Tailor the first experience entry as a start
      const firstExp = experienceData[0];
      
      callLLMAPI('/api/v1/resume/llm/tailor-experience', {
        resume_id: resumeId,
        bullets: firstExp.bullets,
        jobTitle: firstExp.jobTitle,
        company: firstExp.company,
        jobDescription: jobDescription
      })
      .then(response => {
        if (response.success && response.tailored) {
          showAIModal('Tailored Experience', `
            <p>Job match: <strong>${response.matchPercentage}%</strong></p>
            <p>Select which tailored bullet points to use:</p>
            <div class="ai-bullets-comparison">
              ${response.tailored.map((tailored, i) => `
                <div class="ai-bullet-pair">
                  <div class="ai-bullet-original">${firstExp.bullets[i] || ''}</div>
                  <div class="ai-bullet-arrow">→</div>
                  <div class="ai-bullet-enhanced">${tailored}</div>
                  <label class="ai-bullet-checkbox">
                    <input type="checkbox" data-index="${i}" checked>
                    <span class="checkmark"></span>
                  </label>
                </div>
              `).join('')}
            </div>
            <div class="ai-actions">
              <button class="btn btn-outline ai-cancel">Cancel</button>
              <button class="btn btn-primary ai-apply">Apply Selected</button>
            </div>
          `);
          
          document.querySelector('.ai-apply').addEventListener('click', () => {
            const selectedIndices = Array.from(document.querySelectorAll('.ai-bullet-checkbox input:checked')).map(cb => parseInt(cb.getAttribute('data-index')));
            const bulletItems = firstExp.bulletsList.querySelectorAll('li');
            selectedIndices.forEach(index => {
              if (index < bulletItems.length) {
                bulletItems[index].textContent = response.tailored[index];
                triggerSaveEvent(bulletItems[index]);
              } else {
                const newBullet = document.createElement('li');
                newBullet.textContent = response.tailored[index];
                firstExp.bulletsList.appendChild(newBullet);
                triggerSaveEvent(newBullet);
              }
            });
            
            // Also update the summary if available
            if (experienceData.length > 1) {
              showAIModal('Continue Tailoring?', `
                <p>Would you like to tailor more sections of your resume to this job?</p>
                <div class="ai-actions">
                  <button class="btn btn-outline ai-cancel">No, I'm Done</button>
                  <button class="btn btn-primary ai-continue">Yes, Continue</button>
                </div>
              `);
              
              document.querySelector('.ai-continue').addEventListener('click', () => {
                tailorSummaryToJob(jobDescription);
              });
              
              document.querySelector('.ai-cancel').addEventListener('click', closeAIModal);
            } else {
              tailorSummaryToJob(jobDescription);
            }
          });
          
          document.querySelector('.ai-cancel').addEventListener('click', closeAIModal);
        } else {
          showAIError('Could not tailor experience. ' + (response.error || ''));
        }
      })
      .catch(error => {
        console.error('Error tailoring experience:', error);
        showAIError('Could not tailor experience. Please try again.');
      });
    }
    
    // Tailor summary to job
  function tailorSummaryToJob(jobDescription) {
      const summarySection = document.querySelector('.summary-section .section-content');
      if (!summarySection || !summarySection.textContent.trim()) {
        // If no summary, continue to skills
        tailorSkillsToJob(jobDescription);
        return;
      }
      
      const resumeId = 1; // Replace with actual resume ID
      
      showAIModal('Tailoring Summary', `
        <div class="ai-loading">
          <div class="ai-spinner"></div>
          <p>Tailoring your summary to the job description...</p>
        </div>
      `);
      
      callLLMAPI('/api/v1/resume/llm/ats-optimize', {
        resume_id: resumeId,
        text: summarySection.textContent.trim(),
        jobTitle: document.querySelector('.title')?.textContent.trim() || '',
        type: 'summary',
        jobDescription: jobDescription
      })
      .then(response => {
        if (response.success && response.optimized) {
          showAIModal('Tailored Summary', `
            <div class="ai-comparison">
              <div class="ai-before">
                <h4>Original Summary</h4>
                <p>${summarySection.textContent.trim()}</p>
              </div>
              <div class="ai-after">
                <h4>Tailored Summary</h4>
                <p>${response.optimized}</p>
              </div>
            </div>
            <div class="ai-keywords">
              <h4>Key Terms Added:</h4>
              ${response.keywords.map(kw => `<span class="ai-keyword">${kw}</span>`).join('')}
            </div>
            <div class="ai-actions">
              <button class="btn btn-outline ai-cancel">Skip</button>
              <button class="btn btn-primary ai-apply">Apply Changes</button>
            </div>
          `);
          
          document.querySelector('.ai-apply').addEventListener('click', () => {
            summarySection.textContent = response.optimized;
            triggerSaveEvent(summarySection);
            tailorSkillsToJob(jobDescription);
          });
          
          document.querySelector('.ai-cancel').addEventListener('click', () => {
            tailorSkillsToJob(jobDescription);
          });
        } else {
          tailorSkillsToJob(jobDescription);
        }
      })
      .catch(error => {
        console.error('Error tailoring summary:', error);
        tailorSkillsToJob(jobDescription);
      });
    }
    
    // Tailor skills to job
  function tailorSkillsToJob(jobDescription) {
      const resumeId = 1; // Replace with actual resume ID
      
      callLLMAPI('/api/v1/resume/llm/suggest-skills', {
        resume_id: resumeId,
        resumeContent: collectResumeContent(),
        jobDescription: jobDescription
      })
      .then(response => {
        if (response.success && response.suggestedSkills && response.suggestedSkills.length > 0) {
          const skillsSection = document.querySelector('.skills-section .section-container');
          if (!skillsSection) {
            scanResumeForATS();
            return;
          }
          
          showAIModal('Suggested Skills for Job', `
            <p>These skills are recommended based on the job description:</p>
            <div class="ai-skills-grid">
              ${response.suggestedSkills.map((skill, i) => `
                <div class="ai-skill-option">
                  <input type="checkbox" class="ai-skill-checkbox" id="job-skill-${i}" data-skill="${skill}" checked>
                  <label for="job-skill-${i}">
                    <span class="ai-skill-name">${skill}</span>
                    ${response.relevance && response.relevance[i] ? `<span class="ai-skill-relevance">(${response.relevance[i]})</span>` : ''}
                  </label>
                </div>
              `).join('')}
            </div>
            <div class="ai-actions">
              <button class="btn btn-outline ai-cancel">Skip</button>
              <button class="btn btn-primary ai-apply">Add Selected</button>
            </div>
          `);
          
          document.querySelector('.ai-apply').addEventListener('click', () => {
            const selectedSkills = Array.from(document.querySelectorAll('.ai-skill-checkbox:checked')).map(cb => cb.getAttribute('data-skill'));
            const addTagBtn = skillsSection.querySelector('.add-tag-btn');
            
            if (selectedSkills.length > 0) {
              const existingTags = Array.from(skillsSection.querySelectorAll('.section-tag')).map(tag => 
                tag.textContent.trim().replace(/^\s*[✓✔]\s*|\s*[×✖]\s*$/g, '')
              );
              
              selectedSkills.forEach(skill => {
                // Only add if the skill doesn't already exist
                if (!existingTags.includes(skill)) {
                  const newTag = document.createElement('span');
                  newTag.className = 'section-tag';
                  newTag.innerHTML = `
                    <i class="fas fa-check"></i>
                    ${skill}
                    <i class="fas fa-times tag-delete"></i>
                  `;
                  skillsSection.insertBefore(newTag, addTagBtn);
                  
                  // Add event listener for delete button
                  const deleteBtn = newTag.querySelector('.tag-delete');
                  if (deleteBtn) {
                    deleteBtn.addEventListener('click', function() {
                      newTag.remove();
                      // Trigger save
                      document.dispatchEvent(new Event('input'));
                    });
                  }
                }
              });
              
              // Trigger save
              document.dispatchEvent(new Event('input'));
            }
            
            scanResumeForATS();
          });
          
          document.querySelector('.ai-cancel').addEventListener('click', () => {
            scanResumeForATS();
          });
        } else {
          scanResumeForATS();
        }
      })
      .catch(error => {
        console.error('Error suggesting skills for job:', error);
        scanResumeForATS();
      });
    }
    
    // Scan resume for ATS compatibility
  function scanResumeForATS() {
      const resumeContent = collectResumeContent();
      const resumeId = 1; // Replace with actual resume ID
      
      showAIModal('ATS Compatibility Scan', `
        <div class="ai-loading">
          <div class="ai-spinner"></div>
          <p>Scanning your resume for ATS compatibility...</p>
        </div>
      `);
      
      callLLMAPI('/api/v1/resume/llm/ats-scan', {
        resume_id: resumeId,
        resumeContent: resumeContent
      })
      .then(response => {
        if (response.success) {
          showAIModal('ATS Scan Results', `
            <div class="ats-results">
              <div class="ats-score-container">
                <div class="ats-score-circle" style="--score: ${response.atsScore}">
                  <span class="ats-score-value">${response.atsScore}%</span>
                  <span class="ats-score-label">ATS Score</span>
                </div>
              </div>
              
              <div class="ats-details">
                <div class="ats-keywords">
                  <h4>Matched Keywords:</h4>
                  <div class="keywords-container">
                    ${response.matchedKeywords.map(kw => `<span class="ai-keyword">${kw}</span>`).join('')}
                  </div>
                </div>
                
                <div class="ats-keywords">
                  <h4>Missing Keywords:</h4>
                  <div class="keywords-container">
                    ${response.missingKeywords.map(kw => `<span class="ai-keyword">${kw}</span>`).join('')}
                  </div>
                </div>
                
                <div class="ats-recommendations">
                  <h4>Recommendations:</h4>
                  <ul>
                    ${response.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                  </ul>
                </div>
              </div>
            </div>
            <div class="ai-actions">
              <button class="btn btn-outline ai-cancel">Close</button>
            </div>
          `);
          
          // Add CSS for ATS score circle
          const style = document.createElement('style');
          style.textContent = `
            .ats-score-container {
              display: flex;
              justify-content: center;
              margin-bottom: 20px;
            }
            .ats-score-circle {
              position: relative;
              width: 120px;
              height: 120px;
              border-radius: 50%;
              background: conic-gradient(
                var(--primary) calc(var(--score) * 1%),
                #e2e8f0 0
              );
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
            }
            .ats-score-circle::before {
              content: '';
              position: absolute;
              width: 80px;
              height: 80px;
              border-radius: 50%;
              background: white;
            }
            .ats-score-value {
              position: relative;
              font-size: 24px;
              font-weight: bold;
              color: var(--primary);
            }
            .ats-score-label {
              position: relative;
              font-size: 12px;
              color: var(--text-light);
            }
            .ats-details {
              margin-top: 20px;
            }
            .keywords-container {
              margin: 10px 0 15px;
            }
          `;
          document.head.appendChild(style);
          
          document.querySelector('.ai-cancel').addEventListener('click', closeAIModal);
        } else {
          showAIError('Could not scan resume for ATS compatibility. ' + (response.error || ''));
        }
      })
      .catch(error => {
        console.error('Error scanning resume:', error);
        showAIError('Could not scan resume for ATS compatibility. Please try again.');
      });
    }