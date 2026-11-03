; Xak III cinematic subtitle engine (runs from CD-RAM bank $83, mapped at $A000 by the
; $9C00 stub in bank $82). Called once per scene main-loop pass in place of the native
; SAT writer at $8516.
;
;  * clock   : VBlank counter $2338 (incremented by the game's VSync IRQ), accumulated
;              into a 16-bit frame count from the first call of the scene.
;  * text    : rendered at runtime from an 8x12 1bpp font into a 256x12 line buffer, then
;              cut into 16x16 sprite cells. 4 bitplanes x 8 patterns = 32 cells live in
;              VRAM $0D00-$0EFF; each cell uses one plane and a palette that shows only
;              that plane (white) - the other planes come out black on the black band.
;  * band    : the raster helper in bank $81 ($76DF) enables sprites in the lower black
;              band only while RFLAG ($76FE) is set.
;  * leakage : 8 transparent-to-the-eye 32x64 "blocker" sprites at X=-32 sit right after
;              the text in the SAT, covering lines BLK_Y..BLK_Y+63. They use up the 16
;              sprite cells/line budget there, so native sprites (Pixie, mouths, bodies)
;              are dropped *only on band lines*. Natives keep every pixel above BLK_Y:
;              no sprite is cropped or removed in the picture.
        .setcpu "huc6280"

VSYNC   = $2338
SATBLO  = $233F
SATBHI  = $2340
NQ      = $3444
QSEL    = $2EA4
RFLAG   = $76FE
VPAT    = $0D00                 ; VRAM word address of our 8 patterns
PATNO   = VPAT >> 5             ; SAT pattern field of pattern 0

zp_txt  = $10                   ; ZP $10-$17 are saved and restored around the engine
zp_gly  = $12
zp_dst  = $14
zp_src  = $16

        .segment "ENGINE"
entry:  jmp main
initf:  .byte $FF               ; $FF on disc => first call after the module load
frame:  .word 0
last:   .byte 0
cur:    .byte 0
state:  .byte 0                 ; 0 = need render, 1 = rendered/waiting, 2 = shown
ncells: .byte 0
lineno: .byte 0
term:   .byte 0
wid:    .byte 0
x0:     .byte 0
px:     .byte 0
sh:     .byte 0
vhi:    .byte 0
vlo:    .byte 0
cc:     .byte 0
c1:     .byte 0
used:   .byte 0
armv:   .byte 0
zsave:  .res 8

main:
        tii $2010, zsave, 8
        lda initf
        cmp #$FF
        bne @run
        stz initf
        stz frame
        stz frame+1
        lda VSYNC
        sta last
        stz cur
        stz state
        stz RFLAG
@run:
        lda VSYNC
        tax
        sec
        sbc last
        stx last
        clc
        adc frame
        sta frame
        bcc :+
        inc frame+1
:
        lda cur
        cmp #NCUES
        bcs @out
        lda state
        bne @notidle
        jsr render
        lda #1
        sta state
@notidle:
        lda cur
        asl a
        tay
        lda state
        cmp #2
        beq @shown
        lda frame
        cmp cue_start,y
        lda frame+1
        sbc cue_start+1,y
        bcc @out
        jsr upload
        lda #2
        sta state
        lda VSYNC               ; the SAT written below reaches the SATB at the next
        sta armv                ; VBlank: enable band sprites only after that
        bra @out
@shown:
        lda frame
        cmp cue_end,y
        lda frame+1
        sbc cue_end+1,y
        bcc @out
        stz state
        inc cur
@out:
        jsr satwrite
        lda state
        cmp #2
        bne @off
        jsr palettes
        lda VSYNC
        cmp armv
        beq @off
        lda #1
        sta RFLAG
        bra @done
@off:   stz RFLAG
@done:  tii zsave, $2010, 8
        rts

; ---------------------------------------------------------------- text fetch
getc:   lda (zp_txt)
        inc zp_txt
        bne :+
        inc zp_txt+1
:       cmp #0
        rts

; ---------------------------------------------------------------- render cue `cur`
render:
        lda cur
        asl a
        tay
        lda cue_text,y
        sta zp_txt
        lda cue_text+1,y
        sta zp_txt+1
        stz patbuf
        tii patbuf, patbuf+1, 127
        tii patbuf, patbuf+128, 128
        tii patbuf, patbuf+256, 256
        tii patbuf, patbuf+512, 256
        tii patbuf, patbuf+768, 256
        stz ncells
        stz lineno
@line:
        stz linebuf
        tii linebuf, linebuf+1, 383
        ; measure: sum advances up to '|' or 0 (pointer restored afterwards)
        lda zp_txt
        pha
        lda zp_txt+1
        pha
        stz wid
@m:     jsr getc
        beq @mend
        cmp #'|'
        beq @mend
        sec
        sbc #$20
        tax
        lda font_widths,x
        clc
        adc wid
        bcc :+
        lda #$FF
:       sta wid
        bra @m
@mend:  pla
        sta zp_txt+1
        pla
        sta zp_txt
        lda wid
        beq :+
        dec a                   ; last advance includes the inter-glyph gap
        sta wid
:       ; x0 = (256 - wid) / 2
        lda #0
        sec
        sbc wid
        ror a                   ; carry from SBC is 0 unless wid==0 (then 256/2)
        sta x0
        sta px
        ; draw glyphs
@d:     jsr getc
        beq @dend0
        cmp #'|'
        beq @dend1
        sec
        sbc #$20
        pha
        jsr blit
        pla
        tax
        lda font_widths,x
        clc
        adc px
        sta px
        bra @d
@dend0: stz term
        bra @cells
@dend1: lda #1
        sta term
@cells: lda wid
        beq @nextline
        jsr cells
@nextline:
        inc lineno
        lda term
        beq @rdone
        lda lineno
        cmp #2
        bcs @rdone
        jmp @line
@rdone: rts

; blit glyph A (0..95) at pixel px into linebuf
blit:   tax
        lda glyph_lo,x
        sta zp_gly
        lda glyph_hi,x
        sta zp_gly+1
        lda px
        and #7
        sta sh
        lda px
        lsr a
        lsr a
        lsr a
        clc
        adc #<linebuf
        sta zp_dst
        lda #>linebuf
        adc #0
        sta zp_dst+1
        cly
@row:   lda (zp_gly),y
        beq @next
        sta vhi
        stz vlo
        ldx sh
        beq @nosh
@shl:   lsr vhi
        ror vlo
        dex
        bne @shl
@nosh:  phy
        cly
        lda (zp_dst),y
        ora vhi
        sta (zp_dst),y
        iny
        lda (zp_dst),y
        ora vlo
        sta (zp_dst),y
        ply
@next:  lda zp_dst
        clc
        adc #32
        sta zp_dst
        bcc :+
        inc zp_dst+1
:       iny
        cpy #12
        bne @row
        rts

; cut columns x0..x0+wid-1 of linebuf into 16x16 cells, append SAT records
cells:  lda x0
        lsr a
        lsr a
        lsr a
        lsr a
        sta cc
        lda x0
        clc
        adc wid
        bcc :+
        lda #0                  ; ends past 255 -> clamp to last column
:       dec a
        lsr a
        lsr a
        lsr a
        lsr a
        sta c1
@cell:  lda ncells
        cmp #32
        bcc :+
        rts
:       ; dst = patbuf + (k&7)*128 + (k>>3)*32 + 4
        and #7
        lsr a                   ; (k&7)*128 = ((k&7)>>1)*256 + ((k&1)*128)
        php
        clc
        adc #>patbuf
        sta zp_dst+1
        lda #0
        plp
        bcc :+
        lda #$80
:       sta zp_dst
        lda ncells
        lsr a
        lsr a
        lsr a                   ; plane 0..3
        asl a
        asl a
        asl a
        asl a
        asl a                   ; *32
        clc
        adc #4
        clc
        adc zp_dst
        sta zp_dst
        bcc :+
        inc zp_dst+1
:       ; src = linebuf + cc*2
        lda cc
        asl a
        clc
        adc #<linebuf
        sta zp_src
        lda #>linebuf
        adc #0
        sta zp_src+1
        ldx #12
        cly
@r:     phy
        ldy #1
        lda (zp_src),y          ; right 8 px -> low byte
        ply
        sta (zp_dst),y
        iny
        phy
        cly
        lda (zp_src),y          ; left 8 px -> high byte
        ply
        sta (zp_dst),y
        iny
        lda zp_src
        clc
        adc #32
        sta zp_src
        bcc :+
        inc zp_src+1
:       dex
        bne @r
        ; SAT record at satbuf + k*8
        lda ncells
        asl a
        asl a
        asl a
        tax
        ldy lineno
        lda line_ylo,y
        sta satbuf,x
        lda line_yhi,y
        sta satbuf+1,x
        lda cc
        asl a
        asl a
        asl a
        asl a
        clc
        adc #32
        sta satbuf+2,x
        lda #0
        adc #0
        sta satbuf+3,x
        lda ncells
        and #7
        asl a
        clc
        adc #<PATNO
        sta satbuf+4,x
        lda #>PATNO
        sta satbuf+5,x
        lda ncells
        lsr a
        lsr a
        lsr a
        tay
        lda pal_ids,y
        ora #$80
        sta satbuf+6,x
        stz satbuf+7,x
        inc ncells
        lda cc
        cmp c1
        beq @cdone
        inc cc
        jmp @cell
@cdone: rts

; ---------------------------------------------------------------- VRAM upload
upload: lda #0
        sta $F7
        st0 #0
        st1 #<VPAT
        st2 #>VPAT
        lda #2
        sta $F7
        st0 #2
        tia patbuf, $0002, 128
        tia patbuf+128, $0002, 128
        tia patbuf+256, $0002, 128
        tia patbuf+384, $0002, 128
        tia patbuf+512, $0002, 128
        tia patbuf+640, $0002, 128
        tia patbuf+768, $0002, 128
        tia patbuf+896, $0002, 128
        rts

; ---------------------------------------------------------------- palettes
palettes:
        clx
@p:     lda pal_ids,x
        asl a
        asl a
        asl a
        asl a
        sta a:$0402
        lda #1
        sta a:$0403
        txa
        asl a
        asl a
        asl a
        asl a
        asl a
        tay
        phx
        ldx #32
@c:     lda pal_data,y
        sta a:$0404
        iny
        lda pal_data,y
        sta a:$0405
        iny
        dex
        dex
        bne @c
        plx
        inx
        cpx #4
        bne @p
        rts

; ---------------------------------------------------------------- SAT writer ($8516 replacement)
satwrite:
        lda #0
        sta $F7
        st0 #0
        lda SATBLO
        sta a:$0002
        lda SATBHI
        sta a:$0003
        lda #2
        sta $F7
        st0 #2
        stz used
        lda state
        cmp #2
        bne @natives
        ; text cells
        ldx #0
        ldy ncells
        beq @blk
@t:     lda satbuf,x
        sta a:$0002
        lda satbuf+1,x
        sta a:$0003
        lda satbuf+2,x
        sta a:$0002
        lda satbuf+3,x
        sta a:$0003
        lda satbuf+4,x
        sta a:$0002
        lda satbuf+5,x
        sta a:$0003
        lda satbuf+6,x
        sta a:$0002
        lda satbuf+7,x
        sta a:$0003
        txa
        clc
        adc #8
        tax
        dey
        bne @t
@blk:   ldy #8
@b:     lda #<(BLK_Y+64)
        sta a:$0002
        lda #>(BLK_Y+64)
        sta a:$0003
        stz a:$0002             ; X = 0 (screen -32): off-screen, still counted per line
        stz a:$0003
        stz a:$0002             ; pattern 0
        stz a:$0003
        stz a:$0002             ; palette 0, behind BG
        lda #$31                ; 32 x 64
        sta a:$0003
        dey
        bne @b
        lda ncells
        clc
        adc #8
        sta used
@natives:
        lda #64
        sec
        sbc used
        sta cc                  ; room left
        lda NQ
        cmp cc
        bcc :+
        lda cc
:       sta c1                  ; native count to write
        clx
@n:     cpx c1
        bcs @fill
        ldy QSEL,x
        lda $3264,y
        sta a:$0002
        lda $32C4,y
        sta a:$0003
        lda $3324,y
        sta a:$0002
        lda $3384,y
        sta a:$0003
        lda $30E4,y
        sta a:$0002
        lda $3144,y
        sta a:$0003
        lda $33E4,y
        sta a:$0002
        lda $3204,y
        sta a:$0003
        inx
        bra @n
@fill:  txa
        clc
        adc used
        tax
@z:     cpx #64
        bcs @zd
        stz a:$0002
        stz a:$0003
        stz a:$0002
        stz a:$0003
        stz a:$0002
        stz a:$0003
        stz a:$0002
        stz a:$0003
        inx
        bra @z
@zd:    stz NQ
        rts

; ---------------------------------------------------------------- tables
line_ylo: .byte <(LINE1_Y+64), <(LINE2_Y+64)
line_yhi: .byte >(LINE1_Y+64), >(LINE2_Y+64)
        .include "data.inc"     ; generated: cues, text, font, palette ids, BLK_Y, LINE*_Y

        .segment "BUFS"
satbuf:  .res 32*8
linebuf: .res 384
        .segment "PATBUF"
patbuf:  .res 1024
