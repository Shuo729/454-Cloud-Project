let db;
const request = indexedDB.open("CloudSnapDB", 1);

request.onupgradeneeded = function (event) {
    db = event.target.result;
    if (!db.objectStoreNames.contains("photos")) {
        db.createObjectStore("photos", { keyPath: "id" });
    }
};

request.onsuccess = function (event) {
    db = event.target.result;
};

request.onerror = function (event) {
    console.error("IndexedDB error:", event);
};


let albums = [];

function saveAlbums() {
    localStorage.setItem("cloudsnap_albums", JSON.stringify(albums));
}

document.addEventListener("DOMContentLoaded", () => {
    const saved = localStorage.getItem("cloudsnap_albums");
    if (saved) {
        albums = JSON.parse(saved);

        
        albums.forEach(a => {
            if (!Array.isArray(a.photos)) {
                a.photos = [];
            }
        });
    }

    renderAlbums();

    // customer is able to create an album
    const form = document.querySelector(".album-create");

    form.addEventListener("submit", (event) => {
        event.preventDefault();

        const albumName = document.getElementById("albumName").value.trim();
        if (!albumName) return;

        const newAlbum = {
            id: Date.now(),
            name: albumName,
            photos: []
        };

        albums.push(newAlbum);
        saveAlbums();
        renderAlbums();

        document.getElementById("albumName").value = "";
    });
});


function renderAlbums() {
    const grid = document.getElementById("albumsGrid");
    grid.innerHTML = "";
    //message you have not created albums appears if no albums are on page
    if (albums.length === 0) {
        grid.innerHTML = `<p>You haven't created any albums yet.</p>`;
        return;
    }
    
    albums.forEach(album => {
        const card = document.createElement("div");
        card.classList.add("album-card");

        card.innerHTML = `
            <button class="delete-album-simple">✖</button>

            <div class="album-info">
                <div class="album-title">${album.name}</div>
                <div class="album-count">${album.photos.length} / 10 photos</div>
                <button class="upload-photo-btn">Add Photo</button>
                <button class="view-photos-btn">View Photos</button>
            </div>
        `;

        const realAlbum = albums.find(a => a.id === album.id);

        
        
        //let them be able to upload photo inside albums
        card.querySelector(".upload-photo-btn").addEventListener("click", () => {

            if (realAlbum.photos.length >= 10) {
                alert("This album already has 10 photos.");
                return;
            }

            const input = document.createElement("input");
            input.type = "file";
            input.accept = "image/*";

            input.onchange = () => {
                const file = input.files[0];
                if (!file) return;

                const id = Date.now() + Math.random();

                
                const tx = db.transaction(["photos"], "readwrite");
                const store = tx.objectStore("photos");
                store.put({ id, file });

                tx.oncomplete = () => {
                    realAlbum.photos.push(id);
                    saveAlbums();
                    renderAlbums();
                };
            };

            input.click();
        });

        
        
        
        card.querySelector(".view-photos-btn").addEventListener("click", () => {
            openAlbumViewer(realAlbum.id);
        });

        
        
        //if person wants to delete album
        card.querySelector(".delete-album-simple").addEventListener("click", () => {
            if (confirm(`Delete "${realAlbum.name}"?`)) {

                // Delete photos from IndexedDB
                realAlbum.photos.forEach(photoId => {
                    const tx = db.transaction(["photos"], "readwrite");
                    const store = tx.objectStore("photos");
                    store.delete(photoId);
                });

                // Remove album
                albums = albums.filter(a => a.id !== realAlbum.id);
                saveAlbums();
                renderAlbums();
            }
        });

        grid.appendChild(card);
    });
}


//be able to view the photots
function openAlbumViewer(albumId) {
    const album = albums.find(a => a.id === albumId);
    if (!album) return;

    const modal = document.getElementById("photoModal");
    const modalName = document.getElementById("modalAlbumName");
    const modalPhotos = document.getElementById("modalPhotos");

    modalName.textContent = album.name;
    modalPhotos.innerHTML = "";

    
    album.photos.forEach(photoId => {
        const tx = db.transaction(["photos"], "readonly");
        const store = tx.objectStore("photos");
        const req = store.get(photoId);

        req.onsuccess = function (event) {
            const record = event.target.result;
            if (!record) return;

            const url = URL.createObjectURL(record.file);

            const img = document.createElement("img");
            img.src = url;
            modalPhotos.appendChild(img);
        };
    });

    modal.style.display = "flex";

    document.querySelector(".close-modal").onclick = () => {
        modal.style.display = "none";
    };

    window.onclick = (e) => {
        if (e.target === modal) {
            modal.style.display = "none";
        }
    };
}
