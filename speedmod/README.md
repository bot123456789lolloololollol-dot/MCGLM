# MCGLM speedmod (feature 6 - 1.05x movement speed)

A ~40-line client-side Fabric mod that adds a permanent +5%
`MULTIPLICATION_TOTAL` modifier to your movement-speed attribute every tick.

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

Same template flow as feed-mod (https://fabricmc.net/develop/template/,
1.21.x, client, Fabric API). Copy the Java file in, then
`src/main/resources/fabric.mod.json`:

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

`gradlew build` -> jar in `build/libs/`. Load via Feather's mod support, or a
plain Fabric profile if Feather rejects the jar.

## Verify

Join the server, walk in a straight line, and time yourself between two known
points — or watch your position in F3 while strafing along an axis: you
should cover ~5% more blocks per second than with the mod removed.

## Tune

`SPEED_MULTIPLIER = 0.05` is the only knob. Keep it small: the point of 1.05x
is being indistinguishable from normal movement in fights, not raw speed.
