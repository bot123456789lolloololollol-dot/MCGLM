#!/usr/bin/env python3
"""
Feature 5 - Status HUD overlay.

Reads the local player state from the MCGLM feed ({"t":"p"} messages from the
feed Fabric mod: health, armor, armor durability, held/offhand items, totem
count, hunger, active effects, bow charge) and draws a clean panel in the
top-left corner: hearts bar, armor bar, armor durability, totems, effects.

Run:  python status_hud.py     (F9 quits)
"""

import time

import pygame
from pynput import keyboard
from pynput.keyboard import Key

from mc_feed import FeedClient, MAGENTA, make_overlay

EFFECT_SHORT = {  # trim the common PvP potions to label length
    "regeneration": "regen", "fire_resistance": "fire res", "absorption": "absorb",
    "strength": "strength", "speed": "speed", "slowness": "slow",
    "weakness": "weak", "poison": "poison", "wither": "wither",
    "instant_health": "heal", "instant_damage": "damage",
}


def bar_cells(surf, x, y, cells, filled, full, empty, w=14, h=10, gap=3):
    """Draw `cells` segments with `filled` (float, e.g. hp 17 -> 8.5 hearts)."""
    for i in range(cells):
        frac = max(0.0, min(1.0, filled - i))
        rect = pygame.Rect(x + i * (w + gap), y, w, h)
        pygame.draw.rect(surf, empty, rect)
        if frac > 0:
            fill = pygame.Rect(rect.x, rect.y, int(w * frac), h)
            pygame.draw.rect(surf, full, fill)
        pygame.draw.rect(surf, (0, 0, 0), rect, 1)


def short_item(item_id):
    return item_id.split(":")[-1].replace("_", " ") if item_id else "-"


def main():
    flags = {"quit": False}
    keyboard.Listener(on_press=lambda k: flags.__setitem__("quit", k == Key.f9)).start()

    state = {"p": None, "seen": 0.0}

    def handle(msg):
        if msg.get("t") == "p":
            state["p"], state["seen"] = msg, time.time()

    feed = FeedClient(handle)
    feed.bind()
    print(f"feed port {feed.port}; F9 quits")

    screen, (w, h) = make_overlay(title="MCGLM status HUD")
    font = pygame.font.SysFont("consolas", 15)
    small = pygame.font.SysFont("consolas", 13)
    clock = pygame.time.Clock()

    while not flags["quit"]:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                flags["quit"] = True
        screen.fill(MAGENTA)
        p, fresh = state["p"], (time.time() - state["seen"]) < 1.0
        x, y = 14, 30
        pygame.draw.rect(screen, (12, 14, 18), (x - 6, y - 24, 280, 190))

        head = "STATUS" if fresh else "STATUS - waiting for feed..."
        screen.blit(font.render(head, True, (240, 240, 240) if fresh else (110, 114, 120)), (x, y - 18))
        if p and fresh:
            # hearts
            bar_cells(screen, x, y, 10, p["hp"] / 2.0, (235, 60, 70), (60, 26, 30))
            screen.blit(small.render(f"{p['hp']:.0f}/{p['max_hp']:.0f}", True, (235, 120, 130)), (x + 175, y))
            # armor points + durability
            bar_cells(screen, x, y + 16, 10, p["armor"] / 2.0, (160, 190, 255), (30, 36, 50))
            dur = float(p.get("armor_dur", 0.0))
            dur_col = (110, 220, 120) if dur > 0.5 else (235, 200, 80) if dur > 0.2 else (235, 90, 90)
            pygame.draw.rect(screen, (40, 44, 52), (x, y + 32, 172, 8))
            pygame.draw.rect(screen, dur_col, (x, y + 32, int(172 * dur), 8))
            screen.blit(small.render(f"armor {dur*100:.0f}%", True, dur_col), (x + 178, y + 29))
            # hunger
            bar_cells(screen, x, y + 48, 10, p.get("food", 20) / 2.0, (220, 170, 70), (50, 42, 26))
            # held / offhand / totems
            totems = int(p.get("totems", 0))
            held_dur = float(p.get("held_dur", 0.0))
            held_name = short_item(p.get("held"))
            lines = [
                f"held   {held_name}",
                f"off    {short_item(p.get('off'))}",
                f"totems {totems}",
            ]
            for i, txt in enumerate(lines):
                screen.blit(small.render(txt, True, (220, 222, 228)), (x, y + 68 + i * 17))
            # held-item durability bar (only if held_dur > 0 = damageable)
            if held_dur > 0.0:
                hd_col = (110, 220, 120) if held_dur > 0.5 else (235, 200, 80) if held_dur > 0.2 else (235, 90, 90)
                pygame.draw.rect(screen, (40, 44, 52), (x, y + 120, 172, 6))
                pygame.draw.rect(screen, hd_col, (x, y + 120, int(172 * held_dur), 6))
                screen.blit(small.render(f"held {held_dur*100:.0f}%", True, hd_col), (x + 178, y + 117))
            if totems == 0:
                pygame.draw.circle(screen, (255, 80, 80), (x + 96, y + 102 + 17), 4)
            # bow charge while drawing
            bow_y = y + (130 if held_dur > 0.0 else 124)
            if p.get("using_item") and p.get("active_item", "").endswith("bow"):
                charge = min(1.0, p.get("use_ticks", 0) / 20.0)
                col = (120, 255, 140) if charge >= 1.0 else (235, 200, 80)
                pygame.draw.rect(screen, (40, 44, 52), (x, bow_y, 172, 8))
                pygame.draw.rect(screen, col, (x, bow_y, int(172 * charge), 8))
                screen.blit(small.render(f"draw {charge*100:.0f}%", True, col), (x + 178, bow_y - 3))
            # active effects
            ey = y + 140
            for e in (p.get("effects") or [])[:3]:
                name = EFFECT_SHORT.get(e["id"].split(":")[-1], e["id"].split(":")[-1])
                screen.blit(small.render(f"{name} {e['ticks'] // 20 + 1}s", True, (190, 200, 255)), (x, ey))
                ey += 15
        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    main()
