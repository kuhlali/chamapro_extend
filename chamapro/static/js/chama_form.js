document.addEventListener('DOMContentLoaded', function() {
    const frequencySelect = document.getElementById('id_contribution_frequency');
    const monthlyField = document.getElementById('id_contribution_day');
    const weeklyField = document.getElementById('id_contribution_weekday');

    if (!frequencySelect || !monthlyField || !weeklyField) return;

    function toggleFields() {
        const frequency = frequencySelect.value;
        // Find container (Bootstrap 5 .mb-3 or similar)
        const monthlyContainer = document.getElementById('div_id_contribution_day') || monthlyField.closest('.mb-3') || monthlyField.closest('.form-group') || monthlyField.parentElement;
        const weeklyContainer = document.getElementById('div_id_contribution_weekday') || weeklyField.closest('.mb-3') || weeklyField.closest('.form-group') || weeklyField.parentElement;

        if (frequency === 'MONTHLY') {
            if(monthlyContainer) monthlyContainer.style.display = ''; // Reset to default
            if(weeklyContainer) weeklyContainer.style.display = 'none';
            monthlyField.required = true;
            weeklyField.required = false;
        } else {
            if(monthlyContainer) monthlyContainer.style.display = 'none';
            if(weeklyContainer) weeklyContainer.style.display = '';
            monthlyField.required = false;
            weeklyField.required = true;
        }
    }

    frequencySelect.addEventListener('change', toggleFields);
    toggleFields(); // Run on load
});
