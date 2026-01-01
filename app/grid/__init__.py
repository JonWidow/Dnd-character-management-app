# /opt/dnd/grid/__init__.py
from flask import Blueprint, render_template
from app.extensions import socketio
from flask_socketio import join_room, leave_room, emit

# All grid routes will live under /grid/...
grid_bp = Blueprint("grid", __name__, url_prefix="/grid")

# ---------- Simple in-memory state for MVP ----------
# sessions: { code: {"w":20,"h":13,"cell_px":48,"tokens":{id:tok},"next_id":1} }
grids = {}

def _room(code: str) -> str:
    return f"grid:{code}"

def _get_grid(code: str):
    g = grids.get(code)
    if not g:
        g = {"w": 20, "h": 13, "cell_px": 48, "tokens": {}, "next_id": 1}
        grids[code] = g
    return g

# ---------- HTTP route ----------
@grid_bp.route("/<code>")
def grid_view(code):
    return render_template("grid.html", code=code)

# ---------- Socket.IO handlers ----------
@socketio.on("join_grid")
def on_join_grid(data):
    code = (data or {}).get("code")
    user = (data or {}).get("user") or "anon"
    if not code:
        emit("error", {"msg": "missing code"})
        return
    _get_grid(code)  # ensure exists
    join_room(_room(code))
    print(f"[socket] {user} joined {code}")
    emit("presence", {"user": user, "action": "join"}, to=_room(code))

@socketio.on("leave_grid")
def on_leave_grid(data):
    code = (data or {}).get("code")
    user = (data or {}).get("user") or "anon"
    leave_room(_room(code))
    emit("presence", {"user": user, "action": "leave"}, to=_room(code))

@socketio.on("request_state")
def on_request_state(data):
    code = (data or {}).get("code")
    g = _get_grid(code)
    tokens = list(g["tokens"].values())
    print(f"[socket] state for {code}: {len(tokens)} tokens")
    emit("state", {
        "exists": True,
        "grid": {"w": g["w"], "h": g["h"], "cell_px": g["cell_px"], "name": code},
        "tokens": tokens
    })

@socketio.on("spawn_token")
def on_spawn_token(data):
    code = (data or {}).get("code")
    if not code:
        return
    g = _get_grid(code)
    tid = g["next_id"]; g["next_id"] += 1
    tok = {
        "id": tid,
        "name": (data or {}).get("name") or f"T{tid}",
        "x": int((data or {}).get("x", 0)),
        "y": int((data or {}).get("y", 0)),
        "color": (data or {}).get("color") or "#444444",
        "character_id": (data or {}).get("character_id")
    }
    # clamp
    tok["x"] = max(0, min(g["w"] - 1, tok["x"]))
    tok["y"] = max(0, min(g["h"] - 1, tok["y"]))
    g["tokens"][tid] = tok
    print(f"[socket] spawn in {code}: id={tid} @ ({tok['x']},{tok['y']})")

    emit("token_spawned", tok, to=_room(code))
    # optional full state push
    emit("state", {
        "exists": True,
        "grid": {"w": g["w"], "h": g["h"], "cell_px": g["cell_px"], "name": code},
        "tokens": list(g["tokens"].values())
    }, to=_room(code))

@socketio.on("move_token")
def on_move_token(data):
    code = (data or {}).get("code")
    tid  = int((data or {}).get("token_id", 0))
    x    = int((data or {}).get("x", 0))
    y    = int((data or {}).get("y", 0))
    g = _get_grid(code)
    tok = g["tokens"].get(tid)
    if not tok:
        return
    x = max(0, min(g["w"] - 1, x))
    y = max(0, min(g["h"] - 1, y))
    tok["x"], tok["y"] = x, y
    print(f"[socket] move in {code}: id={tid} -> ({x},{y})")
    emit("token_moved", {"token_id": tid, "x": x, "y": y}, to=_room(code), include_self=True)

@socketio.on("remove_token")
def on_remove_token(data):
    code = (data or {}).get("code")
    tid  = int((data or {}).get("token_id", 0))
    g = _get_grid(code)
    if tid in g["tokens"]:
        del g["tokens"][tid]
        emit("token_removed", {"token_id": tid}, to=_room(code))
