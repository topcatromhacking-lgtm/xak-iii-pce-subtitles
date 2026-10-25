#!/usr/bin/env python3
"""Read-only comparison of Geargrafx wide/narrow scene hardware state and SAT.

Pass real native saved states captured from the v0.11 or v0.14 CUE at the
wide shot and at the narrow shot. Does not export proprietary game bytes.
"""
import argparse,json,struct
from pathlib import Path
import build_xak_iii_v14_letterbox_geometry as v

VPC_START=v.VRAM-1059-33
WRAM=21

def summarize(b):
 v.validate(b)
 regs=struct.unpack_from('<20H',b,v.VDC_REGS)
 vp=b[VPC_START:VPC_START+33]
 return dict(vdc_registers={hex(i):hex(regs[i]) for i in (5,6,7,8,9,10,11,12,13,14,15,19)},
             vp_control_hex=vp.hex(' '),
             raster_enable_top64=b[WRAM+0x3E72-0x2000:WRAM+0x3E72-0x2000+64].hex(' '),
             scroll_x_top64=b[WRAM+0x3EB2-0x2000:WRAM+0x3EB2-0x2000+64].hex(' '),
             native_sprites=[s for s in v.sat_info(b) if not s['is_subtitle']],
             subtitle_sprites=[s for s in v.sat_info(b) if s['is_subtitle']])

def compare(a,b):
 va,vb=summarize(a),summarize(b)
 rd={}
 for n in va:
  if n=='vdc_registers':
   diff={k:[va[n][k],vb[n][k]] for k in va[n] if va[n][k]!=vb[n][k]}
  elif n in ('subtitle_sprites','native_sprites'):
   diff={'wide_count':len(va[n]),'narrow_count':len(vb[n]),
         'wide':va[n],'narrow':vb[n]}
  else:
   diff={'wide':va[n],'narrow':vb[n]} if va[n]!=vb[n] else None
  if diff:rd[n]=diff
 return {'status':'READ ONLY','observed_photo_subtitle_x_shift':64,
         'different_hardware_and_sprite_fields':rd,
         'warning':'VPC serialized bytes are opaque until decoded from Geargrafx source; static snapshots may miss per-line writes'}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--wide-state',type=Path,required=True)
 p.add_argument('--narrow-state',type=Path,required=True)
 p.add_argument('--report',type=Path)
 args=p.parse_args()
 output=json.dumps(compare(args.wide_state.read_bytes(),args.narrow_state.read_bytes()),indent=2)+'\n'
 if args.report:args.report.open('x').write(output)
 else:print(output)
