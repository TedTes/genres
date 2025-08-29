/**
 * Frontend optimization API integration
 * Handles form submission, loading states, and API communication
 */

// Global state management
window.optimizationState = {
    currentStep: 1,
    resumeData: null,
    jobData: null,
    isProcessing: false,
    results: null
};

document.addEventListener('DOMContentLoaded', function() {
    initializeOptimization();
});

function initializeOptimization() {
    setupFormSubmission();
    setupCSRFToken();
    enhanceExistingFunctionality();
}

/**
 * Setup CSRF token for secure form submissions
 */
function setupCSRFToken() {
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
        window.csrfToken = csrfToken.getAttribute('content');
    }
}



/**
 * Show job description section and add optimization button
 */
function showJobDescriptionSection() {
    // Expand job section if not already visible
    const jobContent = document.getElementById('job-content');
    const expandIcon = document.getElementById('expand-icon');
    
    if (jobContent.style.display === 'none') {
        jobContent.style.display = 'block';
        expandIcon.innerHTML = '<i class="fas fa-minus"></i>';
    }
    
    // Add optimization button if not already present
    addOptimizationButton();
    
    // Update continue button to show completion of step 1
    const continueBtn = document.getElementById('continue-button');
    continueBtn.innerHTML = '<i class="fas fa-check"></i> Resume Ready';
    continueBtn.disabled = false;
    continueBtn.classList.add('btn-success');
}

/**
 * Add the main optimization submit button
 */
function addOptimizationButton() {
    // Check if button already exists
    if (document.getElementById('optimize-submit-btn')) {
        return;
    }
    
    const jobContent = document.getElementById('job-content');
    const optimizeButton = document.createElement('div');
    optimizeButton.className = 'upload-actions';
    optimizeButton.innerHTML = `
        <button type="button" class="btn btn-primary btn-lg" id="optimize-submit-btn" onclick="startOptimization()">
            <i class="fas fa-magic"></i>
            Optimize My Resume
        </button>
        <p class="help-text" style="margin-top: 1rem; font-size: 0.875rem; color: var(--text-light);">
            <i class="fas fa-clock"></i> Processing typically takes 30-60 seconds
        </p>
    `;
    
    jobContent.appendChild(optimizeButton);
}

/**
 * Enhanced optimization flow with validation and error handling
 */
async function startOptimization() {
    if (window.optimizationState.isProcessing) {
        return; // Prevent double submission
    }
    
    try {
        // Pre-submit validation
        const isValid = await validateBeforeOptimization();
        if (!isValid) {
            return;
        }
        
        // Collect job description data
        collectJobDescriptionData();
        
        // Show loading state
        showLoadingState();
        window.optimizationState.isProcessing = true;
        
        // Prepare API payload
        const payload = await buildAPIPayload();
        
        // Use retry manager for robust submission
        const retryManager = new RetryManager(3, 2000); // 3 retries, 2s base delay
        
        const result = await retryManager.executeWithRetry(async () => {
            return await submitOptimizationRequest(payload);
        }, 'resume optimization');
        
        // Handle successful response
        handleOptimizationSuccess(result);
        
    } catch (error) {
        console.error('Optimization failed:', error);
        handleOptimizationError(error);
    } finally {
        window.optimizationState.isProcessing = false;
        hideLoadingState();
    }
}
/**
 * Collect job description data from form
 */
function collectJobDescriptionData() {
    const jobTitle = document.getElementById('job-title')?.value?.trim() || '';
    const jobDescription = document.getElementById('job-description')?.value?.trim() || '';
    
    window.optimizationState.jobData = {
        title: jobTitle,
        text: jobDescription,
        company: '' // Can be added later if needed
    };
    
    console.log('Job data collected:', {
        hasTitle: !!jobTitle,
        hasDescription: !!jobDescription,
        descriptionLength: jobDescription.length
    });
}

/**
 * Build API payload from collected data
 */
async function buildAPIPayload() {
    const { resumeData, jobData } = window.optimizationState;
    
    const payload = {
        resume_input: {},
        job_description: {
            text: jobData.text || '',
            title: jobData.title || '',
            company: jobData.company || ''
        },
        options: {
            tone: 'professional-concise',
            locale: 'en-US',
            include_pdf: true
        }
    };
    
    // Handle resume input based on type
    if (resumeData.type === 'file') {
        // For file uploads, we'll need to handle file processing
        // For MVP, we can extract text content on frontend or send file directly
        const fileText = await extractTextFromFile(resumeData.file);
        payload.resume_input.text = fileText;
    } else {
        payload.resume_input.text = resumeData.text;
    }
    
    return payload;
}

/**
 * Extract text content from uploaded file
 */
async function extractTextFromFile(file) {
    if (file.type === 'text/plain') {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = e => resolve(e.target.result);
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
      });
    }
    // Non-text: let backend handle it
    return '[FILE_UPLOAD]';
  }

/**
 * Enhanced API submission with better error handling
 */
async function submitOptimizationRequest(payload) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout
    
    try {
        const response = await fetch('/optimizer/optimize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken || ''
            },
            body: JSON.stringify(payload),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ 
                error: 'Request failed', 
                message: `HTTP ${response.status}: ${response.statusText}` 
            }));
            
            const apiError = handleAPIError(response, errorData);
            throw new APIError(apiError.message, response.status, apiError);
        }
        
        const result = await response.json();
        
        // Validate response structure
        if (!result || typeof result !== 'object') {
            throw new Error('Invalid response format from optimization service');
        }
        
        return result;
        
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
            throw new Error('Request timed out after 2 minutes. Please try again with a shorter resume.');
        }
        
        throw error;
    }
}
/**
 * Show loading state during API processing
 */

function showLoadingState() {
    const submitBtn = document.getElementById('optimize-submit-btn');
    
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                Processing Your Resume...
            </div>
        `;
        submitBtn.classList.add('loading');
    }
    
    // Add enhanced loading overlay
    addEnhancedLoadingOverlay();
}
function addEnhancedLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    document.body.appendChild(overlay);
    
    // Show enhanced progress indicator
    showEnhancedProgressIndicator();
}



/**
 * Handle successful optimization response
 */
function handleOptimizationSuccess(result) {
    console.log('Optimization successful:', result);
    
    // Store results for results page
    window.optimizationState.results = result;
    
    // Store in localStorage for results page access
    try {
        localStorage.setItem('optimizationSuccess', JSON.stringify({
            ...result,
            timestamp: Date.now(),
            original_resume: window.optimizationState.resumeData.text || '[Uploaded File]'
        }));
    } catch (e) {
        console.warn('Could not store results in localStorage:', e);
    }
    
    // Show completion and redirect to results
    showOptimizationCompleteAndRedirect(result);
}

/**
 * Show completion and redirect to results page
 */
function showOptimizationCompleteAndRedirect(result) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.innerHTML = `
            <div class="success-content">
                <div class="success-icon">
                    <i class="fas fa-check-circle"></i>
                </div>
                <h3>Resume Optimized Successfully!</h3>
                <div class="result-preview">
                    <p><strong>Match Score:</strong> <span class="score-highlight">${Math.round(result.match_score || 0)}%</span></p>
                    <p><strong>Keywords Added:</strong> ${result.missing_keywords?.length || 0}</p>
                    <p><strong>Processing Time:</strong> ${result.processing_time_ms ? Math.round(result.processing_time_ms / 1000) : 'N/A'} seconds</p>
                </div>
                <div class="success-actions">
                    <button class="btn btn-primary" onclick="redirectToResults()">
                        <i class="fas fa-eye"></i> View Detailed Results
                    </button>
                    <button class="btn btn-outline" onclick="startOver()">
                        <i class="fas fa-redo"></i> Start Over
                    </button>
                </div>
                <p class="auto-redirect">Redirecting to results in <span id="redirect-countdown">5</span> seconds...</p>
            </div>
        `;
        
        // Auto-redirect countdown
        startRedirectCountdown();
    }
}

/**
 * Start countdown and auto-redirect to results
 */
function startRedirectCountdown() {
    let countdown = 5;
    const countdownElement = document.getElementById('redirect-countdown');
    
    const interval = setInterval(() => {
        countdown--;
        if (countdownElement) {
            countdownElement.textContent = countdown;
        }
        
        if (countdown <= 0) {
            clearInterval(interval);
            redirectToResults();
        }
    }, 1000);
    
    // Store interval for manual redirect
    window.redirectInterval = interval;
}

/**
 * Redirect to results page
 */
function redirectToResults() {
    // Clear any redirect interval
    if (window.redirectInterval) {
        clearInterval(window.redirectInterval);
    }
    
    // Generate a simple result ID for URL (timestamp-based)
    const resultId = Date.now().toString(36);
    
    // Redirect to results page
    window.location.href = `/optimizer/results/${resultId}`;
}

/**
 * Enhanced form validation before submission
 */
async function validateBeforeOptimization() {
    // Clear previous messages
    clearMessages();
    
    // Run comprehensive validation
    const validation = validateOptimizationRequest();
    
    if (!validation.isValid) {
        showValidationResults(validation);
        return false;
    }
    
    // Show warnings but allow continuation
    if (validation.warnings.length > 0) {
        showValidationResults({ errors: [], warnings: validation.warnings });
    }
    
    return true;
}

let progressTimers = [];
function simulateProgressUpdates() {
  const steps = [
    { step: 1, delay: 2000,  progress: 15,  text: "Resume parsed successfully" },
    { step: 2, delay: 8000,  progress: 35,  text: "Gap analysis complete" },
    { step: 3, delay: 25000, progress: 70,  text: "AI optimization in progress" },
    { step: 4, delay: 35000, progress: 85,  text: "Generating explanations" },
    { step: 5, delay: 40000, progress: 95,  text: "Applying final checks" },
    { step: 6, delay: 45000, progress: 100, text: "Documents ready" }
  ];
  // clear existing
  progressTimers.forEach(id => clearTimeout(id));
  progressTimers = [];
  steps.forEach(({ step, delay, progress, text }) => {
    const id = setTimeout(() => updateProgressStep(step, progress, text), delay);
    progressTimers.push(id);
  });
}
function hideLoadingState() {
  const submitBtn = document.getElementById('optimize-submit-btn');
  const overlay = document.getElementById('loading-overlay');
  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.classList.remove('loading');
    submitBtn.innerHTML = '<i class="fas fa-magic"></i> Optimize My Resume';
  }
  if (overlay) overlay.remove();
  if (window.processingStepInterval) clearInterval(window.processingStepInterval);
  progressTimers.forEach(id => clearTimeout(id));
  progressTimers = [];
}


/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, status, details = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.details = details;
    }
}


/**
 * Add retry button for failed optimizations
 */
function addRetryButton() {
    const messagesContainer = document.getElementById('upload-messages');
    if (messagesContainer && !document.getElementById('retry-btn')) {
        const retryButton = document.createElement('button');
        retryButton.id = 'retry-btn';
        retryButton.className = 'btn btn-outline btn-sm';
        retryButton.style.marginTop = '1rem';
        retryButton.innerHTML = '<i class="fas fa-redo"></i> Try Again';
        retryButton.onclick = () => {
            retryButton.remove();
            clearMessages();
            startOptimization();
        };
        
        messagesContainer.appendChild(retryButton);
    }
}

/**
 * Enhanced toggle function for job section with state tracking
 */
function toggleJobSection() {
    const jobContent = document.getElementById('job-content');
    const expandIcon = document.getElementById('expand-icon');
    const isVisible = jobContent.style.display !== 'none';
    
    if (isVisible) {
        jobContent.style.display = 'none';
        expandIcon.innerHTML = '<i class="fas fa-plus"></i>';
    } else {
        jobContent.style.display = 'block';
        expandIcon.innerHTML = '<i class="fas fa-minus"></i>';
        
        // Focus on job title field when opened
        setTimeout(() => {
            document.getElementById('job-title')?.focus();
        }, 300);
    }
}

/**
 * Setup job description character counter
 */
function setupJobDescriptionCounter() {
    const jobTextarea = document.getElementById('job-description');
    const charCount = document.getElementById('job-char-count');
    
    if (jobTextarea && charCount) {
        jobTextarea.addEventListener('input', function() {
            const count = this.value.length;
            charCount.textContent = `${count.toLocaleString()} characters`;
            
            // Visual feedback for job description length
            if (count > 500) {
                charCount.style.color = 'var(--success)';
            } else if (count > 100) {
                charCount.style.color = 'var(--warning)';
            } else {
                charCount.style.color = 'var(--text-light)';
            }
        });
    }
}

/**
 * Setup form submission handling
 */
function setupFormSubmission() {
    // Add character counter for job description
    setupJobDescriptionCounter();
    
    // Prevent form submission on Enter key in textareas
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.target.tagName.toLowerCase() === 'textarea') {
            if (e.ctrlKey || e.metaKey) {
                // Ctrl/Cmd + Enter should trigger optimization if ready
                e.preventDefault();
                if (window.optimizationState.currentStep === 2) {
                    startOptimization();
                }
            }
        }
    });
}

/**
 * Temporary functions for handling results (will be replaced by COMMIT 5)
 */
function viewResults() {
    // This will be replaced by proper results page in COMMIT 5
    alert('Results page will be implemented in COMMIT 5. For now, check console for results data.');
    console.log('Optimization Results:', window.optimizationState.results);
    
    // Hide overlay
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.remove();
}

function startOver() {
    // Reset all state
    window.optimizationState = {
        currentStep: 1,
        resumeData: null,
        jobData: null,
        isProcessing: false,
        results: null
    };
    
    // Reset form
    if (window.resetInputs) {
        window.resetInputs();
    }
    
    // Hide job section
    const jobContent = document.getElementById('job-content');
    const expandIcon = document.getElementById('expand-icon');
    if (jobContent) jobContent.style.display = 'none';
    if (expandIcon) expandIcon.innerHTML = '<i class="fas fa-plus"></i>';
    
    // Reset continue button
    const continueBtn = document.getElementById('continue-button');
    if (continueBtn) {
        continueBtn.innerHTML = '<i class="fas fa-arrow-right"></i> Continue to Job Description';
        continueBtn.disabled = true;
        continueBtn.classList.remove('btn-success');
    }
    
    // Remove optimization button
    const optimizeBtn = document.getElementById('optimize-submit-btn');
    if (optimizeBtn && optimizeBtn.parentElement) {
        optimizeBtn.parentElement.remove();
    }
    
    // Hide overlay
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.remove();
    
    // Clear messages
    if (window.clearMessages) {
        window.clearMessages();
    }
}

/**
 * Enhanced message function for API integration
 */
function showMessage(text, type, duration = null) {
    // Use existing showMessage function if available
    if (window.showMessage && typeof window.showMessage === 'function') {
        window.showMessage(text, type);
    } else {
        // Fallback implementation
        console.log(`${type.toUpperCase()}: ${text}`);
        alert(`${type.toUpperCase()}: ${text}`);
    }
    
    // Auto-clear after duration
    if (duration) {
        setTimeout(() => {
            if (window.clearMessages) {
                window.clearMessages();
            }
        }, duration);
    }
}

/**
 * Debug function for development
 */
function debugOptimizationState() {
    console.log('Current Optimization State:', window.optimizationState);
    console.log('Resume Data Valid:', !!window.optimizationState.resumeData);
    console.log('Job Data Valid:', !!window.optimizationState.jobData);
    console.log('Current Step:', window.optimizationState.currentStep);
}

/**
 * Enhanced processing steps with real-time progress
 */
function showEnhancedProgressIndicator() {
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;
    
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="progress-header">
                <h3>AI is optimizing your resume...</h3>
                <div class="estimated-time">
                    <i class="fas fa-clock"></i>
                    <span id="time-remaining">Estimated: 45-60 seconds</span>
                </div>
            </div>
            
            <!-- Progress Bar -->
            <div class="progress-bar-container">
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
                </div>
                <div class="progress-percentage" id="progress-percentage">0%</div>
            </div>
            
            <!-- Step Indicators -->
            <div class="processing-steps-enhanced" id="processing-steps-enhanced">
                <div class="step-item" data-step="1">
                    <div class="step-icon"><i class="fas fa-file-text"></i></div>
                    <div class="step-text">Parsing resume content</div>
                    <div class="step-status pending">⏳</div>
                </div>
                <div class="step-item" data-step="2">
                    <div class="step-icon"><i class="fas fa-search"></i></div>
                    <div class="step-text">Analyzing skill gaps</div>
                    <div class="step-status pending">⏳</div>
                </div>
                <div class="step-item" data-step="3">
                    <div class="step-icon"><i class="fas fa-brain"></i></div>
                    <div class="step-text">AI optimization</div>
                    <div class="step-status pending">⏳</div>
                </div>
                <div class="step-item" data-step="4">
                    <div class="step-icon"><i class="fas fa-clipboard-list"></i></div>
                    <div class="step-text">Generating explanations</div>
                    <div class="step-status pending">⏳</div>
                </div>
                <div class="step-item" data-step="5">
                    <div class="step-icon"><i class="fas fa-shield-alt"></i></div>
                    <div class="step-text">Applying guardrails</div>
                    <div class="step-status pending">⏳</div>
                </div>
                <div class="step-item" data-step="6">
                    <div class="step-icon"><i class="fas fa-file-pdf"></i></div>
                    <div class="step-text">Creating documents</div>
                    <div class="step-status pending">⏳</div>
                </div>
            </div>
        </div>
    `;
    
    // Start progress simulation
    simulateProgressUpdates();
}

/**
 * Simulate progress updates based on typical processing times
 */
function simulateProgressUpdates() {
    const steps = [
        { step: 1, delay: 2000, progress: 15, text: "Resume parsed successfully" },
        { step: 2, delay: 8000, progress: 35, text: "Gap analysis complete" },
        { step: 3, delay: 25000, progress: 70, text: "AI optimization in progress" },
        { step: 4, delay: 35000, progress: 85, text: "Generating explanations" },
        { step: 5, delay: 40000, progress: 95, text: "Applying final checks" },
        { step: 6, delay: 45000, progress: 100, text: "Documents ready" }
    ];
    
    steps.forEach(({ step, delay, progress, text }) => {
        setTimeout(() => {
            updateProgressStep(step, progress, text);
        }, delay);
    });
}

/**
 * Update individual progress step
 */
function updateProgressStep(stepNumber, progressPercent, statusText) {
    const stepItem = document.querySelector(`[data-step="${stepNumber}"]`);
    const progressFill = document.getElementById('progress-fill');
    const progressPercentage = document.getElementById('progress-percentage');
    const timeRemaining = document.getElementById('time-remaining');
    
    if (stepItem) {
        const statusElement = stepItem.querySelector('.step-status');
        statusElement.textContent = '✅';
        statusElement.className = 'step-status complete';
        stepItem.classList.add('completed');
    }
    
    if (progressFill) {
        progressFill.style.width = `${progressPercent}%`;
    }
    
    if (progressPercentage) {
        progressPercentage.textContent = `${progressPercent}%`;
    }
    
    if (timeRemaining && progressPercent < 100) {
        const remainingSeconds = Math.max(5, Math.floor((100 - progressPercent) / 2));
        timeRemaining.innerHTML = `<i class="fas fa-clock"></i> ${remainingSeconds} seconds remaining`;
    } else if (timeRemaining && progressPercent === 100) {
        timeRemaining.innerHTML = `<i class="fas fa-check"></i> Complete!`;
    }
}






// File validation constants
const FILE_VALIDATION = {
    MAX_SIZE: 5 * 1024 * 1024, // 5MB
    MIN_TEXT_LENGTH: 100,
    MAX_TEXT_LENGTH: 50000,
    ALLOWED_TYPES: {
        'application/pdf': 'PDF',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word Document',
        'text/plain': 'Text File'
    },
    MALICIOUS_PATTERNS: [
        /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
        /javascript:/gi,
        /on\w+\s*=/gi,
        /data:text\/html/gi
    ]
};

/**
 * Enhanced file validation with detailed error messages
 */
function validateFileUpload(file) {
    const errors = [];
    const warnings = [];
    
    // Check file size
    if (file.size === 0) {
        errors.push('File appears to be empty. Please select a valid resume file.');
        return { isValid: false, errors, warnings };
    }
    
    if (file.size > FILE_VALIDATION.MAX_SIZE) {
        errors.push(`File size (${formatFileSize(file.size)}) exceeds the 5MB limit. Please compress your file or use a smaller version.`);
    }
    
    // Check file type
    if (!FILE_VALIDATION.ALLOWED_TYPES[file.type]) {
        errors.push(`File type "${file.type}" is not supported. Please upload PDF, DOCX, or TXT files only.`);
        return { isValid: false, errors, warnings };
    }
    
    // Check filename for suspicious content
    if (containsSuspiciousPatterns(file.name)) {
        errors.push('Filename contains invalid characters. Please rename your file and try again.');
    }
    
    // Size warnings
    if (file.size < 1024) {
        warnings.push('File seems very small. Make sure it contains your complete resume.');
    }
    
    if (file.size > 2 * 1024 * 1024) {
        warnings.push('Large file detected. Processing may take longer than usual.');
    }
    
    return {
        isValid: errors.length === 0,
        errors,
        warnings,
        fileInfo: {
            name: file.name,
            size: file.size,
            type: file.type,
            typeDisplay: FILE_VALIDATION.ALLOWED_TYPES[file.type]
        }
    };
}

/**
 * Enhanced text validation
 */
function validateTextInput(text) {
    const errors = [];
    const warnings = [];
    const cleanText = text.trim();
    
    // Length validation
    if (cleanText.length < FILE_VALIDATION.MIN_TEXT_LENGTH) {
        errors.push(`Resume text is too short (${cleanText.length} characters). Please provide at least ${FILE_VALIDATION.MIN_TEXT_LENGTH} characters.`);
        return { isValid: false, errors, warnings };
    }
    
    if (cleanText.length > FILE_VALIDATION.MAX_TEXT_LENGTH) {
        errors.push(`Resume text is too long (${cleanText.length} characters). Please limit to ${FILE_VALIDATION.MAX_TEXT_LENGTH} characters.`);
    }
    
    // Content validation
    if (!containsResumeKeywords(cleanText)) {
        warnings.push('Text doesn\'t appear to contain typical resume content. Please ensure you\'ve pasted your complete resume.');
    }
    
    // Security validation
    if (containsMaliciousContent(cleanText)) {
        errors.push('Text contains potentially harmful content. Please remove any scripts or suspicious code.');
    }
    
    // Quality checks
    const wordCount = cleanText.split(/\s+/).length;
    if (wordCount < 50) {
        warnings.push('Resume seems very brief. Consider adding more details about your experience and skills.');
    }
    
    if (!containsContactInfo(cleanText)) {
        warnings.push('No contact information detected. Make sure to include your name and email address.');
    }
    
    return {
        isValid: errors.length === 0,
        errors,
        warnings,
        textInfo: {
            length: cleanText.length,
            wordCount: wordCount,
            hasContactInfo: containsContactInfo(cleanText),
            hasExperience: containsExperienceSection(cleanText)
        }
    };
}

/**
 * Job description validation
 */
function validateJobDescription(text, title = '') {
    const errors = [];
    const warnings = [];
    const cleanText = text.trim();
    
    // Length validation (more lenient for JD)
    if (cleanText.length > 0 && cleanText.length < 50) {
        warnings.push('Job description seems very brief. More detailed descriptions produce better optimization results.');
    }
    
    if (cleanText.length > 20000) {
        warnings.push('Very long job description. We\'ll focus on the most relevant parts for optimization.');
    }
    
    // Content quality checks
    if (cleanText.length > 0) {
        if (!containsJobKeywords(cleanText)) {
            warnings.push('Text doesn\'t appear to be a typical job description. Please paste the complete job posting.');
        }
        
        if (containsMaliciousContent(cleanText)) {
            errors.push('Job description contains potentially harmful content.');
        }
    }
    
    return {
        isValid: errors.length === 0,
        errors,
        warnings,
        jdInfo: {
            length: cleanText.length,
            wordCount: cleanText.split(/\s+/).length,
            hasTitle: title.trim().length > 0,
            hasRequirements: /requirements?|qualifications?|skills?/i.test(cleanText)
        }
    };
}

/**
 * Helper functions for content validation
 */
function containsResumeKeywords(text) {
    const resumePatterns = [
        /experience|employment|work history/i,
        /skills|proficient|expertise/i,
        /education|degree|university|college/i,
        /@[\w.-]+\.\w+/, // Email pattern
        /\(\d{3}\)|\d{3}[-.\s]\d{3}[-.\s]\d{4}/ // Phone pattern
    ];
    
    return resumePatterns.some(pattern => pattern.test(text));
}

function containsJobKeywords(text) {
    const jobPatterns = [
        /responsibilities|duties|requirements/i,
        /qualifications|experience|skills/i,
        /seeking|looking for|hiring/i,
        /position|role|opportunity/i
    ];
    
    return jobPatterns.some(pattern => pattern.test(text));
}

function containsContactInfo(text) {
    const emailPattern = /@[\w.-]+\.\w+/;
    const phonePattern = /\(\d{3}\)|\d{3}[-.\s]\d{3}[-.\s]\d{4}/;
    
    return emailPattern.test(text) || phonePattern.test(text);
}

function containsExperienceSection(text) {
    const experiencePatterns = [
        /experience|employment|work\s+history/i,
        /\d{4}\s*[-–]\s*\d{4}/, // Date ranges
        /\d{4}\s*[-–]\s*(present|current)/i
    ];
    
    return experiencePatterns.some(pattern => pattern.test(text));
}

function containsSuspiciousPatterns(text) {
    return FILE_VALIDATION.MALICIOUS_PATTERNS.some(pattern => pattern.test(text));
}

function containsMaliciousContent(text) {
    return containsSuspiciousPatterns(text);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/**
 * Enhanced error display with categorization
 */
function showValidationResults(validation, containerId = 'upload-messages') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    let html = '';
    
    // Show errors (blocking)
    if (validation.errors && validation.errors.length > 0) {
        validation.errors.forEach(error => {
            html += `
                <div class="message error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <div class="message-content">
                        <strong>Error:</strong> ${error}
                    </div>
                </div>
            `;
        });
    }
    
    // Show warnings (non-blocking)
    if (validation.warnings && validation.warnings.length > 0) {
        validation.warnings.forEach(warning => {
            html += `
                <div class="message warning">
                    <i class="fas fa-info-circle"></i>
                    <div class="message-content">
                        <strong>Note:</strong> ${warning}
                    </div>
                </div>
            `;
        });
    }
    
    container.innerHTML = html;
    
    // Auto-clear warnings after 8 seconds
    if (validation.warnings && validation.warnings.length > 0 && validation.errors.length === 0) {
        setTimeout(() => {
            const warningMessages = container.querySelectorAll('.message.warning');
            warningMessages.forEach(msg => {
                msg.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => msg.remove(), 300);
            });
        }, 8000);
    }
}

/**
 * Pre-submit validation for entire optimization request
 */
function validateOptimizationRequest() {
    const errors = [];
    const warnings = [];
    
    // Validate resume data
    if (!window.optimizationState.resumeData) {
        errors.push('No resume data found. Please upload a resume or paste resume text.');
        return { isValid: false, errors, warnings };
    }
    
    const { resumeData, jobData } = window.optimizationState;
    
    // Validate resume content
    if (resumeData.type === 'text') {
        const textValidation = validateTextInput(resumeData.text || '');
        errors.push(...textValidation.errors);
        warnings.push(...textValidation.warnings);
    }
    
    // Validate job description (if provided)
    if (jobData && jobData.text) {
        const jdValidation = validateJobDescription(jobData.text, jobData.title);
        errors.push(...jdValidation.errors);
        warnings.push(...jdValidation.warnings);
    } else {
        warnings.push('No job description provided. Adding one significantly improves optimization quality.');
    }
    
    // Check for potential issues
    if (resumeData.type === 'file' && resumeData.file) {
        const fileValidation = validateFileUpload(resumeData.file);
        errors.push(...fileValidation.errors);
        warnings.push(...fileValidation.warnings);
    }
    
    return {
        isValid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * API error response handler
 */
function handleAPIError(response, responseData) {
    const context = {
        status: response.status,
        statusText: response.statusText,
        url: response.url
    };
    
    console.error('API Error:', context, responseData);
    
    let errorMessage = 'Optimization failed. Please try again.';
    let canRetry = true;
    let suggestedAction = null;
    
    switch (response.status) {
        case 400:
            errorMessage = responseData.error || 'Invalid request. Please check your input and try again.';
            canRetry = true;
            suggestedAction = 'verify_input';
            break;
            
        case 401:
            errorMessage = 'Session expired. Please refresh the page and log in again.';
            canRetry = false;
            suggestedAction = 'refresh_page';
            break;
            
        case 413:
            errorMessage = 'File too large. Please use a smaller resume file (under 5MB).';
            canRetry = true;
            suggestedAction = 'reduce_file_size';
            break;
            
        case 429:
            errorMessage = 'Too many requests. Please wait a moment before trying again.';
            canRetry = true;
            suggestedAction = 'wait_and_retry';
            break;
            
        case 500:
            errorMessage = 'Internal server error. Our team has been notified.';
            canRetry = true;
            suggestedAction = 'contact_support';
            break;
            
        case 503:
            errorMessage = 'Service temporarily unavailable. Please try again in a few minutes.';
            canRetry = true;
            suggestedAction = 'wait_and_retry';
            break;
            
        default:
            errorMessage = responseData.error || `Unexpected error (${response.status}). Please try again.`;
            canRetry = true;
    }
    
    return {
        message: errorMessage,
        canRetry,
        suggestedAction,
        details: responseData.details || null
    };
}

/**
 * Enhanced error message display with actions
 */
function showEnhancedError(errorInfo, containerId = 'upload-messages') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const actionsHtml = errorInfo.canRetry ? `
        <div class="error-actions">
            ${getErrorActionButton(errorInfo.suggestedAction)}
            <button class="btn btn-outline btn-sm" onclick="clearMessages()">
                <i class="fas fa-times"></i> Dismiss
            </button>
        </div>
    ` : '';
    
    container.innerHTML = `
        <div class="message error enhanced">
            <div class="message-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="message-content">
                <div class="error-message">${errorInfo.message}</div>
                ${errorInfo.details ? `<div class="error-details">${errorInfo.details}</div>` : ''}
                ${actionsHtml}
            </div>
        </div>
    `;
}

/**
 * Get appropriate action button for error type
 */
function getErrorActionButton(actionType) {
    switch (actionType) {
        case 'verify_input':
            return `
                <button class="btn btn-primary btn-sm" onclick="showInputValidationHelp()">
                    <i class="fas fa-question-circle"></i> Check Input Format
                </button>
            `;
        case 'refresh_page':
            return `
                <button class="btn btn-primary btn-sm" onclick="window.location.reload()">
                    <i class="fas fa-sync"></i> Refresh Page
                </button>
            `;
        case 'reduce_file_size':
            return `
                <button class="btn btn-primary btn-sm" onclick="showFileSizeHelp()">
                    <i class="fas fa-compress"></i> File Size Help
                </button>
            `;
        case 'wait_and_retry':
            return `
                <button class="btn btn-primary btn-sm" onclick="scheduleRetry()">
                    <i class="fas fa-clock"></i> Retry in 30s
                </button>
            `;
        case 'contact_support':
            return `
                <button class="btn btn-primary btn-sm" onclick="showSupportOptions()">
                    <i class="fas fa-life-ring"></i> Get Help
                </button>
            `;
        default:
            return `
                <button class="btn btn-primary btn-sm" onclick="startOptimization()">
                    <i class="fas fa-redo"></i> Try Again
                </button>
            `;
    }
}

/**
 * Help functions for specific error types
 */
function showInputValidationHelp() {
    alert(`Resume Format Help:

Your resume should include:
✓ Your name and contact information
✓ Work experience with dates
✓ Skills and qualifications
✓ Education background

Example format:
John Smith
Email: john@email.com | Phone: (555) 123-4567

EXPERIENCE
Software Developer | TechCorp | 2020-2023
• Built web applications...

SKILLS
Python, JavaScript, SQL...`);
}

function showFileSizeHelp() {
    alert(`File Size Help:

To reduce file size:
• Save as PDF instead of Word document
• Remove unnecessary images or graphics
• Use "Save as Web Quality" option in Word
• Compress images before inserting
• Keep resume to 1-2 pages maximum

If you need help, try converting to plain text first.`);
}

function scheduleRetry() {
    let countdown = 30;
    const container = document.getElementById('upload-messages');
    
    const interval = setInterval(() => {
        countdown--;
        container.querySelector('.btn').innerHTML = `
            <i class="fas fa-clock"></i> Retry in ${countdown}s
        `;
        
        if (countdown <= 0) {
            clearInterval(interval);
            startOptimization();
        }
    }, 1000);
}

function showSupportOptions() {
    alert(`Get Help:

If you continue experiencing issues:

1. Try using plain text instead of file upload
2. Ensure your resume is in a standard format
3. Check that your internet connection is stable
4. Contact our support team with error details

For technical support, include:
• Error message details
• File type and size
• Browser and operating system`);
}

/**
 * Enhanced retry mechanism with exponential backoff
 */
class RetryManager {
    constructor(maxRetries = 3, baseDelay = 1000) {
        this.maxRetries = maxRetries;
        this.baseDelay = baseDelay;
        this.currentRetry = 0;
    }
    
    async executeWithRetry(asyncFunction, context = 'operation') {
        this.currentRetry = 0;
        
        while (this.currentRetry <= this.maxRetries) {
            try {
                return await asyncFunction();
            } catch (error) {
                this.currentRetry++;
                
                if (this.currentRetry > this.maxRetries) {
                    throw new Error(`${context} failed after ${this.maxRetries} retries: ${error.message}`);
                }
                
                const delay = this.baseDelay * Math.pow(2, this.currentRetry - 1);
                console.log(`Retry ${this.currentRetry}/${this.maxRetries} in ${delay}ms...`);
                
                await this.delay(delay);
            }
        }
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    reset() {
        this.currentRetry = 0;
    }
}


/**
 * Connection and service status monitoring
 */
class ServiceMonitor {
    constructor() {
        this.isOnline = navigator.onLine;
        this.lastCheckTime = Date.now();
        this.checkInterval = null;
        this.statusElement = null;
        
        this.init();
    }
    
    init() {
        this.createStatusIndicator();
        this.setupEventListeners();
        this.startPeriodicChecks();
        this.checkServiceStatus();
    }
    
    createStatusIndicator() {
        this.statusElement = document.createElement('div');
        this.statusElement.className = 'connection-status checking';
        this.statusElement.innerHTML = `
            <div class="status-dot"></div>
            <span>Checking...</span>
        `;
        document.body.appendChild(this.statusElement);
    }
    
    setupEventListeners() {
        window.addEventListener('online', () => this.updateConnectionStatus(true));
        window.addEventListener('offline', () => this.updateConnectionStatus(false));
    }
    
    startPeriodicChecks() {
        // Check service every 30 seconds
        this.checkInterval = setInterval(() => {
            this.checkServiceStatus();
        }, 30000);
    }
    
    async checkServiceStatus() {
        try {
            const response = await fetch('/optimizer/status', {
                method: 'GET',
                headers: { 'Cache-Control': 'no-cache' }
            });
            
            const status = await response.json();
            this.updateServiceStatus(status);
            
        } catch (error) {
            console.warn('Service status check failed:', error);
            this.updateServiceStatus({ status: 'error' });
        }
    }
    
    updateConnectionStatus(isOnline) {
        this.isOnline = isOnline;
        
        if (this.statusElement) {
            this.statusElement.className = `connection-status ${isOnline ? 'online' : 'offline'}`;
            this.statusElement.innerHTML = `
                <div class="status-dot"></div>
                <span>${isOnline ? 'Connected' : 'Offline'}</span>
            `;
        }
    }
    
    updateServiceStatus(status) {
        if (!this.statusElement) return;
        
        const isAvailable = status.status === 'available';
        const className = isAvailable ? 'online' : (status.status === 'degraded' ? 'checking' : 'offline');
        const text = isAvailable ? 'Service Ready' : (status.status === 'degraded' ? 'Service Slow' : 'Service Down');
        
        this.statusElement.className = `connection-status ${className}`;
        this.statusElement.innerHTML = `
            <div class="status-dot"></div>
            <span>${text}</span>
        `;
        
        // Auto-hide when service is working
        if (isAvailable) {
            setTimeout(() => {
                if (this.statusElement) {
                    this.statusElement.style.opacity = '0.7';
                }
            }, 3000);
        }
    }
    
    destroy() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
        }
        if (this.statusElement) {
            this.statusElement.remove();
        }
    }
}

// Initialize service monitor when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.serviceMonitor = new ServiceMonitor();
});

/**
 optimization error handler with retry logic
 */
function handleOptimizationError(error) {
    // APIError or generic Error
    const isApi = error instanceof APIError;
    const message = isApi ? error.message : (error?.message || 'Optimization failed. Please try again.');
    const suggestedAction = isApi ? error.details?.suggestedAction : null;
    const canRetry = isApi ? error.details?.canRetry ?? true : true;
  
    showEnhancedError({
      message,
      canRetry,
      suggestedAction,
      details: isApi ? (error.details?.details ?? null) : null
    });
  }
