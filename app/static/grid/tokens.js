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

// Map to store token-to-characterId associations
// Use token.id() as key since Konva custom properties don't work reliably
const tokenCharacterMap = new Map();

// Helper function to bring a token and its label to the front
// Ensures the label stays above its token
function bringTokenToFront(token, label, layer) {
    // Find the highest z-index currently in use
    let maxZ = -1;
    layer.children.forEach(child => {
        const z = child.getZIndex();
        if (z > maxZ) maxZ = z;
    });
    
    // Bring this token and its label to the front
    token.setZIndex(maxZ + 1);
    if (label) {
        label.setZIndex(maxZ + 2);  // Label always one level above its token
    }
}

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

export function getTokenCharacterId(token) {
    return tokenCharacterMap.get(token.id());
}


function showContextMenu(x, y, token) {
    const menu = document.getElementById('contextMenu');
    
    // Keep context menu within viewport
    const menuWidth = 150; // Approximate menu width
    const menuHeight = 100; // Approximate menu height
    let menuX = x;
    let menuY = y;
    
    if (menuX + menuWidth > window.innerWidth) {
        menuX = window.innerWidth - menuWidth - 10;
    }
    if (menuX < 10) {
        menuX = 10;
    }
    
    if (menuY + menuHeight > window.innerHeight) {
        menuY = window.innerHeight - menuHeight - 10;
    }
    if (menuY < 10) {
        menuY = 10;
    }
    
    menu.style.left = menuX + 'px';
    menu.style.top = menuY + 'px';
    menu.style.display = 'block';
    
    // Show stats panel if character is associated
    // Position it to the right of menu, or left if no room
    const characterId = tokenCharacterMap.get(token.id());
    if (characterId) {
        const panelWidth = 320;
        let panelX = menuX + 170; // Try placing to the right of menu
        
        // If stats panel won't fit on the right, place it on the left
        if (panelX + panelWidth > window.innerWidth) {
            panelX = menuX - panelWidth - 10;
        }
        
        // Ensure it stays in bounds
        if (panelX < 10) {
            panelX = 10;
        }
        
        showCharacterStats(characterId, panelX, menuY);
    } else {
        document.getElementById('statsPanel').style.display = 'none';
    }
    selectedToken = token;

    // View character handler
    document.getElementById('viewCharacter').onclick = () => {
        const characterId = tokenCharacterMap.get(token.id());
        if (characterId) {
            // Open character details in new tab
            const characterUrl = `/characters/${characterId}`;
            window.open(characterUrl, '_blank');
        } else {
            alert('This token is not associated with a character');
        }
        menu.style.display = 'none';
    };

    // Delete handler
    document.getElementById('deleteToken').onclick = () => {
        // Clean up the character map
        tokenCharacterMap.delete(token.id());
        
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
}
// Fetch and display character stats
async function showCharacterStats(characterId, x, y) {
    try {
        const response = await fetch(`/grid/api/characters/${characterId}`);
        if (!response.ok) {
            console.error('Failed to fetch character stats:', response.status);
            return;
        }
        
        const character = await response.json();
        const statsPanel = document.getElementById('statsPanel');
        
        // Display character name
        document.getElementById('characterName').textContent = character.name;
        
        // Display HP - store character ID for update button
        document.getElementById('characterCurrentHP').value = character.current_hp;
        document.getElementById('characterMaxHP').textContent = character.hit_points;
        statsPanel.dataset.characterId = character.id;
        
        // Display spell slots with visual indicators
        const spellSlotsContainer = document.getElementById('spellSlotsContainer');
        if (character.spell_slots && character.spell_slots.length > 0) {
            let slotsHTML = '<div style="border-top: 1px solid #e5e7eb; padding-top: 8px; margin-top: 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">';
            character.spell_slots.forEach(slot => {
                // Create visual slot boxes like character details - blue background when available, red when used
                let slotBoxes = '';
                for (let i = 1; i <= slot.total_slots; i++) {
                    const isUsed = i <= slot.used ? true : false;
                    const bgColor = isUsed ? '#f87171' : '#60a5fa';  // brighter red if used, brighter blue if available
                    const borderColor = isUsed ? '#dc2626' : '#2563eb';
                    const hoverBg = isUsed ? '#ef4444' : '#3b82f6';
                    slotBoxes += `<button type="button" 
                        style="width: 20px !important; height: 20px !important; margin: 1px; background-color: ${bgColor} !important; background: ${bgColor} !important; border: 2px solid ${borderColor} !important; border-radius: 3px; font-size: 10px; line-height: 16px; text-align: center; color: white; cursor: pointer; padding: 0 !important; font-weight: bold; transition: all 0.2s; font-family: Arial, sans-serif; box-shadow: none !important;"
                        data-slot-id="${slot.id}"
                        data-slot-index="${i}"
                        data-character-id="${characterId}"
                        class="spell-slot-btn"
                        onmouseover="this.style.backgroundColor='${hoverBg} !important'; this.style.transform='scale(1.1)';"
                        onmouseout="this.style.backgroundColor='${bgColor} !important'; this.style.transform='scale(1)';"
                        onclick="toggleSpellSlot(event, ${characterId}, ${slot.id}, ${i})">${i}</button>`;
                }
                slotsHTML += `<div style="font-size: 12px; min-width: 0;">
                    <div style="font-weight: 600; margin-bottom: 4px; color: #374151; font-size: 11px;">Level ${slot.level}</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 2px; padding: 4px; background: #f9fafb; border-radius: 3px;">${slotBoxes}</div>
                </div>`;
            });
            slotsHTML += '</div>';
            spellSlotsContainer.innerHTML = slotsHTML;
        } else {
            spellSlotsContainer.innerHTML = '<div style="border-top: 1px solid #e5e7eb; padding-top: 8px; margin-top: 8px; color: #999; font-size: 12px;">No spell slots</div>';
        }
        
        // Position panel to the right of the context menu with viewport bounds checking
        // Show panel first to get accurate height
        statsPanel.style.display = 'block';
        const panelWidth = 320;
        // Get actual panel height after rendering
        const actualPanelHeight = statsPanel.offsetHeight;
        const panelHeight = Math.min(actualPanelHeight, window.innerHeight * 0.85);
        let finalX = x;
        let finalY = y;
        
        // Keep panel within viewport horizontally
        if (finalX + panelWidth > window.innerWidth) {
            finalX = window.innerWidth - panelWidth - 10; // 10px margin from edge
        }
        if (finalX < 10) {
            finalX = 10;
        }
        
        // Keep panel within viewport vertically
        if (finalY + panelHeight > window.innerHeight) {
            finalY = window.innerHeight - panelHeight - 10; // 10px margin from edge
        }
        if (finalY < 10) {
            finalY = 10;
        }
        
        statsPanel.style.left = finalX + 'px';
        statsPanel.style.top = finalY + 'px';
    } catch (err) {
        console.error('Failed to fetch character stats:', err);
    }
}

async function toggleSpellSlot(event, characterId, slotId, slotIndex) {
    console.log('toggleSpellSlot called:', { characterId, slotId, slotIndex });
    event.stopPropagation();
    try {
        // Determine if we're using or restoring the slot based on which slot was clicked
        // If clicking on used slots (red), restore it; if clicking on available slots (blue), use it
        const btn = event.target;
        const computedStyle = window.getComputedStyle(btn);
        const bgColor = computedStyle.backgroundColor;
        
        console.log('Button color:', bgColor);
        
        // Check if button is red (used) or blue (available)
        // Red: rgb(239, 68, 68) or #ef4444
        // Blue: rgb(59, 130, 246) or #3b82f6
        const isUsed = bgColor.includes('239') || bgColor === '#ef4444';
        
        console.log('Is used:', isUsed, 'Will use_slot:', !isUsed);
        
        // Use the grid-specific endpoint (no auth required)
        const response = await fetch(`/grid/spell-slots/${slotId}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ use_slot: !isUsed })
        });
        
        console.log('Toggle response:', response.status);
        
        if (response.ok) {
            // Refresh the stats panel to show updated spell slot state
            const statsPanel = document.getElementById('statsPanel');
            const panelLeft = parseInt(statsPanel.style.left);
            const panelTop = parseInt(statsPanel.style.top);
            console.log('Refreshing stats panel at', panelLeft, panelTop);
            await showCharacterStats(characterId, panelLeft, panelTop);
        } else {
            const errorData = await response.json();
            console.error('Failed to toggle spell slot:', response.status, errorData);
        }
    } catch (err) {
        console.error('Error toggling spell slot:', err);
    }
}

async function updateCharacterHP() {
    try {
        const statsPanel = document.getElementById('statsPanel');
        const characterId = statsPanel.dataset.characterId;
        const newHP = parseInt(document.getElementById('characterCurrentHP').value) || 0;
        
        const response = await fetch(`/grid/characters/${characterId}/hp`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ current_hp: newHP })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Failed to update HP:', response.status, errorData);
        }
    } catch (err) {
        console.error('Error updating HP:', err);
    }
}

// Set up HP input change listener when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        document.getElementById('characterCurrentHP').addEventListener('change', updateCharacterHP);
    });
} else {
    document.getElementById('characterCurrentHP').addEventListener('change', updateCharacterHP);
}

// Hide context menu on click outside
document.addEventListener('click', (e) => {
    if (e.target.id !== 'contextMenu' && !e.target.closest('#contextMenu') && 
        e.target.id !== 'statsPanel' && !e.target.closest('#statsPanel')) {
        document.getElementById('contextMenu').style.display = 'none';
        document.getElementById('statsPanel').style.display = 'none';
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
        name: name
    });
    
    // Store characterId in the map using token's Konva id
    if (characterId) {
        tokenCharacterMap.set(`token-${tokenId}`, characterId);
    }

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

    // Store label reference on token for easy deletion
    token.label = label;

    layerRef.add(token);
    layerRef.add(label);
    
    // Center the label on the token by offsetting to the text center
    // Do this AFTER adding to layer so dimensions are properly calculated
    label.offsetX(label.getWidth() / 2);
    label.offsetY(label.getHeight() / 2);

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
        bringTokenToFront(token, label, layerRef);
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
        
        bringTokenToFront(token, label, layerRef);
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

// Make toggleSpellSlot globally available for onclick handlers
window.toggleSpellSlot = toggleSpellSlot;
