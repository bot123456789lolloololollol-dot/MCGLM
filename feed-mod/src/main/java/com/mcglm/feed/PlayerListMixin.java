package com.mcglm.feed;

import com.google.gson.JsonObject;
import net.minecraft.client.multiplayer.ClientPacketListener;
import net.minecraft.network.protocol.game.ClientboundPlayerInfoUpdatePacket;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Clears a stored logout marker when the server adds the player back to tab. */
@Mixin(ClientPacketListener.class)
public abstract class PlayerListMixin {
    @Inject(method = "handlePlayerInfoUpdate", at = @At("HEAD"))
    private void mcglm$onPlayerList(ClientboundPlayerInfoUpdatePacket packet, CallbackInfo ci) {
        if (!packet.actions().contains(ClientboundPlayerInfoUpdatePacket.Action.ADD_PLAYER)) return;
        packet.entries().forEach(entry -> {
            FeedMod.LAST_KNOWN.remove(entry.profileId());
            FeedMod.NAMES.remove(entry.profileId());
            JsonObject message = new JsonObject();
            message.addProperty("t", "login");
            message.addProperty("name", entry.profile().name());
            FeedMod.send(message);
        });
    }
}
