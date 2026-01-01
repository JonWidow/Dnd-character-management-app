// tokens.js
import { tokenLayer } from './grid.js';

export function addTestToken() {
    let token = new Konva.Circle({
        x: 100,
        y: 100,
        radius: 40,
        fill: "red",
        stroke: "black",
        strokeWidth: 4,
        draggable: true
    });
    tokenLayer.add(token);

    let label = new Konva.Text({
        x: 70,
        y: 90,
        text: "Test",
        fontSize: 22,
        fill: "white"
    });
    tokenLayer.add(label);

    token.on("dragmove", () => {
        label.position({ x: token.x() - 30, y: token.y() - 10 });
        tokenLayer.batchDraw();
    });

    tokenLayer.draw();
}
