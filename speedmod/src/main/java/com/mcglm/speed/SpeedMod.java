package com.mcglm.speed;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;

import net.minecraft.resources.Identifier;

/**
 * Feature 6: +5% movement speed, permanently (re-applied each tick if the
 * server or a dimension change clears it).
 *
 * Minecraft 26.2 uses Mojang's official names and the MOVEMENT_SPEED holder.
 */
public class SpeedMod implements ClientModInitializer {

    /** A fixed identifier lets us detect the modifier and avoid stacking it. */
    private static final Identifier MODIFIER_ID = Identifier.fromNamespaceAndPath("mcglm", "speed_boost");

    /** 0.05 = +5%. ADD_MULTIPLIED_TOTAL stacks with sprint's +30%. */
    private static final double SPEED_MULTIPLIER = 0.05;

    @Override
    public void onInitializeClient() {
        ClientTickEvents.END_CLIENT_TICK.register(SpeedMod::apply);
    }

    private static void apply(Minecraft client) {
        LocalPlayer player = client.player;
        if (player == null) return;

        AttributeInstance speed = player.getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed == null || speed.getModifier(MODIFIER_ID) != null) return;

        // transient = not persisted with the player, so relogs/dimension hops
        // that rebuild the attribute just get it back on the next tick
        speed.addTransientModifier(new AttributeModifier(
                MODIFIER_ID,
                SPEED_MULTIPLIER,
                AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
    }
}
