; Small patches outside bank $83 (assembled by build_subs.py).
        .setcpu "huc6280"
RFLAG  = $76FE          ; set by the engine while a cue is on screen
NARROW = $76FD          ; 1 while the game runs a 128-px-wide shot (HSR $0A02 / HDR $0C0F)
WIDE   = $76FC          ; 1 after we widened the lower band in this frame

; bank $81 $76DF: raster CR helper, called from $65AA with A = CR shadow, X = band, inside
; the RCR interrupt before the CR write, so it must stay short (a slow helper lets the BG
; of the first letterbox line show). Original v0.10: AND #$3F / ORA $3E72,X / BPL +2 /
; ORA #$40 / RTS (sprites only where BG is on). Added: sprites also on in the lower band
; (start line $A8..$DF) while the engine has set RFLAG. Y is free here.
        .segment "HELPER"
        and #$3F
        ora $3E72,x
        bmi @on
        ldy RFLAG
        beq @off
        ldy $3E32,x
        cpy #$A8
        bcc @off
        cpy #$E0
        bcs @off
@on:    ora #$40
@off:   rts

; bank $81 $65D3: the raster routine's last write (STA $0003 / RTS) becomes JMP tail.
; The width change is done here, after CR/BYR/BXR, where a late write is harmless
; (the lower band is BG-off and black).
        .segment "TPATCH"
        jmp tail
        nop

; bank $81 $7700 (zero in every King-scene state and on disc).
        .segment "HELPER2"
tail:   sta a:$0003
        lda NARROW              ; only during the game's 128-px shots
        beq @done
        lda RFLAG
        beq @rest
        lda $3E32,x
        cmp #$A8
        bcc @rest
        cmp #$E0
        bcs @rest
        lda WIDE
        bne @done
        st0 #$0A                ; full 256-px window for the subtitle band
        st1 #$02
        st2 #$02
        st0 #$0B
        st1 #$1F
        st2 #$04
        lda #1
        sta WIDE
        rts
@rest:  lda WIDE
        beq @done
        st0 #$0A                ; back to the game's 128-px window
        st1 #$02
        st2 #$0A
        st0 #$0B
        st1 #$0F
        st2 #$0C
        stz WIDE
@done:  rts

; Entry of the game's "narrow" ($8D44) and "full" ($8D59) display-width routines:
; LDA #$0A / STA $F7 is replaced by JSR here / NOP, so we know the current width.
setn:   lda #1
        sta NARROW
        stz WIDE
        lda #$0A
        sta $F7
        rts
setf:   stz NARROW
        stz WIDE
        lda #$0A
        sta $F7
        rts

        .segment "NPATCH"
        jsr setn
        nop
        .segment "FPATCH"
        jsr setf
        nop

; bank $82 $9C00: called from the scene main loop ($8EE5 JSR $9C00), maps bank $83 at
; $A000 and runs the engine (which also does the native SAT write).
        .segment "STUB"
        pha
        phx
        phy
        tma #$20
        pha
        lda #$83
        tam #$20
        jsr $A000
        pla
        tam #$20
        ply
        plx
        pla
        rts
