package com.mcglm.feed;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.registry.Registries;
import net.minecraft.util.math.Vec3d;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * MCGLM feed: once per client tick, broadcast the local player's state and
 * every other player within 64 blocks as JSON datagrams to 127.0.0.1:5010,
 * where the Python overlay tools (trajectory solver, logout radar, HUD)
 * pick them up. Also keeps a last-known-position cache used by
 * PlayerRemoveMixin to report exact logout coordinates.
 *
 * Mappings: Yarn 1.21.x. See feed-mod/README.md for the drift caveats.
 */
public class FeedMod implements ClientModInitializer {

    public static final int PORT = 5010;                 // must match mc_feed.py
    private static final double TARGET_RANGE_SQ = 64.0 * 64.0;

    /** uuid -> {x, y, z, dim, name}; written every tick, read by the mixin. */
    public static final Map<UUID, double[]> LAST_KNOWN = new ConcurrentHashMap<>();
    public static final Map<UUID, String> NAMES = new ConcurrentHashMap<>();

    private static DatagramSocket socket;
    private static InetAddress loopback;

    @Override
    public void onInitializeClient() {
        try {
            socket = new DatagramSocket();
            loopback = InetAddress.getByName("127.0.0.1");
        } catch (Exception e) {
            throw new IllegalStateException("MCGLM feed: cannot open UDP socket", e);
        }
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if (client.player != null && client.world != null) tick(client);
        });
    }

    private void tick(MinecraftClient client) {
        ClientPlayerEntity p = client.player;
        String dim = client.world.getRegistryKey().getValue().toString();

        // ---- self state ("t":"p") ----
        JsonObject self = new JsonObject();
        Vec3d pos = p.getPos(), vel = p.getVelocity();
        self.addProperty("t", "p");
        self.addProperty("x", pos.x);   self.addProperty("y", pos.y);   self.addProperty("z", pos.z);
        self.addProperty("yaw", p.getYaw()); self.addProperty("pitch", p.getPitch());
        self.addProperty("vx", vel.x);  self.addProperty("vy", vel.y);  self.addProperty("vz", vel.z);
        self.addProperty("hp", p.getHealth());
        self.addProperty("max_hp", p.getMaxHealth());
        self.addProperty("armor", p.getArmor());
        self.addProperty("armor_dur", averageArmorDurability(p));
        self.addProperty("food", p.getHungerManager().getFoodLevel());
        self.addProperty("held", Registries.ITEM.getId(p.getMainHandStack().getItem()).toString());
        self.addProperty("off", Registries.ITEM.getId(p.getOffHandStack().getItem()).toString());
        self.addProperty("totems", p.getInventory().count(Items.TOTEM_OF_UNDYING));
        self.addProperty("held_dur", heldDurability(p));
        self.addProperty("using_item", p.isUsingItem());
        self.addProperty("use_ticks", p.getItemUseTime());
        self.addProperty("active_item", Registries.ITEM.getId(p.getActiveItem().getItem()).toString());
        self.addProperty("dim", dim);
        JsonArray effects = new JsonArray();
        // Yarn 1.21.0-1.21.1: getStatusEffects()
        // Yarn 1.21.2+:       getStatusEffectInstances()  (same return type, different name)
        // If compilation fails here, search LivingEntity for the method returning
        // the collection of StatusEffectInstance.
        p.getStatusEffects().forEach(e -> {
            JsonObject o = new JsonObject();
            o.addProperty("id", Registries.STATUS_EFFECT.getId(e.getEffectType()).toString());
            o.addProperty("ticks", e.getDuration());
            effects.add(o);
        });
        self.add("effects", effects);
        send(self);

        // ---- nearby players ("t":"tgt") + logout position cache ----
        LAST_KNOWN.put(p.getUuid(), new double[]{pos.x, pos.y, pos.z});
        for (PlayerEntity other : client.world.getPlayers()) {
            if (other == p) continue;
            Vec3d op = other.getPos(), ov = other.getVelocity();
            LAST_KNOWN.put(other.getUuid(), new double[]{op.x, op.y, op.z});
            NAMES.put(other.getUuid(), other.getName().getString());
            if (other.squaredDistanceTo(p) > TARGET_RANGE_SQ) continue;
            JsonObject t = new JsonObject();
            t.addProperty("t", "tgt");
            t.addProperty("id", other.getId());
            t.addProperty("name", other.getName().getString());
            t.addProperty("x", op.x); t.addProperty("y", op.y); t.addProperty("z", op.z);
            t.addProperty("vx", ov.x); t.addProperty("vy", ov.y); t.addProperty("vz", ov.z);
            t.addProperty("dim", dim);
            send(t);
        }
    }

    /** 0..1 average remaining durability across worn, damageable armor. */
    private static float averageArmorDurability(ClientPlayerEntity p) {
        float sum = 0f;
        int n = 0;
        for (ItemStack s : p.getInventory().armor) {   // 1.21.2+: check accessor name
            if (s.isEmpty() || !s.isDamageable()) continue;
            sum += 1.0f - (float) s.getDamage() / s.getMaxDamage();
            n++;
        }
        return n == 0 ? 0f : sum / n;
    }

    /** 0..1 remaining durability of the held mainhand item, or 0 if undamageable. */
    private static float heldDurability(ClientPlayerEntity p) {
        ItemStack held = p.getMainHandStack();
        if (held.isEmpty() || !held.isDamageable()) return 0f;
        return 1.0f - (float) held.getDamage() / held.getMaxDamage();
    }

    /** Fire-and-forget UDP send; never touch game threads on failure. */
    public static void send(JsonObject o) {
        try {
            byte[] bytes = o.toString().getBytes(StandardCharsets.UTF_8);
            socket.send(new DatagramPacket(bytes, bytes.length, loopback, PORT));
        } catch (Exception ignored) {
        }
    }
}
