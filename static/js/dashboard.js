(function() {
    'use strict';

    // =============================================================================
    // MODULE STATE
    // =============================================================================
    
    let state = {
        selectedFile: null,
        isDragActive: false,
        isSubmitting: false,
        validationState: {
            resume: false,
            jobDescription: false // optional but tracked
        }
    };

    let elements = {};
    let statusElement = null;

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    function initDashboard(root = document) {
        // Cache DOM elements
        elements = {
            dropzone: root.querySelector('#resumeUpload'),
            fileInput: root.querySelector('#resumeFile'),
            uploadState: root.querySelector('#resumeUpload'),
            uploadedState: root.querySelector('#resumeUploaded'),
            jobTitle: root.querySelector('#jobTitle'),
            jobText: root.querySelector('#jobText'),
            jobLink: root.querySelector('#jobLink'),
            optimizeBtn: root.querySelector('#optimizeBtn'),
            resumeStatusItem: root.querySelector('#resumeStatusItem'),
            jobStatusItem: root.querySelector('#jobStatusItem'),
            progressSection: root.querySelector('#progressSection'),
            uploadInterface: root.querySelector('.upload-interface')
        };

        // Create or find aria-live status element
        statusElement = root.querySelector('[aria-live]') || createStatusElement(root);

        // Validate required elements
        if (!elements.dropzone || !elements.fileInput || !elements.optimizeBtn) {
            console.error('Required DOM elements missing for dashboard initialization');
            return false;
        }

        // Initialize components
        bindDropzone(root);
        bindJobDescriptionInputs(root);
        bindOptimizeButton(root);
        
        // Initial state update
        updateOptimizeState(root);
        
        announce('Dashboard ready for resume upload');
        console.log('Dashboard initialized successfully');
        return true;
    }

    function createStatusElement(root) {
        const existingContainer = root.querySelector('.upload-interface') || root.querySelector('.container');
        if (!existingContainer) return null;

        const status = document.createElement('span');
        status.setAttribute('aria-live', 'polite');
        status.setAttribute('aria-atomic', 'true');
        status.className = 'sr-only';
        status.style.cssText = 'position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0;';
        
        existingContainer.appendChild(status);
        return status;
    }

    // =============================================================================
    // DROPZONE FUNCTIONALITY
    // =============================================================================

    function bindDropzone(root) {
        const dropzone = elements.dropzone;
        const fileInput = elements.fileInput;

        if (!dropzone || !fileInput) return;

        // Remove any existing onclick attribute to prevent conflicts
        dropzone.removeAttribute('onclick');

        // Click to browse
        dropzone.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (!state.isSubmitting) {
                fileInput.click();
            }
        });

        // Keyboard support
        dropzone.addEventListener('keydown', (e) => {
            if ((e.key === 'Enter' || e.key === ' ') && !state.isSubmitting) {
                e.preventDefault();
                fileInput.click();
            }
        });

        // Drag counter for nested elements
        let dragCounter = 0;

        // Drag events
        dropzone.addEventListener('dragenter', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dragCounter++;
            
            if (dragCounter === 1 && !state.isSubmitting) {
                state.isDragActive = true;
                dropzone.classList.add('is-dragover');
            }
        });

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            if (!state.isSubmitting) {
                e.dataTransfer.dropEffect = 'copy';
            }
        });

        dropzone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dragCounter--;
            
            if (dragCounter === 0) {
                state.isDragActive = false;
                dropzone.classList.remove('is-dragover', 'is-valid', 'is-error');
            }
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dragCounter = 0;
            state.isDragActive = false;
            
            dropzone.classList.remove('is-dragover');
            
            if (state.isSubmitting) return;

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelection(files[0], root);
            }
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelection(e.target.files[0], root);
            }
        });
    }

    function handleFileSelection(file, root) {
        const validation = validateFile(file);
        
        if (!validation.valid) {
            showFileError(validation.reasons, root);
            return;
        }

        // Store file and update UI
        state.selectedFile = file;
        elements.fileInput.files = createFileList(file);
        
        showFileSuccess(file, root);
        state.validationState.resume = true;
        updateOptimizeState(root);
        
        announce(`Resume file ${file.name} uploaded successfully`);
    }

    function createFileList(file) {
        const dt = new DataTransfer();
        dt.items.add(file);
        return dt.files;
    }

    function showFileSuccess(file, root) {
        const uploadState = elements.uploadState;
        const uploadedState = elements.uploadedState;
        
        if (!uploadState || !uploadedState) return;

        // Update file details in uploaded state
        const fileName = uploadedState.querySelector('.file-name');
        const fileSize = uploadedState.querySelector('.file-size');
        const fileTypeBadge = uploadedState.querySelector('.file-type-badge');
        
        if (fileName) fileName.textContent = file.name;
        if (fileSize) fileSize.textContent = formatFileSize(file.size);
        if (fileTypeBadge) fileTypeBadge.textContent = getFileExtension(file.type).toUpperCase();

        // Switch states
        uploadState.style.display = 'none';
        uploadedState.style.display = 'block';

        // Update status
        const resumeStatus = root.querySelector('#resumeStatus');
        if (resumeStatus) {
            resumeStatus.textContent = 'Ready';
            resumeStatus.classList.add('completed');
        }

        // Clear any error states
        elements.dropzone.classList.remove('is-error');
        elements.fileInput.removeAttribute('aria-invalid');
    }

    function showFileError(reasons, root) {
        elements.dropzone.classList.add('is-error');
        elements.fileInput.setAttribute('aria-invalid', 'true');
        
        const errorMessage = reasons.join(' ');
        announce(`File upload error: ${errorMessage}`);
        
        // Reset file input
        elements.fileInput.value = '';
        state.selectedFile = null;
        state.validationState.resume = false;
        updateOptimizeState(root);
    }

    // =============================================================================
    // FILE VALIDATION
    // =============================================================================

    function validateFile(file) {
        const reasons = [];
        const maxSize = 5 * 1024 * 1024; // 5MB
        const allowedTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ];

        // Size validation
        if (file.size === 0) {
            reasons.push('File appears to be empty.');
        } else if (file.size > maxSize) {
            reasons.push(`File size (${formatFileSize(file.size)}) exceeds 5MB limit.`);
        }

        // Type validation
        if (!allowedTypes.includes(file.type)) {
            reasons.push(`File type not supported. Please use PDF, DOCX, or TXT files.`);
        }

        // Basic security check
        const suspiciousExtensions = /\.(exe|bat|cmd|scr|com|pif|vbs|js)$/i;
        if (suspiciousExtensions.test(file.name)) {
            reasons.push('File type not allowed for security reasons.');
        }

        return {
            valid: reasons.length === 0,
            reasons
        };
    }

    // =============================================================================
    // JOB DESCRIPTION HANDLING
    // =============================================================================

    function bindJobDescriptionInputs(root) {
        const jobText = elements.jobText;
        
        if (jobText) {
            const debouncedValidation = debounce(() => {
                const content = jobText.value.trim();
                state.validationState.jobDescription = content.length > 0;
                
                // Light validation hint - non-blocking
                if (content.length === 0 && state.validationState.resume) {
                    announce('Job description is optional but recommended for better optimization');
                }
                
                updateOptimizeState(root);
            }, 250);

            jobText.addEventListener('input', debouncedValidation);
            jobText.addEventListener('blur', debouncedValidation);
        }

        // Job title and link don't affect validation but are included in form data
        const jobTitle = elements.jobTitle;
        const jobLink = elements.jobLink;
        
        if (jobTitle) {
            jobTitle.addEventListener('input', debounce(() => updateOptimizeState(root), 250));
        }
        
        if (jobLink) {
            jobLink.addEventListener('input', debounce(() => updateOptimizeState(root), 250));
        }
    }

    // =============================================================================
    // VALIDATION & BUTTON STATE
    // =============================================================================

    function validateState(root) {
        const validFile = state.validationState.resume && state.selectedFile;
        
        return {
            valid: validFile, // JD is optional
            reasons: validFile ? [] : ['Please upload a resume file']
        };
    }

    function updateOptimizeState(root) {
        const validation = validateState(root);
        const optimizeBtn = elements.optimizeBtn;
        
        if (!optimizeBtn) return;

        // Update button state
        optimizeBtn.disabled = !validation.valid || state.isSubmitting;
        
        // Update status items
        updateStatusItem(elements.resumeStatusItem, state.validationState.resume);
        updateStatusItem(elements.jobStatusItem, state.validationState.jobDescription);
    }

    function updateStatusItem(statusItem, isValid) {
        if (!statusItem) return;
        
        const icon = statusItem.querySelector('i');
        
        if (isValid) {
            statusItem.classList.add('valid');
            if (icon) icon.className = 'fas fa-check-circle';
        } else {
            statusItem.classList.remove('valid');
            if (icon) icon.className = 'fas fa-circle';
        }
    }

    // =============================================================================
    // FORM SUBMISSION
    // =============================================================================

    function bindOptimizeButton(root) {
        const optimizeBtn = elements.optimizeBtn;
        if (!optimizeBtn) return;

        optimizeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            
            if (state.isSubmitting) return;
            
            const validation = validateState(root);
            if (!validation.valid) {
                // Focus first invalid control
                if (!state.validationState.resume) {
                    elements.fileInput.focus();
                }
                announce(`Cannot proceed: ${validation.reasons.join(' ')}`);
                return;
            }

            const endpoint = root.querySelector('.upload-interface')?.dataset?.endpoint || 
                           root.querySelector('[data-endpoint]')?.dataset?.endpoint;
            
            if (!endpoint) {
                console.error('No endpoint found for form submission');
                announce('Configuration error. Please refresh the page.');
                return;
            }

            submitOptimization(root, endpoint);
        });
    }

    async function submitOptimization(root, endpoint) {
        if (state.isSubmitting) return;

        state.isSubmitting = true;
        
        // Update UI to loading state
        const optimizeBtn = elements.optimizeBtn;
        const btnContent = optimizeBtn.querySelector('.btn-content');
        const btnLoader = optimizeBtn.querySelector('.btn-loader');
        
        optimizeBtn.classList.add('is-loading');
        optimizeBtn.disabled = true;
        
        if (btnContent) btnContent.style.display = 'none';
        if (btnLoader) btnLoader.style.display = 'flex';

        try {
            const formData = buildFormData(root);
            
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.result_id || result.request_hash) {
                const redirectId = result.result_id || result.request_hash;
                announce('Optimization complete! Redirecting to results...');
                window.location.href = `/optimizer/results/${redirectId}`;
            } else {
                console.log('Optimization response:', result);
                announce('Optimization completed successfully');
            }

        } catch (error) {
            console.error('Optimization error:', error);
            handleSubmissionError(error, root);
        }
    }

    function buildFormData(root) {
        const formData = new FormData();
        
        // Resume file
        formData.append('resume_type', 'file');
        formData.append('resume_file', state.selectedFile);
        
        // Job description fields
        if (elements.jobTitle?.value.trim()) {
            formData.append('job_title', elements.jobTitle.value.trim());
        }
        
        if (elements.jobText?.value.trim()) {
            formData.append('job_description', elements.jobText.value.trim());
        }
        
        if (elements.jobLink?.value.trim()) {
            formData.append('job_url', elements.jobLink.value.trim());
        }

        // Check for existing hidden inputs with defaults
        const hiddenInputs = root.querySelectorAll('input[type="hidden"]');
        hiddenInputs.forEach(input => {
            if (input.name && input.value) {
                formData.append(input.name, input.value);
            }
        });

        // Add defaults if not present
        if (!formData.has('tone')) {
            formData.append('tone', 'professional-concise');
        }
        if (!formData.has('locale')) {
            formData.append('locale', 'en-US');
        }
        if (!formData.has('include_pdf')) {
            formData.append('include_pdf', 'true');
        }

        return formData;
    }

    function handleSubmissionError(error, root) {
        state.isSubmitting = false;
        
        // Reset button state
        const optimizeBtn = elements.optimizeBtn;
        const btnContent = optimizeBtn.querySelector('.btn-content');
        const btnLoader = optimizeBtn.querySelector('.btn-loader');
        
        optimizeBtn.classList.remove('is-loading');
        optimizeBtn.disabled = false;
        
        if (btnContent) btnContent.style.display = 'flex';
        if (btnLoader) btnLoader.style.display = 'none';

        // Mark relevant inputs as invalid
        if (error.message.includes('file') || error.message.includes('resume')) {
            elements.fileInput.setAttribute('aria-invalid', 'true');
            elements.fileInput.focus();
        }

        // Announce error
        const errorMessage = error.message || 'An error occurred while processing your request';
        announce(`Error: ${errorMessage}`);
        
        updateOptimizeState(root);
    }

    // =============================================================================
    // UTILITY FUNCTIONS
    // =============================================================================

    function announce(message) {
        if (statusElement) {
            statusElement.textContent = '';
            setTimeout(() => {
                statusElement.textContent = message;
            }, 100);
        }
    }

    function bytesToMB(bytes) {
        return (bytes / (1024 * 1024)).toFixed(2);
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    function getFileExtension(mimeType) {
        const extMap = {
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'text/plain': 'txt'
        };
        return extMap[mimeType] || 'file';
    }

    function getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : '';
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // =============================================================================
    // EXPOSE GLOBAL INTERFACE
    // =============================================================================

    // Main initialization function
    window.initDashboard = initDashboard;

    // Utility functions for onclick handlers
    window.removeFile = function(type) {
        if (type === 'resume') {
            state.selectedFile = null;
            state.validationState.resume = false;
            
            elements.fileInput.value = '';
            elements.uploadState.style.display = 'block';
            elements.uploadedState.style.display = 'none';
            
            const resumeStatus = document.querySelector('#resumeStatus');
            if (resumeStatus) {
                resumeStatus.textContent = 'Required';
                resumeStatus.classList.remove('completed');
            }
            
            updateOptimizeState(document);
            announce('Resume file removed');
        }
    };

    // Auto-initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initDashboard();
        });
    } else {
        // DOM already loaded
        setTimeout(() => initDashboard(), 0);
    }

    // Prevent double-submit on form submission
    document.addEventListener('submit', (e) => {
        if (state.isSubmitting) {
            e.preventDefault();
            return false;
        }
    });

    // Global error handling
    window.addEventListener('error', (e) => {
        if (state.isSubmitting) {
            console.error('Error during submission:', e.error);
            handleSubmissionError(e.error, document);
        }
    });

})();