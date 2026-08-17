package com.mcglm.feed;

import com.google.gson.JsonObject;
import net.minecraft.client.network.ClientPlayNetworkHandler;
import net.minecraft.network.packet.s2c.play.PlayerListS2CPacket;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Clears a stored logout marker when the server adds the player back to tab. */
@Mixin(ClientPlayNetworkHandler.class)
public abstract class PlayerListMixin {
    @Inject(method = "onPlayerList", at = @At("HEAD"))
    private void mcglm$onPlayerList(PlayerListS2CPacket packet, CallbackInfo ci) {
        if (!packet.getActions().contains(PlayerListS2CPacket.Action.ADD_PLAYER)) return;
        packet.getEntries().forEach(entry -> {
            FeedMod.LAST_KNOWN.remove(entry.profileId());
            FeedMod.NAMES.remove(entry.profileId());
            JsonObject message = new JsonObject();
            message.addProperty("t", "login");
            message.addProperty("name", entry.profile().getName());
            FeedMod.send(message);
        });
    }
}
