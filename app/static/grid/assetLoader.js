/**
 * Asset Loader - Manages loading and displaying SVG assets on the Konva grid
 */

class AssetLoader {
    constructor(konvaLayer) {
        this.konvaLayer = konvaLayer;
        this.assetCache = new Map(); // Cache loaded SVG content
        this.assetCategories = {
            tokens: 'Character and creature tokens',
            terrain: 'Terrain and tile assets',
            objects: 'Objects, furniture, and props',
            effects: 'Spell effects and visual effects'
        };
    }

    /**
     * Fetch available assets from the server
     * @param {string} category - Optional: filter by category
     * @returns {Promise<Object>} Assets organized by category
     */
    async fetchAvailableAssets(category = null) {
        try {
            const url = category 
                ? `/api/assets/files?category=${category}`
                : '/api/assets/files';
            
            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to fetch assets');
            
            const assets = await response.json();
            console.log('Loaded assets:', assets);
            return assets;
        } catch (error) {
            console.error('Error fetching assets:', error);
            return {};
        }
    }

    /**
     * Fetch asset categories
     * @returns {Promise<Object>} Categories with descriptions
     */
    async fetchCategories() {
        try {
            const response = await fetch('/api/assets/files/categories');
            if (!response.ok) throw new Error('Failed to fetch categories');
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching categories:', error);
            return this.assetCategories;
        }
    }

    /**
     * Load an SVG asset from the server
     * @param {string} assetPath - Path to the asset (e.g., '/static/assets/tokens/dragon.svg')
     * @returns {Promise<string>} SVG content
     */
    async loadSVGAsset(assetPath) {
        // Check cache first
        if (this.assetCache.has(assetPath)) {
            return this.assetCache.get(assetPath);
        }

        try {
            const response = await fetch(assetPath);
            if (!response.ok) throw new Error(`Failed to load asset: ${assetPath}`);
            
            const svgContent = await response.text();
            this.assetCache.set(assetPath, svgContent);
            return svgContent;
        } catch (error) {
            console.error(`Error loading SVG asset ${assetPath}:`, error);
            return null;
        }
    }

    /**
     * Create a Konva Image from an SVG asset
     * @param {string} assetPath - Path to the SVG asset
     * @param {number} x - X position on grid
     * @param {number} y - Y position on grid
     * @param {number} width - Width in pixels
     * @param {number} height - Height in pixels
     * @returns {Promise<Konva.Image>} Konva image object, or null if loading failed
     */
    async createAssetImage(assetPath, x, y, width = 50, height = 50) {
        try {
            console.log(`[AssetLoader] Creating image from: ${assetPath}`);
            
            // Create image element directly from SVG file path
            const img = new Image();
            img.src = assetPath;
            img.crossOrigin = 'anonymous';

            // Return a promise that resolves when image is loaded
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error(`Image loading timeout for ${assetPath}`));
                }, 5000);

                img.onload = () => {
                    clearTimeout(timeout);
                    console.log(`[AssetLoader] SVG image loaded: ${img.width}x${img.height}`);
                    
                    try {
                        // Create canvas to render SVG
                        const canvas = document.createElement('canvas');
                        canvas.width = width;
                        canvas.height = height;
                        const ctx = canvas.getContext('2d');
                        
                        // Draw the image onto canvas
                        ctx.drawImage(img, 0, 0, width, height);
                        console.log(`[AssetLoader] SVG rendered to canvas (${width}x${height})`);
                        
                        // Create Konva image from canvas
                        const konvaImage = new Konva.Image({
                            image: canvas,
                            x: x,
                            y: y,
                            width: width,
                            height: height,
                            draggable: true,
                            name: 'asset'
                        });

                        console.log(`[AssetLoader] Konva image created at (${x}, ${y})`);
                        resolve(konvaImage);
                    } catch (error) {
                        console.error(`[AssetLoader] Error rendering SVG to canvas:`, error);
                        reject(error);
                    }
                };

                img.onerror = () => {
                    clearTimeout(timeout);
                    console.error(`[AssetLoader] Failed to load SVG image: ${assetPath}`);
                    reject(new Error(`Failed to load asset image: ${assetPath}`));
                };
                
                img.onabort = () => {
                    clearTimeout(timeout);
                    console.error(`[AssetLoader] SVG image loading aborted: ${assetPath}`);
                    reject(new Error(`SVG loading aborted: ${assetPath}`));
                };
            });
        } catch (error) {
            console.error(`[AssetLoader] Error creating asset image:`, error);
            return null;
        }
    }

    /**
     * Add an asset to the grid at specified coordinates
     * @param {string} assetPath - Path to the SVG asset
     * @param {number} gridX - Grid column
     * @param {number} gridY - Grid row
     * @param {number} cellSize - Size of each grid cell (default: 50)
     * @param {number} width - Asset width (default: cellSize)
     * @param {number} height - Asset height (default: cellSize)
     */
    async addAssetToGrid(assetPath, gridX, gridY, cellSize = 50, width = null, height = null) {
        const pixelX = gridX * cellSize;
        const pixelY = gridY * cellSize;
        const assetWidth = width || cellSize;
        const assetHeight = height || cellSize;

        const konvaImage = await this.createAssetImage(assetPath, pixelX, pixelY, assetWidth, assetHeight);
        
        if (konvaImage) {
            this.konvaLayer.add(konvaImage);
            this.konvaLayer.draw();
            return konvaImage;
        }
        
        return null;
    }

    /**
     * Create an asset palette/picker UI
     * @param {string} containerId - ID of container element for the palette
     * @param {Function} onAssetSelect - Callback when asset is selected
     */
    async createAssetPalette(containerId, onAssetSelect) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container not found: ${containerId}`);
            return;
        }

        const assets = await this.fetchAvailableAssets();
        const categories = await this.fetchCategories();

        // Create category tabs
        const tabsContainer = document.createElement('div');
        tabsContainer.className = 'asset-tabs flex border-b border-gray-300 mb-4';

        // Create assets grid
        const assetsContainer = document.createElement('div');
        assetsContainer.className = 'asset-grid grid grid-cols-4 gap-2 p-2';

        const renderCategory = (category) => {
            assetsContainer.innerHTML = '';
            const categoryAssets = assets[category] || [];

            if (categoryAssets.length === 0) {
                assetsContainer.innerHTML = '<p class="text-gray-500 col-span-4">No assets in this category</p>';
                return;
            }

            categoryAssets.forEach(asset => {
                const assetButton = document.createElement('button');
                assetButton.className = 'asset-button p-2 border border-gray-300 rounded hover:bg-gray-100 flex flex-col items-center justify-center h-20';
                assetButton.title = asset.name;

                // Try to display SVG thumbnail
                const img = document.createElement('img');
                img.src = asset.path;
                img.className = 'h-12 w-12 object-contain';
                img.onerror = () => {
                    img.style.display = 'none';
                    assetButton.textContent = asset.name;
                    assetButton.className += ' text-xs text-center';
                };

                assetButton.appendChild(img);
                const nameLabel = document.createElement('span');
                nameLabel.className = 'text-xs mt-1 text-center truncate';
                nameLabel.textContent = asset.name;
                assetButton.appendChild(nameLabel);

                assetButton.addEventListener('click', () => {
                    onAssetSelect(asset.path, asset.name);
                });

                assetsContainer.appendChild(assetButton);
            });
        };

        // Create tabs for each category
        Object.keys(categories).forEach(category => {
            const tab = document.createElement('button');
            tab.className = 'asset-tab px-4 py-2 text-sm font-medium border-b-2 border-transparent hover:border-gray-300';
            tab.textContent = category.charAt(0).toUpperCase() + category.slice(1);
            tab.dataset.category = category;

            tab.addEventListener('click', () => {
                document.querySelectorAll('.asset-tab').forEach(t => {
                    t.classList.remove('border-blue-500', 'text-blue-600');
                    t.classList.add('border-transparent');
                });
                tab.classList.add('border-blue-500', 'text-blue-600');
                renderCategory(category);
            });

            tabsContainer.appendChild(tab);
        });

        container.innerHTML = '';
        container.appendChild(tabsContainer);
        container.appendChild(assetsContainer);

        // Render first category by default
        const firstCategory = Object.keys(categories)[0];
        if (firstCategory) {
            tabsContainer.querySelector(`[data-category="${firstCategory}"]`).click();
        }
    }

    /**
     * Clear the asset cache to free memory
     */
    clearCache() {
        this.assetCache.clear();
    }

    /**
     * Get cache stats
     * @returns {Object} Cache statistics
     */
    getCacheStats() {
        return {
            cachedAssets: this.assetCache.size,
            assetPaths: Array.from(this.assetCache.keys())
        };
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AssetLoader;
}
