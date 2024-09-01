document.getElementById('uploadForm').onsubmit = async function(e) {
    e.preventDefault();
    let formData = new FormData(this);
    let response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });
    let result = await response.json();
    alert(result.message);
    location.reload();  
};

let selectedPhotoElement = null; 

function selectPhoto(filename, element) {
    document.getElementById('selectedPhoto').value = filename;

    if (selectedPhotoElement) {
        selectedPhotoElement.classList.remove('selected');
    }

    selectedPhotoElement = element;
    selectedPhotoElement.classList.add('selected');

    alert(`Selected photo: ${filename}`);
}

document.getElementById('actionSelect').addEventListener('change', function() {
    const action = this.value;
    const paramsInput = document.getElementById('paramsInput');

    if (action === 'delete') {
        paramsInput.value = '';  
        paramsInput.placeholder = ''; 
        paramsInput.disabled = true; 
    } else {
        paramsInput.disabled = false;
        paramsInput.placeholder = 'Params (comma-separated)';  
    }
});

document.getElementById('editForm').onsubmit = async function(e) {
    e.preventDefault();

    let selectedPhotoFilename = document.getElementById('selectedPhoto').value;
    if (!selectedPhotoFilename) {
        alert('Please select a photo to edit or delete.');
        return;
    }

    let formData = new FormData(this);
    let action = formData.get('action');

    if (action === 'delete') {
        let confirmDelete = confirm("Are you sure you want to delete this photo?");
        if (!confirmDelete) return;

        let response = await fetch(`/delete/photo/${selectedPhotoFilename}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            let result = await response.json();
            alert(result.message);
            location.reload(); 
        } else {
            let result = await response.json();
            alert('Error: ' + result.message);
        }
    } else {
        let params = formData.get('params').split(',');

        let url = `/edit/${selectedPhotoFilename}?action=${action}`;
        if (action === 'crop') {
            url += `&left=${params[0]}&top=${params[1]}&right=${params[2]}&bottom=${params[3]}`;
        } else if (action === 'rotate') {
            url += `&degrees=${params[0]}`;
        } else if (action === 'brightness') {
            url += `&factor=${params[0]}`;
        }

        let response = await fetch(url, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            let result = await response.json();
            alert(result.message);
            location.reload();  
        } else {
            let result = await response.json();
            alert('Error: ' + result.message);
        }
    }
};

document.getElementById('deleteForm').onsubmit = async function(e) {
    e.preventDefault();
    let filename = this.filename.value;
    let response = await fetch(`/delete/${filename}`, {
        method: 'DELETE'
    });
    let result = await response.json();
    alert(result.message);
};

document.getElementById('exportPdfForm').onsubmit = function(e) {
    e.preventDefault();
    let album = this.album.value;
    window.open(`/export/pdf/${album}`, '_blank');
};

document.getElementById('exportVideoForm').onsubmit = async function(e) {
    e.preventDefault();

    let formData = new FormData(this);

    let response = await fetch('/export/video', {
        method: 'POST',
        body: formData
    });

    if (response.ok) {
        let result = await response.json();
        let videoSource = document.getElementById('videoSource');
        let videoOutput = document.getElementById('videoOutput');

        videoSource.src = result.video_path;
        videoOutput.style.display = 'block';
        videoOutput.load();
        videoOutput.scrollIntoView({ behavior: 'smooth' });
    } else {
        let result = await response.json();
        alert(result.message);
    }
};

document.getElementById('deleteAlbumForm').onsubmit = async function(e) {
    e.preventDefault();
    
    let formData = new FormData(this);
    let album_name = formData.get('album_name');

    let response = await fetch('/delete/album', {
        method: 'DELETE',
        body: formData
    });
    
    if (response.ok) {
        let result = await response.json();
        alert(result.message);
        location.reload();  
    } else {
        let result = await response.json();
        alert('Error: ' + result.message);
    }
};


