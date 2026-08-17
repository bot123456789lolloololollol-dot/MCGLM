; =====================================================================
; Feature 2 - Frame-perfect eat / gapple swap (AutoHotkey v2)
;
; Press the hotkey: swap to the food/gapple slot -> hold right-click for the
; full eat duration -> release -> snap back to the weapon slot.
;
; Timing facts (Java 1.21.x): eating any food takes exactly 32 ticks.
; At 20 TPS that is 1600 ms. The script holds RMB for HoldMs = 1660 by
; default: the extra ~60 ms is a latency pad so a laggy tick doesn't swallow
; the final tick of consumption. Raising HoldMs is always safe (you just
; stand still holding the apple a moment longer); lowering it below 1600
; risks cancelling the eat entirely, because eating progress resets the
; instant the use-input stops.
;
; Run with AutoHotkey v2. Don't hold right-click yourself during the
; sequence - the script owns RMB until it swaps back.
; =====================================================================
#Requires AutoHotkey v2.0
#SingleInstance Force

; ---- CONFIG (edit to match your hotbar) ------------------------------
GappleSlot   := 3     ; slot with golden apples
FoodSlot     := 8     ; slot with regular food (steak, golden carrot, ...)
WeaponSlot   := 1     ; slot to snap back to after eating
SwapInDelay  := 40    ; ms after the slot swap before holding RMB
HoldMs       := 1660  ; RMB hold: 32 ticks = 1600 ms + latency pad
SwapOutDelay := 30    ; ms after releasing RMB before swapping back

DllCall("Winmm\timeBeginPeriod", "UInt", 1)   ; 1 ms Sleep() accuracy
OnExit(RestoreTimer)

RestoreTimer(*) {
    DllCall("Winmm\timeEndPeriod", "UInt", 1)
    return 0
}

#SuspendExempt
F10::Suspend(-1)
#SuspendExempt False

; Thumb back-button eats a golden apple; F6 eats from the plain food slot.
*XButton1:: EatFrom(GappleSlot)
*F6::       EatFrom(FoodSlot)

EatFrom(slot) {
    global WeaponSlot, SwapInDelay, HoldMs, SwapOutDelay
    static busy := false          ; ignore key auto-repeat while a sequence runs
    if busy
        return
    busy := true
    Send "{" slot "}"             ; gapple/food into the hand
    Sleep SwapInDelay             ; let the swap register server-side
    Send "{RButton down}"         ; start eating
    Sleep HoldMs                  ; exactly 32 ticks (+pad) of uninterrupted use
    Send "{RButton up}"           ; consumption finished on tick 32
    Sleep SwapOutDelay
    Send "{" WeaponSlot "}"       ; weapon back out the moment the eat ends
    busy := false
}
