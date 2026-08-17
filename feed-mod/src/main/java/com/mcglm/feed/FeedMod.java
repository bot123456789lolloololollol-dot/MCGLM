package com.mcglm.feed;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.phys.Vec3;

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
 * Minecraft 26.2 uses Mojang's official names and local-only UDP output.
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
            if (client.player != null && client.level != null) tick(client);
        });
    }

    private void tick(Minecraft client) {
        LocalPlayer p = client.player;
        String dim = client.level.dimension().identifier().toString();

        // ---- self state ("t":"p") ----
        JsonObject self = new JsonObject();
        Vec3 pos = p.position(), vel = p.getDeltaMovement();
        self.addProperty("t", "p");
        self.addProperty("x", pos.x);   self.addProperty("y", pos.y);   self.addProperty("z", pos.z);
        self.addProperty("yaw", p.getYRot()); self.addProperty("pitch", p.getXRot());
        self.addProperty("vx", vel.x);  self.addProperty("vy", vel.y);  self.addProperty("vz", vel.z);
        self.addProperty("hp", p.getHealth());
        self.addProperty("max_hp", p.getMaxHealth());
        self.addProperty("armor", p.getArmorValue());
        self.addProperty("armor_dur", averageArmorDurability(p));
        self.addProperty("food", p.getFoodData().getFoodLevel());
        self.addProperty("held", BuiltInRegistries.ITEM.getKey(p.getMainHandItem().getItem()).toString());
        self.addProperty("off", BuiltInRegistries.ITEM.getKey(p.getOffhandItem().getItem()).toString());
        self.addProperty("totems", countTotems(p));
        self.addProperty("held_dur", heldDurability(p));
        self.addProperty("using_item", p.isUsingItem());
        self.addProperty("use_ticks", p.getTicksUsingItem());
        self.addProperty("active_item", BuiltInRegistries.ITEM.getKey(p.getActiveItem().getItem()).toString());
        self.addProperty("dim", dim);
        JsonArray effects = new JsonArray();
        p.getActiveEffects().forEach(e -> {
            JsonObject o = new JsonObject();
            o.addProperty("id", e.getEffect().unwrapKey()
                    .map(key -> key.identifier().toString()).orElse("unknown"));
            o.addProperty("ticks", e.getDuration());
            effects.add(o);
        });
        self.add("effects", effects);
        send(self);

        // ---- nearby players ("t":"tgt") + logout position cache ----
        LAST_KNOWN.put(p.getUUID(), new double[]{pos.x, pos.y, pos.z});
        for (Player other : client.level.players()) {
            if (other == p) continue;
            Vec3 op = other.position(), ov = other.getDeltaMovement();
            LAST_KNOWN.put(other.getUUID(), new double[]{op.x, op.y, op.z});
            NAMES.put(other.getUUID(), other.getName().getString());
            if (other.distanceToSqr(p) > TARGET_RANGE_SQ) continue;
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
    private static float averageArmorDurability(LocalPlayer p) {
        float sum = 0f;
        int n = 0;
        for (EquipmentSlot slot : new EquipmentSlot[]{EquipmentSlot.HEAD, EquipmentSlot.CHEST,
                EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
            ItemStack s = p.getItemBySlot(slot);
            if (s.isEmpty() || !s.isDamageableItem()) continue;
            sum += 1.0f - (float) s.getDamageValue() / s.getMaxDamage();
            n++;
        }
        return n == 0 ? 0f : sum / n;
    }

    /** 0..1 remaining durability of the held mainhand item, or 0 if undamageable. */
    private static float heldDurability(LocalPlayer p) {
        ItemStack held = p.getMainHandItem();
        if (held.isEmpty() || !held.isDamageableItem()) return 0f;
        return 1.0f - (float) held.getDamageValue() / held.getMaxDamage();
    }

    private static int countTotems(LocalPlayer p) {
        int count = 0;
        for (ItemStack stack : p.getInventory().getNonEquipmentItems()) {
            if (stack.is(Items.TOTEM_OF_UNDYING)) count += stack.getCount();
        }
        if (p.getOffhandItem().is(Items.TOTEM_OF_UNDYING)) count += p.getOffhandItem().getCount();
        return count;
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
