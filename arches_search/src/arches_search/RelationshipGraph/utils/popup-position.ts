interface Point {
    x: number;
    y: number;
}

export interface Size {
    width: number;
    height: number;
}

// Where the top-left corner of a popup goes, so that it sits beside the point
// it is about (past `clearance`, which keeps it off the thing at that point)
// and stays inside the stage. It prefers the right of the point, goes to the
// left when it would not fit there, and is level with the point where it can be.
export function placePopup(
    anchor: Point,
    clearance: number,
    popup: Size,
    stage: Size,
    margin: number,
): Point {
    let x = anchor.x + clearance;
    if (x + popup.width > stage.width - margin) {
        x = anchor.x - clearance - popup.width;
    }

    return {
        x: clamp(x, margin, stage.width - popup.width - margin),
        y: clamp(
            anchor.y - popup.height / 2,
            margin,
            stage.height - popup.height - margin,
        ),
    };
}

// A popup bigger than the room it has keeps to the top-left margin
function clamp(value: number, lowest: number, highest: number): number {
    return Math.max(lowest, Math.min(value, highest));
}
