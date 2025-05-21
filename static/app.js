document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('fileInput');
    const statusContainer = document.getElementById('status-container');
    const statusDiv = document.getElementById('status');
    const spinner = document.getElementById('spinner');
    const dataPreviewContainer = document.getElementById('data-preview-container');
    const statsContainer = document.getElementById('stats-container');
    const downloadContainer = document.getElementById('download-container');
    const downloadArea = document.getElementById('download-area');
    const downloadInfo = document.getElementById('download-info');

    // Form validation
    function validateForm() {
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            showStatus('Please select at least one file.', 'error');
            return false;
        }

        // Check file types
        let valid = true;
        const allowedTypes = [
            'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ];

        for (let i = 0; i < fileInput.files.length; i++) {
            const file = fileInput.files[i];
            const fileExtension = file.name.split('.').pop().toLowerCase();
            const isAllowedExtension = ['csv', 'xls', 'xlsx'].includes(fileExtension);
            const isAllowedType = allowedTypes.includes(file.type);

            if (!isAllowedExtension && !isAllowedType) {
                showStatus(`File "${file.name}" is not a supported format. Please use CSV or Excel files only.`, 'error');
                valid = false;
                break;
            }
        }

        return valid;
    }

    // Show status with appropriate styling
    function showStatus(message, type = 'info') {
        if (!statusContainer || !statusDiv) {
            console.error('Status container or div not found');
            return;
        }

        statusContainer.classList.remove('d-none');
        statusDiv.innerHTML = message;
        statusDiv.className = `alert fade-in d-block alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'}`;
    }

    // Show/hide spinner
    function toggleSpinner(show) {
        if (!spinner) {
            console.error('Spinner element not found');
            return;
        }

        if (show) {
            spinner.classList.remove('d-none');
        } else {
            spinner.classList.add('d-none');
        }
    }

    // Generate table from data
    function renderTable(tableId, data, columns) {
        const table = document.getElementById(tableId);
        if (!table) {
            console.error(`Table element with ID "${tableId}" not found`);
            return;
        }

        // Ensure table has thead and tbody
        let thead = table.querySelector('thead');
        let tbody = table.querySelector('tbody');

        // Clear both to start fresh
        thead.innerHTML = '<tr></tr>';
        tbody.innerHTML = '';

        // Get the header row
        const headerRow = thead.querySelector('tr');

        // Add header cells
        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        });

        // Add data rows
        data.forEach(row => {
            const tr = document.createElement('tr');

            // Add cells for each column
            columns.forEach(col => {
                const td = document.createElement('td');
                const value = row[col];

                // Handle different value types
                if (value === null || value === undefined) {
                    td.innerHTML = '<span class="text-muted">&lt;empty&gt;</span>';
                    td.classList.add('table-danger', 'text-muted');
                } else if (typeof value === 'object') {
                    td.textContent = JSON.stringify(value);
                } else {
                    td.textContent = value;
                }

                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        });
    }

    // Render statistics
    function renderStats(stats) {
        if (!statsContainer) {
            console.error('Stats container not found');
            return;
        }

        statsContainer.classList.remove('d-none');

        // Create stats summary
        const statsSummary = document.getElementById('stats-summary');
        if (!statsSummary) {
            console.error('Stats summary container not found');
            return;
        }

        // Create list of stats
        const statsList = document.createElement('div');
        statsList.className = 'list-group';

        // Add stat items with icons and appropriate styling
        const statItems = [
            {
                label: 'Original Rows',
                value: stats.original_rows,
                icon: 'fa-table'
            },
            {
                label: 'Cleaned Rows',
                value: stats.cleaned_rows,
                icon: 'fa-check-circle',
                highlight: stats.cleaned_rows < stats.original_rows
            },
            {
                label: 'Columns',
                value: stats.columns,
                icon: 'fa-columns'
            },
            {
                label: 'Nulls Removed',
                value: stats.nulls_removed || 0,
                icon: 'fa-eraser',
                highlight: (stats.nulls_removed || 0) > 0
            },
            {
                label: 'Duplicates Removed',
                value: stats.duplicates_removed || 0,
                icon: 'fa-clone',
                highlight: (stats.duplicates_removed || 0) > 0
            },
            {
                label: 'Dates Fixed',
                value: stats.dates_fixed || 0,
                icon: 'fa-calendar-check',
                highlight: (stats.dates_fixed || 0) > 0
            },
            {
                label: 'Numeric Values Fixed',
                value: stats.numerics_fixed || 0,
                icon: 'fa-calculator',
                highlight: (stats.numerics_fixed || 0) > 0
            },
            {
                label: 'Missing Values Filled',
                value: stats.missing_values_filled || 0,
                icon: 'fa-fill-drip',
                highlight: (stats.missing_values_filled || 0) > 0
            }
        ];

        statItems.forEach(item => {
            const listItem = document.createElement('div');
            listItem.className = `list-group-item d-flex justify-content-between align-items-center ${item.highlight ? 'list-group-item-success' : ''}`;

            const leftContent = document.createElement('div');
            leftContent.innerHTML = `<i class="fas ${item.icon} me-2"></i> ${item.label}`;

            const badge = document.createElement('span');
            badge.className = `badge rounded-pill ${item.highlight ? 'bg-success' : 'bg-secondary'}`;
            badge.textContent = item.value;

            listItem.appendChild(leftContent);
            listItem.appendChild(badge);
            statsList.appendChild(listItem);
        });

        // Add percent reduced if available
        if (stats.percent_reduced) {
            const reductionItem = document.createElement('div');
            reductionItem.className = 'list-group-item d-flex justify-content-between align-items-center list-group-item-info';

            const leftContent = document.createElement('div');
            leftContent.innerHTML = '<i class="fas fa-compress-alt me-2"></i> Data Reduction';

            const badge = document.createElement('span');
            badge.className = 'badge rounded-pill bg-info';
            badge.textContent = `${stats.percent_reduced}%`;

            reductionItem.appendChild(leftContent);
            reductionItem.appendChild(badge);
            statsList.appendChild(reductionItem);
        }

        // Clear and add new stats
        statsSummary.innerHTML = '';
        statsSummary.appendChild(statsList);

        // Create chart if available
        const cleaningChart = document.getElementById('cleaning-chart');
        if (cleaningChart && typeof Chart !== 'undefined') {
            // Destroy any existing chart
            if (cleaningChart.chart) {
                cleaningChart.chart.destroy();
            }

            // Create chart data
            const chartData = {
                labels: ['Original', 'Cleaned'],
                datasets: [{
                    label: 'Row Count',
                    data: [stats.original_rows, stats.cleaned_rows],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(75, 192, 192, 0.5)'
                    ],
                    borderColor: [
                        'rgb(255, 99, 132)',
                        'rgb(75, 192, 192)'
                    ],
                    borderWidth: 1
                }]
            };

            // Create chart
            cleaningChart.chart = new Chart(cleaningChart, {
                type: 'bar',
                data: chartData,
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Data Cleaning Results'
                        }
                    }
                }
            });
        }
    }

    // Get cleaning options as an object
    function getCleaningOptions() {
        return {
            removeNulls: document.getElementById('removeNulls')?.checked || true,
            removeDuplicates: document.getElementById('removeDuplicates')?.checked || true,
            standardizeText: document.getElementById('standardizeText')?.checked || true,
            fillNumerics: document.getElementById('fillNumerics')?.checked || true,
            fixDates: document.getElementById('fixDates')?.checked || true,
            trimWhitespace: document.getElementById('trimWhitespace')?.checked || true,
            fixPhoneNumbers: document.getElementById('fixPhoneNumbers')?.checked || true,
            fixEmails: document.getElementById('fixEmails')?.checked || true,
            fixBooleanValues: document.getElementById('fixBooleanValues')?.checked || true,
            extractNumericFromText: document.getElementById('extractNumericFromText')?.checked || true,
            normalizeText: document.getElementById('normalizeText')?.checked || false
        };
    }

    // Reset the UI state for new uploads/samples
    function resetUIState() {
        if (dataPreviewContainer) dataPreviewContainer.classList.add('d-none');
        if (statsContainer) statsContainer.classList.add('d-none');
        if (downloadContainer) downloadContainer.classList.add('d-none');
        if (downloadArea) downloadArea.innerHTML = '';
        if (downloadInfo) downloadInfo.textContent = '';
    }

    // Process API response data
    function processResponseData(data) {
        try {
            console.log("Processing response data:", data);

            // Process AI recommendations if available
            if (data.ai_recommendations) {
                console.log("AI recommendations found:", data.ai_recommendations);
                if (typeof displayAIRecommendations === 'function') {
                    displayAIRecommendations(data.ai_recommendations);
                } else {
                    console.error("displayAIRecommendations function not found");
                }
            } else {
                console.warn("No AI recommendations in response");
            }

            // Render original data if available
            if (data.original_sample && Array.isArray(data.original_sample) &&
                data.original_columns && Array.isArray(data.original_columns.columns)) {
                renderTable('original-table', data.original_sample, data.original_columns.columns);
            } else {
                console.warn('Missing original sample data or columns');
            }

            // Render cleaned data if available
            if (data.cleaned_sample && Array.isArray(data.cleaned_sample) &&
                data.cleaned_columns && Array.isArray(data.cleaned_columns.columns)) {
                renderTable('cleaned-table', data.cleaned_sample, data.cleaned_columns.columns);
            } else {
                console.warn('Missing cleaned sample data or columns');
            }

            // Render stats if available
            if (data.stats && typeof data.stats === 'object') {
                renderStats(data.stats);
            } else {
                console.warn('Missing statistics data');
            }

            // Show data preview if we have any data
            if ((data.original_sample && data.original_sample.length > 0) ||
                (data.cleaned_sample && data.cleaned_sample.length > 0)) {
                if (dataPreviewContainer) dataPreviewContainer.classList.remove('d-none');
            }

            // Handle download link if available
            if (data.download_filename) {
                if (downloadContainer) downloadContainer.classList.remove('d-none');

                // Add info about the download
                if (downloadInfo) {
                    downloadInfo.innerHTML = `<div class="alert alert-success">
                        <i class="fas fa-check-circle me-2"></i>
                        Your cleaned data file is ready for download.
                    </div>`;
                }

                // Create download button
                if (downloadArea) {
                    downloadArea.innerHTML = `
                        <a href="/download/${encodeURIComponent(data.download_filename)}"
                           class="btn btn-primary btn-lg" download>
                            <i class="fas fa-download me-2"></i>Download Cleaned Data
                        </a>`;
                }
            } else {
                console.warn('No download filename provided in response');
            }
        } catch (error) {
            console.error('Error processing response data:', error);
            showStatus(`Error processing data: ${error.message}`, 'error');
        }
    }

    // Main upload form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(event) {
            event.preventDefault();

            if (!validateForm()) {
                return;
            }

            // Reset UI state
            resetUIState();

            // Show status and spinner
            showStatus('Uploading and processing your data...', 'info');
            toggleSpinner(true);

            // Create form data with files and options
            const formData = new FormData();

            // Add all selected files
            for (let i = 0; i < fileInput.files.length; i++) {
                formData.append('files', fileInput.files[i]);
            }

            // Add cleaning options
            const cleaningOptions = getCleaningOptions();
            for (const [key, value] of Object.entries(cleaningOptions)) {
                formData.append(key, value);
            }

            // Send request to server
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                // Check for HTTP errors
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Server error during upload');
                    });
                }
                return response.json();
            })
            .then(data => {
                // Hide spinner and show success message
                toggleSpinner(false);
                showStatus('Data processed successfully!', 'success');

                // Process response data
                processResponseData(data);
            })
            .catch(error => {
                // Hide spinner and show error message
                toggleSpinner(false);
                showStatus(`Error: ${error.message}`, 'error');
                console.error('Upload error:', error);
            });
        });
    }

    // Sample file links handler
    const sampleLinks = document.querySelectorAll('.sample-file-link');
    sampleLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();

            // Get filename from data attribute
            const filename = this.getAttribute('data-filename');
            if (!filename) {
                showStatus('Sample filename not specified', 'error');
                return;
            }

            // Reset UI state
            resetUIState();

            // Show loading status with visual styling
            showStatus(`<div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                Processing sample file: <strong>${filename}</strong>...
            </div>`, 'info');

            toggleSpinner(true);

            // Get cleaning options
            const cleaningOptions = getCleaningOptions();
            const queryParams = new URLSearchParams();

            // Add cleaning options as query parameters
            for (const [key, value] of Object.entries(cleaningOptions)) {
                queryParams.append(key, value);
            }

            // Send request to use sample file
            fetch(`/use-sample/${encodeURIComponent(filename)}?${queryParams}`)
            .then(response => {
                // Check for HTTP errors
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || `Error processing sample file: ${filename}`);
                    });
                }

                // Try to parse response as JSON
                try {
                    return response.json();
                } catch (error) {
                    throw new Error('Failed to parse sample response as JSON');
                }
            })
            .then(data => {
                // Hide spinner and show success message
                toggleSpinner(false);

                const sampleName = this.querySelector('h6').textContent || filename;
                showStatus(`<i class="fas fa-check-circle me-2"></i> Sample "${sampleName}" processed successfully!`, 'success');

                // Process the response data
                processResponseData(data);
            })
            .catch(error => {
                // Hide spinner and show error message
                toggleSpinner(false);
                showStatus(`<i class="fas fa-exclamation-triangle me-2"></i> Error: ${error.message}`, 'error');
                console.error('Sample processing error:', error);
            });
        });
    });
});
