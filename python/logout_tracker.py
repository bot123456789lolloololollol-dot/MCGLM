#!/usr/bin/env python3
"""
Feature 4 - Logout spot tracker.

Listens on the MCGLM feed for {"t":"logout"} events (emitted by the Fabric
mod's PlayerRemoveMixin the moment the server drops a player from the tab
list - the mod reads the entity's position before the client discards it),
stores last-known coordinates in logout_spots.json, and renders a ghost
panel plus a top-down radar showing where everyone vanished relative to you.

Usage:
    python logout_tracker.py               # overlay panel + radar
    python logout_tracker.py --no-overlay  # console log only

Nothing here records anything about the person behind the account - just
in-game name, position, dimension and time.
"""

import argparse
import json
import math
import time
from pathlib import Path

import pygame

from mc_feed import FeedClient, MAGENTA, make_overlay

STORE = Path(__file__).with_name("logout_spots.json")
MAX_RECORDS = 50


class Tracker:
    def __init__(self):
        self.records = []       # [{name, x, y, z, dim, ts}]
        self.player = None
        self.load()

    def load(self):
        if STORE.exists():
            try:
                self.records = json.loads(STORE.read_text())[:MAX_RECORDS]
            except ValueError:
                self.records = []

    def save(self):
        STORE.write_text(json.dumps(self.records, indent=1))

    def handle(self, msg):
        t = msg.get("t")
        if t == "p":
            self.player = msg
        elif t == "logout":
            # ignore duplicates: same name within 10 s (server re-sends sometimes)
            recent = [r for r in self.records if r["name"] == msg["name"]
                      and time.time() - r["ts"] < 10.0]
            if recent:
                return
            self.records.insert(0, {
                "name": msg["name"], "x": msg["x"], "y": msg["y"], "z": msg["z"],
                "dim": msg.get("dim", "?"), "ts": time.time(),
            })
            self.records = self.records[:MAX_RECORDS]
            self.save()
            print(f"[logout] {msg['name']} @ "
                  f"{msg['x']:.0f} {msg['y']:.0f} {msg['z']:.0f} ({msg.get('dim', '?')})")
        elif t == "login":
            self.records = [r for r in self.records if r["name"] != msg["name"]]
            self.save()
            print(f"[login ] {msg['name']} - cleared ghost")


def age_str(ts):
    s = int(time.time() - ts)
    return f"{s // 60}m{s % 60:02d}s ago" if s >= 60 else f"{s}s ago"


def rel_str(p, r):
    dx, dz = r["x"] - p["x"], r["z"] - p["z"]
    dist = math.hypot(dx, dz)
    if dist < 1.0:
        return "on top of you"
    compass = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int((math.degrees(math.atan2(dx, -dz)) + 360 + 22.5) // 45) % 8]
    return f"{dist:.0f}m {compass}"


def run_console(tracker):
    feed = FeedClient(tracker.handle)
    feed.bind()
    print(f"logging logouts to console + {STORE.name} (feed port {feed.port}); Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def run_overlay(tracker):
    from pynput import keyboard
    from pynput.keyboard import Key
    flags = {"quit": False}
    keyboard.Listener(on_press=lambda k: flags.__setitem__("quit", k == Key.f9)).start()

    feed = FeedClient(tracker.handle)
    feed.bind()
    print(f"feed port {feed.port}; F9 quits the overlay")

    screen, (w, h) = make_overlay(title="MCGLM logout tracker")
    font = pygame.font.SysFont("consolas", 15)
    clock = pygame.time.Clock()
    px, py = 60, 460                    # radar center on screen
    RAD, SCALE = 110, 2.0               # radar radius px, px per block

    while not flags["quit"]:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                flags["quit"] = True
        screen.fill(MAGENTA)

        p = tracker.player
        # ---------------- ghost list ----------------
        pygame.draw.rect(screen, (12, 14, 18), (w - 360, 30, 350, 24 + 12 * min(len(tracker.records), 14)))
        screen.blit(font.render("LOGOUT SPOTS (F9 quit)", True, (240, 240, 240)),
                    (w - 350, 36))
        for i, r in enumerate(tracker.records[:14]):
            rel = rel_str(p, r) if p else "?"
            same_dim = (p or {}).get("dim") == r["dim"]
            color = (255, 120, 120) if same_dim else (140, 140, 150)
            tag = "" if same_dim else f"  [{r['dim'].split(':')[-1]}]"
            screen.blit(font.render(f"{r['name']:<16} {age_str(r['ts']):<10} {rel}{tag}",
                                     True, color), (w - 350, 60 + i * 12))

        # ---------------- top-down radar ----------------
        pygame.draw.rect(screen, (12, 14, 18), (px - RAD - 8, py - RAD - 8, 2 * RAD + 16, 2 * RAD + 16))
        pygame.draw.circle(screen, (60, 66, 76), (px, py), RAD, 1)
        screen.blit(font.render("N", True, (120, 126, 136), ), (px - 4, py - RAD - 4))
        if p:
            pygame.draw.circle(screen, (120, 220, 255), (px, py), 3)   # you
            for r in tracker.records:
                if r["dim"] != p.get("dim"):
                    continue
                sx = px + (r["x"] - p["x"]) * SCALE
                sy = py + (r["z"] - p["z"]) * SCALE     # north (-Z) is up
                if abs(sx - px) <= RAD and abs(sy - py) <= RAD:
                    pygame.draw.circle(screen, (255, 90, 90), (int(sx), int(sy)), 4)
                    label = font.render(r["name"][:8], True, (255, 160, 160))
                    screen.blit(label, (sx + 6, sy - 7))

        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-overlay", action="store_true", help="console logging only")
    args = ap.parse_args()
    tr = Tracker()
    run_console(tr) if args.no_overlay else run_overlay(tr)
