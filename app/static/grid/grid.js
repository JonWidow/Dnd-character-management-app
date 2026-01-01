// grid.js — core grid setup
console.log("grid.js loaded");

// ----- CONSTANTS -----
export const CELL_SIZE = 50;
export const GRID_WIDTH = 40;
export const GRID_HEIGHT = 40;

// ----- CONTAINER -----
export const container = document.getElementById("grid-container");

// Ensure the container has some height (e.g., 60% of viewport)
container.style.width = "100%";
container.style.height = "60vh"; // adjust this as needed

// ----- STAGE -----
export const stage = new Konva.Stage({
    container: "grid-container",
    width: container.clientWidth,
    height: container.clientHeight,
    draggable: true // allow panning
});

const testDiv = document.createElement("div");
testDiv.style.width = "100px";
testDiv.style.height = "100px";
testDiv.style.background = "red";
document.body.appendChild(testDiv);


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

    // background
    gridLayer.add(new Konva.Rect({
        x: 0,
        y: 0,
        width: GRID_WIDTH * CELL_SIZE,
        height: GRID_HEIGHT * CELL_SIZE,
        fill: "#bbbbbb"
    }));

    // vertical lines
    for (let i = 0; i <= GRID_WIDTH; i++) {
        let x = i * CELL_SIZE;
        gridLayer.add(new Konva.Line({
            points: [x, 0, x, GRID_HEIGHT * CELL_SIZE],
            stroke: "black",
            strokeWidth: 2
        }));
    }

    // horizontal lines
    for (let j = 0; j <= GRID_HEIGHT; j++) {
        let y = j * CELL_SIZE;
        gridLayer.add(new Konva.Line({
            points: [0, y, GRID_WIDTH * CELL_SIZE, y],
            stroke: "black",
            strokeWidth: 2
        }));
    }

    // crosshairs at origin
    gridLayer.add(new Konva.Line({ points: [-2000, 0, 2000, 0], stroke: "red", strokeWidth: 4 }));
    gridLayer.add(new Konva.Line({ points: [0, -2000, 0, 2000], stroke: "red", strokeWidth: 4 }));

    gridLayer.draw();
}

// ----- HANDLE WINDOW RESIZE -----
window.addEventListener("resize", () => {
    stage.width(container.clientWidth);
    stage.height(container.clientHeight);
    stage.batchDraw();
});
