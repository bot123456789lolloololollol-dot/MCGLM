#!/usr/bin/env python3
"""
Feature 3 - Projectile trajectory predictor + aiming overlay.

Two modes:

  demo (python trajectory_overlay.py --demo [bow|crossbow|pearl])
      No game needed: prints a pitch->range table from the physics constants
      and draws a side-view parabola so you can sanity-check the math.

  live (python trajectory_overlay.py)
      Subscribes to the MCGLM feed (feed-mod/), picks the best target, solves
      for the launch angles every frame, and draws an aiming overlay (error
      indicators around the crosshair, lock ring when on-solution). With aim
      assist (F7) it drifts your crosshair onto the solution by moving the
      mouse; with auto-fire (F8) it releases your bow draw when locked.

Physics (Java Edition; one game tick = 50 ms):
  bow       v0 = look * 3.00 blocks/tick, then each tick: pos += v;
            v = (v.x*0.99, v.y*0.99 - 0.05, v.z*0.99)
  crossbow  same as bow but v0 = look * 3.15
  pearl     v0 = look * 1.50, each tick: pos += v;
            v = (v*0.98, then vy -= 0.03). Pearls get a small random spread
            from the game itself, so expect ~1 block of jitter.

The shooter's own velocity is added to the launch velocity (vanilla does this
in AbstractArrow/ProjectileEntity#shootFromRotation), which is why the feed
sends your per-axis velocity.

Constants verified against current Java behavior; if a future update retunes
projectiles, edit SPECS below.
"""

import argparse
import math
import time
from dataclasses import dataclass

import pygame
from pynput import keyboard
from pynput.keyboard import Key
from pynput.mouse import Button, Controller as MouseController

from mc_feed import FeedClient, MAGENTA, make_overlay

# ---------------------------------------------------------------- config
SENSITIVITY = 0.5          # in-game Options -> Sensitivity (0.0-1.0, 0.5 = "100%")
PROJECTILE = "bow"         # "bow" | "crossbow" | "pearl"
TARGET_RANGE = 64.0        # only consider targets within this many blocks
MAX_STEP_DEG = 5.0         # aim-assist: max crosshair travel per frame (smoothing)
DEADBAND_DEG = 0.25        # aim-assist: stop nudging below this error
FIRE_ERROR_DEG = 1.0       # auto-fire: "locked" angular threshold
FIRE_COOLDOWN_S = 0.8      # auto-fire: min seconds between shots
PX_PER_DEG = 12            # overlay: error-marker pixels per degree


@dataclass(frozen=True)
class ProjectileSpec:
    name: str
    speed: float    # blocks/tick at launch
    drag: float     # per-tick velocity multiplier
    gravity: float  # blocks/tick^2 applied to vy after drag


SPECS = {
    "bow": ProjectileSpec("bow", 3.00, 0.99, 0.05),
    "crossbow": ProjectileSpec("crossbow", 3.15, 0.99, 0.05),
    "pearl": ProjectileSpec("pearl", 1.50, 0.98, 0.03),
}

MOUSE = MouseController()
FLAGS = {"aim": False, "shoot": False, "quit": False, "spec": None}

# keys deliberately avoid F5/F3/F2 (vanilla perspective/debug/screenshot)
# and F6 (gapple macro in macros/gapple_swap.ahk)
CYCLE_KEY = Key.f4        # cycle projectile: bow -> crossbow -> pearl
AIM_KEY = Key.f7          # toggle assisted rotation
SHOOT_KEY = Key.f8        # toggle auto-fire (releases the bow when locked)
QUIT_KEY = Key.f9         # the overlay window is click-through; F9 kills it
SPEC_ORDER = ("bow", "crossbow", "pearl")

# ---------------------------------------------------------------- vector helpers
def v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def v_dist(a, b):
    return math.dist(a, b)


def look_vector(yaw_deg, pitch_deg):
    """Minecraft convention: yaw 0 -> +Z (south), 90 -> -X (west); pitch + = down."""
    y, p = math.radians(yaw_deg), math.radians(pitch_deg)
    return (-math.sin(y) * math.cos(p), -math.sin(p), math.cos(y) * math.cos(p))


def yaw_pitch_to(dx, dy, dz):
    """Inverse of look_vector: direction -> (yaw, pitch) in degrees."""
    horiz = math.hypot(dx, dz)
    return math.degrees(math.atan2(-dx, dz)), math.degrees(-math.atan2(dy, horiz))


def wrap180(a):
    while a > 180.0:
        a -= 360.0
    while a < -180.0:
        a += 360.0
    return a


# ---------------------------------------------------------------- simulation
def simulate(origin, velocity, spec, target=None, max_ticks=200):
    """Step the projectile one game tick at a time.

    Returns (points, best_tick, best_dist): the sampled trajectory, plus the
    tick and distance of closest approach to `target` (unused in demo mode).
    """
    pos, vel = origin, velocity
    points = [pos]
    best_i, best_d = 0, (math.inf if target else 0.0)
    floor_y = (min(origin[1], target[1]) - 8.0) if target else origin[1] - 96.0
    for i in range(1, max_ticks + 1):
        pos = v_add(pos, vel)
        points.append(pos)
        if target is not None:
            # sub-tick samples reduce the per-tick discretization error
            for f in (0.25, 0.5, 0.75, 1.0):
                d = v_dist(v_add(pos, v_scale(vel, f)), target)
                if d < best_d:
                    best_d, best_i = d, i
        if pos[1] < floor_y and vel[1] < 0.0:
            break
        vel = (vel[0] * spec.drag, vel[1] * spec.drag - spec.gravity, vel[2] * spec.drag)
    return points, best_i, best_d


def solve_shot(origin, shooter_vel, spec, target, hit_tolerance=1.0):
    """Find launch yaw/pitch bringing the projectile closest to `target`.

    Projectiles at PvP ranges usually have TWO hitting solutions (a flat
    direct shot and a steep mortar arc); the flat one flies faster, needs
    less target lead and is what you actually want, so we scan pitch outward
    from 0 degrees and accept the first solution whose closest approach is
    within `hit_tolerance` blocks of the target (~1 block suits a player
    hitbox). If nothing hits, we fall back to the globally closest arc.
    """
    yaw, _ = yaw_pitch_to(target[0] - origin[0], target[1] - origin[1], target[2] - origin[2])

    def miss(pitch):
        v0 = v_add(v_scale(look_vector(yaw, pitch), spec.speed), shooter_vel)
        return simulate(origin, v0, spec, target)[2]

    # outward scan: 0, -1, +1, -2, +2 ... first hit wins as the flattest shot;
    # simultaneously remember the global minimum as the fallback
    best_p, best_m = 0.0, miss(0.0)
    if best_m > hit_tolerance:
        for d in range(1, 90):
            found = False
            for sign in (-1.0, 1.0):
                m = miss(sign * d)
                if m < best_m:
                    best_m, best_p = m, sign * d
                if m <= hit_tolerance:
                    found = True
                    break
            if found:
                break
    # ternary-search refine around the chosen solution
    lo, hi = best_p - 2.0, best_p + 2.0
    for _ in range(14):
        c1, c2 = lo + (hi - lo) / 3.0, hi - (hi - lo) / 3.0
        if miss(c1) < miss(c2):
            hi = c2
        else:
            lo = c1
    pitch = (lo + hi) / 2.0
    v0 = v_add(v_scale(look_vector(yaw, pitch), spec.speed), shooter_vel)
    _, ticks, miss_d = simulate(origin, v0, spec, target)
    return {"yaw": yaw, "pitch": pitch, "ticks": ticks, "miss": miss_d}


def solve_shot_with_lead(origin, shooter_vel, spec, t_pos, t_vel, iterations=4):
    """Target leading: aim at where the target *will be*. Fixed-point iteration -
    estimate flight time, re-aim at the predicted spot, repeat. Converges fast."""
    aim = t_pos
    sol = None
    for _ in range(iterations):
        sol = solve_shot(origin, shooter_vel, spec, aim)
        aim = v_add(t_pos, v_scale(t_vel, sol["ticks"]))
    return sol


def deg_per_mouse_count(sens=SENSITIVITY):
    """Degrees of camera rotation per raw mouse count (vanilla MouseHandler
    formula: f = s*0.6+0.2; deg = 0.15 * f^3 * 8)."""
    f = sens * 0.6 + 0.2
    return 0.15 * (f * f * f) * 8.0


class MouseNudger:
    """Converts degree deltas into integer mouse counts, carrying the
    fractional remainder between frames so small corrections don't vanish."""

    def __init__(self):
        self.rem_x = 0.0
        self.rem_y = 0.0

    def move_deg(self, dyaw_deg, dpitch_deg):
        dpc = deg_per_mouse_count()
        self.rem_x += dyaw_deg / dpc     # +x counts turn right (+yaw)
        self.rem_y += dpitch_deg / dpc   # +y counts look down (+pitch)
        ix, iy = int(self.rem_x), int(self.rem_y)
        if ix or iy:
            self.rem_x -= ix
            self.rem_y -= iy
            MOUSE.move(ix, iy)


# ---------------------------------------------------------------- feed state
class LiveState:
    def __init__(self):
        self.player = None
        self.targets = {}       # id -> latest "tgt" message

    def handle(self, msg):
        t = msg.get("t")
        if t == "p":
            self.player = msg
        elif t == "tgt":
            msg["_seen"] = time.time()      # arrival time drives freshness/expiry
            self.targets[msg["id"]] = msg

    def fresh_targets(self, max_age=0.5):
        now = time.time()
        out = []
        for tgt in list(self.targets.values()):
            age = now - tgt.get("_seen", now)
            if age <= max_age:
                out.append(tgt)
            else:
                self.targets.pop(tgt["id"], None)
        return out


def pick_target(state):
    """Prefer targets near the crosshair; distance breaks ties."""
    p = state.player
    if not p:
        return None
    best, best_cost = None, math.inf
    for t in state.fresh_targets():
        dx, dy, dz = t["x"] - p["x"], t["y"] - p["y"], t["z"] - p["z"]
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        if dist > TARGET_RANGE:
            continue
        yaw_to, pitch_to = yaw_pitch_to(dx, dy, dz)
        ang = math.hypot(wrap180(yaw_to - p["yaw"]), pitch_to - p["pitch"])
        if ang > 60.0:            # way off screen - not worth aiming at
            continue
        cost = ang * 2.0 + dist / 50.0
        if cost < best_cost:
            best, best_cost = t, cost
    return best


# ---------------------------------------------------------------- demo mode
def run_demo(name, plot_pitch):
    spec = SPECS[name]
    origin = (0.0, 68.0, 0.0)          # eye height above flat ground at y=64
    print(f"{name}: speed={spec.speed} b/t, drag={spec.drag}/tick, gravity={spec.gravity}/tick^2")
    print(f"{'pitch':>6} {'range (blocks)':>15}")
    best = (0.0, 0.0)
    for pitch in range(10, 61, 5):
        pts, _, _ = simulate(origin, v_scale(look_vector(0, -pitch), spec.speed), spec, None, 500)
        landing = next((q for q in pts if q[1] <= 64.0), pts[-1])
        rng = math.hypot(landing[0], landing[2])
        print(f"{pitch:>6} {rng:>15.1f}")
        if rng > best[1]:
            best = (pitch, rng)
    print(f"max range ~{best[1]:.1f} blocks near {best[0]} degrees")

    pygame.init()
    screen = pygame.display.set_mode((900, 520))
    pygame.display.set_caption(f"{name} trajectory - pitch {plot_pitch} deg")
    font = pygame.font.SysFont("consolas", 14)
    pts, _, _ = simulate(origin, v_scale(look_vector(0, -plot_pitch), spec.speed), spec, None, 500)
    max_r = max(math.hypot(q[0], q[2]) for q in pts) or 1.0
    clock = pygame.time.Clock()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return
        screen.fill((18, 20, 26))
        prev = None
        for q in pts:
            sx = 60 + (math.hypot(q[0], q[2]) / max_r) * 800
            sy = 470 - (q[1] - 64.0) * 4.2
            if prev:
                pygame.draw.line(screen, (90, 220, 130), prev, (sx, sy), 2)
            prev = (sx, sy)
        pygame.draw.line(screen, (70, 74, 84), (60, 470), (860, 470), 2)
        screen.blit(font.render(f"{name}  pitch {plot_pitch} deg  range {max_r:.0f} blocks", True, (220, 224, 230)), (60, 20))
        pygame.display.flip()
        clock.tick(30)


# ---------------------------------------------------------------- live mode
def run_live():
    state = LiveState()
    FLAGS["spec"] = SPECS[PROJECTILE]

    def on_press(key):
        if key == CYCLE_KEY:
            nxt = SPEC_ORDER[(SPEC_ORDER.index(FLAGS["spec"].name) + 1) % len(SPEC_ORDER)]
            FLAGS["spec"] = SPECS[nxt]
            print(f"projectile -> {nxt}")
        elif key == AIM_KEY:
            FLAGS["aim"] = not FLAGS["aim"]
        elif key == SHOOT_KEY:
            FLAGS["shoot"] = not FLAGS["shoot"]
        elif key == QUIT_KEY:
            FLAGS["quit"] = True

    keyboard.Listener(on_press=on_press).start()
    feed = FeedClient(state.handle)
    feed.bind()
    print(f"feed on port {feed.port} | projectile: {FLAGS['spec'].name} | "
          f"hotkeys: F4 projectile, F7 aim assist, F8 auto-fire, F9 quit")

    screen, (w, h) = make_overlay(title="MCGLM trajectory overlay")
    font = pygame.font.SysFont("consolas", 15)
    cx, cy = w // 2, h // 2
    nudger = MouseNudger()
    clock = pygame.time.Clock()
    last_fire = 0.0

    while not FLAGS["quit"]:
        spec = FLAGS["spec"]
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                FLAGS["quit"] = True

        screen.fill(MAGENTA)
        p = state.player
        tgt = pick_target(state)
        sol = None
        err_yaw = err_pitch = None

        if p and tgt:
            origin = (p["x"], p["y"] + 1.62, p["z"])     # eye height
            shooter_vel = (p.get("vx", 0.0), p.get("vy", 0.0), p.get("vz", 0.0))
            t_pos = (tgt["x"], tgt["y"] + 0.9, tgt["z"])  # aim mid-body
            t_vel = (tgt.get("vx", 0.0), tgt.get("vy", 0.0), tgt.get("vz", 0.0))
            sol = solve_shot_with_lead(origin, shooter_vel, spec, t_pos, t_vel)
            err_yaw = wrap180(sol["yaw"] - p["yaw"])
            err_pitch = sol["pitch"] - p["pitch"]
            err = math.hypot(err_yaw, err_pitch)
            valid = sol["miss"] < 3.0   # only assist/fire when solver found a real solution

            # ---- aim assist: nudge the camera toward the solution ----
            # move_deg(+yaw_deg, +pitch_deg) turns the camera right and down.
            # +err_yaw means "you need to look more right", +err_pitch means
            # "you need to look more down" (pitch axis is inverted in screens).
            if FLAGS["aim"] and valid \
                    and (abs(err_yaw) > DEADBAND_DEG or abs(err_pitch) > DEADBAND_DEG):
                step_y = max(-MAX_STEP_DEG, min(MAX_STEP_DEG, err_yaw))
                step_p = max(-MAX_STEP_DEG, min(MAX_STEP_DEG, -err_pitch))
                nudger.move_deg(step_y, step_p)

            # ---- auto-fire: release the draw when locked ----
            if FLAGS["shoot"] and valid \
                    and p.get("using_item") \
                    and p.get("active_item", "").endswith("bow") \
                    and p.get("use_ticks", 0) >= 20 \
                    and err < FIRE_ERROR_DEG \
                    and time.time() - last_fire > FIRE_COOLDOWN_S:
                MOUSE.release(Button.right)
                last_fire = time.time()

        # ---------------- overlay drawing ----------------
        if p and sol and err_yaw is not None:
            err = math.hypot(err_yaw, err_pitch)
            # horizontal error marker (chevron slides toward crosshair)
            mx = int(max(-220, min(220, err_yaw * PX_PER_DEG)))
            pygame.draw.line(screen, (240, 240, 240), (cx - 220, cy + 46), (cx + 220, cy + 46), 1)
            hx = cx + mx
            pygame.draw.polygon(screen, (255, 210, 80), [(hx, cy + 42), (hx - 6, cy + 52), (hx + 6, cy + 52)])
            # vertical error marker
            my = int(max(-160, min(160, err_pitch * PX_PER_DEG)))
            pygame.draw.line(screen, (240, 240, 240), (cx + 46, cy - 160), (cx + 46, cy + 160), 1)
            vy = cy + my
            pygame.draw.polygon(screen, (255, 210, 80), [(cx + 42, vy), (cx + 52, vy - 6), (cx + 52, vy + 6)])
            # lock ring when the solution is centered
            if err < FIRE_ERROR_DEG:
                pygame.draw.circle(screen, (90, 255, 120), (cx, cy), 27, 2)
            dist = v_dist((p["x"], p["y"], p["z"]), (tgt["x"], tgt["y"], tgt["z"]))
            lines = [
                f"{spec.name.upper()} | {tgt['name']}  {dist:.1f}m  "
                f"flight {sol['ticks']}t  miss {sol['miss']:.2f}m",
                f"aim yaw {sol['yaw']:+.1f}  pitch {sol['pitch']:+.1f}  "
                f"err {err_yaw:+.1f}/{err_pitch:+.1f}",
                f"[F4] proj  [F7] aim {'ON' if FLAGS['aim'] else 'off'}  "
                f"[F8] fire {'ON' if FLAGS['shoot'] else 'off'}  [F9] quit",
            ]
            for i, txt in enumerate(lines):
                screen.blit(font.render(txt, True, (235, 235, 235)), (cx - 230, cy + 70 + i * 20))
        else:
            screen.blit(font.render(
                f"MCGLM {spec.name} - waiting for target  |  "
                f"aim {'ON' if FLAGS['aim'] else 'off'}  "
                f"fire {'ON' if FLAGS['shoot'] else 'off'}  |  "
                f"F4 proj  F7 aim  F8 fire  F9 quit",
                True, (150, 155, 160)), (cx - 290, cy + 70))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", nargs="?", const="bow", choices=SPECS, help="run physics demo, no game needed")
    ap.add_argument("--pitch", type=float, default=35.0, help="demo plot pitch")
    args = ap.parse_args()
    if args.demo:
        run_demo(args.demo, args.pitch)
    else:
        run_live()
