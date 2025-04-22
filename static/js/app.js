document.addEventListener('DOMContentLoaded', function() {
    // Check dependencies button functionality
    const checkDependenciesBtn = document.getElementById('checkDependenciesBtn');
    if (checkDependenciesBtn) {
        checkDependenciesBtn.addEventListener('click', function() {
            checkDependencies();
        });
    }

    // Enable Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add syntax highlighting to code blocks if Prism is available
    if (typeof Prism !== 'undefined') {
        Prism.highlightAll();
    }
    
    // Add sample search functionality
    const searchInput = document.getElementById('sampleSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            filterSamples();
        });
    }
});

/**
 * Filter samples based on search input
 */
function filterSamples() {
    const searchInput = document.getElementById('sampleSearch');
    const searchText = searchInput.value.toLowerCase();
    const sampleRows = document.querySelectorAll('#samplesTable tbody tr');
    
    sampleRows.forEach(row => {
        const name = row.querySelector('td:first-child').textContent.toLowerCase();
        const description = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        
        if (name.includes(searchText) || description.includes(searchText)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
    
    // Show message if no results
    const noResultsMessage = document.getElementById('noSamplesFound');
    const visibleRows = document.querySelectorAll('#samplesTable tbody tr:not([style*="display: none"])');
    
    if (noResultsMessage) {
        if (visibleRows.length === 0 && searchText.length > 0) {
            noResultsMessage.style.display = '';
        } else {
            noResultsMessage.style.display = 'none';
        }
    }
}

/**
 * Check if all required dependencies for ADK are installed
 */
function checkDependencies() {
    const btn = document.getElementById('checkDependenciesBtn');
    const originalText = btn.innerHTML;
    
    // Show loading state
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Checking...';
    btn.disabled = true;
    
    fetch('/check_dependencies')
        .then(response => response.json())
        .then(data => {
            // Restore button state
            btn.innerHTML = originalText;
            btn.disabled = false;
            
            // Create modal to display results
            let modalHtml = `
                <div class="modal fade" id="dependenciesModal" tabindex="-1" aria-labelledby="dependenciesModalLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="dependenciesModalLabel">
                                    <i class="fas fa-check-circle me-2"></i>
                                    Dependency Check Results
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="alert ${data.success ? 'alert-success' : 'alert-danger'}">
                                    ${data.success ? 
                                        '<i class="fas fa-check-circle me-2"></i>All dependencies are installed correctly!' : 
                                        '<i class="fas fa-exclamation-triangle me-2"></i>Some dependencies are missing or have issues.'}
                                </div>
                                
                                <h6>Details:</h6>
                                <ul class="list-group">`;
            
            // Add individual dependency status
            for (const dep of data.dependencies) {
                modalHtml += `
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        ${dep.name} 
                        <span class="badge ${dep.installed ? 'bg-success' : 'bg-danger'} rounded-pill">
                            ${dep.installed ? 'Installed' : 'Missing'}
                        </span>
                    </li>`;
            }
            
            modalHtml += `
                                </ul>
                                
                                ${data.message ? `<div class="mt-3"><strong>Message:</strong> ${data.message}</div>` : ''}
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>`;
            
            // Add modal to document and show it
            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = modalHtml;
            document.body.appendChild(modalContainer);
            
            const modal = new bootstrap.Modal(document.getElementById('dependenciesModal'));
            modal.show();
            
            // Remove modal from DOM when it's hidden
            document.getElementById('dependenciesModal').addEventListener('hidden.bs.modal', function () {
                document.body.removeChild(modalContainer);
            });
        })
        .catch(error => {
            // Restore button state
            btn.innerHTML = originalText;
            btn.disabled = false;
            
            // Show error alert
            const alertHtml = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error checking dependencies: ${error.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`;
            
            document.querySelector('.container').insertAdjacentHTML('afterbegin', alertHtml);
        });
}
