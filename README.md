# MCGLM — PvP Toolkit for Dawn (formerly Feather) / Minecraft 26.2

A collection of external macros (AutoHotkey v2), Python overlay tools, and two
small Fabric mods for 1v1 PvP on the server you described (anarchy, no
anti-cheat, only rule is "don't reveal real-life identity"). None of these
tools record anything about the person behind an account — just in-game names,
positions, and timestamps.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Requirements](#requirements)
3. [Feature 1 — Shield-Breaker Macro](#feature-1--shield-breaker-macro)
4. [Feature 2 — Frame-Perfect Gapple / Food Swap](#feature-2--frame-perfect-gapple--food-swap)
5. [Feature 3 — Trajectory Predictor + Aim Overlay](#feature-3--trajectory-predictor--aim-overlay)
6. [Feature 4 — Logout Spot Tracker](#feature-4--logout-spot-tracker)
7. [Feature 5 — Status HUD Overlay](#feature-5--status-hud-overlay)
8. [Feature 6 — 1.50× Walk/Sprint Speed (testing)](#feature-6--150-walksprint-speed-testing)
9. [The MCGLM Data Feed](#the-mcglm-data-feed)
10. [Building the Fabric Mods](#building-the-fabric-mods)
11. [Dawn Compatibility](#dawn-compatibility)
12. [Troubleshooting](#troubleshooting)

---

## Quick Start

**Macros only (features 1 & 2) — no mods needed:**
1. Install [AutoHotkey v2](https://www.autohotkey.com/) (v1 will **not** run these scripts).
2. Double-click `macros/shield_breaker.ahk` and `macros/gapple_swap.ahk`.
3. Open Minecraft, join the server, arrange your hotbar as shown in each script's config block.
4. The hotkeys are live immediately.

**Full toolkit (features 3–6):**
1. Do the macros step above.
2. Build the two Fabric mods (`feed-mod/` and `speedmod/`) — see [Building the Fabric Mods](#building-the-fabric-mods).
3. Install Python 3.10+ and run `pip install -r requirements.txt`.
4. Launch the game with both mods loaded.
5. Run the overlays: double-click `run_overlays.bat`, or open three terminals and run each `python/` script individually.

---

## Requirements

| Component | Needed for | Install |
|---|---|---|
| **AutoHotkey v2** | Features 1, 2 | [autohotkey.com](https://www.autohotkey.com/) — get v2, not v1 |
| **Python 3.10+** | Features 3, 4, 5 | [python.org](https://www.python.org/) — check "Add to PATH" |
| **pygame + pynput** | Features 3, 4, 5 | `pip install -r requirements.txt` |
| **Java 25 + Gradle 9.5.1** | Fabric mod builds | [adoptium.net](https://adoptium.net/) for Java; the repo includes Gradle wrappers |
| **Fabric API 0.154.2+26.2** | feed-mod, speedmod | Enable Fabric API in the Dawn Fabric 26.2 profile |

---

## Hotbar Layout

Both macros and the feed mod assume this layout by default. Edit the config
constants at the top of each script if yours differs.

| Hotbar Slot | Item | Used by |
|---|---|---|
| 1 | Sword (main weapon) | shield_breaker, gapple_swap |
| 2 | Axe (shield-breaker) | shield_breaker |
| 3 | Golden Apples | gapple_swap |
| 8 | Regular food (steak, golden carrot, etc.) | gapple_swap |

---

## Feature 1 — Shield-Breaker Macro

**File:** `macros/shield_breaker.ahk`

**What it does:** When you press/hold the hotkey, it instantly swaps to your
axe slot, attacks once (rolling the shield-disable chance), then snaps back
to your sword slot. While held, it repeats every 300ms so you can hammer
axe hits through a shield.

**How to use:**
1. Open `shield_breaker.ahk` in any text editor and verify `AxeSlot = 2` and `SwordSlot = 1` match your hotbar.
2. Double-click the file to run it (a green "H" icon appears in your system tray).
3. In-game, hold **mouse forward side button** (XButton2) to trigger the combo. Change this to any key you want by editing the `*XButton2::` line.
4. Press **F10** to pause/resume all hotkeys in the script.

**How it works:**
- Sends the hotbar slot number as a key press (same as pressing 1–9 in-game).
- Waits 25ms for the server to acknowledge the swap.
- Sends a left-click (the axe hit).
- Waits 35ms, then sends the sword slot.
- If held, repeats every 300ms (within vanilla attack cooldown).
- Uses `timeBeginPeriod(1)` for 1ms Windows timer accuracy — without this, Sleep() has ~15ms jitter.

**Tuning:**
- `SwapDelay` (default 25): increase if the axe swing registers with the sword instead of the axe (packet ordering).
- `BackDelay` (default 35): increase if you see the axe in your hand for too long.
- `HitEvery` (default 300): minimum ms between axe hits while held. Lower = faster hits but risks cooldown skips.
- `Repeat` (default true): set to false for single-tap behavior.

**Vanilla mechanics note:** Axe shield-disable is chance-based in Java 26.2
versions (25% base chance + 5% per Efficiency enchantment level on the axe).
This is exactly why the macro repeats while held — you'll see "Shield disabled!"
in chat when the roll succeeds.

---

## Feature 2 — Frame-Perfect Gapple / Food Swap

**File:** `macros/gapple_swap.ahk`

**What it does:** Press the hotkey → instantly swaps to the food slot → holds
right-click for the exact eating duration → releases → snaps back to the weapon
slot the moment consumption finishes.

**How to use:**
1. Open `gapple_swap.ahk` and verify slots: `GappleSlot = 3`, `FoodSlot = 8`, `WeaponSlot = 1`.
2. Double-click to run.
3. In-game:
   - **Mouse back side button (XButton1)** → eat a golden apple from slot 3.
   - **F6** → eat regular food from slot 8.
4. **F10** pauses/resumes.

**Timing explanation:**
Eating any food in Java Edition takes exactly **32 game ticks**. At 20 TPS
(ticks per second), that is exactly **1600 ms**. The script holds right-click
for `HoldMs = 1660` by default — the extra 60ms is a safety pad so a single
laggy tick doesn't swallow the final tick of consumption.

**Important:** If you release right-click before the full 32 ticks, eating
progress **resets to zero**. You don't get partial progress. This is why the
hold time is deliberately longer than 1600ms — raising it further is always
safe (you just stand still holding the apple slightly longer), but lowering it
below 1600 will cause dropped eats.

**Tuning:**
- `HoldMs` (default 1660): raise in 20ms increments if eats are getting
  cancelled on a laggy connection. Lower if you want faster cycles and have
  a stable connection.
- `SwapInDelay` (default 40): time between slot swap and starting the hold.
- `SwapOutDelay` (default 30): time between releasing and swapping back.
- **Do not hold right-click yourself during the sequence** — the script owns RMB until it finishes.

---

## Feature 3 — Trajectory Predictor + Aim Overlay

**File:** `python/trajectory_overlay.py`

**What it does:** Two modes:
- **Demo mode** (`--demo`): No game needed. Prints a pitch-to-range table and
  draws a side-view parabola of the projectile arc. Use this to verify the
  physics constants are correct for your version.
- **Live mode** (default): Subscribes to the MCGLM feed mod, picks the best
  nearby target, solves for the optimal launch angle every frame (with target
  leading for moving players), and draws a transparent overlay showing aim
  error and a lock indicator. Optionally nudges your crosshair toward the
  solution (aim assist) and auto-releases your bow draw when locked.

**Physics constants (Java Edition 26.2):**

| Projectile | Launch speed | Drag/tick | Gravity/tick² |
|---|---|---|---|
| Bow | 3.00 blocks/tick | ×0.99 | −0.05 |
| Crossbow | 3.15 blocks/tick | ×0.99 | −0.05 |
| Ender Pearl | 1.50 blocks/tick | ×0.98 | −0.03 |

The solver simulates each tick step-by-step (position += velocity, then apply
drag and gravity) and finds the pitch angle that minimizes closest-approach
distance to the target. For moving targets, it iterates: estimate flight time,
aim at the predicted position, re-estimate, repeat (4 iterations, converges in
<1ms).

**How to use (demo):**
```
python trajectory_overlay.py --demo bow
python trajectory_overlay.py --demo pearl --pitch 20
python trajectory_overlay.py --demo crossbow
```

**How to use (live — requires feed-mod):**
```
python trajectory_overlay.py
```
Hotkeys:
| Key | Action |
|---|---|
| **F4** | Cycle projectile: bow → crossbow → pearl |
| **F7** | Toggle aim assist (smoothly nudges crosshair toward solution) |
| **F8** | Toggle auto-fire (releases bow draw when crosshair is within 1° of solution) |
| **F9** | Quit the overlay |

**Calibration — critical step:**
Set `SENSITIVITY = 0.5` at the top of the file to match your in-game
Options → Sensitivity slider:
- Slider at 100% → `0.5`
- Slider at 50% → `0.25`
- The formula is: `slider_percent / 100 / 2`

If aim assist over-steers (oscillates around the target), lower the value.
If it under-steers (never quite reaches the solution), raise it.

**Overlay display:**
- **Yellow chevrons** near the crosshair show how far off your aim is (horizontal = yaw error, vertical = pitch error).
- **Green circle** around the crosshair appears when you're within 1° of the solution (locked).
- **Text readout** shows target name, distance, flight time in ticks, miss distance, and the recommended yaw/pitch.

**Game requirements:**
- Windowed or borderless fullscreen. Exclusive fullscreen cannot be overdrawn by an external overlay.
- Feed-mod must be installed and running (see "The MCGLM Data Feed" below).

---

## Feature 4 — Logout Spot Tracker

**File:** `python/logout_tracker.py`

**What it does:** When a player disconnects from the server, the feed mod
captures their last known position and sends it to the Python tool. The tool
stores logout spots in `logout_spots.json` and renders two things:
1. A **ghost list** panel (top-right corner) showing each logout with name, time ago, distance, and compass direction from you.
2. A **top-down radar** (bottom-left corner) with red dots at logout positions relative to you (blue dot = you).

When a player reconnects, their ghost is automatically cleared.

**How to use:**
```
python logout_tracker.py                    # overlay + radar
python logout_tracker.py --no-overlay       # console log only (no pygame window)
```
Press **F9** to quit the overlay.

**What it stores:** In-game name, x/y/z coordinates, dimension, and Unix
timestamp. Nothing about the person behind the account.

**How the radar works:**
- Center of the circle = your position.
- North (−Z) is up on the radar.
- Each grid square = `SCALE` blocks (default 2.0; edit at the top of `run_overlay()`).
- Only shows logouts in your current dimension.
- Red dots fade when the player reconnects.

---

## Feature 5 — Status HUD Overlay

**File:** `python/status_hud.py`

**What it does:** Reads your local player state from the feed mod and draws a
clean HUD panel in the top-left corner of your screen showing:

- **Health bar**: 10 heart segments, red fill, with numeric HP.
- **Armor bar**: 10 segments, blue fill.
- **Armor durability**: percentage bar (green → yellow → red as it drops).
- **Hunger bar**: 10 drumstick segments, gold fill.
- **Held item**: name of your mainhand item.
- **Offhand item**: name of your offhand item.
- **Held durability**: percentage bar for your held weapon/tool (appears only if damageable).
- **Totem count**: numeric count; red warning dot when at zero.
- **Bow charge bar**: fills as you draw your bow, turns green at full charge.
- **Active effects**: up to 3 potion effects with remaining duration in seconds.

**How to use:**
```
python status_hud.py
```
Press **F9** to quit. The panel auto-hides (shows "waiting for feed...") when
the feed mod isn't sending data.

---

## Feature 6 — 1.50× Walk/Sprint Speed (testing)

**File:** `speedmod/` (Fabric mod)

**What it does:** Adds a permanent +50% `ADD_MULTIPLIED_TOTAL` modifier to the
`generic.movement_speed` attribute of your player entity. This makes you
slightly faster in all situations — walking, sprinting, swimming, flying.

**Why a mod and not a macro:** Movement speed is an attribute stored inside the
client's living-entity instance. No amount of keyboard/mouse input can change
it from outside the game process. You have to modify the attribute from within.

**Expected speeds:**
| Movement | Vanilla | With 1.50× mod |
|---|---|---|
| Walking | 4.317 b/s | ~6.48 b/s |
| Sprinting | 5.612 b/s | ~8.42 b/s |
| Sneaking | 1.30 b/s | ~1.95 b/s |

**Testing warning:** A 1.50× speed increase can cause server corrections,
rubber-banding, or anti-cheat action. The modifier is transient (not saved with
your player data), so it re-applies on world join, dimension change, or server
switch.

**Tuning:** The only config value is `SPEED_MULTIPLIER = 0.50` in
`SpeedMod.java`. Reduce it before normal use if the server corrects movement.

---

## The MCGLM Data Feed

Features 3, 4, and 5 need live game data that Python cannot read directly
(encrypted protocol, no public memory API). The `feed-mod/` Fabric mod
broadcasts your state as JSON datagrams over local UDP to `127.0.0.1:5010`.

**Message types** (one JSON object per UDP datagram):

```jsonc
// Local player state (sent every tick)
{"t":"p", "x":0.0, "y":64.0, "z":0.0, "yaw":0.0, "pitch":0.0,
 "vx":0.0, "vy":0.0, "vz":0.0,
 "hp":20.0, "max_hp":20.0, "armor":15.0, "armor_dur":0.92,
 "held_dur":0.85, "food":20, "totems":2,
 "held":"minecraft:netherite_sword", "off":"minecraft:totem_of_undying",
 "using_item":false, "use_ticks":0,
 "active_item":"minecraft:bow",
 "dim":"minecraft:overworld",
 "effects":[{"id":"minecraft:speed","ticks":172}]}

// Nearby player (sent every tick per player in range)
{"t":"tgt", "id":123, "name":"playername",
 "x":..,"y":..,"z":..,"vx":..,"vy":..,"vz":..,"dim":".."}

// Player disconnected
{"t":"logout", "name":"playername", "x":..,"y":..,"z":..,"dim":".."}

// Player joined / respawned (clears their ghost)
{"t":"login", "name":"playername"}
```

**Port sharing:** Only one process can bind a UDP port, so whichever Python
tool starts first grabs port 5010 and relays all datagrams to 5011 and 5012.
This means you can run all three overlays (trajectory, logout tracker, HUD)
simultaneously and they all receive the same data.

**Security:** Everything stays on `127.0.0.1` (localhost). No data leaves your
machine. No data about real people is collected or transmitted.

---

## Building the Fabric Mods

Both mods (`feed-mod/` and `speedmod/`) follow the same build process:

### Step 1: Match the Minecraft profile

The included projects target **Minecraft 26.2**, Java 25, Fabric Loader
0.19.3, and Fabric API 0.154.2+26.2. In Dawn, use a **Fabric 26.2** profile.
A jar built for another Minecraft minor version is not interchangeable.

### Step 2: Build the included projects

From PowerShell in the repository root:
```
cd feed-mod
.\gradlew.bat build
cd ..\speedmod
.\gradlew.bat build
```

The installable jars are `feed-mod\build\libs\mcglm-feed-1.0.0.jar` and
`speedmod\build\libs\mcglm-speed-1.0.0.jar`.

### Step 3: Add them to Dawn

In Dawn's selected Fabric profile, open the Mods area and add both local
Fabric jars. Enable them before launching. If the launcher has no local-mod
control, copy both jars into that profile's `mods` directory. Fabric API must
also be enabled; MCGLM does not bundle it.

The old template-copy workflow is no longer needed because both directories
are complete Fabric/Loom projects.

### Version changes

If your profile is not 26.2, update the version properties in
`feed-mod/gradle.properties` and `speedmod/gradle.properties` together, then
rebuild. Mojang names and mixin methods can change between minor versions, so a
successful build is required before installing the jars.

### Historical template workflow (do not use for this project)

This old template workflow is retained only as historical context. Do not use
it: the repository already contains complete 26.2 projects and uses Mojang's
official names rather than Yarn mappings.

The 26.2 source, metadata, and mixin resources are already present in the
two module directories. Do not copy them into a separate old-version template.

### Historical template notes

The template-copy notes above are obsolete. Build the included modules directly
and install their jars through Dawn.

### Historical Yarn mapping notes

This section is retained only as a warning. Minecraft 26.2 uses Mojang's
official names; the current source no longer uses Yarn mappings.

Field and method names in Yarn change between minor Minecraft versions. The code
has comments at every drift-prone spot. If compilation fails, open the named
class in your IDE, find the equivalent member, and update the single line.
Known drift points:

| Historical pre-26.1 | 26.1+ |
|---|---|
| Yarn names | Mojang names |

---

## Dawn Compatibility

**Straightforward — no issues:**

| Feature | Works on Dawn? | Notes |
|---|---|---|
| **1. Shield-breaker macro** | ✅ Yes | Pure external input — Dawn does not load it. |
| **2. Gapple swap macro** | ✅ Yes | Runs as a standalone AHK process. |
| **6. Speed mod** | ✅ Yes, with custom Fabric mods enabled | Add the jar through Dawn. |

**Works, but requires configuration:**

| Feature | Works on Dawn? | Notes |
|---|---|---|
| **3. Trajectory overlay** | ✅ Yes (with feed-mod) | Requires the feed Fabric mod. See below. |
| **4. Logout tracker** | ✅ Yes (with feed-mod) | Same — requires the feed mod. |
| **5. Status HUD** | ✅ Yes (with feed-mod) | Same. |

**About loading third-party mod jars on Dawn:**

The client is now called Dawn, formerly Feather, and advertises support for
adding your own Fabric mods. Use Dawn's local-mod
control when available; if a particular release blocks custom jars, use a
normal Fabric 26.2 profile in the official launcher with the same server and
account. The Python overlays and AHK macros remain external to Dawn and do
not belong in the `mods` directory.

**The AHK macros (features 1 & 2) always work regardless** — they're separate
processes sending keyboard/mouse input to whatever window is focused. Dawn
doesn't need to load those external tools.

---

## Troubleshooting

### Macros don't seem to do anything in-game

- **Run both the script and the game at the same privilege level.** If Minecraft is running as admin but the AHK script is not (or vice versa), Windows blocks the input. Right-click the AHK script → "Run as administrator" if the game runs elevated.
- **Verify your hotbar matches the slot numbers.** Open the script and check the config block. The slot numbers are 1–9, matching the hotbar left to right.
- **Another program is consuming the hotkey.** Close Discord, OBS, or other overlay tools that might bind mouse side buttons or F-keys.

### Eats get cancelled (gapple swap)

- Raise `HoldMs` in 20ms increments. Start at 1700, go to 1800 if needed.
- Make sure you're not pressing right-click yourself during the sequence.
- On very laggy connections (200ms+), you may need `HoldMs` of 2000+.

### Axe swap shows sword instead of axe (shield-breaker)

- Raise `SwapDelay` from 25 to 50ms. The slot-change packet might arrive after the attack packet on slow connections.
- Make sure you're not already holding right-click (blocking with a shield) when you press the macro — it sends left-click, not right-click.

### Python overlays don't appear

- **Game must be in windowed or borderless mode.** Exclusive fullscreen owns the entire screen and cannot be overdrawn.
- Run `pip install -r requirements.txt` from the MCGLM directory.
- If you get `ModuleNotFoundError: pygame`, Python isn't finding the package. Try `python -m pip install pygame pynput`.

### Python overlays show "waiting for feed..."

- The feed-mod Fabric mod must be loaded in the game. Check your mods list.
- Verify the mod compiled and loaded without errors (check the game log for "MCGLM feed" or mixin errors).
- If the Python tool says "port 5010 is taken", another MCGLM tool grabbed it first — that's fine, the relay will forward data.

### Solver gives bad aim / over-steers / under-steers

- **Set SENSITIVITY correctly.** This is the #1 issue. Open Minecraft Options, note your sensitivity percentage, and set `SENSITIVITY = percentage / 100 / 2` in `trajectory_overlay.py`.
- The aim-assist `MAX_STEP_DEG` (default 5.0) controls how fast the crosshair moves per frame. Lower it for smoother, slower tracking. Raise it for snappier tracking.
- The `DEADBAND_DEG` (default 0.25) is the "close enough" threshold. If your crosshair jitters around the solution at low values, raise this.

### Mod won't compile (Gradle errors)

- Make sure Dawn is using a **Fabric 26.2** profile and that Java 25 is installed.
- Run `gradlew.bat build --refresh-dependencies` from the affected module.
- Do not copy a 1.21.x jar into a 26.2 profile; these are different toolchain generations.

---

## File Listing

```
MCGLM/
├── README.md                          ← this file
├── requirements.txt                   ← pip install -r requirements.txt
├── run_overlays.bat                   ← launches all three Python overlays at once
├── .gitignore
│
├── macros/
│   ├── shield_breaker.ahk             ← Feature 1
│   └── gapple_swap.ahk                ← Feature 2
│
├── python/
│   ├── mc_feed.py                    ← shared UDP listener + overlay window setup
│   ├── trajectory_overlay.py          ← Feature 3
│   ├── logout_tracker.py              ← Feature 4
│   ├── status_hud.py                  ← Feature 5
│   └── logout_spots.json              ← (generated at runtime — gitignored)
│
├── feed-mod/
│   ├── README.md                      ← build instructions
│   └── src/main/java/com/mcglm/feed/
│       ├── FeedMod.java               ← tick-based player/target broadcaster
│       └── PlayerRemoveMixin.java     ← logout detection mixin
│
└── speedmod/
    ├── README.md                      ← build instructions
    └── src/main/java/com/mcglm/speed/
        └── SpeedMod.java              ← +50% testing movement speed modifier
```

---

## Point It Only Where It's Allowed

You described a server where anything except doxxing goes. On servers with
actual rules or anti-cheat systems, everything here is bannable. These tools are
designed for the environment you specified — keep them pointed at the anarchy box.
