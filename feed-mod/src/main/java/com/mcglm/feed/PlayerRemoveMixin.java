package com.mcglm.feed;

import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientPacketListener;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.network.protocol.game.ClientboundPlayerInfoRemovePacket;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.UUID;

/**
 * Feature 4 hook: when the server removes a player from the tab list, that
 * player just logged out (or died). We grab their last known position -
 * from the live entity if it still exists, otherwise from FeedMod's
 * per-tick LAST_KNOWN cache - and emit {"t":"logout", ...} for the Python
 * tracker, which draws the ghost marker at those coordinates.
 */
@Mixin(ClientPacketListener.class)
public abstract class PlayerRemoveMixin {

    @Inject(method = "handlePlayerInfoRemove", at = @At("HEAD"))
    private void mcglm$onPlayerRemove(ClientboundPlayerInfoRemovePacket packet, CallbackInfo ci) {
        Minecraft client = Minecraft.getInstance();
        String dim = client.level != null ? client.level.dimension().identifier().toString() : "?";

        for (UUID id : packet.profileIds()) {
            String name = FeedMod.NAMES.getOrDefault(id, id.toString().substring(0, 8));

            double[] pos = null;
            if (client.level != null) {
                for (AbstractClientPlayer player : client.level.players()) {
                    if (player.getUUID().equals(id)) {
                        pos = new double[]{player.getX(), player.getY(), player.getZ()};
                        break;
                    }
                }
            }
            if (pos == null) {
                double[] cached = FeedMod.LAST_KNOWN.get(id);   // fallback: our cache
                if (cached != null) pos = cached;
            }
            if (pos == null) continue;

            JsonObject o = new JsonObject();
            o.addProperty("t", "logout");
            o.addProperty("name", name);
            o.addProperty("x", pos[0]);
            o.addProperty("y", pos[1]);
            o.addProperty("z", pos[2]);
            o.addProperty("dim", dim);
            FeedMod.send(o);

            FeedMod.LAST_KNOWN.remove(id);
            FeedMod.NAMES.remove(id);
        }
    }
}
