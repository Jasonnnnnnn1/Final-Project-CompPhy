# Change Log

This file records every change made from the original project state (wall collisions working, no ball-ball collision, no restart, corner pockets not registering).

Baseline files at start of this session: `main.py`, `ball.py`, `table.py`, `constants.py`, `cue_stick.py`, `power_bar.py`.

---

## New file: `collisions.py`

- Added `resolve_ball_collisions(balls, restitution, iterations)` to detect overlapping ball pairs and resolve them with elastic collision physics.
- Added private helper `_resolve_pair(a, b, restitution)` that:
  - Separates overlapping balls along the line of centers (positional correction weighted by mass).
  - Computes relative velocity along the collision normal.
  - Applies impulse using `j = -(1 + e) * v_rel / (1/m_a + 1/m_b)` and updates both velocities.
- Runs 3 passes per frame so clustered balls do not stay interpenetrating.

---

## Modified: `constants.py`

- Added `BALL_RESTITUTION = 0.95` for ball-on-ball collision energy loss (separate from cushion restitution).

---

## Modified: `table.py`

- **Pocket detection fix:** `self.pockets` positions were using `(left + RAIL_W//2, top + RAIL_W//2)` which did not match where pockets are drawn on screen.
- Replaced with the same coordinates used in `draw()`:
  - Corner pockets: `(CORNER_POCKET_LENGTH // 2) + 28` inset from each screen margin.
  - Side pockets: `(SIDE_POCKET_LENGTH // 2) - 1` inset from top/bottom margin, centered horizontally.
- Pocket capture radius uses full `CORNER_POCKET_LENGTH` / `SIDE_POCKET_LENGTH` from `constants.py` (scaled real-table cm values). No arbitrary scale factors.

---

## Modified: `main.py`

- **Imports:** Added `from collisions import resolve_ball_collisions`.
- **Initial layout:** Extracted ball starting positions/colors into `INITIAL_LAYOUT` constant for reuse.
- **New helpers:**
  - `create_balls(layout)` — builds the ball list from layout data.
  - `reset_game(balls, cue_stick, layout)` — restores every ball to its start position, zeroes velocity, revives pocketed balls, re-enables cue stick, resets power bar to `INIT_FORCE`.
  - `resolve_wall_collisions(balls, table)` — moved inline cushion checks into a named function (logic unchanged).
- **Game loop:**
  - After `ball.update(dt)`, calls `resolve_ball_collisions(balls)` then `resolve_wall_collisions(balls, table)`.
  - Ball-ball runs before walls so balls bounce off each other first, then cushions.
- **Restart:** Press `R` (`pygame.K_r`) calls `reset_game(...)`.
- **Stopped check:** `all_stopped` now skips dead (pocketed) balls so cue stick reactivates correctly when only pocketed balls remain.

---

## Not changed (intentionally)

- `ball.py` — friction, force application, and drawing unchanged.
- `cue_stick.py` — aiming and shooting unchanged.
- `power_bar.py` — unchanged.

---

## How to verify

1. Run `python main.py`.
2. Shoot the cue ball into object balls — they should scatter with realistic elastic bounces.
3. Press `R` — all balls return to rack positions, velocities cleared, cue stick active again.
4. Roll a ball into a corner pocket — it should disappear when it reaches the visible black hole.

---

## 2026-05-19 — Object ball potting and side pocket fix

### Problem

- Object balls could not reliably pot: `check_pockets` ran but the top/bottom cushion always pushed balls away from side pockets before they reached the capture zone.
- Corner pocket fix worked, but middle (side) pockets broke for the same reason — detection coords were correct but balls never reached them.

### Modified: `table.py`

- Centralized pocket layout in `__init__` (`corner_offset`, `side_offset`, capture radii) so `draw()` and `check_pockets()` use the same numbers.
- **Cushion cutout helpers** (used by wall collision in `main.py`):
  - `is_top_cushion_open(ball)` / `is_bottom_cushion_open(ball)` — skip top/bottom bounce when ball is over a side pocket lane (center ± `side_lane_half_w`) or a corner pocket zone.
  - `is_left_cushion_open(ball)` / `is_right_cushion_open(ball)` — skip left/right bounce near top/bottom corners.
- **`check_pockets` improvements:**
  - Works for all alive balls (cue and object balls); object balls set `alive = False` and are no longer drawn.
  - Zeros velocity on pocket so a potted ball does not keep simulating.
  - Removed duplicate `side_offset` / `corner_offset` literals inside `draw()` — uses `self.corner_offset` and `self.side_offset`.

### 2026-05-19 (follow-up) — Restore real-table measurements only

Per project rule: all sizes come from `constants.py` (9-foot table cm values × `SCALE`). Removed tuning multipliers that were added earlier:

| Removed | Replaced with |
|--------|----------------|
| `CORNER_POCKET_LENGTH * 0.55` capture radius | `c.CORNER_POCKET_LENGTH` |
| `SIDE_POCKET_LENGTH * 0.65` capture radius | `c.SIDE_POCKET_LENGTH` |
| `SIDE_POCKET_LENGTH * 0.55` cushion lane | `c.SIDE_POCKET_LENGTH // 2` |
| `corner_offset + CORNER_POCKET_LENGTH * 0.35` corner lane | `corner_offset` (existing draw alignment) |
| `pr + ball.radius * 0.15` capture fudge | `pr` only (`dx² + dy² ≤ pr²`) |

Cushion cutouts and potting behavior unchanged; only measurement sources were corrected.

### 2026-05-19 (fix) — Pocket art matches pocket detection (no early vanish)

**Bug:** Balls disappeared in the dark cushion “gap” before reaching the black pocket. Detection used a large circle at an old center (`MARGIN + side_offset`), while the black hole was drawn lower in the rail.

**Fix in `table.py`:**
- Play area lip defined as `play_* = margin + RAIL_W` (real rail width from `constants.py`).
- Side pockets: black square mouth flush with `play_top` / `play_bottom`; hole extends into the rail by `SIDE_POCKET_LENGTH`.
- Corner pockets: mouth at play-area corners; hole extends into margin by `CORNER_POCKET_LENGTH`.
- **One definition** for draw + hit test: `pocket_defs` with `rect`, `center`, `size`, `angle`.
- `check_pockets` uses circle-vs-rectangle overlap on that rect (not an oversized circle).
- Removed `corner_offset` / `side_offset` margin hacks that misaligned art and physics.

### Modified: `main.py`

- **`resolve_wall_collisions`:** Only bounces off a cushion when `table.is_*_cushion_open(ball)` is `False` for that edge. Balls can roll into pocket openings on all six pockets.

### How to verify

1. Shoot an object ball into a **middle** (top or bottom) pocket — it should pass the cushion opening and disappear.
2. Corner pockets should still work as before.
3. Object balls potted stay off the table until **R** restart.
4. Cue ball can also pocket (scratch); restart with **R** to reset.

---

## 2026-05-19 — Revert pocket animation; add ghost-ball aim indicator

### Reverted

- Removed pocket roll-in / shrink animation from `ball.py` (pocketing state, `update_pocketing`, etc.).
- `table.py` uses instant `check_pockets()` again when the ball reaches the pocket mouth.
- `main.py` / `collisions.py` no longer reference `pocketing` or `on_table`.

### New file: `ghost_ball.py`

Billiards **ghost ball** collision indicator while aiming (cue stick active):

- Finds the first object ball the cue ball would hit along the shot line (ray vs circle at `2 * BALL_RADIUS` separation).
- **Ghost position** = object center − (object travel direction) × `2 * BALL_RADIUS`, where travel direction points from the object ball toward the mouse (where you want the object ball to go).
- Draws:
  - Semi-transparent white circle = ghost ball (cue contact position)
  - Blue dashed line = cue ball → ghost ball
  - Yellow dashed line = object ball path after contact
- Hides the ghost if another ball blocks the cue-to-ghost path.

Uses only `BALL_RADIUS` from `constants.py` for spacing (real ball diameter on table).

### Modified: `main.py`

- After drawing balls, calls `draw_ghost_indicator(...)` when aiming so the ghost appears on top of the table layout.
- `cue_stick.draw(screen)` unchanged otherwise.

### How to verify

1. Wait until all balls stop; aim at an object ball with the mouse past it.
2. A faint white circle appears where the cue ball must strike (ghost ball).
3. Yellow dashed line shows the object ball’s outgoing direction toward the mouse.
4. Potting is instant again when the ball enters a pocket (no sink animation).

### 2026-05-19 (follow-up) — 8 Ball Pool style ghost visuals

Updated `ghost_ball.py` drawing to match 8 Ball Pool:

| Element | Style |
|--------|--------|
| Ghost ball | Thin **white ring** only (no fill) |
| Cue path | **Solid white** line: cue center → ghost center |
| Object path | **Solid white** line: ghost → through object ball → mouse/aim direction |
| Cue after hit | **Solid white** line from ghost, **perpendicular** to object path (shorter tangent) |

Removed blue/yellow dashed lines and filled ghost circle.

- When the ghost is visible, the colored power-bar aim dashes are hidden so only the white 8 Ball Pool guides show (cue stick still draws).

### 2026-05-19 (fix) — Ghost ball at contact point, not on object ball

**Bug:** Ghost ring drew on top of the object ball when the mouse was on/near the ball or on the cue side of it (`ghost = obj - normalize(mouse - obj) * 2r` pointed the wrong way).

**Fix in `compute_ghost_shot`:**
- If mouse is within one ball diameter of the object center → full-ball aim: object path = cue → object line.
- Otherwise object path = toward mouse; if that would put the ghost on the far side of the object, flip direction so the ghost stays on the **cue side**.
- Ghost position is always exactly `2 * BALL_RADIUS` from object center (touching circles).
- Reject invalid shots where the ghost would not sit between cue and object.

---

## 2026-05-19 — Pocket roll-in animation (realistic potting) [REVERTED]

### Problem

Balls vanished the instant their center entered the pocket zone, which did not look like real pool (no roll into the hole).

### Modified: `ball.py`

- Added pocketing state: `pocketing`, `pocket_center`, `pocket_radius`, `pocket_progress`, `pocket_start_dist`.
- `begin_pocketing(px, py, pocket_radius)` — starts when the ball reaches a pocket mouth; uses `CORNER_POCKET_LENGTH` / `SIDE_POCKET_LENGTH` from the table (no new size constants).
- `update_pocketing(dt)` — moves the ball toward the pocket center, keeps some roll speed (`max(speed, BALL_RADIUS * 6)` so timing scales with table scale), shrinks the drawn radius up to 90% as `pocket_progress` increases, darkens color slightly while sinking.
- `_finish_pocketing()` — sets `alive = False` only after the roll-in completes.
- `on_table` property — `alive` or still `pocketing` (used for physics/cue logic).
- `reset_pocket_state()` — cleared on **R** restart.
- `draw()` — sinking balls render smaller/darker instead of popping off.

### Modified: `table.py`

- Replaced instant `check_pockets()` with `update_pockets(balls, dt)`.
- `_ball_overlaps_pocket()` — entry when ball edge reaches mouth: distance ≤ `pocket_radius + ball.radius` (real measurements only).
- On entry, calls `begin_pocketing` + one `update_pocketing` step same frame.

### Modified: `main.py`

- Calls `table.update_pockets(balls, dt)` instead of `check_pockets`.
- Wall collisions and `all_stopped` skip or include pocketing balls correctly.
- `reset_game` clears pocket state.

### Modified: `collisions.py`

- Skips pairs where either ball is `pocketing` (or off table).

### How to verify

1. Pot any ball — it should roll toward the black hole, shrink, then disappear.
2. Cue stick stays inactive until the sink animation finishes.
3. Corner and side pockets should behave the same way.
