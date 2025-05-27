// Main JavaScript for the application
// Add your custom JavaScript here

document.addEventListener('DOMContentLoaded', function() {
    // Add any JavaScript that should run when the page loads
    console.log('Application JavaScript loaded');
    
    // Example: Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
