# MCGLM feed mod (features 3, 4, 5 data source)

A minimal client-side Fabric mod that broadcasts your local player state,
nearby players, and logout events as JSON datagrams to `127.0.0.1:5010` for
the Python overlay tools (`python/trajectory_overlay.py`, `logout_tracker.py`,
`status_hud.py`). Nothing leaves your machine.

Protocol: see the "MCGLM feed" section of the root README.

## Build

1. Generate a Fabric mod template at https://fabricmc.net/develop/template/
   for your exact Minecraft version (1.21.x), client environment, with
   **Fabric API** included.
2. Copy `src/main/java/com/mcglm/feed/*.java` into the template's source tree.
3. Set up `src/main/resources/fabric.mod.json`:

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

4. Add `src/main/resources/mcglm-feed.mixins.json`:

```json
{
  "required": true,
  "package": "com.mcglm.feed",
  "compatibilityLevel": "JAVA_21",
  "client": ["PlayerRemoveMixin"],
  "injectors": { "defaultRequire": 1 }
}
```

5. `gradlew build` -> jar in `build/libs/`. Load it in Feather (Fabric-based);
   if Feather refuses third-party jars, use a plain Fabric profile.

## Mappings note

Field/method names below match Yarn 1.21.x but drift between minor versions
(`getInventory().armor` vs accessor, `EntityAttributes.GENERIC_*`, the exact
`onPlayerList` method name...). If something doesn't compile, open the class
in your IDE, find the equivalent member, and adjust — the structure is stable.
