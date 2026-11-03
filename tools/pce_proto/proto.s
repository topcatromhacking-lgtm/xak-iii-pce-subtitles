; Xak III subtitle renderer prototype (HuCard homebrew, runs in Mednafen pce).
; Demonstrates the proposed renderer: subtitle lines pre-rendered offline into
; 16x16 sprite patterns, uploaded to an off-screen VRAM buffer in <=512-byte
; chunks inside the VBlank IRQ (double-buffered A=$4000 / B=$5000), then a
; prepared SAT image is copied to $7F00 and picked up by auto SATB DMA.
; Cues are keyed to a VBlank frame counter here; on the disc build the key is
; the CD-DA play position (see docs/renderer-design.md).
        .setcpu "huc6280"

frame   = $00       ; word, VBlank counter
state   = $02       ; 0 idle/wait, 1 uploading patterns, 2 write SAT, 3 done
cueptr  = $03       ; word -> current cue_tab entry
src     = $05       ; word
remain  = $07       ; word
vdst    = $09       ; word
chunk   = $0B       ; word
t_src   = $0D
t_dst   = $0F
t_len   = $11
STUB    = $2200     ; RAM copy of "tia src,dst,len / rts"

VDC_AR  = $0000     ; NB: use a: prefix, $00xx would assemble as zero page ($20xx)
VDC_LO  = $0002
VDC_HI  = $0003

        .segment "CODE"
        .include "data.inc"

vdc_regs:
        .byte $05,$00,$00   ; CR: display off during init
        .byte $06,$00,$00   ; RCR
        .byte $07,$00,$00   ; BXR
        .byte $08,$00,$00   ; BYR
        .byte $09,$00,$00   ; MWR 32x32 BAT
        .byte $0A,$02,$02   ; HSR
        .byte $0B,$1F,$03   ; HDR 256 px
        .byte $0C,$02,$0F   ; VSR
        .byte $0D,$EF,$00   ; VDR 240 lines
        .byte $0E,$03,$00   ; VCR
        .byte $0F,$10,$00   ; DCR: SATB DMA auto-repeat every VBlank
        .byte $13,$00,$7F   ; DVSSR = $7F00
vdc_regs_end:

stub_rom:
        tia $0000, $0002, $0000
        rts

reset:  sei
        csh
        cld
        ldx #$FF
        txs
        lda #$FF
        tam #$01            ; MPR0 = I/O page
        lda #$F8
        tam #$02            ; MPR1 = work RAM ($2000)
        lda #$01
        tam #$10            ; MPR4..6 = ROM banks 1..3 at $8000-$DFFF
        lda #$02
        tam #$20
        lda #$03
        tam #$40
        lda #$07
        sta $1402           ; mask all IRQs during init
        stz $0C01           ; timer off
        ldx #$1F
@zp:    stz $00,x
        dex
        bpl @zp
        stz $0400           ; VCE: 5.37 MHz dot clock (256 px)
        ldx #0
@vdc:   lda vdc_regs,x
        sta a:VDC_AR
        lda vdc_regs+1,x
        sta a:VDC_LO
        lda vdc_regs+2,x
        sta a:VDC_HI
        inx
        inx
        inx
        cpx #(vdc_regs_end - vdc_regs)
        bne @vdc
        ldx #7
@stub:  lda stub_rom,x
        sta STUB,x
        dex
        bpl @stub
        ; clear SAT ($7F00, 256 words) from zero padding at end of data bank
        lda #<VRAM_SAT
        sta vdst
        lda #>VRAM_SAT
        sta vdst+1
        jsr set_mawr
        lda #$00
        sta t_src
        lda #$DE
        sta t_src+1
        lda #$00
        sta t_len
        lda #$02
        sta t_len+1
        jsr tia_vdc
        ; init blocks (palette, tiles, BAT)
        ldx #0
@blk:   lda init_tab+2,x
        sta vdst
        lda init_tab+3,x
        sta vdst+1
        lda init_tab+4,x
        sta t_src
        lda init_tab+5,x
        sta t_src+1
        lda init_tab+6,x
        sta t_len
        lda init_tab+7,x
        sta t_len+1
        lda init_tab,x
        beq @vram
        lda vdst            ; VCE colour address
        sta $0402
        lda vdst+1
        sta $0403
        lda #$04
        sta t_dst
        lda #$04
        sta t_dst+1
        jsr tia_any
        bra @next
@vram:  jsr set_mawr
        jsr tia_vdc
@next:  txa
        clc
        adc #8
        tax
        cpx #(NUM_INIT*8)
        bne @blk
        lda #<cue_tab
        sta cueptr
        lda #>cue_tab
        sta cueptr+1
        lda #$05            ; CR: BG + sprites on, VBlank IRQ enabled
        sta a:VDC_AR
        lda #$C8
        sta a:VDC_LO
        lda #$00
        sta a:VDC_HI
        lda #$05
        sta $1402           ; unmask IRQ1 (VDC) only
        cli
main:   bra main

; ---- helpers ------------------------------------------------------------
set_mawr:                   ; VRAM write address = vdst, select VWR
        lda #$00
        sta a:VDC_AR
        lda vdst
        sta a:VDC_LO
        lda vdst+1
        sta a:VDC_HI
        lda #$02
        sta a:VDC_AR
        rts
tia_vdc:
        lda #$02
        sta t_dst
        stz t_dst+1
tia_any:                    ; tia t_src -> t_dst, t_len bytes (via RAM stub)
        lda t_src
        sta STUB+1
        lda t_src+1
        sta STUB+2
        lda t_dst
        sta STUB+3
        lda t_dst+1
        sta STUB+4
        lda t_len
        sta STUB+5
        lda t_len+1
        sta STUB+6
        jmp STUB

; ---- VBlank IRQ: cue engine --------------------------------------------
irq1:   pha
        phx
        phy
        lda a:VDC_AR          ; acknowledge VDC interrupt
        inc frame
        bne @s
        inc frame+1
@s:     jsr service
        ply
        plx
        pla
nullirq:
        rti

service:
        lda state
        beq st_idle
        cmp #1
        beq st_up
        cmp #2
        bne @done
        jmp st_sat
@done:  rts

st_idle:
        ldy #1
        lda (cueptr),y      ; cue frame hi
        cmp #$FF
        bne @cmp
        lda #3
        sta state
        rts
@cmp:   lda frame+1
        cmp (cueptr),y
        bcc @wait
        bne @go
        lda frame
        cmp (cueptr)
        bcc @wait
@go:    ldy #2
        lda (cueptr),y
        sta src
        iny
        lda (cueptr),y
        sta src+1
        iny
        lda (cueptr),y
        sta remain
        iny
        lda (cueptr),y
        sta remain+1
        iny
        lda (cueptr),y
        sta vdst
        iny
        lda (cueptr),y
        sta vdst+1
        lda #1
        sta state
@wait:  rts

st_up:  lda remain
        ora remain+1
        bne @more
        lda #2
        sta state
        rts
@more:  lda remain+1        ; chunk = min(remain, $200)
        cmp #$02
        bcc @small
        stz chunk
        lda #$02
        sta chunk+1
        bra @xfer
@small: lda remain
        sta chunk
        lda remain+1
        sta chunk+1
@xfer:  jsr set_mawr
        lda src
        sta t_src
        lda src+1
        sta t_src+1
        lda chunk
        sta t_len
        lda chunk+1
        sta t_len+1
        jsr tia_vdc
        clc                 ; src += chunk
        lda src
        adc chunk
        sta src
        lda src+1
        adc chunk+1
        sta src+1
        sec                 ; remain -= chunk
        lda remain
        sbc chunk
        sta remain
        lda remain+1
        sbc chunk+1
        sta remain+1
        lsr chunk+1         ; vdst += chunk/2 (words)
        ror chunk
        clc
        lda vdst
        adc chunk
        sta vdst
        lda vdst+1
        adc chunk+1
        sta vdst+1
        rts

st_sat: lda #<VRAM_SAT
        sta vdst
        lda #>VRAM_SAT
        sta vdst+1
        jsr set_mawr
        ldy #8
        lda (cueptr),y
        sta t_src
        iny
        lda (cueptr),y
        sta t_src+1
        stz t_len
        lda #$02
        sta t_len+1
        jsr tia_vdc
        clc
        lda cueptr
        adc #10
        sta cueptr
        bcc @n
        inc cueptr+1
@n:     stz state
        rts

        .segment "DATA"
        .incbin "data.bin"

        .segment "VEC"
        .word nullirq, irq1, nullirq, nullirq, reset
