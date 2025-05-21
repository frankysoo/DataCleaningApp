/**
 * AI Recommendations Handler for DataCleaningApp
 *
 * This script handles displaying and applying AI-powered cleaning recommendations
 * from the Gemini AI model.
 */

// Function to display AI recommendations
function displayAIRecommendations(recommendations) {
    console.log("displayAIRecommendations called with:", recommendations);

    // Check if recommendations exist
    if (!recommendations || !recommendations.operations || Object.keys(recommendations.operations).length === 0) {
        console.log("No AI recommendations available");
        return;
    }

    // Get the recommendations card
    let recommendationsCard = document.getElementById('ai-recommendations-card');

    if (!recommendationsCard) {
        console.error("AI recommendations card not found in the DOM");
        return;
    }

    // Make sure it's visible
    console.log("Using existing recommendations card");
    recommendationsCard.style.display = 'block';

    // Get the container for the recommendations list
    const container = document.getElementById('recommendations-container');
    if (!container) {
        console.error("Recommendations container not found");
        return;
    }

    // Clear previous recommendations
    container.innerHTML = '';

    // Update summary if available
    const summaryEl = document.getElementById('ai-summary');
    if (summaryEl && recommendations.summary) {
        summaryEl.textContent = recommendations.summary;
    } else if (summaryEl) {
        summaryEl.textContent = "Our AI has analyzed your data and recommends the following cleaning operations:";
    }

    // Create a list of recommendations
    const recList = document.createElement('ul');
    recList.className = 'list-group';

    // Add each recommendation
    for (const [operation, recommended] of Object.entries(recommendations.operations)) {
        if (recommended) {
            const confidence = recommendations.confidence[operation] || 0;
            const reasoning = recommendations.reasoning[operation] || '';

            const item = document.createElement('li');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';

            // Create a pretty name for the operation
            const prettyName = operation
                .replace(/([A-Z])/g, ' $1')
                .replace(/^./, str => str.toUpperCase());

            // Create confidence badge
            const badge = document.createElement('span');
            badge.className = `badge ${confidence > 0.8 ? 'bg-success' : confidence > 0.5 ? 'bg-warning' : 'bg-secondary'} rounded-pill`;
            badge.textContent = `${Math.round(confidence * 100)}% confidence`;

            // Create checkbox
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'form-check-input me-2';
            checkbox.checked = true;
            checkbox.dataset.operation = operation;

            // Create label with operation name and reasoning
            const label = document.createElement('label');
            label.className = 'form-check-label flex-grow-1';
            label.innerHTML = `<strong>${prettyName}</strong>: ${reasoning}`;

            // Add elements to item
            item.appendChild(checkbox);
            item.appendChild(label);
            item.appendChild(badge);

            // Add item to list
            recList.appendChild(item);
        }
    }

    container.appendChild(recList);

    // Set up the "Apply All Recommendations" button
    const applyButton = document.getElementById('apply-recommendations');
    if (applyButton) {
        // Remove any existing event listeners
        const newApplyButton = applyButton.cloneNode(true);
        applyButton.parentNode.replaceChild(newApplyButton, applyButton);

        // Add new event listener
        newApplyButton.addEventListener('click', function() {
            applyAIRecommendations(container);
        });
    }
}



// Function to apply the selected AI recommendations
function applyAIRecommendations(container) {
    // Get all checked recommendations
    const checkedOps = Array.from(container.querySelectorAll('input[type="checkbox"]:checked'))
        .map(cb => cb.dataset.operation);

    // Map operation names to form field names
    const operationToFormField = {
        'removeNulls': 'removeNulls',
        'removeDuplicates': 'removeDuplicates',
        'standardizeText': 'standardizeText',
        'fillNumerics': 'fillNumerics',
        'fixDates': 'fixDates',
        'trimWhitespace': 'trimWhitespace',
        'fixPhoneNumbers': 'fixPhoneNumbers',
        'fixEmails': 'fixEmails',
        'fixBooleanValues': 'fixBooleanValues',
        'extractNumericFromText': 'extractNumericFromText',
        'normalizeText': 'normalizeText'
    };

    // Apply recommendations by checking the corresponding options
    checkedOps.forEach(op => {
        const formField = operationToFormField[op];
        if (formField) {
            const checkbox = document.querySelector(`input[name="${formField}"]`);
            if (checkbox) {
                checkbox.checked = true;
            }
        }
    });

    // Show a success message
    alert('AI recommendations applied! Click "Upload and Clean" to process your data.');
}

// Function to handle the response from the server
function handleAIRecommendationsResponse(response) {
    if (response && response.ai_recommendations) {
        displayAIRecommendations(response.ai_recommendations);
    }
}
