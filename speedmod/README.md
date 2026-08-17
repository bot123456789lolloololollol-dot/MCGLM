# MCGLM speedmod (feature 6 - 1.50x movement speed, testing)

A ~40-line client-side Fabric mod that adds a permanent +50%
`ADD_MULTIPLIED_TOTAL` modifier to your movement-speed attribute every tick.

Why a mod and not AHK/Python: your walk speed is an *attribute inside the
client's living-entity instance*. No amount of external mouse/keyboard input
changes that attribute; you have to touch the entity. The modifier is
transient (never saved to player data), so it simply re-applies on world join
— that's what the tick handler is for.

This 1.50x value is intended for testing. A server may correct movement that
differs substantially from the expected position, causing rubber-banding or
anti-cheat action. Expected numbers: walk 4.317 -> ~6.48 b/s, sprint 5.612
-> ~8.42 b/s (sprint's +30% stacks multiplicatively).

## Build

This directory is already a complete Fabric/Loom project targeting Minecraft
26.2. Build it directly:

```
.\gradlew.bat build
```

The installable jar is `build/libs/mcglm-speed-1.0.0.jar`. It requires Fabric
API in the Dawn Fabric profile; mod metadata is already included.

```json
{
  "schemaVersion": 1,
  "id": "mcglm-speed",
  "version": "1.0.0",
  "name": "MCGLM Speed",
  "environment": "client",
  "entrypoints": { "client": ["com.mcglm.speed.SpeedMod"] },
  "depends": { "fabricloader": ">=0.19.3", "fabric-api": "*", "minecraft": "26.2" }
}
```

Add the resulting jar through Dawn's local Fabric mod control, or place it
in the selected profile's `mods` directory. Keep the Minecraft version at
26.2, or rebuild against the exact profile version.

## Verify

Join the server, walk in a straight line, and time yourself between two known
points — or watch your position in F3 while strafing along an axis: you
should cover ~50% more blocks per second than with the mod removed, unless the
server corrects the movement.

## Tune

`SPEED_MULTIPLIER = 0.50` is the current testing value. Reduce it before
normal use if the server corrects movement or flags the client.
