document.addEventListener('DOMContentLoaded', () => {
    
    const albumCountElement = document.getElementById('album-stat-count');
    if (albumCountElement) {
        // Read the same storage key used in albums.js
        const savedAlbums = localStorage.getItem("cloudsnap_albums");
        if (savedAlbums) {
            try {
                const albums = JSON.parse(savedAlbums);
                // Update the number on the profile page
                albumCountElement.textContent = albums.length;
            } catch (e) {
                console.error("Error reading albums count", e);
            }
        }
    }

    /* --- AVATAR UPLOAD --- */
    const changeAvatarBtn = document.getElementById('change-avatar-btn');
    const avatarInput = document.getElementById('avatar-input');
    const avatarImage = document.getElementById('avatar-image');

    changeAvatarBtn.addEventListener('click', () => {
        avatarInput.click();
    });

    avatarInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            changeAvatarBtn.textContent = "Uploading...";
            changeAvatarBtn.disabled = true;

            const response = await fetch('/api/upload-avatar', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Upload failed');

            const data = await response.json();
            if (data.success) {
                window.location.reload(); 
            } else {
                alert(data.error || 'Failed to upload avatar');
            }

        } catch (error) {
            console.error(error);
            alert('An error occurred while uploading the avatar.');
        } finally {
            changeAvatarBtn.textContent = "Change Avatar";
            changeAvatarBtn.disabled = false;
        }
    });

    /* --- PASSWORD UPDATE --- */
    const settingsForm = document.getElementById('settings-form');

    settingsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const passwordInput = document.getElementById('password');
        const password = passwordInput.value.trim();

        if (!password) {
            alert("Please enter a new password to save changes.");
            return;
        }

        try {
            const response = await fetch('/api/update-profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: password })
            });

            const data = await response.json();
            
            if (data.success) {
                alert("Password updated successfully!");
                passwordInput.value = '';
            } else {
                alert(data.error || "Failed to update profile.");
            }

        } catch (error) {
            console.error(error);
            alert("An error occurred. Please try again.");
        }
    });
});