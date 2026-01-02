// tokens.js
import { tokenLayer, stage, CELL_SIZE } from './grid.js';

let tokenId = 1;
let selectedToken = null;
let contextMenuStage = null;
let contextMenuLayer = null;
let longPressTimer = null;
let touchStartX = 0;
let touchStartY = 0;
let isDragging = false;
let socketRef = null;
let gridCodeRef = null;

export function initContextMenu(stageRef, layerRef) {
    contextMenuStage = stageRef;
    contextMenuLayer = layerRef;
}

export function initSocket(socket, gridCode) {
    socketRef = socket;
    gridCodeRef = gridCode;
}

// Helper function to sync label position with token
// Centers the label on the token without relying on offset properties
export function syncLabelPosition(token, label) {
    if (label) {
        // Position label at token center, Konva will handle centering via align/verticalAlign
        label.x(token.x());
        label.y(token.y());
    }
}

function showContextMenu(x, y, token) {
    const menu = document.getElementById('contextMenu');
    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
    menu.style.display = 'block';
    selectedToken = token;

    // Delete handler
    document.getElementById('deleteToken').onclick = () => {
        // Emit to server if token has been acknowledged
        if (socketRef && gridCodeRef && token.serverId) {
            socketRef.emit('remove_token', {
                code: gridCodeRef,
                token_id: token.serverId
            });
        }
        // Destroy the label if it exists
        if (token.label) {
            token.label.destroy();
        }
        token.destroy();
        contextMenuLayer.draw();
        menu.style.display = 'none';
    };

    // Bring to front
    document.getElementById('bringToFront').onclick = () => {
        token.setZIndex(contextMenuLayer.children.length - 1);
        contextMenuLayer.draw();
        menu.style.display = 'none';
    };

    // Send to back
    document.getElementById('sendToBack').onclick = () => {
        token.setZIndex(0);
        contextMenuLayer.draw();
        menu.style.display = 'none';
    };
}

// Hide context menu on click outside
document.addEventListener('click', (e) => {
    if (e.target.id !== 'contextMenu' && !e.target.closest('#contextMenu')) {
        document.getElementById('contextMenu').style.display = 'none';
    }
});

export function addToken(stageRef, layerRef, name = "Token", color = "#ff0000", characterId = null) {
    const x = stageRef.width() / 2;
    const y = stageRef.height() / 2;
    
    // Token radius - slightly larger for better hitbox
    const tokenRadius = CELL_SIZE / 2;
    
    const token = new Konva.Circle({
        id: `token-${tokenId}`,
        x: x,
        y: y,
        radius: tokenRadius,
        fill: color,
        stroke: "black",
        strokeWidth: 2,
        hitStrokeWidth: 2,
        draggable: true,
        name: name,
        characterId: characterId
    });

    const label = new Konva.Text({
        x: x,
        y: y,
        text: name,
        fontSize: 14,
        fill: "white",
        fontStyle: "bold",
        align: "center",
        verticalAlign: "middle",
        pointerEvents: "none",
        listening: false
    });
    
    // Center the label on the token by offsetting to the text center
    const textWidth = label.getWidth();
    label.offsetX(textWidth / 2);
    label.offsetY(label.getHeight() / 2);

    // Store label reference on token for easy deletion
    token.label = label;

    layerRef.add(token);
    layerRef.add(label);

    // Update label position when token moves
    token.on("dragmove", () => {
        syncLabelPosition(token, label);
        layerRef.batchDraw();
    });

    // Drag start
    token.on("dragstart", () => {
        if (longPressTimer) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
        }
        isDragging = true;
        // Hide context menu when starting to drag
        document.getElementById('contextMenu').style.display = 'none';
        token.setZIndex(layerRef.children.length - 1);
        label.setZIndex(layerRef.children.length - 1);
        stageRef.container().style.cursor = "grabbing";
    });

    // Drag end
    token.on("dragend", () => {
        isDragging = false;
        stageRef.container().style.cursor = "default";
        
        // Snap token to nearest grid cell center
        const CELL_SIZE = 50;
        
        // Convert stage coordinates to grid cell indices (accounting for cell center offset)
        const gridX = Math.round((token.x() - CELL_SIZE / 2) / CELL_SIZE);
        const gridY = Math.round((token.y() - CELL_SIZE / 2) / CELL_SIZE);
        
        // Convert back to stage coordinates (snap to cell center)
        const snappedX = gridX * CELL_SIZE + CELL_SIZE / 2;
        const snappedY = gridY * CELL_SIZE + CELL_SIZE / 2;
        
        // Update token position
        token.x(snappedX);
        token.y(snappedY);
        
        // Sync label using the same method as dragmove
        syncLabelPosition(token, label);
        
        layerRef.draw();
        
        // Emit move event to server if token has server ID
        if (socketRef && gridCodeRef && token.serverId) {
            socketRef.emit('move_token', {
                code: gridCodeRef,
                token_id: token.serverId,
                x: gridX,
                y: gridY
            });
        }
        // If no serverId yet (token not acknowledged by server), that's ok
        // The local position is still updated
    });

    // Mouse events
    token.on("mousedown", () => {
        if (longPressTimer) clearTimeout(longPressTimer);
        isDragging = false;
        
        token.setZIndex(layerRef.children.length - 1);
        label.setZIndex(layerRef.children.length - 1);
        layerRef.draw();
        
        stageRef.container().style.cursor = "grabbing";
    });

    token.on("mouseup", () => {
        if (!isDragging) {
            token.strokeWidth(3);
            layerRef.batchDraw();
        }
        stageRef.container().style.cursor = "grab";
    });

    token.on("mouseenter", () => {
        stageRef.container().style.cursor = "grab";
    });

    token.on("mouseleave", () => {
        stageRef.container().style.cursor = "default";
        if (!isDragging) {
            token.strokeWidth(2);
            layerRef.batchDraw();
        }
    });

    // Touch events for long-press context menu
    token.on("touchstart", () => {
        isDragging = false;
        
        token.setZIndex(layerRef.children.length - 1);
        label.setZIndex(layerRef.children.length - 1);
        layerRef.draw();
        
        longPressTimer = setTimeout(() => {
            if (!isDragging) {
                const pos = stageRef.getPointerPosition();
                showContextMenu(pos.x, pos.y, token);
            }
            longPressTimer = null;
        }, 500);
    });

    token.on("touchend", () => {
        if (longPressTimer) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
            if (!isDragging) {
                token.strokeWidth(3);
                layerRef.batchDraw();
            }
        }
    });

    // Right-click context menu
    token.on("contextmenu", (e) => {
        e.evt.preventDefault();
        const pos = stageRef.getPointerPosition();
        showContextMenu(pos.x, pos.y, token);
    });

    layerRef.draw();
    tokenId++;

    return token;
}

export function addTestToken() {
    addToken(stage, tokenLayer, "Test", "#ff0000");
}
