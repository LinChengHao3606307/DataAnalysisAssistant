// File tree view initialization
console.log('app_left.js loaded successfully!');

function displayTree(tree, container, currentPath = 'tree') {
    // 清空容器
    container.innerHTML = '';
    
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
            arrow.textContent = 'v';

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

            // 不再在这里添加事件监听器，使用事件委托
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
    // 添加导航按钮事件监听器
    const backBtn = document.querySelector('.to_mother_dir-btn');
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            window.ws.send(JSON.stringify({
                type: 'file-explorer-to_parent_dir'
            }));
    });
}
}

// 显示文件浏览器内容
function displayFileExplorer(items, currentPath) {
    console.log(`items: ${items}`)
    console.log(`currentPath: ${currentPath}`)
    const fileExplorerWindow = document.getElementById('file-explorer-window');
    const currentPathElement = document.querySelector('.current-path');
    
    // 更新当前路径显示
    currentPathElement.textContent = currentPath
    
    // 清空现有内容
    fileExplorerWindow.innerHTML = '';
    
    // 如果没有项目，显示空状态
    if (!items || items.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.style.textAlign = 'center';
        emptyState.style.padding = '20px';
        emptyState.style.color = '#666';
        emptyState.textContent = 'No files in this directory';
        fileExplorerWindow.appendChild(emptyState);
        return;
    }
    
    // 创建简单的文件列表
    items.forEach(item => {
        const isFile = /^[^\.]+\..+$/.test(item);

        const elementDiv = document.createElement('div');
        elementDiv.id = item;
        elementDiv.draggable = true;
        const name = item.split('/').pop();
        if (!isFile) {
            // Directory handling
            elementDiv.classList.add('dir_name_div');
            
            const arrow = document.createElement('span');
            arrow.classList.add('arrow');
            arrow.textContent = '>'; // 表示可以进入的文件夹

            elementDiv.appendChild(arrow);
            elementDiv.appendChild(document.createTextNode(name));
        } else {
            // File handling
            elementDiv.classList.add('file_name_div');

            elementDiv.appendChild(document.createTextNode(name));
        }

        fileExplorerWindow.appendChild(elementDiv);
    });
}

// 内部元素的逻辑---------------------------------------------------------------------------------------------------------
// Event delegation for drag and drop operations
    let ghostElement = null;
    let draggedElement = null;

function setupEventDelegation() {
    const treeContainer = document.getElementById('file tree root');
    const fileExplorerWindow = document.getElementById('file-explorer-window');
    
    // 检查是否已经设置过事件委托
    if (window._eventDelegationSetup) {
        console.log('Event delegation already set up, skipping...');
        return; // 已经设置过了
    }
    
    // 1. 拖拽活动主角的逻辑
    // 1.1. 拖拽开始
    function handleDragStart(e) {
        draggedElement = e.target;
            
        console.log('Drag start event triggered');
        console.log('Dragged element ID:', e.target.id);
        console.log('Dragged element class:', e.target.className);
        
        ghostElement = e.target.cloneNode(true);
            ghostElement.classList.add('ghost');
        ghostElement.style.width = e.target.offsetWidth + 'px';
        ghostElement.style.height = e.target.offsetHeight + 'px';

        const rect = e.target.getBoundingClientRect();
            ghostElement.style.left = rect.left + 'px';
            ghostElement.style.top = rect.top + 'px';
            document.body.appendChild(ghostElement);

        e.target.classList.add('dragging-source');
        e.dataTransfer.setData('text/plain', e.target.id);
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setDragImage(new Image(), 0, 0);
    }
    treeContainer.addEventListener('dragstart', (e) => {
        handleDragStart(e);
        });
    fileExplorerWindow.addEventListener('dragstart', (e) => {
        handleDragStart(e);
    });

    // 1.2. 拖拽过程
    function handleDrag(e) {
            if (ghostElement) {
                ghostElement.style.left = e.clientX + 10 + 'px';
                ghostElement.style.top = e.clientY + 10 + 'px';
            }
    }
    treeContainer.addEventListener('drag', (e) => {
        handleDrag(e);
        });
    fileExplorerWindow.addEventListener('drag', (e) => {
        handleDrag(e);
    });

    // 1.3. 拖拽结束
    function handleDragEnd(e) {
            if (ghostElement) {
                document.body.removeChild(ghostElement);
                ghostElement = null;
            }
        if (draggedElement) {
            draggedElement.classList.remove('dragging-source');
            draggedElement = null;
        }
    }
    treeContainer.addEventListener('dragend', (e) => {
        handleDragEnd(e);
    });
    fileExplorerWindow.addEventListener('dragend', (e) => {
        handleDragEnd(e);
    });

    // 2. 被活动主角触及的元素的逻辑
    // 2.1. 主角进入的元素的逻辑
    function handleDragEnter(e) {
        if (e.target.matches('.dir_name_div')) {
            e.preventDefault();
            e.target.classList.add('drop-target');
        }
    }
    treeContainer.addEventListener('dragenter', (e) => {
        handleDragEnter(e);
    });
    fileExplorerWindow.addEventListener('dragenter', (e) => {
        handleDragEnter(e);
    });

    // 2.2. 主角悬停的元素的逻辑
    function handleDragOver(e) {
        if (e.target.matches('.dir_name_div')) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        } else if (e.target.closest('#file-explorer-window') || e.target.closest('#file-explorer')) {
            // 拖拽到文件浏览器区域
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        }
    }
    treeContainer.addEventListener('dragover', (e) => {
        handleDragOver(e);
    });
    fileExplorerWindow.addEventListener('dragover', (e) => {
        handleDragOver(e);
    });

    // 2.3. 被主角离开的元素的逻辑
    function handleDragLeave(e) {
        if (e.target.matches('.dir_name_div')) {
            e.target.classList.remove('drop-target');
        }
    }
    treeContainer.addEventListener('dragleave', (e) => {
        handleDragLeave(e);
    });
    fileExplorerWindow.addEventListener('dragleave', (e) => {
        handleDragLeave(e);
    });

    // 2.4. 主角放置的元素的逻辑
    function handleDrop(e) {
            e.preventDefault();

            const draggedId = e.dataTransfer.getData('text/plain');

        if (e.target.matches('.dir_name_div')) {
            // 拖拽到文件夹
            e.target.classList.remove('drop-target');
                window.ws.send(JSON.stringify({
                    type: "file-move",
                    from: draggedId,
                to: e.target.id
            }));
        } else if (e.target.closest('#file-explorer-window') || e.target.closest('#file-explorer')) {
            // 拖拽到文件浏览器区域
            console.log('Drop event triggered');
            console.log('Dragged ID:', draggedId);
            
            // 获取当前explorer的路径
            const currentPathElement = document.querySelector('.current-path');
            const currentExplorerPath = currentPathElement ? currentPathElement.textContent : 'expl/';
            
            console.log('Current explorer path:', currentExplorerPath);
            
            // 发送文件移动消息到后端
                window.ws.send(JSON.stringify({
                type: 'file-move',
                    from: draggedId,
                to: currentExplorerPath
                }));
            }
    }
    treeContainer.addEventListener('drop', (e) => {
        handleDrop(e);
    });
    fileExplorerWindow.addEventListener('drop', (e) => {
        handleDrop(e);
    });

    // 3. 元素被点击的逻辑
    function handleClick(e) {
        if (e.target.matches('.dir_name_div, .file_name_div')) {
            const fileId = e.target.id;
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
        } else if (e.target.matches('.arrow')) {
            const dirDiv = e.target.closest('.dir_name_div');
            if (dirDiv) {
                const ddid = dirDiv.id;
                if (ddid.startsWith('expl/')) {
                    window.ws.send(JSON.stringify({
                        type: "file-explorer-enter-dir",
                        dir_name: ddid
                    }));
}
                else{
                    const containerId = ddid + 'container';
                    const subContainer = document.getElementById(containerId);
                    if (subContainer) {
                        const isVisible = subContainer.style.display === 'block';
                        subContainer.style.display = isVisible ? 'none' : 'block';
                        e.target.textContent = isVisible ? '>' : 'v';
                    }
                }
            }
        }
    }
    treeContainer.addEventListener('click', (e) => {
        handleClick(e);
    });
    fileExplorerWindow.addEventListener('click', (e) => {
        handleClick(e);
    });

    // 标记已设置事件委托
    window._eventDelegationSetup = true;
    console.log('Event delegation set up successfully');
}

// File selection management
let currentSelectedFileId = null;

function handleFileSelection(msg) {
    if (currentSelectedFileId) {
        const prevElement = document.getElementById(currentSelectedFileId);
        if (prevElement) {
            prevElement.style.border = currentSelectedFileId.includes('.')
                ? '1px solid #ffeb00'
                : '1px solid #FF0000';
        }
    }

    if (msg.action === "selected") {
        currentSelectedFileId = msg.id;
        const element = document.getElementById(msg.id);
        if (element) element.style.border = '2px solid rgb(183, 0, 255)';
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
    // 显存使用率用于高度显示
    const vramPercentage = Math.round(msg.memory_usage || msg.percentage_full * 100);
    // GPU运算使用率用于速度控制
    const gpuPercentage = Math.round(msg.gpu_usage || msg.percentage_full * 100);
    
    const chatBox = document.getElementById('chat-box');
    const gpuWaterLevel = document.getElementById('gpu-water-level');

    // 更新聊天框水波纹效果（使用显存使用率）
    gpuWaterLevel.textContent = `—— ${vramPercentage}% ——`;

    if (vramPercentage > 0) {
        chatBox.classList.add('gpu-active');
        
        // 设置水的高度（从底部开始）
        chatBox.style.setProperty('--gpu-water-height', `${vramPercentage}%`);
    } else {
        chatBox.classList.remove('gpu-active');
        chatBox.style.setProperty('--gpu-water-height', '0%');
    }
    
    // 数字保持暗红色，水保持橙色不变
    gpuWaterLevel.style.color = 'rgba(139, 0, 0, 0.9)';
    gpuWaterLevel.style.textShadow = '0 0 15px rgba(139, 0, 0, 0.7)';
    
    // 触发波浪动画更新事件，传递显存和GPU使用率
    window.dispatchEvent(new CustomEvent('gpu-usage-update', {
        detail: { 
            usage: gpuPercentage,  // GPU运算使用率用于速度
            vram: vramPercentage   // 显存使用率用于高度
        }
    }));
}

// Memory usage monitoring
function logMemoryUsage() {
    if (performance.memory) {
        console.log('Memory usage:', {
            used: Math.round(performance.memory.usedJSHeapSize / 1048576) + ' MB',
            total: Math.round(performance.memory.totalJSHeapSize / 1048576) + ' MB',
            limit: Math.round(performance.memory.jsHeapSizeLimit / 1048576) + ' MB'
        });
    }
}

// Event listeners for WebSocket messages
window.addEventListener('left-panel-event', (e) => {
    const msg = e.detail;

    switch(msg.type) {
        case "file-display_tree":
            const treeContainer = document.getElementById('file tree root');
            displayTree(msg.tree, treeContainer);
            setupEventDelegation(); // 使用事件委托，只设置一次
            initializeFileExplorer();
            logMemoryUsage(); // 监控内存使用
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
        case "gpu-memory-usage":
            updateGpuUsage(msg);
            break;

        case "file-display_expl":
            console.log(`msg.items: ${msg.items}`)
            console.log(`msg.root: ${msg.root}`)
            // 显示文件浏览器内容
            displayFileExplorer(msg.items, msg.root);
            break;

        case "file-explorer-update":
            // Handle updates to the file explorer from the backend
            // 这个case现在由file-display_expl处理
            break;
    }
});