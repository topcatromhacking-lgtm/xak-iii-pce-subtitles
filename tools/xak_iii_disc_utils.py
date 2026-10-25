"""Raw Mode1/2352 sector verification and IPS helpers used by Xak III v0.10.

Original, standard EDC/ECC implementation (not game data).
"""
SECTOR_SIZE=2352
HOOK_RAW=0x1AC0C0
SYNC=bytes((0,)+(255,)*10+(0,))

def _edc_table():
    table=[]
    for i in range(256):
        v=i
        for _ in range(8):
            v=((v>>1) ^ (0xD8018001 if v&1 else 0))&0xffffffff
        table.append(v)
    return table

def _ecc_tables():
    fwd=[0]*256
    back=[0]*256
    for i in range(256):
        j=(i<<1)^(0x11D if i&0x80 else 0)
        fwd[i]=j
        back[j^i]=i
    return fwd,back

EDC_TABLE=_edc_table()
ECC_FWD,ECC_BACK=_ecc_tables()

def _edc(b):
    n=0
    for c in b:
        n=(n>>8)^EDC_TABLE[(n^c)&0xff]
    return n

def _ecc(source, major_count, minor_count, major_mult, minor_inc):
    size=major_count*minor_count
    out=bytearray(major_count*2)
    for major in range(major_count):
        idx=(major>>1)*major_mult+(major&1)
        a=b=0
        for _ in range(minor_count):
            t=source[idx]
            idx+=minor_inc
            if idx>=size:idx-=size
            a^=t;b^=t
            a=ECC_FWD[a]
        a=ECC_BACK[ECC_FWD[a]^b]
        out[major]=a
        out[major+major_count]=a^b
    return bytes(out)

def restore_mode1_sector(raw):
    if len(raw)!=SECTOR_SIZE or raw[:12]!=SYNC or raw[15]!=1:
        raise ValueError('Expected raw MODE1/2352 sector')
    b=bytearray(raw)
    b[2064:2068]=_edc(b[:2064]).to_bytes(4,'little')
    b[2068:2076]=b'\0'*8
    b[2076:2248]=_ecc(b[12:12+2064],86,24,2,86)
    b[2248:2352]=_ecc(b[12:12+2236],52,43,86,88)
    return bytes(b)

def verify_mode1_sector(raw):
    return restore_mode1_sector(raw)==raw

def create_ips(before,after):
    if len(before)!=len(after):raise ValueError('IPS file lengths differ')
    diffs=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
    result=bytearray(b'PATCH')
    if diffs:
        groups=[];first=last=diffs[0]
        for i in diffs[1:]:
            if i-last>4 or i-first>=65535:
                groups.append((first,last+1));first=i
            last=i
        groups.append((first,last+1))
        for lo,hi in groups:
            if hi>1<<24:raise ValueError('IPS position exceeds 24bit')
            data=after[lo:hi]
            result+=lo.to_bytes(3,'big')+len(data).to_bytes(2,'big')+data
    result+=b'EOF'
    return bytes(result)

def apply_ips(before,patch):
    if not patch.startswith(b'PATCH') or not patch.endswith(b'EOF'):
        raise ValueError('Invalid IPS marker')
    out=bytearray(before)
    at=5
    while at<len(patch)-3:
        lo=int.from_bytes(patch[at:at+3],'big')
        n=int.from_bytes(patch[at+3:at+5],'big')
        at+=5
        if n:
            data=patch[at:at+n];at+=n
        else:
            count=int.from_bytes(patch[at:at+2],'big')
            data=bytes((patch[at+2],))*count;at+=3
        if lo+len(data)>len(out):raise ValueError('IPS writes outside source')
        out[lo:lo+len(data)]=data
    if at!=len(patch)-3:raise ValueError('Malformed IPS')
    return bytes(out)
