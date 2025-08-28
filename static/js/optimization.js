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
 * Enhance existing upload functionality with API integration
 */
function enhanceExistingFunctionality() {
    // Override the existing proceedToNextStep function to include API logic
    window.originalProceedToNextStep = window.proceedToNextStep;
    
    window.proceedToNextStep = function() {
        collectResumeData();
        showJobDescriptionSection();
        window.optimizationState.currentStep = 2;
    };
}

/**
 * Collect and store resume data from current form state
 */
function collectResumeData() {
    const activeType = document.querySelector('.upload-type-btn.active').dataset.type;
    
    if (activeType === 'file' && window.currentFile) {
        window.optimizationState.resumeData = {
            type: 'file',
            file: window.currentFile,
            text: null
        };
    } else if (activeType === 'text' && window.currentText) {
        window.optimizationState.resumeData = {
            type: 'text',
            file: null,
            text: window.currentText.trim()
        };
    }
    
    console.log('Resume data collected:', {
        type: window.optimizationState.resumeData.type,
        hasData: window.optimizationState.resumeData.file || window.optimizationState.resumeData.text
    });
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
 * Main optimization function - submits data to API
 */
async function startOptimization() {
    if (window.optimizationState.isProcessing) {
        return; // Prevent double submission
    }
    
    try {
        // Collect job description data
        collectJobDescriptionData();
        
        // Validate we have minimum required data
        if (!validateOptimizationData()) {
            return;
        }
        
        // Show loading state
        showLoadingState();
        window.optimizationState.isProcessing = true;
        
        // Prepare API payload
        const payload = await buildAPIPayload();
        
        // Submit to optimization API
        const result = await submitOptimizationRequest(payload);
        
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
 * Validate that we have minimum data required for optimization
 */
function validateOptimizationData() {
    const { resumeData, jobData } = window.optimizationState;
    
    // Must have resume data
    if (!resumeData || (!resumeData.file && !resumeData.text)) {
        showMessage('Please upload or paste your resume first', 'error');
        return false;
    }
    
    // Job description is optional but recommended
    if (!jobData || !jobData.text) {
        const proceed = confirm('No job description provided. We recommend adding one for better optimization. Continue anyway?');
        if (!proceed) {
            return false;
        }
        // Set default empty job data
        window.optimizationState.jobData = { title: '', text: '', company: '' };
    }
    
    return true;
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
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            if (file.type === 'text/plain') {
                resolve(e.target.result);
            } else {
                // For PDF/DOCX files, send the text as is for now
                // Backend will handle file processing
                resolve('[FILE_CONTENT]'); // Backend will process the actual file
            }
        };
        
        reader.onerror = function() {
            reject(new Error('Failed to read file'));
        };
        
        if (file.type === 'text/plain') {
            reader.readAsText(file);
        } else {
            // For non-text files, let backend handle processing
            resolve('[FILE_UPLOAD]');
        }
    });
}

/**
 * Submit optimization request to backend API
 */
async function submitOptimizationRequest(payload) {
    const response = await fetch('/optimizer/optimize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.csrfToken || ''
        },
        body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Request failed' }));
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
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
 * Add loading overlay to prevent form interaction
 */
function addLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="loading-spinner large"></div>
            <h3>AI is optimizing your resume...</h3>
            <p>This usually takes 30-60 seconds</p>
            <div class="processing-steps" id="processing-steps"></div>
        </div>
    `;
    
    document.body.appendChild(overlay);
}

/**
 * Show processing steps during optimization
 */
function showProcessingSteps() {
    const steps = [
        'Parsing resume content...',
        'Analyzing skill gaps...',
        'Optimizing with AI...',
        'Generating explanations...',
        'Applying guardrails...',
        'Creating documents...'
    ];
    
    const stepsContainer = document.getElementById('processing-steps');
    if (!stepsContainer) return;
    
    let currentStepIndex = 0;
    
    const stepInterval = setInterval(() => {
        if (currentStepIndex < steps.length) {
            const stepElement = document.createElement('div');
            stepElement.className = 'processing-step';
            stepElement.innerHTML = `
                <i class="fas fa-check-circle"></i>
                ${steps[currentStepIndex]}
            `;
            stepsContainer.appendChild(stepElement);
            currentStepIndex++;
        } else {
            clearInterval(stepInterval);
        }
    }, 8000); // Show new step every 8 seconds
    
    // Store interval for cleanup
    window.processingStepInterval = stepInterval;
}

/**
 * Hide loading state and reset UI
 */
function hideLoadingState() {
    const submitBtn = document.getElementById('optimize-submit-btn');
    const overlay = document.getElementById('loading-overlay');
    
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('loading');
        submitBtn.innerHTML = '<i class="fas fa-magic"></i> Optimize My Resume';
    }
    
    if (overlay) {
        overlay.remove();
    }
    
    // Clear processing step interval
    if (window.processingStepInterval) {
        clearInterval(window.processingStepInterval);
    }
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
        localStorage.setItem('optimizationResults', JSON.stringify({
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
 * Handle optimization API errors
 */
function handleOptimizationError(error) {
    console.error('Optimization error:', error);
    
    let errorMessage = 'Optimization failed. Please try again.';
    
    // Parse specific error messages
    if (error.message) {
        if (error.message.includes('Rate limit')) {
            errorMessage = 'You\'ve reached the optimization limit. Please try again later.';
        } else if (error.message.includes('Invalid input')) {
            errorMessage = 'Invalid resume or job description format. Please check your input.';
        } else if (error.message.includes('authentication') || error.message.includes('login')) {
            errorMessage = 'Session expired. Please refresh the page and try again.';
        } else {
            errorMessage = error.message;
        }
    }
    
    // Show error message
    showMessage(errorMessage, 'error');
    
    // Add retry button
    addRetryButton();
}

/**
 * Show optimization completion (temporary - will be replaced by COMMIT 5)
 */
function showOptimizationComplete(result) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.innerHTML = `
            <div class="success-content">
                <div class="success-icon">
                    <i class="fas fa-check-circle"></i>
                </div>
                <h3>Resume Optimized Successfully!</h3>
                <div class="result-preview">
                    <p><strong>Match Score:</strong> ${result.match_score || 'N/A'}%</p>
                    <p><strong>Processing Time:</strong> ${result.processing_time_ms ? Math.round(result.processing_time_ms / 1000) : 'N/A'} seconds</p>
                    <p><strong>Keywords Added:</strong> ${result.missing_keywords?.length || 0}</p>
                </div>
                <div class="success-actions">
                    <button class="btn btn-primary" onclick="viewResults()">
                        <i class="fas fa-eye"></i> View Results
                    </button>
                    <button class="btn btn-outline" onclick="startOver()">
                        <i class="fas fa-redo"></i> Start Over
                    </button>
                </div>
            </div>
        `;
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            if (overlay) overlay.remove();
        }, 10000);
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


function storeResultsForDownload(result) {
    try {
        // Store in localStorage with expiration
        const resultData = {
            ...result,
            timestamp: Date.now(),
            expires_at: Date.now() + (24 * 60 * 60 * 1000), // 24 hours
            original_resume: window.optimizationState.resumeData?.text || '[Uploaded File]'
        };
        
        localStorage.setItem('optimizationResults', JSON.stringify(resultData));
        
        // Also store with result_id for direct access
        const resultId = result.request_hash || Date.now().toString(36);
        localStorage.setItem(`result_${resultId}`, JSON.stringify(resultData));
        
        console.log(`Results stored with ID: ${resultId}`);
        return resultId;
        
    } catch (e) {
        console.warn('Could not store results:', e);
        return null;
    }
}