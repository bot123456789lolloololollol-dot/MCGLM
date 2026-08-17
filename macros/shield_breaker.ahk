; =====================================================================
; Feature 1 - Shield-breaker combo (AutoHotkey v2)
;
; Press/hold the hotkey: swap to the axe slot -> attack (axe hits roll the
; shield-disable) -> swap straight back to the sword.
;
; Shield-disable facts (Java Edition): an axe hit on a blocking shield
; disables it for 100 ticks (5 s). On most versions the chance is 25% base
; +5% per Efficiency level on the axe, so repeat hits are the point of the
; hold-to-repeat loop below.
;
; Run with AutoHotkey v2 (v1 will not parse this). If the game ignores the
; input, make sure script and game run at the same privilege level.
; =====================================================================
#Requires AutoHotkey v2.0
#SingleInstance Force

; ---- CONFIG (edit to match your hotbar) ------------------------------
AxeSlot   := 2      ; hotbar slot holding your axe
SwordSlot := 1      ; hotbar slot holding your sword
SwapDelay := 25     ; ms between "switch to axe" and the attack registering
BackDelay := 35     ; ms after the attack before switching back to the sword
Repeat    := true   ; true = keep repeating while the hotkey is held
HitEvery  := 300    ; ms between axe hits while held (attack-cooldown friendly)

; 1 ms Windows timer resolution so Sleep() is actually millisecond accurate
; (default granularity is ~15.6 ms, which is sloppy for tick-precise swaps).
DllCall("Winmm\timeBeginPeriod", "UInt", 1)
OnExit(RestoreTimer)

RestoreTimer(*) {
    DllCall("Winmm\timeEndPeriod", "UInt", 1)
    return 0
}

; F10 pauses/resumes every hotkey in this script. #SuspendExempt keeps F10
; itself working while suspended.
#SuspendExempt
F10::Suspend(-1)
#SuspendExempt False

; Mouse "forward" side button - comfortable under the thumb mid-fight.
; Change to any key, e.g. *X:: or *CapsLock::
*XButton2:: ShieldBreaker()

ShieldBreaker() {
    global AxeSlot, SwordSlot, SwapDelay, BackDelay, Repeat, HitEvery
    loop {
        Send "{" AxeSlot "}"      ; hotbar slot 2 -> axe in hand
        Sleep SwapDelay           ; one game tick or so for the swap to land
        Click                     ; left-click: the axe hit that rolls the disable
        Sleep BackDelay           ; let the attack packet leave with the axe held
        Send "{" SwordSlot "}"    ; snap back to the sword
        if !Repeat || !GetKeyState("XButton2", "P")
            break
        Sleep HitEvery            ; held: keep hammering axe hits
    }
}
