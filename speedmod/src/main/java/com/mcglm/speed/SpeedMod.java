package com.mcglm.speed;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.entity.attribute.EntityAttributeInstance;
import net.minecraft.entity.attribute.EntityAttributeModifier;
import net.minecraft.entity.attribute.EntityAttributes;

import java.util.UUID;

/**
 * Feature 6: +5% movement speed, permanently (re-applied each tick if the
 * server or a dimension change clears it).
 *
 * Mappings note: on Yarn 1.21.1 the attribute is
 * EntityAttributes.GENERIC_MOVEMENT_SPEED; 1.21.2+ dropped the GENERIC_
 * prefix (EntityAttributes.MOVEMENT_SPEED). Adjust the single line below if
 * it doesn't compile.
 */
public class SpeedMod implements ClientModInitializer {

    /** Any fixed UUID identifies our modifier so we never stack duplicates. */
    private static final UUID MODIFIER_ID = UUID.fromString("d76f4b7a-6f0a-4bfd-9a0a-9f2a4d6f1c05");

    /** 0.05 = +5%. MULTIPLICATION_TOTAL stacks with sprint's +30%. */
    private static final double SPEED_MULTIPLIER = 0.05;

    @Override
    public void onInitializeClient() {
        ClientTickEvents.END_CLIENT_TICK.register(SpeedMod::apply);
    }

    private static void apply(MinecraftClient client) {
        ClientPlayerEntity player = client.player;
        if (player == null) return;

        EntityAttributeInstance speed = player.getAttribute(
                EntityAttributes.GENERIC_MOVEMENT_SPEED);   // 1.21.2+: EntityAttributes.MOVEMENT_SPEED
        if (speed == null || speed.getModifier(MODIFIER_ID) != null) return;

        // transient = not persisted with the player, so relogs/dimension hops
        // that rebuild the attribute just get it back on the next tick
        speed.addTransientModifier(new EntityAttributeModifier(
                MODIFIER_ID,
                "MCGLM speed boost",
                SPEED_MULTIPLIER,
                EntityAttributeModifier.Operation.MULTIPLICATION_TOTAL));
    }
}
