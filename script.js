// Mock data
const mockPhotos = [
    { id: 1, url: 'https://placehold.co/600x400/FF6B6B/FFFFFF?text=Sunset', title: 'Beautiful Sunset', description: 'Watched the sunset at the beach', likes: 24, comments: 8, date: '2024-03-15', album: 'Vacation' },
    { id: 2, url: 'https://placehold.co/600x400/4ECDC4/FFFFFF?text=Mountain', title: 'Mountain Adventure', description: 'Hiked to the summit today', likes: 42, comments: 12, date: '2024-03-10', album: 'Adventure' }
];

const mockAlbums = [
    { id: 1, name: 'Vacation', cover: 'https://placehold.co/200x200/FF6B6B/FFFFFF?text=Vacation', photoCount: 12, date: '2024-03-15' },
    { id: 2, name: 'Adventure', cover: 'https://placehold.co/200x200/4ECDC4/FFFFFF?text=Adventure', photoCount: 8, date: '2024-03-10' }
];

// DOM Elements
const navItems = document.querySelectorAll('.nav-item');
const exploreTab = document.getElementById('exploreTab');
const albumsTab = document.getElementById('albumsTab');
const profileTab = document.getElementById('profileTab');
const photosGrid = document.getElementById('photosGrid');
const albumsGrid = document.getElementById('albumsGrid');
const uploadBtnExplore = document.getElementById('uploadBtnExplore');
const profileAvatar = document.getElementById('profileAvatar');
const logoutBtn = document.getElementById('logoutBtn');
const createAlbumBtn = document.getElementById('createAlbumBtn');
const albumName = document.getElementById('albumName');
const photoCount = document.getElementById('photoCount');
const albumCount = document.getElementById('albumCount');
const likesCount = document.getElementById('likesCount');
const changeAvatarBtn = document.getElementById('changeAvatarBtn');

// Initialization
function init() {
    setupEventListeners();
    loadPhotos();
    loadAlbums();
    updateProfileStats();
}

function setupEventListeners() {
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            activateTab(item.dataset.tab);
        });
    });

    uploadBtnExplore.addEventListener('click', () => {
        alert('Upload functionality would open here');
    });

    profileAvatar.addEventListener('click', () => {
        activateTab('profile');
    });

    logoutBtn.addEventListener('click', handleLogout);
    createAlbumBtn.addEventListener('click', createAlbum);
    changeAvatarBtn.addEventListener('click', () => {
        alert('Change avatar functionality would be implemented here');
    });
}

function activateTab(tabName) {
    exploreTab.style.display = 'none';
    albumsTab.style.display = 'none';
    profileTab.style.display = 'none';

    if (tabName === 'explore') exploreTab.style.display = 'block';
    else if (tabName === 'albums') albumsTab.style.display = 'block';
    else if (tabName === 'profile') profileTab.style.display = 'block';

    navItems.forEach(item => {
        item.classList.remove('active');
        if (item.dataset.tab === tabName) {
            item.classList.add('active');
        }
    });
}

function loadPhotos() {
    photosGrid.innerHTML = '';
    mockPhotos.forEach(photo => {
        const photoCard = document.createElement('div');
        photoCard.className = 'photo-card';
        photoCard.innerHTML = `
            <img src="${photo.url}" alt="${photo.title}" class="photo-image">
            <div class="photo-info">
                <h3 class="photo-title">${photo.title}</h3>
                <p class="photo-description">${photo.description}</p>
                <div class="photo-meta">
                    <span>${photo.date}</span>
                    <span>${photo.album}</span>
                </div>
            </div>
            <div class="photo-actions">
                <button class="action-btn">${photo.likes}</button>
                <button class="action-btn">${photo.comments}</button>
                <button class="action-btn">Share</button>
            </div>
        `;
        photosGrid.appendChild(photoCard);
    });
}

function loadAlbums() {
    albumsGrid.innerHTML = '';
    mockAlbums.forEach(album => {
        const albumCard = document.createElement('div');
        albumCard.className = 'album-card';
        albumCard.innerHTML = `
            <img src="${album.cover}" alt="${album.name}" class="album-image">
            <div class="album-info">
                <h3 class="album-title">${album.name}</h3>
                <div class="album-meta">
                    <span>${album.photoCount} photos</span>
                    <span>${album.date}</span>
                </div>
            </div>
        `;
        albumsGrid.appendChild(albumCard);
    });
}

function createAlbum() {
    const name = albumName.value.trim();
    if (!name) {
        alert('Please enter an album name');
        return;
    }
    alert(`Album "${name}" created successfully!`);
    albumName.value = '';
}

function updateProfileStats() {
    photoCount.textContent = mockPhotos.length;
    albumCount.textContent = mockAlbums.length;
    const totalLikes = mockPhotos.reduce((sum, photo) => sum + photo.likes, 0);
    likesCount.textContent = totalLikes;
}

function handleLogout() {
    if (confirm('Are you sure you want to log out?')) {
        alert('Logged out successfully!');
    }
}

document.addEventListener('DOMContentLoaded', init);