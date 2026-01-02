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
    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
    menu.style.display = 'block';
    
    // Show stats panel if character is associated
    const characterId = tokenCharacterMap.get(token.id());
    if (characterId) {
        showCharacterStats(characterId, x + 180, y);
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
        
        // Display HP
        document.getElementById('characterHP').textContent = `${character.current_hp}/${character.hit_points}`;
        
        // Display spell slots with visual indicators
        const spellSlotsContainer = document.getElementById('spellSlotsContainer');
        if (character.spell_slots && character.spell_slots.length > 0) {
            let slotsHTML = '<div style="border-top: 1px solid #eee; padding-top: 6px; margin-top: 6px;">';
            character.spell_slots.forEach(slot => {
                // Create visual slot boxes like character details
                let slotBoxes = '';
                for (let i = 1; i <= slot.total_slots; i++) {
                    const isUsed = i <= slot.used ? true : false;
                    const bgColor = isUsed ? '#ef4444' : '#3b82f6';  // red if used, blue if available
                    const borderColor = isUsed ? '#dc2626' : '#1d4ed8';
                    slotBoxes += `<button type="button" 
                        style="width: 20px; height: 20px; margin: 2px; background-color: ${bgColor}; border: 2px solid ${borderColor}; border-radius: 3px; font-size: 10px; line-height: 16px; text-align: center; color: white; cursor: pointer; padding: 0; font-weight: bold; transition: all 0.2s;"
                        data-slot-id="${slot.id}"
                        data-slot-index="${i}"
                        data-character-id="${characterId}"
                        class="spell-slot-btn"
                        onclick="toggleSpellSlot(event, ${characterId}, ${slot.id}, ${i})">${i}</button>`;
                }
                slotsHTML += `<div style="margin-top: 4px; font-size: 12px;">
                    <span style="font-weight: bold;">Lvl ${slot.level}</span>
                    <div style="margin-top: 2px;">${slotBoxes}</div>
                </div>`;
            });
            slotsHTML += '</div>';
            spellSlotsContainer.innerHTML = slotsHTML;
        } else {
            spellSlotsContainer.innerHTML = '<div style="border-top: 1px solid #eee; padding-top: 6px; margin-top: 6px; color: #999; font-size: 12px;">No spell slots</div>';
        }
        
        // Position panel to the right of the context menu
        statsPanel.style.left = x + 'px';
        statsPanel.style.top = y + 'px';
        statsPanel.style.display = 'block';
    } catch (err) {
        console.error('Failed to fetch character stats:', err);
    }
}

async function toggleSpellSlot(event, characterId, slotId, slotIndex) {
    event.stopPropagation();
    try {
        // Determine if we're using or restoring the slot based on which slot was clicked
        // If clicking on used slots (red), restore it; if clicking on available slots (blue), use it
        const btn = event.target;
        const isUsed = btn.style.backgroundColor === 'rgb(239, 68, 68)' || btn.style.backgroundColor === '#ef4444';
        
        const response = await fetch(`/api/characters/${characterId}/spell-slots/${slotId}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ use_slot: !isUsed })
        });
        
        if (response.ok) {
            // Refresh the stats panel to show updated spell slot state
            const statsPanel = document.getElementById('statsPanel');
            const panelLeft = parseInt(statsPanel.style.left);
            const panelTop = parseInt(statsPanel.style.top);
            await showCharacterStats(characterId, panelLeft, panelTop);
        } else {
            console.error('Failed to toggle spell slot');
        }
    } catch (err) {
        console.error('Error toggling spell slot:', err);
    }
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
