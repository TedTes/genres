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
    results: null,
    validationStatus: { resume: false, job: false },
    extractedContent: null,
    contentMetrics: { wordCount: 0, sectionCount: 0, hasContact: false }
};

document.addEventListener('DOMContentLoaded', function() {
    initializeOptimization();
});

function initializeOptimization() {
    setupCSRFToken();
    console.log('Optimization.js initialized for dashboard.html');
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
 * Enhanced optimization flow with validation and error handling
 * Now works with dashboard.html elements
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
        
        // Collect data from dashboard elements
        collectDashboardData();
        
        // Show loading state
        showLoadingState();
        window.optimizationState.isProcessing = true;
        
        // Prepare API payload
        const formData = await buildFormDataPayload();
        
        // Submit optimization request
        const result = await submitOptimizationRequest(formData);
        
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
 * Collect data from dashboard.html form elements
 */
function collectDashboardData() {
    // Get elements using dashboard.html IDs
    const jobTitle = document.getElementById('jobTitle')?.value?.trim() || '';
    const jobText = document.getElementById('jobText')?.value?.trim() || '';
    const jobLink = document.getElementById('jobLink')?.value?.trim() || '';
    
    window.optimizationState.jobData = {
        title: jobTitle,
        text: jobText,
        description: jobText, // alias for compatibility
        company: '',
        url: jobLink
    };
    
    console.log('Dashboard data collected:', {
        hasTitle: !!jobTitle,
        hasDescription: !!jobText,
        hasLink: !!jobLink,
        descriptionLength: jobText.length
    });
}

/**
 * Build API payload from collected data
 */
function buildFormDataPayload() {
    const { resumeData, jobData } = window.optimizationState;
    const formData = new FormData();
    
    // Add job description fields
    formData.append('job_title', jobData.title || '');
    formData.append('job_description', jobData.text || '');
    formData.append('job_company', jobData.company || '');
    formData.append('job_url', jobData.url || '');
    
    // Add options
    formData.append('tone', 'professional-concise');
    formData.append('locale', 'en-US');
    formData.append('include_pdf', 'true');
    
    // Handle resume input
    if (resumeData && resumeData.type === 'file') {
        formData.append('resume_file', resumeData.file); // Actual File object
        formData.append('resume_type', 'file');
    } else if (resumeData && resumeData.type === 'text') {
        formData.append('resume_text', resumeData.content);
        formData.append('resume_type', 'text');
    }
    
    return formData;
}

/**
 * Enhanced API submission with better error handling
 */
async function submitOptimizationRequest(formData) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout
    
    try {
        const response = await fetch('/api/v1/optimizer/optimize', {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.csrfToken || ''
            },
            body: formData,
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
 * Updated to work with dashboard.html elements
 */
function showLoadingState() {
    const submitBtn = document.getElementById('optimizeBtn');
    
    if (submitBtn) {
        submitBtn.disabled = true;
        const btnContent = submitBtn.querySelector('.btn-content');
        const btnLoader = submitBtn.querySelector('.btn-loader');
        
        if (btnContent) btnContent.style.display = 'none';
        if (btnLoader) btnLoader.style.display = 'flex';
        
        submitBtn.classList.add('is-loading');
    }
    
    // Show progress section if it exists
    const progressSection = document.getElementById('progressSection');
    if (progressSection) {
        progressSection.style.display = 'block';
    }
    
    // Add enhanced loading overlay
    addEnhancedLoadingOverlay();
}

/**
 * Hide loading state
 */
function hideLoadingState() {
    const submitBtn = document.getElementById('optimizeBtn');
    const overlay = document.getElementById('loading-overlay');
    
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('is-loading');
        const btnContent = submitBtn.querySelector('.btn-content');
        const btnLoader = submitBtn.querySelector('.btn-loader');
        
        if (btnContent) btnContent.style.display = 'flex';
        if (btnLoader) btnLoader.style.display = 'none';
    }
    
    if (overlay) overlay.remove();
    
    // Clear progress timers
    if (window.progressTimers) {
        window.progressTimers.forEach(id => clearTimeout(id));
        window.progressTimers = [];
    }
}

function addEnhancedLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.95);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        backdrop-filter: blur(2px);
    `;
    document.body.appendChild(overlay);
    
    // Show enhanced progress indicator
    showEnhancedProgressIndicator();
}

/**
 * Enhanced processing steps with real-time progress
 */
function showEnhancedProgressIndicator() {
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;
    
    overlay.innerHTML = `
        <div class="loading-content" style="
            text-align: center;
            padding: 3rem;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            max-width: 500px;
            width: 90%;
        ">
            <div class="progress-header" style="margin-bottom: 2rem;">
                <h3 style="margin: 0 0 0.5rem 0; color: #1f2937;">AI is optimizing your resume...</h3>
                <div class="estimated-time" style="color: #6b7280; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    <i class="fas fa-clock"></i>
                    <span id="time-remaining">Estimated: 45-60 seconds</span>
                </div>
            </div>
            
            <!-- Progress Bar -->
            <div class="progress-bar-container" style="margin-bottom: 2rem;">
                <div class="progress-bar" style="
                    width: 100%;
                    height: 8px;
                    background: #e5e7eb;
                    border-radius: 4px;
                    overflow: hidden;
                    margin-bottom: 0.5rem;
                ">
                    <div class="progress-fill" id="progress-fill" style="
                        width: 0%;
                        height: 100%;
                        background: linear-gradient(90deg, #3b82f6, #1d4ed8);
                        border-radius: 4px;
                        transition: width 0.5s ease;
                    "></div>
                </div>
                <div class="progress-percentage" id="progress-percentage" style="
                    font-size: 0.875rem;
                    color: #6b7280;
                    text-align: right;
                ">0%</div>
            </div>
            
            <!-- Step Indicators -->
            <div class="processing-steps-enhanced" id="processing-steps-enhanced" style="
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
            ">
                <div class="step-item" data-step="1" style="
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    padding: 0.5rem;
                    border-radius: 8px;
                    transition: all 0.3s ease;
                ">
                    <div class="step-icon" style="color: #3b82f6;"><i class="fas fa-file-text"></i></div>
                    <div class="step-text" style="flex: 1; text-align: left; color: #374151;">Parsing resume content</div>
                    <div class="step-status pending" style="color: #6b7280;">⏳</div>
                </div>
                <div class="step-item" data-step="2" style="
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    padding: 0.5rem;
                    border-radius: 8px;
                    transition: all 0.3s ease;
                ">
                    <div class="step-icon" style="color: #3b82f6;"><i class="fas fa-search"></i></div>
                    <div class="step-text" style="flex: 1; text-align: left; color: #374151;">Analyzing skill gaps</div>
                    <div class="step-status pending" style="color: #6b7280;">⏳</div>
                </div>
                <div class="step-item" data-step="3" style="
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    padding: 0.5rem;
                    border-radius: 8px;
                    transition: all 0.3s ease;
                ">
                    <div class="step-icon" style="color: #3b82f6;"><i class="fas fa-brain"></i></div>
                    <div class="step-text" style="flex: 1; text-align: left; color: #374151;">AI optimization</div>
                    <div class="step-status pending" style="color: #6b7280;">⏳</div>
                </div>
                <div class="step-item" data-step="4" style="
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    padding: 0.5rem;
                    border-radius: 8px;
                    transition: all 0.3s ease;
                ">
                    <div class="step-icon" style="color: #3b82f6;"><i class="fas fa-clipboard-list"></i></div>
                    <div class="step-text" style="flex: 1; text-align: left; color: #374151;">Generating explanations</div>
                    <div class="step-status pending" style="color: #6b7280;">⏳</div>
                </div>
                <div class="step-item" data-step="5" style="
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    padding: 0.5rem;
                    border-radius: 8px;
                    transition: all 0.3s ease;
                ">
                    <div class="step-icon" style="color: #3b82f6;"><i class="fas fa-shield-alt"></i></div>
                    <div class="step-text" style="flex: 1; text-align: left; color: #374151;">Applying guardrails</div>
                    <div class="step-status pending" style="color: #6b7280;">⏳</div>
                </div>
                <div class="step-item" data-step="6" style="
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    padding: 0.5rem;
                    border-radius: 8px;
                    transition: all 0.3s ease;
                ">
                    <div class="step-icon" style="color: #3b82f6;"><i class="fas fa-file-pdf"></i></div>
                    <div class="step-text" style="flex: 1; text-align: left; color: #374151;">Creating documents</div>
                    <div class="step-status pending" style="color: #6b7280;">⏳</div>
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
    
    // Clear existing timers
    if (window.progressTimers) {
        window.progressTimers.forEach(id => clearTimeout(id));
    }
    window.progressTimers = [];
    
    steps.forEach(({ step, delay, progress, text }) => {
        const id = setTimeout(() => updateProgressStep(step, progress, text), delay);
        window.progressTimers.push(id);
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
        statusElement.style.color = '#10b981';
        stepItem.style.background = 'rgba(16, 185, 129, 0.1)';
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
            original_resume: window.optimizationState.resumeData?.text || '[Uploaded File]'
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
            <div class="success-content" style="
                text-align: center;
                padding: 3rem;
                background: white;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                max-width: 500px;
                width: 90%;
            ">
                <div class="success-icon" style="
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #10b981, #059669);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 1.5rem auto;
                ">
                    <i class="fas fa-check-circle" style="font-size: 2.5rem; color: white;"></i>
                </div>
                <h3 style="margin: 0 0 1.5rem 0; color: #1f2937;">Resume Optimized Successfully!</h3>
                <div class="result-preview" style="
                    background: #f9fafb;
                    padding: 1.5rem;
                    border-radius: 12px;
                    margin-bottom: 2rem;
                    text-align: left;
                ">
                    <p style="margin: 0 0 0.5rem 0;"><strong>Match Score:</strong> <span class="score-highlight" style="color: #10b981; font-weight: bold;">${Math.round(result.match_score || 0)}%</span></p>
                    <p style="margin: 0 0 0.5rem 0;"><strong>Keywords Added:</strong> ${result.missing_keywords?.length || 0}</p>
                    <p style="margin: 0;"><strong>Processing Time:</strong> ${result.processing_time_ms ? Math.round(result.processing_time_ms / 1000) : 'N/A'} seconds</p>
                </div>
                <div class="success-actions" style="display: flex; flex-direction: column; gap: 1rem;">
                    <button class="btn btn-primary" onclick="redirectToResults()" style="
                        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
                        color: white;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        border-radius: 8px;
                        font-weight: 600;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 0.5rem;
                    ">
                        <i class="fas fa-eye"></i> View Detailed Results
                    </button>
                    <button class="btn btn-outline" onclick="startOver()" style="
                        background: transparent;
                        color: #6b7280;
                        border: 1px solid #d1d5db;
                        padding: 0.75rem 1.5rem;
                        border-radius: 8px;
                        font-weight: 600;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 0.5rem;
                    ">
                        <i class="fas fa-redo"></i> Start Over
                    </button>
                </div>
                <p class="auto-redirect" style="margin: 1.5rem 0 0 0; color: #6b7280; font-size: 0.875rem;">
                    Redirecting to results in <span id="redirect-countdown">5</span> seconds...
                </p>
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
    window.location.href = '/optimizer/results';
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
    
    // Validate job description (if provided)
    if (jobData && jobData.text) {
        if (jobData.text.length < 50) {
            warnings.push('Job description seems very brief. More detailed descriptions produce better optimization results.');
        }
    } else {
        warnings.push('No job description provided. Adding one significantly improves optimization quality.');
    }
    
    return {
        isValid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * Clear messages from any message container
 */
function clearMessages() {
    // Clear upload messages
    const uploadMessages = document.getElementById('upload-messages');
    if (uploadMessages) {
        uploadMessages.innerHTML = '';
    }
    
    // Clear any other message containers
    const messages = document.getElementById('messages');
    if (messages) {
        messages.innerHTML = '';
    }
    
    // Remove retry button if it exists
    const retryBtn = document.getElementById('retry-btn');
    if (retryBtn) {
        retryBtn.remove();
    }
}

/**
 * Show validation results
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
 * Optimization error handler with retry logic
 */
function handleOptimizationError(error) {
    // APIError or generic Error
    const isApi = error instanceof APIError;
    const message = isApi ? error.message : (error?.message || 'Optimization failed. Please try again.');
    
    console.error('Optimization error:', error);
    
    // Show error in dashboard UI
    showMessage(message, 'error', null, 'upload-messages');
}

/**
 * Show message in dashboard UI
 */
function showMessage(text, type = 'info', duration = null, containerId = 'messages') {
    const icons = { success: 'check-circle', error: 'exclamation-triangle', warning: 'info-circle', info: 'info-circle' };
    const container = document.getElementById(containerId);
  
    // Fallback if container not found
    if (!container) {
        const label = (type || 'info').toUpperCase();
        (type === 'error' ? console.error : console.log)(`${label}: ${text}`);
        return;
    }
  
    // Build DOM safely
    const wrapper = document.createElement('div');
    wrapper.className = `message ${type}`;
  
    const iconEl = document.createElement('i');
    iconEl.className = `fas fa-${icons[type] || icons.info}`;
  
    const textEl = document.createElement('span');
    textEl.textContent = String(text);
  
    wrapper.append(iconEl, textEl);
  
    // Replace existing content
    container.innerHTML = '';
    container.appendChild(wrapper);
  
    // Auto clear
    const auto = duration ?? (type === 'success' ? 4000 : null);
    if (auto) setTimeout(() => { if (container.firstChild === wrapper) container.innerHTML = ''; }, auto);
}

/**
 * Start over function
 */
function startOver() {
    // Reset all state
    window.optimizationState = {
        currentStep: 1,
        resumeData: null,
        jobData: null,
        isProcessing: false,
        results: null,
        validationStatus: { resume: false, job: false },
        extractedContent: null,
        contentMetrics: { wordCount: 0, sectionCount: 0, hasContact: false }
    };
    
    // Reset dashboard form elements
    const jobTitle = document.getElementById('jobTitle');
    const jobText = document.getElementById('jobText');
    const jobLink = document.getElementById('jobLink');
    
    if (jobTitle) jobTitle.value = '';
    if (jobText) jobText.value = '';
    if (jobLink) jobLink.value = '';
    
    // Reset button state
    const optimizeBtn = document.getElementById('optimizeBtn');
    if (optimizeBtn) {
        optimizeBtn.disabled = true;
        optimizeBtn.classList.remove('is-loading');
    }
    
    // Hide overlay
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.remove();
    
    // Clear messages
    clearMessages();
    
    // Trigger dashboard.js to reset file upload state if available
    if (typeof window.removeFile === 'function') {
        window.removeFile('resume');
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