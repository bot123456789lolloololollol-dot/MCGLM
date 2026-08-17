package com.mcglm.feed;

import com.google.gson.JsonObject;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayNetworkHandler;
import net.minecraft.entity.Entity;
import net.minecraft.network.packet.s2c.play.PlayerListS2CPacket;
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
@Mixin(ClientPlayNetworkHandler.class)
public abstract class PlayerRemoveMixin {

    // The method name for handling PlayerListS2CPacket depends on your yarn version:
    //   1.21.0 / 1.21.1: "onPlayerList"
    //   1.21.2 / 1.21.3 / 1.21.4: "handlePlayerList"
    // If compilation fails on the line below, search ClientPlayNetworkHandler for the
    // method that takes PlayerListS2CPacket and update this string accordingly.
    @Inject(method = "onPlayerList", at = @At("HEAD"))
    private void mcglm$onPlayerList(PlayerListS2CPacket packet, CallbackInfo ci) {
        MinecraftClient client = MinecraftClient.getInstance();
        String dim = client.world != null
                ? client.world.getRegistryKey().getValue().toString() : "?";

        boolean isLogout = packet.getActions().contains(PlayerListS2CPacket.Action.REMOVE_PLAYER);
        boolean isLogin  = packet.getActions().contains(PlayerListS2CPacket.Action.ADD_PLAYER);

        for (PlayerListS2CPacket.Entry entry : packet.getEntries()) {
            UUID id = entry.profileId();

            if (isLogin) {
                // player joined or respawned — clear any existing ghost marker
                FeedMod.LAST_KNOWN.remove(id);
                FeedMod.NAMES.remove(id);
                JsonObject o = new JsonObject();
                o.addProperty("t", "login");
                o.addProperty("name", entry.profile().getName());
                FeedMod.send(o);
                continue;
            }

            if (!isLogout) continue;
            String name = FeedMod.NAMES.getOrDefault(id, id.toString().substring(0, 8));

            double[] pos = null;
            if (client.world != null) {
                Entity e = client.world.getEntity(id);   // entity may already be gone
                if (e != null) pos = new double[]{e.getX(), e.getY(), e.getZ()};
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
