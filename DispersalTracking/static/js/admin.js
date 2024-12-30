document.addEventListener('DOMContentLoaded', function () {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const pullTab = document.querySelector('.pull-tab');
    
    // Toggle the sidebar
    sidebarToggle.addEventListener('click', function () {
        sidebar.classList.toggle('active');
        pullTab.classList.toggle('active'); // Add this line to toggle the pull tab
        
        // Change the button icon or text based on the sidebar state
        if (sidebar.classList.contains('active')) {
            sidebarToggle.innerHTML = '‹'; // Collapse icon
        } else {
            sidebarToggle.innerHTML = '›'; // Expand icon
        }
    });
});