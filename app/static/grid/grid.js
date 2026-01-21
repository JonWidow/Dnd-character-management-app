// grid.js – core grid setup
console.log("grid.js loaded");

// ----- CONSTANTS -----
export const CELL_SIZE = 50;
export const GRID_WIDTH = 40;
export const GRID_HEIGHT = 40;

// ----- CONTAINER -----
export const container = document.getElementById("grid-container");

// Ensure the container has some height
container.style.width = "100%";
container.style.height = "calc(100vh - 150px)";

// ----- STAGE -----
export const stage = new Konva.Stage({
    container: "grid-container",
    width: container.clientWidth,
    height: container.clientHeight,
    draggable: true
});


// ----- LAYERS -----
export const gridLayer = new Konva.Layer();
export const debugLayer = new Konva.Layer();
export const tokenLayer = new Konva.Layer();

stage.add(gridLayer);
stage.add(debugLayer);
stage.add(tokenLayer);

// ----- DRAW GRID -----
export function drawDebugGrid() {
    gridLayer.destroyChildren(); // clear previous

    // background - warm charcoal stone
    gridLayer.add(new Konva.Rect({
        x: 0,
        y: 0,
        width: GRID_WIDTH * CELL_SIZE,
        height: GRID_HEIGHT * CELL_SIZE,
        fill: "#3d3d3d"
    }));

    // vertical lines - complementary bronze/copper accent
    for (let i = 0; i <= GRID_WIDTH; i++) {
        let x = i * CELL_SIZE;
        gridLayer.add(new Konva.Line({
            points: [x, 0, x, GRID_HEIGHT * CELL_SIZE],
            stroke: "#b8860b",
            strokeWidth: 2
        }));
    }

    // horizontal lines - complementary bronze/copper accent
    for (let j = 0; j <= GRID_HEIGHT; j++) {
        let y = j * CELL_SIZE;
        gridLayer.add(new Konva.Line({
            points: [0, y, GRID_WIDTH * CELL_SIZE, y],
            stroke: "#b8860b",
            strokeWidth: 2
        }));
    }

    gridLayer.draw();
}

// ----- HANDLE WINDOW RESIZE -----
window.addEventListener("resize", () => {
    stage.width(container.clientWidth);
    stage.height(container.clientHeight);
    stage.batchDraw();
});

// ----- ZOOM CONFIGURATION -----
const ZOOM_CONFIG = {
    minScale: 0.3,
    maxScale: 3,
    zoomSpeed: 0.1
};

// ----- MOUSE WHEEL ZOOM (Desktop) -----
container.addEventListener('wheel', (e) => {
    e.preventDefault();
    
    // Get mouse position relative to stage
    const rect = container.getBoundingClientRect();
    const pointerX = e.clientX - rect.left;
    const pointerY = e.clientY - rect.top;
    
    const oldScale = stage.scaleX();
    const direction = e.deltaY > 0 ? -1 : 1;
    const newScale = Math.max(
        ZOOM_CONFIG.minScale,
        Math.min(ZOOM_CONFIG.maxScale, oldScale + direction * ZOOM_CONFIG.zoomSpeed)
    );
    
    const scaleFactor = newScale / oldScale;
    
    // Pan to keep the mouse position fixed
    const newX = pointerX - (pointerX - stage.x()) * scaleFactor;
    const newY = pointerY - (pointerY - stage.y()) * scaleFactor;
    
    stage.scaleX(newScale);
    stage.scaleY(newScale);
    stage.x(newX);
    stage.y(newY);
    stage.batchDraw();
});

// ----- TOUCH PINCH ZOOM (Mobile) -----
let lastDistance = 0;

container.addEventListener('touchstart', (e) => {
    if (e.touches.length === 2) {
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const dx = touch2.clientX - touch1.clientX;
        const dy = touch2.clientY - touch1.clientY;
        lastDistance = Math.sqrt(dx * dx + dy * dy);
    }
});

container.addEventListener('touchmove', (e) => {
    if (e.touches.length === 2) {
        e.preventDefault();
        
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const dx = touch2.clientX - touch1.clientX;
        const dy = touch2.clientY - touch1.clientY;
        const currentDistance = Math.sqrt(dx * dx + dy * dy);
        
        if (lastDistance === 0) {
            lastDistance = currentDistance;
            return;
        }
        
        const oldScale = stage.scaleX();
        const scaleFactor = currentDistance / lastDistance;
        const newScale = Math.max(
            ZOOM_CONFIG.minScale,
            Math.min(ZOOM_CONFIG.maxScale, oldScale * scaleFactor)
        );
        
        // Get center point between two touches
        const rect = container.getBoundingClientRect();
        const centerX = (touch1.clientX + touch2.clientX) / 2 - rect.left;
        const centerY = (touch1.clientY + touch2.clientY) / 2 - rect.top;
        
        const scaleChange = newScale / oldScale;
        const newX = centerX - (centerX - stage.x()) * scaleChange;
        const newY = centerY - (centerY - stage.y()) * scaleChange;
        
        stage.scaleX(newScale);
        stage.scaleY(newScale);
        stage.x(newX);
        stage.y(newY);
        stage.batchDraw();
        
        lastDistance = currentDistance;
    }
});

container.addEventListener('touchend', () => {
    lastDistance = 0;
});
