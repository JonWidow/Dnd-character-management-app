/**
 * Asset Placement Handler - Handles placing SVG assets on the Konva grid
 */

export class AssetPlacementHandler {
    constructor(stage, assetLayer, gridModule) {
        this.stage = stage;
        this.assetLayer = assetLayer;
        this.gridModule = gridModule;
        this.assetLoader = null;
        this.placedAssets = new Map(); // Map of asset ID -> Konva object
        this.assetIdCounter = 0;
        this.assetsLoaded = false; // Prevent duplicate loads
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Click on canvas to place selected asset
        this.stage.on('click', (e) => {
            console.log('[AssetPlacement] Stage clicked, placement mode:', this.gridModule.assetPlacementMode);
            
            if (!this.gridModule.assetPlacementMode || !this.gridModule.selectedAssetPath) {
                console.log('[AssetPlacement] Placement mode inactive or no asset selected');
                return;
            }

            // Prevent placing on UI elements
            if (e.target === this.stage) {
                const pos = this.stage.getPointerPosition();
                console.log('[AssetPlacement] Placing asset at:', pos);
                this.placeAsset(pos.x, pos.y);
            }
        });

        // Drag and drop from asset panel
        const gridContainer = document.getElementById('grid-container');
        if (!gridContainer) {
            console.error('[AssetPlacement] Grid container not found');
            return;
        }
        
        console.log('[AssetPlacement] Setting up drag-drop listeners on grid container');
        
        gridContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            gridContainer.style.backgroundColor = 'rgba(30, 60, 114, 0.1)';
        });

        gridContainer.addEventListener('dragleave', (e) => {
            if (e.target === gridContainer) {
                gridContainer.style.backgroundColor = '';
            }
        });

        gridContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            gridContainer.style.backgroundColor = '';
            
            console.log('[AssetPlacement] Drop event received');
            
            // First check if we have asset data in global variable
            if (window.draggedAssetData) {
                console.log('[AssetPlacement] Found asset in window.draggedAssetData:', window.draggedAssetData);
                const asset = window.draggedAssetData;
                window.draggedAssetData = null; // Clear it
                
                const rect = gridContainer.getBoundingClientRect();
                const stagePos = this.stage.getPointerPosition();
                console.log('[AssetPlacement] Drop position (stage):', stagePos);
                this.placeAsset(stagePos.x, stagePos.y, asset.path);
                return;
            }
            
            // Fallback to dataTransfer
            const assetData = e.dataTransfer.getData('text/plain');
            if (assetData) {
                try {
                    const asset = JSON.parse(assetData);
                    console.log('[AssetPlacement] Dropped asset from dataTransfer:', asset);
                    const rect = gridContainer.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    
                    // Convert to stage coordinates
                    const stagePos = this.stage.getPointerPosition();
                    console.log('[AssetPlacement] Drop position (stage):', stagePos);
                    this.placeAsset(stagePos.x, stagePos.y, asset.path);
                } catch (error) {
                    console.error('[AssetPlacement] Error parsing dropped asset:', error);
                }
            } else {
                console.log('[AssetPlacement] No asset data in drop event');
            }
        });
    }

    /**
     * Initialize the asset loader
     * @param {AssetLoader} loader - Instance of AssetLoader class
     */
    setAssetLoader(loader) {
        this.assetLoader = loader;
    }

    /**
     * Place an asset on the grid
     * @param {number} x - X coordinate on stage
     * @param {number} y - Y coordinate on stage
     * @param {string} assetPath - Path to asset (optional, uses selected if not provided)
     */
    async placeAsset(x, y, assetPath = null) {
        console.log('[AssetPlacement] placeAsset called with:', {x, y, assetPath});
        
        // Snap to grid (50px cells) - assets snap to center of cells for 1x1
        const CELL_SIZE = 50;
        const HALF_CELL = CELL_SIZE / 2;
        const gridX = Math.round((x - HALF_CELL) / CELL_SIZE);
        const gridY = Math.round((y - HALF_CELL) / CELL_SIZE);
        const snappedX = gridX * CELL_SIZE + HALF_CELL;
        const snappedY = gridY * CELL_SIZE + HALF_CELL;
        console.log('[AssetPlacement] Snapped from (', x, ',', y, ') to grid cell center (', snappedX, ',', snappedY, ')');
        
        const path = assetPath || this.gridModule.selectedAssetPath;
        
        if (!path) {
            console.warn('[AssetPlacement] No asset path provided');
            return;
        }

        if (!this.assetLoader) {
            console.error('[AssetPlacement] AssetLoader not initialized');
            return;
        }

        console.log(`[AssetPlacement] Placing asset at (${x}, ${y}): ${path}`);

        try {
            // Create Konva image from SVG
            console.log('[AssetPlacement] Calling createAssetImage...');
            const konvaImage = await this.assetLoader.createAssetImage(path, x, y, 50, 50);
            
            console.log('[AssetPlacement] createAssetImage returned:', {konvaImage: !!konvaImage, type: konvaImage?.constructor?.name});
            
            if (konvaImage) {
                console.log('[AssetPlacement] Asset image created, adding to layer');
                console.log('[AssetPlacement] Layer info:', {
                    layerExists: !!this.assetLayer,
                    layerClassName: this.assetLayer?.constructor?.name,
                    layerChildrenCount: this.assetLayer?.children?.length || 0
                });
                
                // Update position to snapped coordinates
                konvaImage.x(snappedX);
                konvaImage.y(snappedY);
                
                // Add interaction
                this.addAssetInteraction(konvaImage);
                
                // Add to layer
                this.assetLayer.add(konvaImage);
                this.assetLayer.draw();
                
                console.log('[AssetPlacement] Asset added to layer and drawn');
                console.log('[AssetPlacement] After draw - layer children:', this.assetLayer.children.length);
                
                // Track placed asset
                const assetId = this.assetIdCounter++;
                this.placedAssets.set(assetId, konvaImage);
                konvaImage.assetId = assetId;
                konvaImage.assetPath = path;
                
                console.log(`[AssetPlacement] Asset placed with ID: ${assetId}`);
                
                // Save to database
                await this.saveAssetToDatabase(path, snappedX, snappedY);
            } else {
                console.error('[AssetPlacement] Failed to create asset image - returned null/undefined');
            }
        } catch (error) {
            console.error('[AssetPlacement] Error placing asset:', error, error.stack);
        }
    }

    /**
     * Add interaction handlers to a placed asset
     * @param {Konva.Image} konvaImage - Konva image object
     */
    addAssetInteraction(konvaImage) {
        konvaImage.on('mouseenter', () => {
            if (this.stage && this.stage.container) {
                this.stage.container.style.cursor = 'move';
            }
            konvaImage.shadowColor('black');
            konvaImage.shadowBlur(10);
            konvaImage.shadowOpacity(0.5);
            this.assetLayer.draw();
        });

        konvaImage.on('mouseleave', () => {
            if (this.stage && this.stage.container) {
                this.stage.container.style.cursor = 'default';
            }
            konvaImage.shadowOpacity(0);
            this.assetLayer.draw();
        });

        // Right-click context menu
        konvaImage.on('contextmenu', (e) => {
            e.evt.preventDefault();
            this.showAssetContextMenu(e.evt.clientX, e.evt.clientY, konvaImage);
        });

        // Snap to grid on drag end and save position
        konvaImage.on('dragend', () => {
            // Snap to grid based on asset dimensions
            const CELL_SIZE = 50;
            const widthSquares = Math.round(konvaImage.width() / CELL_SIZE);
            const heightSquares = Math.round(konvaImage.height() / CELL_SIZE);
            
            // For odd dimensions: snap to cell centers (25, 75, 125, ...)
            // For even dimensions: snap to grid lines (0, 50, 100, ...)
            let snappedX, snappedY;
            
            if (widthSquares % 2 === 1) {
                // Odd: center in square
                const HALF_CELL = CELL_SIZE / 2;
                const gridX = Math.round((konvaImage.x() - HALF_CELL) / CELL_SIZE);
                snappedX = gridX * CELL_SIZE + HALF_CELL;
            } else {
                // Even: center on line
                const gridX = Math.round(konvaImage.x() / CELL_SIZE);
                snappedX = gridX * CELL_SIZE;
            }
            
            if (heightSquares % 2 === 1) {
                // Odd: center in square
                const HALF_CELL = CELL_SIZE / 2;
                const gridY = Math.round((konvaImage.y() - HALF_CELL) / CELL_SIZE);
                snappedY = gridY * CELL_SIZE + HALF_CELL;
            } else {
                // Even: center on line
                const gridY = Math.round(konvaImage.y() / CELL_SIZE);
                snappedY = gridY * CELL_SIZE;
            }
            
            konvaImage.x(snappedX);
            konvaImage.y(snappedY);
            
            this.assetLayer.draw();
            
            // Update in database if this asset was loaded from DB
            if (konvaImage.databaseId) {
                this.updateAssetInDatabase(konvaImage.databaseId, snappedX, snappedY);
            }
        });
    }

    /**
     * Show context menu for asset
     * @param {number} x - Mouse X position
     * @param {number} y - Mouse Y position
     * @param {Konva.Image} asset - The asset Konva object
     */
    showAssetContextMenu(x, y, asset) {
        const menu = document.getElementById('assetContextMenu');
        if (!menu) return;

        menu.style.display = 'block';
        menu.style.left = x + 'px';
        menu.style.top = y + 'px';
        menu.currentAsset = asset;
        
        // Close resize dropdown when menu opens
        const resizeDropdown = menu.querySelector('#resizeDropdown');
        if (resizeDropdown) {
            resizeDropdown.style.display = 'none';
        }
        const resizeToggle = menu.querySelector('#resizeToggle');
        const chevron = resizeToggle?.querySelector('.fa-chevron-down');
        if (chevron) {
            chevron.style.transform = 'rotate(0deg)';
        }

        // Handle delete
        const deleteBtn = menu.querySelector('#deleteAsset');
        if (deleteBtn) {
            deleteBtn.onclick = () => {
                // Delete from database if it has a database ID
                if (asset.databaseId) {
                    this.deleteAssetFromDatabase(asset.databaseId);
                }
                asset.destroy();
                this.assetLayer.draw();
                menu.style.display = 'none';
            };
        }

        // Handle rotate
        const rotateBtn = menu.querySelector('#rotateAsset');
        if (rotateBtn) {
            // Remove any previous handlers
            const newRotateBtn = rotateBtn.cloneNode(true);
            rotateBtn.parentNode.replaceChild(newRotateBtn, rotateBtn);
            
            newRotateBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                const currentRotation = asset.rotation() || 0;
                const newRotation = currentRotation + 45;
                asset.rotation(newRotation);
                this.assetLayer.draw();
                
                // Update in database if this asset was loaded from DB
                if (asset.databaseId) {
                    this.updateAssetRotationInDatabase(asset.databaseId, newRotation);
                }
                
                menu.style.display = 'none';
            };
        }

        // Handle resize dropdown toggle
        if (resizeToggle) {
            resizeToggle.onclick = (e) => {
                e.stopPropagation();
                const isShowing = resizeDropdown.style.display === 'grid';
                resizeDropdown.style.display = isShowing ? 'none' : 'grid';
                
                // Animate chevron
                const chevron = resizeToggle.querySelector('.fa-chevron-down');
                if (chevron) {
                    chevron.style.transform = isShowing ? 'rotate(0deg)' : 'rotate(180deg)';
                }
            };
        }

        // Handle resize buttons (1x1, 2x2, 3x3, etc.)
        const resizeButtons = menu.querySelectorAll('.resize-btn');
        resizeButtons.forEach(btn => {
            btn.onclick = (e) => {
                e.stopPropagation();
                const size = btn.getAttribute('data-size');
                
                if (size === 'custom') {
                    // Show custom resize dialog
                    this.showCustomResizeDialog(asset);
                } else {
                    // Resize to grid squares (50px per square)
                    const squareSize = parseInt(size);
                    this.resizeAsset(asset, squareSize, squareSize);
                }
                menu.style.display = 'none';
            };
        });

        // Handle duplicate
        const duplicateBtn = menu.querySelector('#duplicateAsset');
        if (duplicateBtn) {
            duplicateBtn.onclick = async () => {
                const newX = asset.x() + 20;
                const newY = asset.y() + 20;
                const clone = asset.clone({
                    x: newX,
                    y: newY
                });
                this.addAssetInteraction(clone);
                this.assetLayer.add(clone);
                this.assetLayer.draw();
                
                // Save the duplicated asset to database with explicit position
                const assetPath = asset.assetPath || '';
                const width = clone.width() || 50;
                const height = clone.height() || 50;
                console.log('[AssetPlacement] Saving duplicated asset at position:', {x: newX, y: newY, width, height});
                const savedData = await this.saveAssetToDatabase(assetPath, newX, newY, width, height);
                
                // Set the database ID on the clone so position updates are persisted
                if (savedData && savedData.id) {
                    clone.databaseId = savedData.id;
                    console.log('[AssetPlacement] Set databaseId on cloned asset:', savedData.id);
                }
                
                menu.style.display = 'none';
            };
        }
    }

    /**
     * Resize an asset to specific grid square dimensions
     * @param {Konva.Image} asset - The asset to resize
     * @param {number} widthSquares - Width in grid squares
     * @param {number} heightSquares - Height in grid squares
     */
    resizeAsset(asset, widthSquares, heightSquares) {
        const CELL_SIZE = 50;
        const newWidth = widthSquares * CELL_SIZE;
        const newHeight = heightSquares * CELL_SIZE;
        
        console.log('[AssetPlacement] Resizing asset to', widthSquares, 'x', heightSquares, 'squares (', newWidth, 'x', newHeight, 'px)');
        
        // Calculate old and new offsets
        const oldWidth = asset.width();
        const oldHeight = asset.height();
        const oldOffsetX = asset.offsetX();
        const oldOffsetY = asset.offsetY();
        
        // For odd dimensions: center in the middle of a square
        // For even dimensions: center on grid lines (no offset)
        const newOffsetX = widthSquares % 2 === 1 ? newWidth / 2 : 0;
        const newOffsetY = heightSquares % 2 === 1 ? newHeight / 2 : 0;
        
        // Adjust position to compensate for offset change
        // The visual position should stay the same, but the anchor point changes
        const offsetDiffX = newOffsetX - oldOffsetX;
        const offsetDiffY = newOffsetY - oldOffsetY;
        
        asset.width(newWidth);
        asset.height(newHeight);
        asset.offsetX(newOffsetX);
        asset.offsetY(newOffsetY);
        
        // Move the asset to compensate for offset change
        asset.x(asset.x() - offsetDiffX);
        asset.y(asset.y() - offsetDiffY);
        
        // Store dimensions for later persistence
        asset.assetWidth = newWidth;
        asset.assetHeight = newHeight;
        
        this.assetLayer.draw();
        
        // Update in database if this asset was loaded from DB
        if (asset.databaseId) {
            this.updateAssetDimensionsInDatabase(asset.databaseId, newWidth, newHeight);
        }
    }

    /**
     * Show custom resize dialog
     * @param {Konva.Image} asset - The asset to resize
     */
    showCustomResizeDialog(asset) {
        const dialog = document.getElementById('customResizeDialog');
        if (!dialog) return;
        
        const widthInput = document.getElementById('customWidth');
        const heightInput = document.getElementById('customHeight');
        const confirmBtn = document.getElementById('confirmCustomResize');
        const cancelBtn = document.getElementById('cancelCustomResize');
        
        // Set current dimensions
        const CELL_SIZE = 50;
        widthInput.value = Math.max(1, Math.round(asset.width() / CELL_SIZE));
        heightInput.value = Math.max(1, Math.round(asset.height() / CELL_SIZE));
        
        dialog.style.display = 'block';
        
        // Handle confirm
        const handleConfirm = () => {
            const widthSquares = parseInt(widthInput.value) || 1;
            const heightSquares = parseInt(heightInput.value) || 1;
            
            this.resizeAsset(asset, widthSquares, heightSquares);
            dialog.style.display = 'none';
            
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
        };
        
        // Handle cancel
        const handleCancel = () => {
            dialog.style.display = 'none';
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
        };
        
        confirmBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);
        
        // Focus width input
        widthInput.focus();
        widthInput.select();
    }

    /**
     * Clear all placed assets
     */
    clearAssets() {
        this.assetLayer.destroyChildren();
        this.placedAssets.clear();
        this.assetIdCounter = 0;
        this.assetLayer.draw();
    }

    /**
     * Get all placed assets
     * @returns {Array} Array of placed asset data
     */
    getPlacedAssets() {
        const assets = [];
        this.placedAssets.forEach((konvaImage, id) => {
            assets.push({
                id,
                x: konvaImage.x(),
                y: konvaImage.y(),
                rotation: konvaImage.rotation() || 0,
                scaleX: konvaImage.scaleX(),
                scaleY: konvaImage.scaleY()
            });
        });
        return assets;
    }

    /**
     * Save an asset to the database
     * @param {string} assetPath - Path to the asset SVG
     * @param {number} x - X coordinate
     * @param {number} y - Y coordinate
     * @param {number} width - Asset width in pixels (optional, defaults to 50)
     * @param {number} height - Asset height in pixels (optional, defaults to 50)
     * @param {number} rotation - Asset rotation in degrees (optional, defaults to 0)
     */
    async saveAssetToDatabase(assetPath, x, y, width = 50, height = 50, rotation = 0) {
        try {
            // Get grid code from URL (path format: /grid/{code})
            const gridCode = window.location.pathname.split('/').pop();
            console.log('[AssetPlacement] Saving asset with grid code:', gridCode, 'path:', assetPath, 'coords:', {x, y, width, height, rotation});
            
            const response = await fetch('/api/assets/placed', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    grid_code: gridCode,
                    asset_path: assetPath,
                    x: x,
                    y: y,
                    width: width,
                    height: height,
                    rotation: rotation
                })
            });
            
            if (!response.ok) {
                console.error('[AssetPlacement] Failed to save asset to database:', response.status);
                return;
            }
            
            const data = await response.json();
            console.log('[AssetPlacement] Asset saved to database:', data);
            return data;
        } catch (error) {
            console.error('[AssetPlacement] Error saving asset to database:', error);
        }
    }

    /**
     * Update an asset's position in the database
     * @param {number} assetId - Database ID of the asset
     * @param {number} x - New X coordinate
     * @param {number} y - New Y coordinate
     */
    async updateAssetInDatabase(assetId, x, y) {
        try {
            console.log('[AssetPlacement] Updating asset in database:', {assetId, x, y});
            
            const response = await fetch(`/api/assets/placed/${assetId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    x: x,
                    y: y
                })
            });
            
            if (!response.ok) {
                console.error('[AssetPlacement] Failed to update asset:', response.status);
                return;
            }
            
            const data = await response.json();
            console.log('[AssetPlacement] Asset updated in database:', data);
        } catch (error) {
            console.error('[AssetPlacement] Error updating asset in database:', error);
        }
    }

    /**
     * Update an asset's dimensions in the database
     * @param {number} assetId - Database ID of the asset
     * @param {number} width - New width in pixels
     * @param {number} height - New height in pixels
     */
    async updateAssetDimensionsInDatabase(assetId, width, height) {
        try {
            console.log('[AssetPlacement] Updating asset dimensions in database:', {assetId, width, height});
            
            const response = await fetch(`/api/assets/placed/${assetId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    width: width,
                    height: height
                })
            });
            
            if (!response.ok) {
                console.error('[AssetPlacement] Failed to update asset dimensions:', response.status);
                return;
            }
            
            const data = await response.json();
            console.log('[AssetPlacement] Asset dimensions updated in database:', data);
        } catch (error) {
            console.error('[AssetPlacement] Error updating asset dimensions in database:', error);
        }
    }

    /**
     * Update an asset's rotation in the database
     * @param {number} assetId - Database ID of the asset
     * @param {number} rotation - New rotation in degrees
     */
    async updateAssetRotationInDatabase(assetId, rotation) {
        try {
            console.log('[AssetPlacement] Updating asset rotation in database:', {assetId, rotation});
            
            const response = await fetch(`/api/assets/placed/${assetId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    rotation: rotation
                })
            });
            
            if (!response.ok) {
                console.error('[AssetPlacement] Failed to update asset rotation:', response.status);
                return;
            }
            
            const data = await response.json();
            console.log('[AssetPlacement] Asset rotation updated in database:', data);
        } catch (error) {
            console.error('[AssetPlacement] Error updating asset rotation in database:', error);
        }
    }

    /**
     * Delete an asset from the database
     * @param {number} assetId - Database ID of the asset to delete
     */
    async deleteAssetFromDatabase(assetId) {
        try {
            console.log('[AssetPlacement] Deleting asset from database:', assetId);
            
            const response = await fetch(`/api/assets/placed/${assetId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                console.error('[AssetPlacement] Failed to delete asset:', response.status);
                return;
            }
            
            console.log('[AssetPlacement] Asset deleted from database:', assetId);
        } catch (error) {
            console.error('[AssetPlacement] Error deleting asset from database:', error);
        }
    }

    /**
     * Load placed assets from database for this grid
     * @param {string} gridCode - The grid code
     */
    async loadPlacedAssets(gridCode) {
        // Prevent duplicate loads
        if (this.assetsLoaded) {
            console.log('[AssetPlacement] Assets already loaded, skipping');
            return;
        }
        
        try {
            console.log('[AssetPlacement] Loading placed assets for grid:', gridCode);
            
            const response = await fetch(`/api/assets/placed/${gridCode}`);
            if (!response.ok) {
                console.error('[AssetPlacement] Failed to load assets:', response.status);
                return;
            }
            
            const assetsData = await response.json();
            console.log('[AssetPlacement] Loaded assets:', assetsData);
            
            // Place each asset on the grid
            for (const assetData of assetsData) {
                try {
                    const konvaImage = await this.assetLoader.createAssetImage(
                        assetData.asset_path,
                        assetData.x,
                        assetData.y,
                        assetData.width,
                        assetData.height
                    );
                    
                    if (konvaImage) {
                        this.addAssetInteraction(konvaImage);
                        this.assetLayer.add(konvaImage);
                        
                        const assetId = this.assetIdCounter++;
                        this.placedAssets.set(assetId, konvaImage);
                        konvaImage.assetId = assetId;
                        konvaImage.assetPath = assetData.asset_path;
                        konvaImage.databaseId = assetData.id;
                        
                        // Restore rotation from database
                        if (assetData.rotation) {
                            konvaImage.rotation(assetData.rotation);
                        }
                        
                        console.log('[AssetPlacement] Loaded asset with ID:', assetId);
                    }
                } catch (error) {
                    console.error('[AssetPlacement] Error loading asset:', assetData, error);
                }
            }
            
            this.assetLayer.draw();
            this.assetsLoaded = true;
            console.log('[AssetPlacement] All assets loaded and drawn');
        } catch (error) {
            console.error('[AssetPlacement] Error loading placed assets:', error);
        }
    }
}

export default AssetPlacementHandler;
