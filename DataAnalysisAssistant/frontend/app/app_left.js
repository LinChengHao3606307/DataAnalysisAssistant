// File tree view initialization
function displayTree(tree, container, currentPath = 'tree') {
    const udiv = document.createElement('div');
    udiv.classList.add('udiv');

    for (const [name, contents] of Object.entries(tree)) {
        const isFile = /^[^\.]+\..+$/.test(name);
        const elementPath = currentPath + (isFile ? `/${name}` : `/${name}/`);

        const elementDiv = document.createElement('div');
        elementDiv.id = elementPath;
        elementDiv.draggable = true;

        if (!isFile) {
            // Directory handling
            elementDiv.classList.add('sub_files_div');

            const dirDiv = document.createElement('div');
            dirDiv.classList.add('dir_name_div');
            dirDiv.id = elementPath;
            dirDiv.draggable = true;

            const arrow = document.createElement('span');
            arrow.classList.add('arrow');
            arrow.textContent = '▼';

            dirDiv.appendChild(arrow);
            dirDiv.appendChild(document.createTextNode(name));
            udiv.appendChild(dirDiv);

            // Recursively handle sub-content
            const subContainer = document.createElement('div');
            subContainer.classList.add('container_div');
            subContainer.id = elementPath + 'container';
            subContainer.style.display = 'block';

            displayTree(contents, subContainer, elementPath.slice(0, -1));
            elementDiv.appendChild(subContainer);

            arrow.addEventListener('click', () => {
                const isVisible = subContainer.style.display === 'block';
                subContainer.style.display = isVisible ? 'none' : 'block';
                arrow.textContent = isVisible ? '▶' : '▼';
            });
        } else {
            // File handling
            elementDiv.classList.add('file_name_div');
            elementDiv.appendChild(document.createTextNode(name));
        }

        udiv.appendChild(elementDiv);
    }

    container.appendChild(udiv);
}

// File drag and drop operations
function isValidDrop(dragged, target) {
    const draggedPath = dragged.id;
    const targetPath = target.id;

    if (draggedPath === targetPath) return false;
    if (!targetPath.endsWith('/')) return false;
    if (targetPath.startsWith(draggedPath + '/')) return false;

    return true;
}

// File explorer functionality
function initializeFileExplorer() {
    const fileExplorer = document.getElementById('file-explorer');

    // Add drag and drop event listeners for the file explorer container
    fileExplorer.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    });

    fileExplorer.addEventListener('drop', (e) => {
        e.preventDefault();
        const draggedId = e.dataTransfer.getData('text/plain');
        const draggedElement = document.getElementById(draggedId);

        if (draggedElement && draggedElement.classList.contains('file_name_div')) {
            // Create a new file explorer item
            const fileName = draggedElement.textContent;
            const fileItem = createFileExplorerItem(fileName, draggedId);
            fileExplorer.appendChild(fileItem);

            // Send message to backend about the file being added to explorer
            window.ws.send(JSON.stringify({
                type: 'file-add-to-explorer',
                path: draggedId
            }));
        }
    });
}

function createFileExplorerItem(fileName, originalPath) {
    const item = document.createElement('div');
    item.classList.add('file-explorer-item');
    item.textContent = fileName;
    item.draggable = true;
    item.dataset.originalPath = originalPath;

    // Add drag and drop event listeners for the file explorer item
    item.addEventListener('dragstart', (e) => {
        item.classList.add('dragging');
        e.dataTransfer.setData('text/plain', item.dataset.originalPath);
        e.dataTransfer.setData('application/explorer-item', 'true');
    });

    item.addEventListener('dragend', () => {
        item.classList.remove('dragging');
    });

    return item;
}

// Modify the existing setupDragAndDrop function to handle file explorer items
function setupDragAndDrop() {
    let ghostElement = null;
    let draggedElement = null;

    const draggableElements = document.querySelectorAll('.dir_name_div, .file_name_div');

    draggableElements.forEach(element => {
        element.addEventListener('mousedown', function(e) {
            if (e.button === 0) draggedElement = this;
        });

        element.addEventListener('dragstart', function(e) {
            ghostElement = this.cloneNode(true);
            ghostElement.classList.add('ghost');
            ghostElement.style.width = this.offsetWidth + 'px';
            ghostElement.style.height = this.offsetHeight + 'px';

            const rect = this.getBoundingClientRect();
            ghostElement.style.left = rect.left + 'px';
            ghostElement.style.top = rect.top + 'px';
            document.body.appendChild(ghostElement);

            this.classList.add('dragging-source');
            e.dataTransfer.setData('text/plain', this.id);
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setDragImage(new Image(), 0, 0);
        });

        element.addEventListener('drag', function(e) {
            if (ghostElement) {
                ghostElement.style.left = e.clientX + 10 + 'px';
                ghostElement.style.top = e.clientY + 10 + 'px';
            }
        });

        element.addEventListener('dragend', function() {
            if (ghostElement) {
                document.body.removeChild(ghostElement);
                ghostElement = null;
            }
            this.classList.remove('dragging-source');
            draggedElement = null;
        });
    });

    const dropTargets = document.querySelectorAll('.dir_name_div');

    dropTargets.forEach(target => {
        target.addEventListener('dragenter', function(e) {
            e.preventDefault();
            this.classList.add('drop-target');
        });

        target.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        });

        target.addEventListener('dragleave', function() {
            this.classList.remove('drop-target');
        });

        target.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drop-target');

            const draggedId = e.dataTransfer.getData('text/plain');
            const isFromExplorer = e.dataTransfer.getData('application/explorer-item') === 'true';
            const draggedElement = document.getElementById(draggedId);

            if (isFromExplorer) {
                // Handle drop from file explorer to file tree
                window.ws.send(JSON.stringify({
                    type: "file-move",
                    from: draggedId,
                    to: this.id,
                    fromExplorer: true
                }));

                // Remove the item from file explorer
                const explorerItem = document.querySelector(`.file-explorer-item[data-original-path="${draggedId}"]`);
                if (explorerItem) {
                    explorerItem.remove();
                }
            } else if (draggedElement && isValidDrop(draggedElement, this)) {
                // Handle normal file tree drag and drop
                window.ws.send(JSON.stringify({
                    type: "file-move",
                    from: draggedId,
                    to: this.id
                }));
            }
        });
    });
}

// File selection management
let currentSelectedFileId = null;

function setupFileSelection() {
    const downloadableElements = document.querySelectorAll('.dir_name_div, .file_name_div');

    downloadableElements.forEach(element => {
        element.addEventListener('click', () => {
            const fileId = element.id;

            if (currentSelectedFileId === fileId) {
                window.ws.send(JSON.stringify({
                    type: "file-unchoose",
                    id: fileId
                }));
            } else {
                window.ws.send(JSON.stringify({
                    type: "file-choose",
                    id: fileId
                }));
            }
        });
    });
}

function handleFileSelection(msg) {
    if (currentSelectedFileId) {
        const prevElement = document.getElementById(currentSelectedFileId);
        if (prevElement) {
            prevElement.style.border = currentSelectedFileId.includes('.')
                ? '1px solid #0000FF'
                : '1px solid #FF0000';
        }
    }

    if (msg.action === "selected") {
        currentSelectedFileId = msg.id;
        const element = document.getElementById(msg.id);
        if (element) element.style.border = '2px solid #00FF00';
    } else {
        currentSelectedFileId = null;
    }
}

// File upload/download handling
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

function sendFile(file) {
    dropZone.innerHTML = `Uploading: ${file.name}...`;
    const fileId = Date.now();

    window.ws.send(JSON.stringify({
        type: 'file-upload-start',
        name: file.name,
        size: file.size,
        id: fileId
    }));

    const chunkSize = 64 * 1024;
    let offset = 0;

    const reader = new FileReader();
    reader.onload = (e) => {
        window.ws.send(e.target.result);
        offset += e.target.result.byteLength;

        window.ws.send(JSON.stringify({
            type: 'file-progress',
            id: fileId,
            loaded: offset,
            total: file.size
        }));

        if (offset < file.size) {
            readNextChunk();
        } else {
            window.ws.send(JSON.stringify({
                type: 'file-upload-end',
                id: fileId
            }));
        }
    };

    function readNextChunk() {
        const chunk = file.slice(offset, offset + chunkSize);
        reader.readAsArrayBuffer(chunk);
    }

    readNextChunk();
}

dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) sendFile(e.target.files[0]);
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'blue';
});

dropZone.addEventListener('dragleave', (e) => {
    e.currentTarget.style.borderColor = '#ccc';
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#ccc';

    if (e.dataTransfer.files.length) {
        sendFile(e.dataTransfer.files[0]);
    }
});

let receivedChunks = [];

function handleFileChunk(msg) {
    const byteCharacters = atob(msg.chunk);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    receivedChunks.push(byteArray);

    if (msg.isLastChunk) {
        const blob = new Blob(receivedChunks, { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = msg.fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        receivedChunks = [];
    }
}

// File operations
document.getElementById('download-btn').addEventListener('click', function() {
    if (!currentSelectedFileId) return;
    window.ws.send(JSON.stringify({
        type: "file-download",
        path: currentSelectedFileId,
    }));
});

document.getElementById('delete-btn').addEventListener('click', function() {
    if (!currentSelectedFileId) return;
    window.ws.send(JSON.stringify({
        type: "file-delete",
        path: currentSelectedFileId,
    }));
});

// Folder creation and renaming
document.getElementById('create-btn').addEventListener('click', function() {
    const modal = document.getElementById('create-folder-modal');
    const title = modal.querySelector('h3');
    const input = document.getElementById('new-folder-name');

    title.textContent = "Create New Folder";
    input.placeholder = "Enter folder name";
    modal.style.display = 'flex';
    input.value = '';
    input.focus();
});

document.getElementById('rename-btn').addEventListener('click', function() {
    if (!currentSelectedFileId) {
        const hint = document.getElementById('rename-hint');
        hint.style.display = 'block';
        setTimeout(() => hint.style.display = 'none', 1000);
        return;
    }

    const isFile = currentSelectedFileId.includes('.');
    const modal = document.getElementById('create-folder-modal');
    const title = modal.querySelector('h3');
    const input = document.getElementById('new-folder-name');

    title.textContent = `Rename ${isFile ? 'File' : 'Folder'}`;
    input.placeholder = `Enter new ${isFile ? 'file' : 'folder'} name`;
    modal.style.display = 'flex';
    input.value = currentSelectedFileId.split('/').pop();
    input.focus();
});

document.getElementById('cancel-create-btn').addEventListener('click', function() {
    document.getElementById('create-folder-modal').style.display = 'none';
});

document.getElementById('confirm-create-btn').addEventListener('click', function() {
    const newName = document.getElementById('new-folder-name').value.trim();
    const modal = document.getElementById('create-folder-modal');
    const isRenameOperation = modal.querySelector('h3').textContent.includes('Rename');

    if (!isValidName(newName, isRenameOperation ? currentSelectedFileId.includes('.') : false)) {
        alert(`Invalid ${isRenameOperation ? 'name' : 'folder name'}!\nCannot contain: \\ / : * ? " < > |`);
        return;
    }

    if (isRenameOperation) {
        window.ws.send(JSON.stringify({
            type: "file-rename",
            name: newName
        }));
    } else {
        window.ws.send(JSON.stringify({
            type: "file-create",
            name: newName
        }));
    }

    modal.style.display = 'none';
});

function isValidName(name, isFile) {
    if (!name || !name.trim()) return false;
    const illegalChars = /[\\/:*?"<>|]/;
    if (illegalChars.test(name)) return false;

    if (isFile) {
        if (!name.includes('.')) return false;
        if (name.endsWith('.')) return false;
    } else {
        if (name.startsWith('.')) return false;
        if (name.endsWith('.')) return false;
    }

    return true;
}

// GPU monitoring
function updateGpuUsage(msg) {
    const percentage = Math.round(msg.percentage_full * 100);
    const bar = document.getElementById('gpu-usage-bar');
    const text = document.getElementById('gpu-usage-text');

    bar.style.width = `${percentage}%`;
    text.textContent = `${percentage}%`;

    if (percentage > 85) {
        bar.style.background = '#e74c3c';
    } else if (percentage > 60) {
        bar.style.background = '#f1c40f';
    } else {
        bar.style.background = '#2ecc71';
    }

    if (msg.gpu_model) {
        document.getElementById('gpu-model').textContent = msg.gpu_model;
    }
}

// Event listeners for WebSocket messages
window.addEventListener('left-panel-event', (e) => {
    const msg = e.detail;

    switch(msg.type) {
        case "file-display_tree":
            const treeContainer = document.getElementById('file tree root');
            treeContainer.innerHTML = '';
            displayTree(msg.tree, treeContainer);
            setupDragAndDrop();
            setupFileSelection();
            initializeFileExplorer(); // Initialize file explorer
            break;

        case "file-current-selection":
            handleFileSelection(msg);
            break;

        case "file-upload-end":
            dropZone.innerHTML = `Drop files here or <u>click to select</u>`;
            break;

        case "file-chunk":
            handleFileChunk(msg);
            break;

        case "gpu-usage":
            updateGpuUsage(msg);
            break;

        case "file-explorer-update":
            // Handle updates to the file explorer from the backend
            const fileExplorer = document.getElementById('file-explorer');
            fileExplorer.innerHTML = '';
            msg.files.forEach(file => {
                const fileItem = createFileExplorerItem(file.name, file.path);
                fileExplorer.appendChild(fileItem);
            });
            break;
    }
});