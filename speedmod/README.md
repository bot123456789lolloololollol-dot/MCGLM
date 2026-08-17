# MCGLM speedmod (feature 6 - 1.05x movement speed)

A ~40-line client-side Fabric mod that adds a permanent +5%
`ADD_MULTIPLIED_TOTAL` modifier to your movement-speed attribute every tick.

Why a mod and not AHK/Python: your walk speed is an *attribute inside the
client's living-entity instance*. No amount of external mouse/keyboard input
changes that attribute; you have to touch the entity. The modifier is
transient (never saved to player data), so it simply re-applies on world join
— that's what the tick handler is for.

Why 1.05x is safe on a vanilla/no-anticheat server: vanilla servers only
reject position packets that jump absurdly far per tick (on the order of 10
blocks), and they never validate the speed attribute itself. +5% is ~0.2
blocks/s and passes trivially. Expected numbers: walk 4.317 -> ~4.53 b/s,
sprint 5.612 -> ~5.89 b/s (sprint's +30% stacks multiplicatively).

## Build

This directory is already a complete Fabric/Loom project targeting Minecraft
1.21.1. Build it directly:

```
.\gradlew.bat build
```

The installable jar is `build/libs/mcglm-speed-1.0.0.jar`. It requires Fabric
API in the Feather profile; mod metadata is already included.

```json
{
  "schemaVersion": 1,
  "id": "mcglm-speed",
  "version": "1.0.0",
  "name": "MCGLM Speed",
  "environment": "client",
  "entrypoints": { "client": ["com.mcglm.speed.SpeedMod"] },
  "depends": { "fabricloader": ">=0.15.0", "minecraft": "~1.21" }
}
```

Add the resulting jar through Feather's local Fabric mod control, or place it
in the selected profile's `mods` directory. Keep the Minecraft version at
1.21.1, or rebuild against the exact profile version.

## Verify

Join the server, walk in a straight line, and time yourself between two known
points — or watch your position in F3 while strafing along an axis: you
should cover ~5% more blocks per second than with the mod removed.

## Tune

`SPEED_MULTIPLIER = 0.05` is the only knob. Keep it small: the point of 1.05x
is being indistinguishable from normal movement in fights, not raw speed.
