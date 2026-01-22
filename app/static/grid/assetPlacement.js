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
        
        // Snap to grid (50px cells) - assets snap to top-left corner of cells
        const CELL_SIZE = 50;
        const gridX = Math.round(x / CELL_SIZE);
        const gridY = Math.round(y / CELL_SIZE);
        const snappedX = gridX * CELL_SIZE;
        const snappedY = gridY * CELL_SIZE;
        console.log('[AssetPlacement] Snapped from (', x, ',', y, ') to grid cell (', gridX, ',', gridY, ') = pixels (', snappedX, ',', snappedY, ')');
        
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
            // Snap to grid
            const CELL_SIZE = 50;
            const gridX = Math.round(konvaImage.x() / CELL_SIZE);
            const gridY = Math.round(konvaImage.y() / CELL_SIZE);
            const snappedX = gridX * CELL_SIZE;
            const snappedY = gridY * CELL_SIZE;
            
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

        // Handle delete
        const deleteBtn = menu.querySelector('#deleteAsset');
        if (deleteBtn) {
            deleteBtn.onclick = () => {
                asset.destroy();
                this.assetLayer.draw();
                menu.style.display = 'none';
            };
        }

        // Handle rotate
        const rotateBtn = menu.querySelector('#rotateAsset');
        if (rotateBtn) {
            rotateBtn.onclick = () => {
                const currentRotation = asset.rotation() || 0;
                asset.rotation(currentRotation + 45);
                this.assetLayer.draw();
                menu.style.display = 'none';
            };
        }

        // Handle duplicate
        const duplicateBtn = menu.querySelector('#duplicateAsset');
        if (duplicateBtn) {
            duplicateBtn.onclick = () => {
                const clone = asset.clone({
                    x: asset.x() + 20,
                    y: asset.y() + 20
                });
                this.addAssetInteraction(clone);
                this.assetLayer.add(clone);
                this.assetLayer.draw();
                menu.style.display = 'none';
            };
        }
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
     */
    async saveAssetToDatabase(assetPath, x, y) {
        try {
            // Get grid code from URL (path format: /grid/{code})
            const gridCode = window.location.pathname.split('/').pop();
            console.log('[AssetPlacement] Saving asset with grid code:', gridCode, 'path:', assetPath, 'coords:', {x, y});
            
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
                    width: 50,
                    height: 50,
                    rotation: 0
                })
            });
            
            if (!response.ok) {
                console.error('[AssetPlacement] Failed to save asset to database:', response.status);
                return;
            }
            
            const data = await response.json();
            console.log('[AssetPlacement] Asset saved to database:', data);
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
     * Load placed assets from database for this grid
     * @param {string} gridCode - The grid code
     */
    async loadPlacedAssets(gridCode) {
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
                        konvaImage.databaseId = assetData.id;
                        
                        console.log('[AssetPlacement] Loaded asset with ID:', assetId);
                    }
                } catch (error) {
                    console.error('[AssetPlacement] Error loading asset:', assetData, error);
                }
            }
            
            this.assetLayer.draw();
            console.log('[AssetPlacement] All assets loaded and drawn');
        } catch (error) {
            console.error('[AssetPlacement] Error loading placed assets:', error);
        }
    }
}

export default AssetPlacementHandler;
