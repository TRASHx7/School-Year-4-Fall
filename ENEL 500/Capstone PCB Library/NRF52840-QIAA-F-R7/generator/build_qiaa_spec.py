# Build the QIAA (aQFN73) spec for gen_altium.py from nRF52840 PS v1.8 chapter 7.
#  - Ball names/functions: Table 145 (text on PDF pages 2-4 of the upload).
#  - Ball positions: circle centres in Figure 207 (PDF page 1), scaled with the
#    Figure 210 / Table 148 dimensions (e = 0.50, e1 = 2.75, e2 = 0.559, b = 0.25, D2 = 4.85).
import json, re, sys

# Usage: build_qiaa_spec.py <dir with table145.txt and p1_paths.txt> <out spec.json>
#   table145.txt: pdftotext -layout of the Table 145 pages
#   p1_paths.txt: pdf_circles.py output for the Figure 207 page
pkg = sys.argv[1]

# ---- Table 145
lines = open(pkg + '/table145.txt').read().splitlines()
start = next(i for i, l in enumerate(lines) if l.strip().startswith('A8 '))
end = next(i for i, l in enumerate(lines) if 'Table 145' in l)
balls = {}  # ball -> [names]
order = []
cur = None
for l in lines[start:end]:
    m = re.match(r'^(\S+)\s{2,}(\S+(?: \S+)?)\s{2,}(Digital I/O|Analog input|Power|RF|Debug|USB|NFC input|Trace clock|Trace data|Trace buffer)?', l)
    m2 = re.match(r'^\s{8,}(\S+)\s{2,}(Analog input|NFC input|Trace clock|Trace data)\b', l)
    if re.match(r'^(Die pad)\s', l):
        cur = 'EP'; balls[cur] = ['VSS']; order.append(cur); continue
    if m and re.fullmatch(r'[A-Z]{1,2}\d{1,2}', m.group(1)):
        cur = m.group(1); balls[cur] = [m.group(2).strip()]; order.append(cur)
    elif m2 and cur:
        balls[cur].append(m2.group(1))
    elif cur and re.match(r'^\s{8,}(nRESET)\s', l):
        balls[cur].append('nRESET')
    elif cur and re.match(r'^\s{8,}Not connected\s*$', l):
        balls[cur].append('NC')
assert len(balls) == 74, len(balls)

# ---- Figure 207 ball centres -> mm
ROWS = 'A B C D E F G H J K L M N P R T U V W Y AA AB AC AD'.split()
pts = [l.split() for l in open(pkg + '/p1_paths.txt')]
cen = [(float(p[0]), float(p[1])) for p in pts if 8.5 < float(p[2]) < 9.2 and 11.2 < float(p[3]) < 11.8]
def clusters(v, tol=0.6):
    v = sorted(v); out = [[v[0]]]
    for a in v[1:]:
        if a - out[-1][-1] < tol: out[-1].append(a)
        else: out.append([a])
    return [sum(c) / len(c) for c in out]
xs, ys = clusters([c[0] for c in cen]), clusters([c[1] for c in cen])
assert len(xs) == 24 and len(ys) == 24
cx, cy = (xs[0] + xs[-1]) / 2, (ys[0] + ys[-1]) / 2
scale = (xs[-1] - xs[0]) / 6.5          # outer columns at +/-(e1 + e) = +/-3.25 mm
def snap(v): return round(v / 0.25) * 0.25
colx = {i + 1: snap((x - cx) / scale) for i, x in enumerate(xs)}
rowy = {r: snap((cy - y) / scale) for r, y in zip(ROWS, ys)}   # +Y up (top view)
occupied = set()
for x, y in cen:
    c = min(colx, key=lambda k: abs(xs[k - 1] - x)); r = min(ROWS, key=lambda k: abs(ys[ROWS.index(k)] - y))
    occupied.add(f'{r}{c}')
named = set(b for b in balls if b != 'EP')
assert occupied == named, (sorted(occupied - named), sorted(named - occupied))

def pos(b):
    m = re.fullmatch(r'([A-Z]+)(\d+)', b)
    return colx[int(m.group(2))], rowy[m.group(1)]

# Mechanical check: outer ring on odd multiples of 0.25 along the edge, inner ring on multiples of 0.5
for b in named:
    x, y = pos(b)
    if abs(abs(x) - 3.25) < 1e-6 or abs(abs(y) - 3.25) < 1e-6:
        along = y if abs(abs(x) - 3.25) < 1e-6 else x
        assert abs((along / 0.25) % 2 - 1) < 1e-6, ('outer', b, x, y)
    else:
        assert abs(abs(x) - 2.75) < 1e-6 or abs(abs(y) - 2.75) < 1e-6, ('inner ring', b, x, y)
        along = y if abs(abs(x) - 2.75) < 1e-6 else x
        assert abs((along / 0.5) - round(along / 0.5)) < 1e-6, ('inner', b, x, y)

# ---- pin names, types, symbol placement
def pin_name(b):
    n = balls[b]
    if b == 'N24': return 'NC'                   # DEC5 on build code D, not connected on F
    if b == 'AD22': return 'P1.00/TRACEDATA0'
    return '/'.join(n)
def classify(b, name):
    p = name.split('/')[0]
    if b == 'EP' or p in ('VSS', 'VSS_PA'): return 'bottom', 'GND', 'power'
    if p.startswith('P0.'): return 'right', 'P0', 'io'
    if p.startswith('P1.'): return 'left', 'P1', 'io'
    if p in ('VDDH', 'VDD'): return 'left', '1 Supply', 'power'
    if p in ('DEC1', 'DEC2', 'DEC3', 'DEC4', 'DEC6', 'DCC', 'DCCH', 'NC'): return 'left', '2 Regulator', 'passive'
    if p in ('XC1', 'XC2'): return 'left', '3 Clock', 'passive'
    if p == 'ANT': return 'left', '4 RF', 'passive'
    if p == 'SWDIO': return 'left', '5 Debug', 'io'
    if p == 'SWDCLK': return 'left', '5 Debug', 'in'
    if p in ('VBUS',): return 'left', '6 USB', 'power'
    if p in ('DECUSB',): return 'left', '6 USB', 'passive'
    if p in ('D+', 'D-'): return 'left', '6 USB', 'io'
    raise ValueError(b, name)
def key(pin):
    side_rank = {'1 Supply': 0, '2 Regulator': 1, '3 Clock': 2, '4 RF': 3, '5 Debug': 4, '6 USB': 5, 'P1': 6, 'P0': 0, 'GND': 0}
    nm = pin['name'].split('/')[0]
    m = re.match(r'P(\d)\.(\d+)', nm)
    sub = int(m.group(2)) if m else ['VDDH', 'VDD', 'DEC1', 'DEC2', 'DEC3', 'DEC4', 'DEC6', 'DCC', 'DCCH', 'NC', 'XC1', 'XC2', 'ANT',
                                     'SWDIO', 'SWDCLK', 'VBUS', 'DECUSB', 'D+', 'D-', 'VSS', 'VSS_PA'].index(nm) if nm in (
        'VDDH', 'VDD', 'DEC1', 'DEC2', 'DEC3', 'DEC4', 'DEC6', 'DCC', 'DCCH', 'NC', 'XC1', 'XC2', 'ANT', 'SWDIO', 'SWDCLK', 'VBUS', 'DECUSB', 'D+', 'D-', 'VSS', 'VSS_PA') else 99
    return (side_rank[pin['group']], sub, pin['num'] == 'EP', pin['num'])
pins = []
for b in order:
    name = pin_name(b)
    side, group, typ = classify(b, name)
    pins.append(dict(num=b, name=name, side=side, group=group, type=typ))
pins.sort(key=key)

pads = []
for b in order:
    if b == 'EP': continue
    x, y = pos(b)
    pads.append(dict(name=b, x=x, y=y, dx=0.25, dy=0.25, shape='round'))

spec = dict(
    title='Nordic nRF52840-QIAA-F-R7 (aQFN73 7 x 7 mm): Altium footprint and schematic symbol',
    source='nRF52840 Product Specification v1.8, section 7.1.1 (Figure 207, Table 145) and section 7.2.1 (Figure 210, Table 148)',
    date='2026-11-01', basename='NRF52840-QIAA-F-R7',
    footprint=dict(
        name='NORDIC_AQFN73_7X7MM_P0.5', height_note='A max 0.85',
        description='Nordic aQFN73 7.0 x 7.0 mm, 0.5 mm pitch staggered rows, 0.25 mm round pads, 4.85 mm exposed pad (nRF52840 PS v1.8 Fig. 207/210)',
        body=dict(D=7.0, E=7.0, A=0.85), pads=pads,
        ep=dict(name='EP', x=0, y=0, dx=4.85, dy=4.85),
        paste_windows=[dict(x=sx * 1.1, y=sy * 1.1, dx=1.9, dy=1.9) for sx in (-1, 1) for sy in (1, -1)],
        mask_expansion=0.05,
        silk_offset=0.11, silk_corner_len=0.6, silk_width=0.12, pin1_dot=dict(x=-3.95, y=3.95, r=0.15),
        assembly_chamfer=0.5, assembly_layer='eMechanical13', courtyard_layer='eMechanical15', courtyard_expansion=0.30),
    symbol=dict(
        name='NRF52840-QIAA-F-R7', designator='U?',
        description='nRF52840 BLE 5 / 802.15.4 SoC, Cortex-M4F 64 MHz, 1 MB flash, 256 kB RAM, aQFN73 7x7 mm',
        pin_pitch_mil=100, pin_length_mil=200, body_width_mil=2000, pins=pins,
        parameters={'Manufacturer': 'Nordic Semiconductor', 'Manufacturer Part Number': 'NRF52840-QIAA-F-R7',
                    'Package': 'aQFN73 7 x 7 mm', 'Datasheet': 'nRF52840 Product Specification v1.8',
                    'Supplier 1': 'Digi-Key', 'Supplier Part Number 1': 'NRF52840-QIAA-F-R7 (Cut Tape)'}))
json.dump(spec, open(sys.argv[2], 'w'), indent=1)
print('balls', len(balls), 'pads', len(pads), 'pins', len(pins))
for p in pins: print(p['num'], p['name'], p['type'], p['side'], pos(p['num']) if p['num'] != 'EP' else 'EP')
