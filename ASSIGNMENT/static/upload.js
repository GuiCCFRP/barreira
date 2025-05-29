document.addEventListener('DOMContentLoaded', () => {
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const fileNameInput = document.getElementById('file-name');
    const submitBtn = document.getElementById('submit-btn');
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);
    
    // Handle file selection via browse button
    fileInput.addEventListener('change', handleFiles);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        dropArea.classList.add('highlight');
    }
    
    function unhighlight() {
        dropArea.classList.remove('highlight');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles({target: {files}});
    }
    
    function handleFiles(e) {
        const files = e.target.files;
        
        if (files.length > 0) {
            const file = files[0];
            
            // Validate file type
            if (file.type === 'application/pdf') {
                const fileName = sanitizeFilename(file.name);
                
                fileInfo.innerHTML = `
                    <div class="file-preview">
                        <i class="fas fa-file-pdf"></i>
                        <div class="file-details">
                            <span class="filename">${fileName}</span>
                            <span class="file-size">${formatFileSize(file.size)}</span>
                        </div>
                    </div>
                `;
                
                fileNameInput.value = fileName;
                submitBtn.disabled = false;
                dropArea.classList.add('file-selected');
            } else {
                fileInfo.innerHTML = '<div class="error">Please select a PDF file</div>';
                submitBtn.disabled = true;
            }
        }
    }
    
    function sanitizeFilename(name) {
        return name.replace(/[^a-zA-Z0-9_.-]/g, '_');
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
});
