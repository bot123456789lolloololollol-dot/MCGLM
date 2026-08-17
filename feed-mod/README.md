# MCGLM feed mod (features 3, 4, 5 data source)

A minimal client-side Fabric mod that broadcasts your local player state,
nearby players, and logout events as JSON datagrams to `127.0.0.1:5010` for
the Python overlay tools (`python/trajectory_overlay.py`, `logout_tracker.py`,
`status_hud.py`). Nothing leaves your machine.

Protocol: see the "MCGLM feed" section of the root README.

## Build

This directory is already a complete Fabric/Loom project targeting Minecraft
1.21.1. Build it directly:

```
.\gradlew.bat build
```

The installable jar is `build/libs/mcglm-feed-1.0.0.jar`. It requires Fabric
API in the Feather profile; metadata and mixin resources are already included.

The generated metadata is:

```json
{
  "schemaVersion": 1,
  "id": "mcglm-feed",
  "version": "1.0.0",
  "name": "MCGLM Feed",
  "description": "Broadcasts local player/target state to the MCGLM overlay tools.",
  "environment": "client",
  "entrypoints": { "client": ["com.mcglm.feed.FeedMod"] },
  "mixins": ["mcglm-feed.mixins.json"],
  "depends": { "fabricloader": ">=0.15.0", "fabric-api": "*", "minecraft": "~1.21" }
}
```

The mixin resource is:

```json
{
  "required": true,
  "package": "com.mcglm.feed",
  "compatibilityLevel": "JAVA_21",
  "client": ["PlayerRemoveMixin", "PlayerListMixin"],
  "injectors": { "defaultRequire": 1 }
}
```

Add the resulting jar through Feather's local Fabric mod control, or place it
in the selected profile's `mods` directory. Keep the Minecraft version at
1.21.1, or rebuild against the exact profile version.

## Mappings note

Field/method names below match Yarn 1.21.x but drift between minor versions
(`getInventory().armor` vs accessor, `EntityAttributes.GENERIC_*`, the exact
`onPlayerList` method name...). If something doesn't compile, open the class
in your IDE, find the equivalent member, and adjust — the structure is stable.
