// Change application status
function changeStatus(id, newStatus) {
    fetch(`/status/${id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(res => res.json())
    .then(data => {
        console.log('Status updated:', data);
        // Reload page to show updated status
        location.reload();
    })
    .catch(err => {
        console.error('Error updating status:', err);
        alert('Failed to update status. Please try again.');
    });
}

// Delete application
function deleteApp(id) {
    if (!confirm('Are you sure you want to delete this application?')) {
        return;
    }

    fetch(`/delete/${id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(res => res.json())
    .then(data => {
        console.log('Application deleted:', data);
        // Reload page to show updated list
        location.reload();
    })
    .catch(err => {
        console.error('Error deleting application:', err);
        alert('Failed to delete application. Please try again.');
    });
}

// Set today's date as default in add form
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('date_applied');
    if (dateInput && !dateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
});