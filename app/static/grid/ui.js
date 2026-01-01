// ui.js
import { stage, debugLayer, container, CELL_SIZE, GRID_WIDTH, GRID_HEIGHT } from './grid.js';

// debug text
const debugText = new Konva.Text({
    x: 10,
    y: 10,
    fontSize: 22,
    fill: "blue",
    text: "debug..."
});
debugLayer.add(debugText);

// update debug text
export function updateDebug() {
    debugText.text(
        "stage pos: " + JSON.stringify(stage.position()) +
        "\nstage scale: " + stage.scaleX() +
        "\ncell size: " + CELL_SIZE +
        "\ngrid size px: " + (GRID_WIDTH * CELL_SIZE) + " × " + (GRID_HEIGHT * CELL_SIZE)
    );
    debugLayer.draw();
}
setInterval(updateDebug, 200);

// resize handler
window.addEventListener("resize", () => {
    stage.width(container.clientWidth);
    stage.height(container.clientHeight);
    debugLayer.draw();
});
