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
            if (!this.gridModule.assetPlacementMode || !this.gridModule.selectedAssetPath) {
                return;
            }

            // Prevent placing on UI elements
            if (e.target === this.stage) {
                const pos = this.stage.getPointerPosition();
                this.placeAsset(pos.x, pos.y);
            }
        });

        // Drag and drop from asset panel
        const gridContainer = document.getElementById('grid-container');
        
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

            const assetData = e.dataTransfer.getData('application/json');
            if (assetData) {
                try {
                    const asset = JSON.parse(assetData);
                    const rect = gridContainer.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    
                    // Convert to stage coordinates
                    const stagePos = this.stage.getPointerPosition();
                    this.placeAsset(stagePos.x, stagePos.y, asset.path);
                } catch (error) {
                    console.error('Error parsing dropped asset:', error);
                }
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
        const path = assetPath || this.gridModule.selectedAssetPath;
        
        if (!path) {
            console.warn('No asset selected');
            return;
        }

        if (!this.assetLoader) {
            console.error('AssetLoader not initialized');
            return;
        }

        try {
            // Create Konva image from SVG
            const konvaImage = await this.assetLoader.createAssetImage(path, x, y, 50, 50);
            
            if (konvaImage) {
                // Add interaction
                this.addAssetInteraction(konvaImage);
                
                // Add to layer
                this.assetLayer.add(konvaImage);
                this.assetLayer.draw();
                
                // Track placed asset
                const assetId = this.assetIdCounter++;
                this.placedAssets.set(assetId, konvaImage);
                konvaImage.assetId = assetId;
                
                console.log(`Asset placed at (${x}, ${y})`);
                
                // Disable placement mode after single placement
                this.gridModule.disableAssetPlacementMode();
            }
        } catch (error) {
            console.error('Error placing asset:', error);
        }
    }

    /**
     * Add interaction handlers to a placed asset
     * @param {Konva.Image} konvaImage - Konva image object
     */
    addAssetInteraction(konvaImage) {
        konvaImage.on('mouseenter', () => {
            this.stage.container.style.cursor = 'move';
            konvaImage.shadowColor('black');
            konvaImage.shadowBlur(10);
            konvaImage.shadowOpacity(0.5);
            this.assetLayer.draw();
        });

        konvaImage.on('mouseleave', () => {
            this.stage.container.style.cursor = 'default';
            konvaImage.shadowOpacity(0);
            this.assetLayer.draw();
        });

        // Right-click context menu
        konvaImage.on('contextmenu', (e) => {
            e.evt.preventDefault();
            this.showAssetContextMenu(e.evt.clientX, e.evt.clientY, konvaImage);
        });

        // Update stage on drag
        konvaImage.on('dragend', () => {
            this.assetLayer.draw();
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
     * Load placed assets from data
     * @param {Array} assetsData - Array of asset data
     */
    async loadPlacedAssets(assetsData) {
        if (!Array.isArray(assetsData)) return;

        for (const assetData of assetsData) {
            // Would need to know the path, which isn't stored in this example
            // This is a placeholder for persistence implementation
            console.log('Loading asset:', assetData);
        }
    }
}

export default AssetPlacementHandler;
