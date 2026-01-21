/**
 * Grid assets module - handles asset placement and management on the grid
 */

let assetLayer = null;
let placedAssets = [];

export function initAssetLayer(stage, layerRef) {
    assetLayer = layerRef;
    return {
        addAssetToGrid,
        removeAsset,
        getAssets: () => placedAssets
    };
}

/**
 * Add an asset to the grid at specified coordinates
 */
export function addAssetToGrid(asset, x, y) {
    if (!assetLayer) return null;
    
    const CELL_SIZE = 50;
    const stageX = x * CELL_SIZE + CELL_SIZE / 2;
    const stageY = y * CELL_SIZE + CELL_SIZE / 2;
    
    // Create image from asset
    const img = new Image();
    img.src = `/static/assets/${asset.file_path}`;
    
    img.onload = () => {
        const Konva = window.Konva;
        
        const imageObj = new Konva.Image({
            x: stageX,
            y: stageY,
            image: img,
            width: asset.width,
            height: asset.height,
            offset: {
                x: asset.width / 2,
                y: asset.height / 2
            },
            draggable: true,
            name: 'asset'
        });
        
        // Store asset metadata
        imageObj.assetId = asset.id;
        imageObj.assetName = asset.name;
        imageObj.isPassable = asset.is_passable;
        
        // Add drag functionality
        imageObj.on('dragend', () => {
            // Could emit socket event to sync position
        });
        
        // Right-click context menu
        imageObj.on('contextmenu', (e) => {
            e.evt.preventDefault();
            showAssetMenu(imageObj);
        });
        
        assetLayer.add(imageObj);
        assetLayer.draw();
        
        placedAssets.push({
            id: asset.id,
            name: asset.name,
            konvaObj: imageObj,
            x: x,
            y: y,
            worldX: stageX,
            worldY: stageY
        });
    };
}

/**
 * Remove an asset from the grid
 */
export function removeAsset(konvaObj) {
    konvaObj.destroy();
    placedAssets = placedAssets.filter(a => a.konvaObj !== konvaObj);
    assetLayer.draw();
}

/**
 * Show context menu for asset
 */
function showAssetMenu(assetObj) {
    const menu = document.getElementById('assetContextMenu');
    if (!menu) return;
    
    menu.style.display = 'block';
    menu.style.left = window.mouseX + 'px';
    menu.style.top = window.mouseY + 'px';
    
    // Store reference to current asset
    menu.currentAsset = assetObj;
}

/**
 * Get grid coordinates from world coordinates
 */
export function worldToGridCoords(worldX, worldY) {
    const CELL_SIZE = 50;
    return {
        x: Math.floor(worldX / CELL_SIZE),
        y: Math.floor(worldY / CELL_SIZE)
    };
}

/**
 * Get world coordinates from grid coordinates
 */
export function gridToWorldCoords(gridX, gridY) {
    const CELL_SIZE = 50;
    return {
        x: gridX * CELL_SIZE + CELL_SIZE / 2,
        y: gridY * CELL_SIZE + CELL_SIZE / 2
    };
}
