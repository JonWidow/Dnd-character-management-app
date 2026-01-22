# Asset System Testing Guide

## What's Been Fixed

1. **AssetLoader Export**: Added `window.AssetLoader = AssetLoader` to make the class available to the grid module
2. **Enhanced Logging**: Added comprehensive logging throughout the asset placement pipeline to help debug any issues
3. **Error Handling**: Improved error handling with stack traces
4. **Test Button**: Added a "Test: Place Grass" button to simplify testing

## How to Test

1. **Open the Grid**: Visit `http://localhost:5000/grid/test123` (or your grid code)
2. **Open Developer Console**: Press `F12` and go to the "Console" tab
3. **Click the Test Button**: Look for the orange "Test: Place Grass" button in the Assets panel
4. **Check the Console**: You should see logs like:
   ```
   [AssetPanel] Test button clicked
   [AssetPanel] Handlers ready, calling placeAsset
   [AssetPlacement] placeAsset called with: {x: 200, y: 200, assetPath: '/static/assets/terrain/grass.svg'}
   [AssetLoader] createAssetImage called with: {...}
   [AssetLoader] Image element created, src=/static/assets/terrain/grass.svg
   [AssetLoader] SVG image loaded: (width)x(height)
   [AssetLoader] SVG rendered to canvas (50x50)
   [AssetLoader] Konva image created at (200, 200)
   [AssetPlacement] Asset image created, adding to layer
   [AssetPlacement] Asset added to layer and drawn
   [AssetPlacement] Asset placed with ID: 0
   ```

## If You See Errors

### "AssetLoader not initialized"
- The AssetLoader instance wasn't created properly. Check that `window.assetLoader` is defined in the console.

### "SVG image loading timeout" 
- The SVG file didn't load. Check that the URL `/static/assets/terrain/grass.svg` is accessible by opening it directly in the browser.

### "Konva not defined"
- The Konva.js library didn't load. Check that the CDN script is working: `https://unpkg.com/konva@9/konva.min.js`

### "Layer doesn't exist"
- The assetLayer wasn't created properly. Check that `window.gridModule.assetLayer` exists.

## What Should Happen

If everything works:
1. A grass tile should appear on the grid at position (200, 200) pixels from the top-left
2. You should be able to hover over it (cursor changes to "move")
3. You should be able to drag it around
4. Right-click should show a context menu (rotate, duplicate, delete)

## Files Modified

- `/app/static/grid/assetLoader.js` - Added enhanced logging and error handling
- `/app/static/grid/assetPlacement.js` - Added detailed logging at each step
- `/app/templates/asset_panel.html` - Added test button with click handler
- `/app/static/grid/assetLoader.js` - Exported AssetLoader to window object

## Layer Order

The rendering order is (bottom to top):
1. Grid Layer (grid lines)
2. Asset Layer (terrain, objects, effects)
3. Debug Layer (diagnostics)
4. Token Layer (characters - on top)

This ensures tokens always appear above terrain assets.
