# MCGLM feed mod (features 3, 4, 5 data source)

A minimal client-side Fabric mod that broadcasts your local player state,
nearby players, and logout events as JSON datagrams to `127.0.0.1:5010` for
the Python overlay tools (`python/trajectory_overlay.py`, `logout_tracker.py`,
`status_hud.py`). Nothing leaves your machine.

Protocol: see the "MCGLM feed" section of the root README.

## Build

This directory is already a complete Fabric/Loom project targeting Minecraft
26.2. Build it directly:

```
.\gradlew.bat build
```

The installable jar is `build/libs/mcglm-feed-1.0.0.jar`. It requires Fabric
API in the Dawn Fabric profile; metadata and mixin resources are already included.

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
  "depends": { "fabricloader": ">=0.19.3", "fabric-api": "*", "minecraft": "26.2" }
}
```

The mixin resource is:

```json
{
  "required": true,
  "package": "com.mcglm.feed",
  "compatibilityLevel": "JAVA_25",
  "client": ["PlayerRemoveMixin", "PlayerListMixin"],
  "injectors": { "defaultRequire": 1 }
}
```

Add the resulting jar through Dawn's local Fabric mod control, or place it
in the selected profile's `mods` directory. Keep the Minecraft version at
26.2, or rebuild against the exact profile version.

## Mappings note

The 26.2 sources use Mojang's official names. Minecraft 26.1+ is unobfuscated,
so do not apply old Yarn mapping edits to this project.
