document.addEventListener('DOMContentLoaded', () => {
    const chooseButton = document.getElementById('choose-button');
    const fileInput = document.getElementById('file-input');
    const statusMessage = document.getElementById('diet');

    const modal = document.getElementById('preview-modal');
    const modalPreview = document.getElementById('modal-image-preview');
    const modalConfirmBtn = document.getElementById('modal-confirm-btn');
    const modalChangeBtn = document.getElementById('modal-change-btn');
    const modalCloseBtn = document.getElementById('modal-close-btn');

    if (chooseButton) {
        chooseButton.addEventListener('click', () => {
            fileInput.click();
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', ViewModal);
    }

    if (modalChangeBtn) {
        modalChangeBtn.addEventListener('click', () => {
            closeModal();
            fileInput.click();
        });
    }
    
    if (modalConfirmBtn) {
        modalConfirmBtn.addEventListener('click', () => {
            sendPhoto();
            closeModal();
        });
    }

    function closeModal() {
        modal.classList.add('hidden');
        fileInput.value = ""; // Reset file input
    }

    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closeModal);
    }

    if (modal) {
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                closeModal();
            }
        });
    }

    function ViewModal() {
        const file = fileInput.files[0];
        if (file) {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                modalPreview.src = e.target.result;
                modal.classList.remove('hidden');
            };
            
            reader.readAsDataURL(file);
        }
    }

    function sendPhoto() {
        if (!fileInput.files || fileInput.files.length === 0) {
            alert('Please choose a file first!');
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        statusMessage.innerHTML = '<p>Uploading...</p>';

        fetch('/upload-image', { 
            method: 'POST',
            body: formData
        })
        .then(response => response.json()) 
        .then(data => {
            if (data.url) { 
                window.location.href = '/profile';
            } else {
                statusMessage.innerHTML = `<p>Upload failed: ${data.error || 'Unknown error'}</p>`;
                alert('Upload failed: ' + (data.error || 'Unknown error'));
            }
        })
        .catch((error) => {
            console.error('Upload error:', error);
            statusMessage.innerHTML = `<p>Upload failed: ${error}</p>`;
            alert('Upload failed: ' + error);
        });
    }
});