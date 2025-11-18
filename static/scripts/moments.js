document.addEventListener('DOMContentLoaded', () => {
    
    // Get elements from moments.html
    const photoInput = document.getElementById('moment-photo');
    
    // Get elements from the pasted modal HTML
    const modal = document.getElementById('preview-modal');
    const previewImage = document.getElementById('modal-image-preview');
    const closeBtn = document.getElementById('modal-close-btn');
    const changeBtn = document.getElementById('modal-change-btn');
    const confirmBtn = document.getElementById('modal-confirm-btn');

    // Open modal when a file is selected
    photoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            
            reader.onload = (event) => {
                previewImage.src = event.target.result;
                modal.classList.remove('hidden');
            };
            
            reader.readAsDataURL(file);
        }
    });

    // Function to close modal and clear the file selection
    const cancelPhotoSelection = () => {
        photoInput.value = null; 
        previewImage.src = ''; 
        modal.classList.add('hidden');
    };

    closeBtn.addEventListener('click', cancelPhotoSelection);
    changeBtn.addEventListener('click', cancelPhotoSelection);

    // Close modal on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            cancelPhotoSelection();
        }
    });

    // Confirm the photo (just close the modal, keep the file)
    confirmBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    const createMomentForm = document.getElementById('create-moment-form');
    const momentFeedContainer = document.getElementById('moment-feed-container');

    /* --- FUNCTION TO LOAD ALL MOMENTS --- */
    const loadMoments = async () => {
        try {
            const response = await fetch('/api/moments');
            if (!response.ok) throw new Error('Failed to fetch moments');
            
            const moments = await response.json();
            momentFeedContainer.innerHTML = '';
            
            if (moments.length === 0) {
                momentFeedContainer.innerHTML = '<p>No moments yet. Be the first to share!</p>';
            } else {
                moments.forEach(moment => {
                    const momentElement = createMomentElement(moment);
                    momentFeedContainer.appendChild(momentElement);
                });
            }

        } catch (error) {
            console.error('Error loading moments:', error);
            momentFeedContainer.innerHTML = '<p>Could not load moments. Please try again later.</p>';
        }
    };

    /* --- FUNCTION TO CREATE HTML FOR A SINGLE MOMENT --- */
    const createMomentElement = (moment) => {
        const momentDiv = document.createElement('div');
        momentDiv.className = 'moment';
        momentDiv.dataset.momentId = moment.id;

        const timestamp = new Date(moment.timestamp).toLocaleString();
        
        let photoHtml = '';
        if (moment.photo_url) {
            photoHtml = `<img src="${moment.photo_url}" alt="Moment Photo">`;
        }

        let commentsHtml = '';
        moment.comments.forEach(comment => {
            commentsHtml += `
                <div class="comment" data-comment-id="${comment.id}">
                    <span class="comment-author">${comment.author_username}:</span>
                    <span>${comment.text}</span>
                </div>
            `;
        });

        const likeButtonClass = moment.is_liked_by_user ? 'like-btn liked' : 'like-btn';

        momentDiv.innerHTML = `
            <div class="moment-header">${moment.author_username}</div>
            <div class="moment-timestamp">${timestamp}</div>
            <div class="moment-body">
                <p>${moment.text}</p>
                ${photoHtml}
            </div>
            <div class="moment-actions">
                <span class="${likeButtonClass}" data-moment-id="${moment.id}">
                    Like (${moment.like_count})
                </span>
                <span>Comment</span>
            </div>
            <div class="comments-section" data-moment-id="${moment.id}">
                ${commentsHtml}
                <form class="comment-form" data-moment-id="${moment.id}">
                    <input type="text" placeholder="Write a comment..." required>
                    <button type="submit">Post</button>
                </form>
            </div>
        `;
        return momentDiv;
    };

    /* --- EVENT LISTENER FOR CREATING A NEW MOMENT --- */
    if (createMomentForm) {
        createMomentForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const text = document.getElementById('moment-text').value;
            const fileInput = document.getElementById('moment-photo');
            
            const formData = new FormData();
            formData.append('text', text);
            if (fileInput.files.length > 0) {
                formData.append('file', fileInput.files[0]);
            }

            try {
                const response = await fetch('/api/moments', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to create moment');
                }

                const newMoment = await response.json();
                const momentElement = createMomentElement(newMoment);
                if (momentFeedContainer.querySelector('p')) {
                    momentFeedContainer.innerHTML = '';
                }
                
                momentFeedContainer.prepend(momentElement);

                createMomentForm.reset();

            } catch (error) {
                console.error('Error creating moment:', error);
                alert(`Error: ${error.message}`);
            }
        });
    }

    /* --- EVENT LISTENER FOR LIKES AND COMMENTS --- */
    momentFeedContainer.addEventListener('click', async (e) => {
        
        // Handle Like Button Clicks
        if (e.target.classList.contains('like-btn')) {
            const likeButton = e.target;
            const momentId = likeButton.dataset.momentId;
            
            try {
                const response = await fetch(`/api/moments/${momentId}/like`, {
                    method: 'POST'
                });
                
                if (!response.ok) throw new Error('Like request failed');
                
                const data = await response.json();
                
                // Update the button text and class
                likeButton.textContent = `Like (${data.like_count})`;
                if (data.action === 'liked') {
                    likeButton.classList.add('liked');
                } else {
                    likeButton.classList.remove('liked');
                }

            } catch (error) {
                console.error('Error liking moment:', error);
            }
        }
    });

    momentFeedContainer.addEventListener('submit', async (e) => {
        // Handle Comment Form Submissions
        if (e.target.classList.contains('comment-form')) {
            e.preventDefault();
            const commentForm = e.target;
            const momentId = commentForm.dataset.momentId;
            const commentInput = commentForm.querySelector('input[type="text"]');
            const text = commentInput.value;

            if (!text) return;

            try {
                const response = await fetch(`/api/moments/${momentId}/comment`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                });

                if (!response.ok) throw new Error('Comment request failed');
                
                const data = await response.json();
                
                // Add the new comment to the UI
                const newComment = data.comment;
                const commentElement = document.createElement('div');
                commentElement.className = 'comment';
                commentElement.dataset.commentId = newComment.id;
                commentElement.innerHTML = `
                    <span class="comment-author">${newComment.author_username}:</span>
                    <span>${newComment.text}</span>
                `;
                
                const commentsSection = commentForm.closest('.comments-section');
                commentsSection.insertBefore(commentElement, commentForm);
                
                commentInput.value = '';

            } catch (error) {
                console.error('Error posting comment:', error);
            }
        }
    });
    
    loadMoments();
});