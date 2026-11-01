# Extract closed Bezier subpaths (circles) from one PDF page, in page points (y down).
import sys
from pypdf import PdfReader
from pypdf.generic import ContentStream

def mat_mul(a, b):
    return [a[0]*b[0]+a[1]*b[2], a[0]*b[1]+a[1]*b[3], a[2]*b[0]+a[3]*b[2], a[2]*b[1]+a[3]*b[3],
            a[4]*b[0]+a[5]*b[2]+b[4], a[4]*b[1]+a[5]*b[3]+b[5]]

def main(path, pageno):
    r = PdfReader(path)
    page = r.pages[pageno - 1]
    H = float(page.mediabox.height)
    cs = ContentStream(page.get_contents(), r)
    ctm = [1, 0, 0, 1, 0, 0]; stack = []
    sub = []; curves = 0; out = []
    def tp(x, y):
        return (ctm[0]*x + ctm[2]*y + ctm[4], ctm[1]*x + ctm[3]*y + ctm[5])
    def close():
        nonlocal sub, curves
        if len(sub) >= 8:
            xs = [p[0] for p in sub]; ys = [p[1] for p in sub]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            out.append(((max(xs) + min(xs)) / 2, H - (max(ys) + min(ys)) / 2, w, h, curves))
        sub = []; curves = 0
    for ops, op in cs.operations:
        op = op.decode() if isinstance(op, bytes) else op
        if op == 'q': stack.append(ctm[:])
        elif op == 'Q': ctm = stack.pop()
        elif op == 'cm': ctm = mat_mul([float(v) for v in ops], ctm)
        elif op == 'm': close(); sub = [tp(float(ops[0]), float(ops[1]))]
        elif op == 'l': sub.append(tp(float(ops[0]), float(ops[1])))
        elif op == 'c':
            v = [float(x) for x in ops]
            sub += [tp(v[0], v[1]), tp(v[2], v[3]), tp(v[4], v[5])]; curves += 1
        elif op in ('h', 'S', 's', 'f', 'F', 'f*', 'B', 'b', 'n'): close()
    for c in out:
        print('%.3f %.3f %.3f %.3f %d' % c)

main(sys.argv[1], int(sys.argv[2]))
