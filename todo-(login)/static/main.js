// static/main.js

document.addEventListener('DOMContentLoaded', () => {
    
    // --- Dark/Light Mode Toggle ---
    const themeToggleButton = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme');

    if (currentTheme) {
        document.body.classList.add(currentTheme);
    }

    themeToggleButton.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        if (document.body.classList.contains('dark-mode')) {
            document.body.classList.remove('light-mode');
            localStorage.setItem('theme', 'dark-mode');
        } else {
            document.body.classList.add('light-mode');
            localStorage.setItem('theme', 'light-mode');
        }
    });

    // --- Edit Task Modal ---
    const editModal = document.getElementById('edit-modal');
    const closeModalButton = document.querySelector('#edit-modal .close-button'); 
    const editForm = document.getElementById('edit-form');
    const editInput = document.getElementById('edit-task-text');
    
    function setupEditButtons() {
        const editButtons = document.querySelectorAll('.edit-btn');
        editButtons.forEach(button => {
            button.onclick = null;
            button.addEventListener('click', () => {
                const taskId = button.dataset.taskId;
                const taskText = button.dataset.taskText;
                
                editForm.action = `/edit/${taskId}`;
                editInput.value = taskText;
                editModal.style.display = 'block';
            });
        });
    }
    setupEditButtons(); 

    closeModalButton.addEventListener('click', () => {
        editModal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target == editModal) {
            editModal.style.display = 'none';
        }
    });

    // --- Text-to-Speech (TTS) ---
    function setupTtsButtons() {
        const ttsButtons = document.querySelectorAll('.tts-btn');
        ttsButtons.forEach(button => {
            button.onclick = null;
            button.addEventListener('click', () => {
                const textToSpeak = button.dataset.taskText;
                if ('speechSynthesis' in window) {
                    const utterance = new SpeechSynthesisUtterance(textToSpeak);
                    utterance.lang = 'en-US';
                    window.speechSynthesis.speak(utterance);
                } else {
                    alert("Sorry, your browser does not support Text-to-Speech.");
                }
            });
        });
    }
    setupTtsButtons();

    // --- Emoji Picker ---
    const emojiToggleButton = document.getElementById('emoji-toggle');
    const emojiPickerContainer = document.getElementById('emoji-picker-container');
    const taskInput = document.querySelector('.add-task-form input[name="task"]');
    const emojiPicker = document.querySelector('emoji-picker'); 

    emojiToggleButton.addEventListener('click', (event) => {
        event.stopPropagation(); 
        emojiPickerContainer.classList.toggle('is-visible');
        if (emojiPickerContainer.classList.contains('is-visible')) {
            taskInput.focus(); 
        }
    });

    if (emojiPicker) {
        emojiPicker.addEventListener('emoji-click', event => {
            taskInput.value += event.detail.unicode;
            taskInput.focus();
        });
    }

    window.addEventListener('click', (event) => {
        if (emojiPickerContainer && emojiPickerContainer.classList.contains('is-visible') && 
            !emojiPickerContainer.contains(event.target) && 
            event.target !== emojiToggleButton) {
            emojiPickerContainer.classList.remove('is-visible');
        }
    });

    // --- Drag-and-Drop Reordering with SortableJS ---
    const taskList = document.getElementById('task-list');

    if (taskList) {
        new Sortable(taskList, {
            animation: 150,
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            filter: '.no-drag', // Pinned tasks cannot be dragged
            preventOnFilter: true,

            onEnd: function (evt) {
                const newOrder = Array.from(taskList.children)
                    .map(item => item.dataset.taskId)
                    .filter(id => id); 
                
                fetch('/api/reorder', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_ids: newOrder })
                })
                .then(response => {
                    if (!response.ok) {
                        alert('Failed to save new task order. Please reload.');
                    }
                })
                .catch(error => {
                    console.error('Error saving reorder:', error);
                    alert('An error occurred during reordering.');
                });
            }
        });
    }

    // --- Task Details Modal Logic (Tag management via SELECT) ---
    const detailsModal = document.getElementById('details-modal');
    const closeDetailsButton = document.getElementById('close-details-modal');
    const taskItemListener = document.querySelector('.task-list');

    const detailsTaskText = document.getElementById('details-task-text');
    const detailsCreatedAt = document.getElementById('details-created-at');
    const detailsUpdatedAt = document.getElementById('details-updated-at');
    const detailsDueDateInput = document.getElementById('details-due-date');
    const duedateForm = document.getElementById('duedate-form');
    const detailsWarningMessage = document.getElementById('details-warning-message');
    const detailsTimeRemaining = document.getElementById('details-time-remaining');
    
    // Tag Elements (newTagInput is now a SELECT)
    const detailsTagsList = document.getElementById('details-tags-list');
    const newTagInput = document.getElementById('new-tag-input'); 
    const addTagButton = document.getElementById('add-tag-btn');
    let currentTaskDetailsId = null;

    closeDetailsButton.addEventListener('click', () => {
        detailsModal.style.display = 'none';
    });

    // Function to render tags in the management list
    function renderTags(taskId, tags) {
        detailsTagsList.innerHTML = '';
        tags.forEach(tag => {
            const tagItem = document.createElement('span');
            tagItem.className = 'tag-management-item';
            tagItem.innerHTML = `#${tag} <button data-tag-name="${tag}" title="Remove Tag">x</button>`;
            detailsTagsList.appendChild(tagItem);
        });
        
        detailsTagsList.querySelectorAll('button').forEach(button => {
            button.addEventListener('click', () => {
                removeTag(taskId, button.dataset.tagName);
            });
        });
    }

    // AJAX function to remove a tag
    async function removeTag(taskId, tagName) {
        try {
            const response = await fetch(`/api/tags/${taskId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tag_name: tagName })
            });

            if (response.ok) {
                alert("Tag removed! Refreshing page to update filters.");
                window.location.reload();
            } else {
                alert("Failed to remove tag.");
            }
        } catch (error) {
            console.error("Error removing tag:", error);
        }
    }

    // AJAX function to add a tag (gets value from <select>)
    addTagButton.addEventListener('click', async () => {
        const tagName = newTagInput.value.trim().toLowerCase();
        
        if (!tagName || !currentTaskDetailsId) {
            alert("Please select a tag to add.");
            return;
        }

        try {
            const response = await fetch(`/api/tags/${currentTaskDetailsId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tag_name: tagName })
            });

            if (response.ok) {
                // Reset the select input after success
                newTagInput.value = ''; 
                alert("Tag added! Refreshing page to update filters.");
                window.location.reload();
            } else {
                const errorData = await response.json();
                alert(`Failed to add tag: ${errorData.message}`);
            }
        } catch (error) {
            console.error("Error adding tag:", error);
        }
    });

    // Event Delegation for clicking tasks to open details
    taskItemListener.addEventListener('click', async (event) => {
        let taskItem = event.target.closest('.task-item');
        
        if (event.target.closest('.task-actions')) {
            return;
        }

        if (taskItem && taskItem.dataset.taskId) {
            const taskId = taskItem.dataset.taskId;
            currentTaskDetailsId = taskId;

            try {
                const response = await fetch(`/api/task-details/${taskId}`);
                if (!response.ok) throw new Error('Failed to fetch task details');
                
                const task = await response.json();

                // Populate modal content
                detailsTaskText.textContent = task.task;
                detailsCreatedAt.textContent = task.created_at_display;
                detailsUpdatedAt.textContent = task.updated_at_display;
                detailsDueDateInput.value = task.due_date || ''; 
                detailsWarningMessage.textContent = task.warning_message || '';
                detailsTimeRemaining.textContent = task.time_remaining || '';
                
                // Populate Tags
                renderTags(taskId, task.tags);

                // Reset the tag select input every time the modal opens
                newTagInput.value = ''; 

                // Set form action for due date submission
                duedateForm.action = `/set-duedate/${taskId}`;
                
                // Show modal
                detailsModal.style.display = 'block';

            } catch (error) {
                console.error("Error fetching task details:", error);
                alert("Could not load task details.");
            }
        }
    });

    // Handle Due Date form submission (use AJAX)
    duedateForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        
        const formData = new FormData(duedateForm);
        const url = duedateForm.action;

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                alert("Due Date saved successfully! Page reloading to update status.");
                window.location.reload(); 
            } else {
                throw new Error('Server error saving date');
            }
        } catch (error) {
            console.error("Error setting due date:", error);
            alert("Failed to save due date.");
        }
    });

    window.addEventListener('click', (event) => {
        if (event.target == detailsModal) {
            detailsModal.style.display = 'none';
        }
    });
});