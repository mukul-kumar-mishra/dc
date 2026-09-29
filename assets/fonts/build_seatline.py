"""Destro Seatline — invented typeface system for DestroCorp v1.
Seat (Kirvyn: 16 seats) + Line (AuditScan: file:line).

Why this replaces Meridian:
  - UPRIGHT 0deg (no shear). Code, prices, chat need upright.
  - TRUE ELLIPSE bowls (exp 2.0), open apertures — legible at 13-15px.
  - 16DEG FORWARD CUT (v2): free bar terminals shear forward 16deg
    (tan16=0.2867, top edge leads); joining ends stay square and buried.
    Crossed 7, slashed zero. Arches recentered on stems, flush outer/inner.
  - DOUBLE-STOREY a/g for paragraph reading (Buildopsy).
  - SLASHED ZERO + distinct I/1/l, S/5, B/8 for file paths + UPI IDs.
  - TABULAR figures in Sans; fixed 600 advance in Mono.
  - Sans Regular/Bold + Mono Regular. No fake variable range.
All outlines generated in code. No tracing, no third-party font data.
"""
import math, sys, os
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

UPM = 1000; ASC = 750; DESC = -250; CAP = 700; XH = 500
LSB_SANS = 40
ADV_MONO = 600
SQN = 2.0  # true ellipse -> open, humanist, survives small sizes

class C:
    def __init__(self, pts, closed=True):
        self.pts = list(pts); self.closed = closed
    def reversed(self):
        return C(list(reversed(self.pts)), self.closed)

def area(pts):
    s = 0; n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return s / 2

class Ctx:
    """Per-weight drawing context (avoids globals)."""
    def __init__(self, S, B, LSB):
        self.S = S; self.B = B; self.BW = B + 12; self.LSB = LSB
    def emit(self, pen, cont, hole=False):
        poly = cont.pts
        a = area(poly)
        if hole and a < 0: cont = cont.reversed()
        if not hole and a > 0: cont = cont.reversed()
        pts = [(x + self.LSB, y) for x, y in cont.pts]  # upright, no shear
        pen.moveTo(pts[0])
        for p in pts[1:]: pen.lineTo(p)
        pen.closePath()
    def sqpt(self, cx, cy, rx, ry, t):
        e = 2.0 / SQN
        c = math.cos(t); s = math.sin(t)
        x = rx * math.copysign(abs(c) ** e, c)
        y = ry * math.copysign(abs(s) ** e, s)
        return (cx + x, cy + y)
    def sqarc(self, cx, cy, rx, ry, a0, a1, segs=None):
        a0 = math.radians(a0); a1 = math.radians(a1)
        if segs is None:
            segs = max(8, int(abs(a1 - a0) / (math.pi / 28) + 0.999))
        return [self.sqpt(cx, cy, rx, ry, a0 + (a1 - a0) * i / segs) for i in range(segs + 1)]
    def band(self, cx, cy, rxo, ryo, rxi, ryi, a0, a1):
        outer = self.sqarc(cx, cy, rxo, ryo, a0, a1)
        inner = self.sqarc(cx, cy, rxi, ryi, a0, a1)
        return C(outer + list(reversed(inner)))
    def ring(self, cx, cy, rxo, ryo, rxi, ryi):
        o = self.sqarc(cx, cy, rxo, ryo, 0, 360, 72)[:-1]
        i = self.sqarc(cx, cy, rxi, ryi, 0, 360, 72)[:-1]
        return C(o), C(i)
    def oring(self, pen, cx, cy, rxo, ryo, rxi, ryi):
        o, i = self.ring(cx, cy, rxo, ryo, rxi, ryi)
        self.emit(pen, o); self.emit(pen, i, hole=True)
    def stroke(self, pts, w, cap0='flat', cap1='flat'):
        n = len(pts); left = []; right = []
        for i in range(n):
            if i == 0: dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
            elif i == n - 1: dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
            else: dx, dy = pts[i+1][0] - pts[i-1][0], pts[i+1][1] - pts[i-1][1]
            L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L * w / 2, dx / L * w / 2
            left.append((pts[i][0] + nx, pts[i][1] + ny))
            right.append((pts[i][0] - nx, pts[i][1] - ny))
        body = []
        if cap0 == 'round':
            d = math.atan2(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0])
            a = d - math.pi / 2
            for t in range(7):
                ang = a - math.pi * t / 6
                body.append((pts[0][0] + w/2*math.cos(ang), pts[0][1] + w/2*math.sin(ang)))
            body += left[1:]
        else:
            body = left[:]
        if cap1 == 'round':
            d = math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])
            a = d + math.pi / 2
            for t in range(7):
                ang = a - math.pi * t / 6
                body.append((pts[-1][0] + w/2*math.cos(ang), pts[-1][1] + w/2*math.sin(ang)))
            body += right[-2:0:-1]
        else:
            body += right[::-1]
        return C(body)
    def sp(self, pen, pts, w, c0='flat', c1='flat'):
        self.emit(pen, self.stroke(pts, w, c0, c1))
    def dot(self, pen, cx, cy, r, n=24):
        pts = [(cx + r*math.cos(2*math.pi*i/n), cy + r*math.sin(2*math.pi*i/n)) for i in range(n)]
        self.emit(pen, C(pts))
    def cub(self, p0, c1, c2, p1, n=24):
        out = []
        for i in range(n + 1):
            t = i / n; u = 1 - t
            out.append((u*u*u*p0[0]+3*u*u*t*c1[0]+3*u*t*t*c2[0]+t*t*t*p1[0],
                        u*u*u*p0[1]+3*u*u*t*c1[1]+3*u*t*t*c2[1]+t*t*t*p1[1]))
        return out
    def quad(self, p0, c, p1, n=16):
        out = []
        for i in range(n + 1):
            t = i / n; u = 1 - t
            out.append((u*u*p0[0]+2*u*t*c[0]+t*t*p1[0], u*u*p0[1]+2*u*t*c[1]+t*t*p1[1]))
        return out
    def stem(self, pen, x, y0, y1, w=None):
        # exact quad edge-to-edge (no inset) so T/H/E joints overlap solidly.
        # Callers pass edge coordinates; joining bars must start at stem edge.
        w = self.S if w is None else w
        self.emit(pen, C([(x - w/2, y0), (x - w/2, y1), (x + w/2, y1), (x + w/2, y0)]))
    def bar(self, pen, x0, x1, y, w=None, slant='none'):
        # v2 signature: free terminals shear forward 16deg (top edge leads).
        # tan16 = 0.2867. Joining ends stay square and buried in stems;
        # free ends get the cut. 'right' = free right end, 'both' = free bar.
        w = self.B if w is None else w
        dx = int(round(0.2867 * w)) if slant != 'none' else 0
        if slant == 'right':
            pts = [(x0, y - w/2), (x0, y + w/2), (x1 + dx, y + w/2), (x1, y - w/2)]
        elif slant == 'both':
            pts = [(x0, y - w/2), (x0 + dx, y + w/2), (x1 + dx, y + w/2), (x1, y - w/2)]
        else:
            pts = [(x0, y - w/2), (x0, y + w/2), (x1, y + w/2), (x1, y - w/2)]
        self.emit(pen, C(pts))


def define_glyphs(ctx):
    S = ctx.S
    DRAW = {}; WIDTH = {}
    def glyph(name, width, fn):
        WIDTH[name] = width; DRAW[name] = fn
    def stem(pen, x, y0, y1, w=None): ctx.stem(pen, x, y0, y1, w)
    def bar(pen, x0, x1, y, w=None, slant='none'): ctx.bar(pen, x0, x1, y, w, slant)

    # ---- UPPERCASE (flat-cut precision, open apertures) ----
    def g_A(p):
        ctx.sp(p, [(70,0),(330,690)], S); ctx.sp(p, [(590,0),(330,690)], S)
        bar(p, 170, 490, 240)
    glyph('A', 660, g_A)
    def g_B(p):
        stem(p, 58, 0, 690)
        ctx.emit(p, ctx.band(58, 516, 390, 172, 278, 60, 90, -90))
        ctx.emit(p, ctx.band(58, 174, 402, 172, 290, 60, 90, -90))
    glyph('B', 610, g_B)
    def g_C(p): ctx.emit(p, ctx.band(320, 345, 295, 350, 185, 246, 42, 318))
    glyph('C', 630, g_C)
    def g_D(p):
        stem(p, 58, 0, 690)
        ctx.emit(p, ctx.band(58, 345, 410, 350, 298, 246, 90, -90))
    glyph('D', 670, g_D)
    def g_E(p):
        stem(p, 58, 0, 690); bar(p, 58 - S/2, 460, 640, slant='right'); bar(p, 58 - S/2, 390, 345, slant='right'); bar(p, 58 - S/2, 460, 50, slant='right')
    glyph('E', 530, g_E)
    def g_F(p):
        stem(p, 58, 0, 690); bar(p, 58 - S/2, 440, 640, slant='right'); bar(p, 58 - S/2, 370, 345, slant='right')
    glyph('F', 510, g_F)
    def g_G(p):
        ctx.emit(p, ctx.band(320, 345, 295, 350, 185, 246, 42, 318))
        ctx.sp(p, [(555,120),(555,300)], S)
        bar(p, 330, 555 + S/2, 250)
    glyph('G', 650, g_G)
    def g_H(p):
        stem(p, 58, 0, 690); stem(p, 555, 0, 690); bar(p, 58 - S/2, 555 + S/2, 345)
    glyph('H', 650, g_H)
    def g_I(p):
        # slab I: distinct from l and 1
        stem(p, 110, 0, 690)
        bar(p, 20, 200, 640); bar(p, 20, 200, 50)
    glyph('I', 240, g_I)
    def g_J(p):
        stem(p, 460, 150, 690)
        ctx.emit(p, ctx.band(285, 180, 228, 185, 228 - S, 185 - S, 180, 360))
    glyph('J', 530, g_J)
    def g_K(p):
        stem(p, 58, 0, 690)
        ctx.sp(p, [(60,330),(515,660)], S)
        ctx.sp(p, [(70,320),(535,30)], S)
    glyph('K', 630, g_K)
    def g_L(p): stem(p, 58, 0, 690); bar(p, 58 - S/2, 440, 50, slant='right')
    glyph('L', 510, g_L)
    def g_M(p):
        stem(p, 58, 0, 690); stem(p, 635, 0, 690)
        ctx.sp(p, [(80,640),(350,130)], 104); ctx.sp(p, [(615,640),(350,130)], 104)
    glyph('M', 750, g_M)
    def g_N(p):
        stem(p, 58, 0, 690); stem(p, 555, 0, 690)
        ctx.sp(p, [(80,620),(575,70)], 104)
    glyph('N', 650, g_N)
    def g_O(p): ctx.oring(p, 325, 345, 300, 350, 190, 246)
    glyph('O', 670, g_O)
    def g_P(p):
        stem(p, 58, 0, 690)
        ctx.emit(p, ctx.band(58, 516, 390, 172, 278, 60, 90, -90))
    glyph('P', 590, g_P)
    def g_Q(p):
        ctx.oring(p, 325, 345, 300, 350, 190, 246)
        ctx.sp(p, [(395,120),(595,-40)], 96)
    glyph('Q', 670, g_Q)
    def g_R(p):
        stem(p, 58, 0, 690)
        ctx.emit(p, ctx.band(58, 516, 390, 172, 278, 60, 90, -90))
        ctx.sp(p, [(230,330),(535,30)], S, c0='round')
    glyph('R', 610, g_R)
    def g_S(p):
        pts = ctx.cub((485,576),(425,676),(255,700),(168,630),20)+ctx.cub((168,630),(88,564),(104,442),(212,394),20)[1:]+ctx.cub((212,394),(298,356),(330,342),(390,302),14)[1:]+ctx.cub((390,302),(488,238),(508,118),(406,54),20)[1:]+ctx.cub((406,54),(310,-2),(150,14),(86,104),20)[1:]
        ctx.emit(p, ctx.stroke(pts, 104))
    glyph('S', 590, g_S)
    def g_T(p):
        bar(p, 60, 530, 640, slant='both'); stem(p, 295, 0, 640)
    glyph('T', 590, g_T)
    def g_U(p):
        stem(p, 58, 140, 690); stem(p, 555, 140, 690)
        ctx.emit(p, ctx.band(306, 180, 248.5 + S/2, 185, 248.5 - S/2, 185 - S, 180, 360))
    glyph('U', 650, g_U)
    def g_V(p):
        ctx.sp(p, [(70,660),(337,-6)], S); ctx.sp(p, [(566,660),(299,-6)], S)
    glyph('V', 630, g_V)
    def g_W(p):
        ctx.sp(p, [(60,660),(238,40)], 102, c1='round'); ctx.sp(p, [(238,40),(426,460)], 102, c0='round')
        ctx.sp(p, [(426,460),(614,40)], 102, c1='round'); ctx.sp(p, [(614,40),(792,660)], 102, c0='round')
    glyph('W', 850, g_W)
    def g_X(p):
        ctx.sp(p, [(60,660),(555,30)], S); ctx.sp(p, [(60,30),(555,660)], S)
    glyph('X', 610, g_X)
    def g_Y(p):
        ctx.sp(p, [(60,660),(308,320)], S); ctx.sp(p, [(556,660),(308,320)], S)
        stem(p, 308, 0, 330)
    glyph('Y', 610, g_Y)
    def g_Z(p):
        bar(p, 60, 490, 640, slant='both'); ctx.sp(p, [(455,600),(100,90)], 102); bar(p, 60, 490, 50, slant='both')
    glyph('Z', 550, g_Z)

    # ---- LOWERCASE: double-storey a/g for reading ----
    def g_a(p):
        # double-storey: upper + lower counters + right stem
        ctx.oring(p, 250, 380, 175, 128, 85, 58)
        ctx.oring(p, 250, 170, 205, 172, 105, 87)
        stem(p, 415, 0, 500)
    glyph('a', 550, g_a)
    def g_b(p):
        stem(p, 58, 0, 740)
        ctx.oring(p, 315, 255, 235, 265, 125, 165)
    glyph('b', 590, g_b)
    def g_c(p): ctx.emit(p, ctx.band(265, 255, 235, 265, 125, 165, 42, 318))
    glyph('c', 530, g_c)
    def g_d(p):
        ctx.oring(p, 245, 255, 235, 265, 125, 165)
        stem(p, 425, 0, 740)
    glyph('d', 590, g_d)
    def g_e(p):
        ctx.emit(p, ctx.band(265, 255, 239, 265, 129, 165, 10, 308))
        bar(p, 60, 440, 265, 88)
    glyph('e', 550, g_e)
    def g_f(p):
        stem(p, 235, 0, 600)
        ctx.emit(p, ctx.band(235, 600, 165, 138, 65, 38, 90, 5))
        bar(p, 60, 350, 280, 88, slant='both')
    glyph('f', 430, g_f)
    def g_g(p):
        # double-storey g: upper bowl, lower bowl, link
        ctx.oring(p, 250, 300, 235, 220, 125, 125)
        ctx.oring(p, 250, -60, 235, 150, 125, 60)
        stem(p, 445, -60, 480)
        bar(p, 250, 445, 480, 88)
    glyph('g', 590, g_g)
    def g_h(p):
        stem(p, 58, 0, 740)
        ctx.emit(p, ctx.band(254, 265, 196 + S/2, 245, 196 - S/2, 245 - S, 180, 0))
        stem(p, 450, 0, 295)
    glyph('h', 590, g_h)
    def g_i(p):
        stem(p, 58, 0, 500); ctx.dot(p, 58, 625, 58)
    glyph('i', 160, g_i)
    def g_j(p):
        stem(p, 175, -160, 500); ctx.dot(p, 175, 625, 58)
    glyph('j', 270, g_j)
    def g_k(p):
        stem(p, 58, 0, 740)
        ctx.sp(p, [(60,235),(425,475)], 102)
        ctx.sp(p, [(70,225),(445,30)], 102)
    glyph('k', 550, g_k)
    def g_l(p):
        # l with tail hook -> distinct from I and 1
        ctx.sp(p, [(58,740),(58,120)], S)
        ctx.emit(p, ctx.band(150, 105, 110, 110, 45, 40, 180, 320))
    glyph('l', 220, g_l)
    def g_m(p):
        stem(p, 58, 0, 500)
        ctx.emit(p, ctx.band(244, 265, 186 + S/2, 245, 186 - S/2, 245 - S, 180, 0))
        stem(p, 430, 0, 295)
        ctx.emit(p, ctx.band(595, 265, 165 + S/2, 245, 165 - S/2, 245 - S, 180, 0))
        stem(p, 760, 0, 295)
    glyph('m', 870, g_m)
    def g_n(p):
        stem(p, 58, 0, 500)
        ctx.emit(p, ctx.band(254, 265, 196 + S/2, 245, 196 - S/2, 245 - S, 180, 0))
        stem(p, 450, 0, 295)
    glyph('n', 590, g_n)
    def g_o(p): ctx.oring(p, 275, 255, 258, 265, 148, 165)
    glyph('o', 570, g_o)
    def g_p(p):
        stem(p, 58, -220, 500)
        ctx.oring(p, 315, 255, 235, 265, 125, 165)
    glyph('p', 590, g_p)
    def g_q(p):
        ctx.oring(p, 245, 255, 235, 265, 125, 165)
        stem(p, 425, -220, 500)
    glyph('q', 590, g_q)
    def g_r(p):
        stem(p, 58, 0, 500)
        ctx.emit(p, ctx.band(245, 265, 215, 245, 105, 145, 180, 55))
    glyph('r', 430, g_r)
    def g_s(p):
        pts = ctx.cub((425,415),(375,495),(238,512),(160,455),18)+ctx.cub((160,455),(92,405),(106,318),(190,284),18)[1:]+ctx.cub((190,284),(258,256),(283,246),(328,216),12)[1:]+ctx.cub((328,216),(400,166),(415,80),(338,32),18)[1:]+ctx.cub((338,32),(263,-10),(140,4),(90,72),18)[1:]
        ctx.emit(p, ctx.stroke(pts, 96))
    glyph('s', 510, g_s)
    def g_t(p):
        pts = [(195,590),(195,160)] + ctx.quad((195,160),(195,60),(315,60),12)[1:]
        ctx.emit(p, ctx.stroke(pts, 102))
        bar(p, 60, 320, 295, 88, slant='both')
    glyph('t', 410, g_t)
    def g_u(p):
        stem(p, 58, 160, 500)
        ctx.emit(p, ctx.band(264, 165, 206 + S/2, 175, 206 - S/2, 175 - S, 180, 360))
        stem(p, 470, 0, 500)
    glyph('u', 590, g_u)
    def g_v(p):
        ctx.sp(p, [(60,480),(286,4)], 102); ctx.sp(p, [(476,480),(250,4)], 102)
    glyph('v', 530, g_v)
    def g_w(p):
        ctx.sp(p, [(50,480),(198,40)], 96); ctx.sp(p, [(198,40),(376,345)], 96)
        ctx.sp(p, [(376,345),(554,40)], 96); ctx.sp(p, [(554,40),(702,480)], 96)
    glyph('w', 750, g_w)
    def g_x(p):
        ctx.sp(p, [(50,480),(465,30)], 102); ctx.sp(p, [(50,30),(465,480)], 102)
    glyph('x', 510, g_x)
    def g_y(p):
        ctx.sp(p, [(60,480),(268,40)], 102); ctx.sp(p, [(476,480),(188,-200)], 102)
    glyph('y', 530, g_y)
    def g_z(p):
        bar(p, 60, 430, 460, slant='both'); ctx.sp(p, [(395,420),(100,90)], 96); bar(p, 60, 430, 50, slant='both')
    glyph('z', 490, g_z)

    # ---- DIGITS: tabular, slashed zero, open 6/9 ----
    def g_0(p):
        ctx.oring(p, 305, 340, 285, 350, 175, 250)
        ctx.sp(p, [(430,90),(180,590)], 72)  # slash -> survives small sizes
    glyph('zero', 620, g_0)
    def g_1(p):
        # flag + stem + foot -> distinct from I and l; tabular 620 like other digits
        ctx.sp(p, [(335,640),(190,505)], 88)
        stem(p, 335, 0, 690)
        bar(p, 210, 460, 50, 88, slant='both')
    glyph('one', 620, g_1)
    def g_2(p):
        ctx.emit(p, ctx.band(285, 495, 235, 188, 125, 88, 170, 10))
        ctx.sp(p, [(490,425),(90,90)], 102)
        bar(p, 60, 490, 50, slant='both')
    glyph('two', 620, g_2)
    def g_3(p):
        ctx.emit(p, ctx.band(285, 505, 235, 172, 125, 72, 150, -60))
        ctx.emit(p, ctx.band(285, 178, 245, 182, 135, 82, 60, -170))
    glyph('three', 620, g_3)
    def g_4(p):
        ctx.sp(p, [(325,655),(70,235)], 102)
        bar(p, 40, 550, 235, slant='both')
        stem(p, 425, 0, 690)
    glyph('four', 620, g_4)
    def g_5(p):
        bar(p, 80, 460, 635, slant='both')
        stem(p, 80, 355, 685)
        bar(p, 80 - S/2, 325, 355, slant='right')
        ctx.emit(p, ctx.band(295, 198, 235, 192, 125, 92, 80, -160))
    glyph('five', 620, g_5)
    def g_6(p):
        ctx.sp(p, ctx.cub((445,645),(295,625),(150,475),(130,295),20), 102)
        ctx.oring(p, 295, 188, 255, 202, 145, 102)
    glyph('six', 620, g_6)
    def g_7(p):
        bar(p, 60, 510, 635, slant='both'); ctx.sp(p, [(470,595),(178,40)], 102); bar(p, 344, 446, 452, slant='both')
    glyph('seven', 620, g_7)
    def g_8(p):
        ctx.oring(p, 295, 505, 225, 172, 115, 72)
        ctx.oring(p, 295, 178, 250, 192, 140, 92)
    glyph('eight', 620, g_8)
    def g_9(p):
        ctx.oring(p, 295, 495, 255, 202, 145, 102)
        stem(p, 445, 0, 495)
    glyph('nine', 620, g_9)

    # ---- PUNCTUATION / SYMBOLS ----
    def g_space(p): pass
    glyph('space', 340, g_space)
    def g_period(p): ctx.dot(p, 58, 58, 56)
    glyph('period', 200, g_period)
    def g_comma(p):
        ctx.dot(p, 58, 58, 56); ctx.sp(p, [(58,58),(10,-90)], 88)
    glyph('comma', 200, g_comma)
    def g_colon(p): ctx.dot(p, 58, 110, 54); ctx.dot(p, 58, 385, 54)
    glyph('colon', 200, g_colon)
    def g_semi(p):
        ctx.dot(p, 95, 385, 54); ctx.dot(p, 95, 110, 54); ctx.sp(p, [(95,110),(47,-40)], 88)
    glyph('semicolon', 240, g_semi)
    def g_excl(p): stem(p, 58, 180, 690, 96); ctx.dot(p, 58, 60, 60)
    glyph('exclam', 200, g_excl)
    def g_ques(p):
        ctx.emit(p, ctx.band(275, 465, 225, 198, 115, 98, -50, 210))
        ctx.sp(p, [(275,295),(258,150)], 96)
        ctx.dot(p, 252, 45, 60)
    glyph('question', 560, g_ques)
    def g_hyphen(p): bar(p, 60, 315, 285, slant='both')
    glyph('hyphen', 380, g_hyphen)
    def g_minus(p): bar(p, 60, 530, 340, slant='both')
    glyph('minus', 600, g_minus)
    def g_endash(p): bar(p, 40, 550, 285, slant='both')
    glyph('endash', 600, g_endash)
    def g_emdash(p): bar(p, 40, 850, 285, slant='both')
    glyph('emdash', 900, g_emdash)
    def g_slash(p): ctx.sp(p, [(395,-40),(90,725)], 96)
    glyph('slash', 480, g_slash)
    def g_bslash(p): ctx.sp(p, [(70,-40),(415,725)], 96)
    glyph('backslash', 480, g_bslash)
    def g_lpar(p): ctx.sp(p, ctx.cub((295,705),(60,465),(60,225),(295,-10),24), 100)
    glyph('parenleft', 360, g_lpar)
    def g_rpar(p): ctx.sp(p, ctx.cub((60,705),(295,465),(295,225),(60,-10),24), 100)
    glyph('parenright', 360, g_rpar)
    def g_qdbl(p):
        ctx.sp(p, [(60,655),(100,455)], 84); ctx.sp(p, [(205,655),(245,455)], 84)
    glyph('quotedbl', 340, g_qdbl)
    def g_apos(p): ctx.sp(p, [(60,655),(100,455)], 84)
    glyph('quotesingle', 190, g_apos)
    def g_amp(p):
        ctx.oring(p, 235, 168, 185, 172, 85, 72)
        ctx.sp(p, [(60,635),(465,0)], 100)
        bar(p, 60, 390, 515)
    glyph('ampersand', 610, g_amp)
    def g_at(p):
        ctx.oring(p, 295, 248, 275, 282, 165, 170)
        ctx.sp(p, [(385,128),(385,425)], 96)
        ctx.oring(p, 325, 295, 98, 118, 30, 50)
    glyph('at', 690, g_at)
    def g_hash(p):
        ctx.sp(p, [(148,0),(148,690)], 92); ctx.sp(p, [(384,0),(384,690)], 92)
        bar(p, 40, 512, 238, 88); bar(p, 40, 512, 435, 88)
    glyph('numbersign', 550, g_hash)
    def g_dollar(p):
        g_S(p); ctx.sp(p, [(295,-60),(295,745)], 92)
    glyph('dollar', 590, g_dollar)
    def g_pct(p):
        ctx.oring(p, 138, 535, 132, 132, 56, 56)
        ctx.oring(p, 432, 148, 132, 132, 56, 56)
        ctx.sp(p, [(472,685),(100,0)], 84)
    glyph('percent', 650, g_pct)
    def g_star(p):
        ctx.sp(p, [(275,60),(275,655)], 88)
        ctx.sp(p, [(90,190),(462,525)], 88); ctx.sp(p, [(90,525),(462,190)], 88)
    glyph('asterisk', 550, g_star)
    def g_plus(p): ctx.sp(p, [(295,80),(295,615)], 92); bar(p, 60, 530, 348, 92, slant='both')
    glyph('plus', 590, g_plus)
    def g_eq(p): bar(p, 60, 530, 218, 92, slant='both'); bar(p, 60, 530, 425, 92, slant='both')
    glyph('equal', 590, g_eq)
    def g_lt(p): ctx.sp(p, [(445,635),(90,335)], 100); ctx.sp(p, [(90,335),(445,40)], 100)
    glyph('less', 530, g_lt)
    def g_gt(p): ctx.sp(p, [(90,635),(445,335)], 100); ctx.sp(p, [(445,335),(90,40)], 100)
    glyph('greater', 530, g_gt)
    def g_lb(p):
        bar(p, 60, 315, 50, 92); ctx.sp(p, [(110,50),(110,645)], 92); bar(p, 60, 315, 645, 92)
    glyph('bracketleft', 350, g_lb)
    def g_rb(p):
        bar(p, 40, 295, 50, 92); ctx.sp(p, [(245,50),(245,645)], 92); bar(p, 40, 295, 645, 92)
    glyph('bracketright', 350, g_rb)
    def g_lbr(p):
        bar(p, 90, 335, 595, 88); ctx.sp(p, [(138,595),(138,415)], 88); ctx.sp(p, [(138,275),(138,100)], 88); bar(p, 90, 335, 100, 88); ctx.sp(p, [(138,415),(138,275)], 64)
    glyph('braceleft', 390, g_lbr)
    def g_rbr(p):
        bar(p, 60, 305, 595, 88); ctx.sp(p, [(256,595),(256,415)], 88); ctx.sp(p, [(256,275),(256,100)], 88); bar(p, 60, 305, 100, 88); ctx.sp(p, [(256,415),(256,275)], 64)
    glyph('braceright', 390, g_rbr)
    def g_us(p): bar(p, 40, 512, -40, 88, slant='both')
    glyph('underscore', 550, g_us)
    def g_caret(p):
        ctx.sp(p, [(60,355),(218,555)], 88); ctx.sp(p, [(218,555),(376,355)], 88)
    glyph('asciicircum', 430, g_caret)
    def g_grave(p): ctx.sp(p, [(138,655),(60,495)], 84)
    glyph('grave', 200, g_grave)
    def g_bar(p): ctx.sp(p, [(118,-220),(118,735)], 92)
    glyph('bar', 270, g_bar)
    def g_tilde(p):
        ctx.sp(p, ctx.cub((50,285),(150,415),(250,175),(350,305),16) + [(350,305)], 84)
    glyph('asciitilde', 410, g_tilde)
    def g_middot(p): ctx.dot(p, 58, 255, 54)
    glyph('periodcentered', 200, g_middot)
    def g_copy(p):
        ctx.oring(p, 315, 258, 285, 292, 175, 180)
        ctx.emit(p, ctx.band(315, 258, 122, 122, 54, 54, 45, 315))
    glyph('copyright', 690, g_copy)
    def g_bull(p): ctx.dot(p, 148, 255, 96)
    glyph('bullet', 330, g_bull)
    def g_hellip(p): ctx.dot(p, 55, 55, 53); ctx.dot(p, 250, 55, 53); ctx.dot(p, 445, 55, 53)
    glyph('ellipsis', 550, g_hellip)
    def g_qll(p):
        ctx.sp(p, [(60,555),(100,355)], 84); ctx.sp(p, [(205,555),(245,355)], 84)
    glyph('quotedblleft', 340, g_qll)
    def g_qr(p): ctx.sp(p, [(60,655),(100,455)], 84)
    glyph('quoteright', 190, g_qr)
    def g_ql(p): ctx.sp(p, [(60,655),(100,455)], 84)
    glyph('quoteleft', 190, g_ql)
    def g_qrr(p):
        ctx.sp(p, [(60,555),(100,355)], 84); ctx.sp(p, [(205,555),(245,355)], 84)
    glyph('quotedblright', 340, g_qrr)
    def g_arrow(p):
        bar(p, 40, 550, 285, 92)
        ctx.sp(p, [(395,490),(610,285)], 104); ctx.sp(p, [(610,285),(395,80)], 104)
    glyph('arrowright', 690, g_arrow)
    def g_rupee(p):
        # native ₹: stem + two bars + diagonal leg, flat-cut
        stem(p, 60, 0, 690)
        bar(p, 60 - S/2, 490, 635, slant='right'); bar(p, 60 - S/2, 490, 420, slant='right')
        ctx.emit(p, ctx.band(255, 420, 245, 215, 145, 115, 200, -60))
        ctx.sp(p, [(200,220),(480,0)], 104)
    glyph('rupee', 590, g_rupee)
    return DRAW, WIDTH


CMAP = {
 32:'space',33:'exclam',34:'quotedbl',35:'numbersign',36:'dollar',37:'percent',38:'ampersand',
 39:'quotesingle',40:'parenleft',41:'parenright',42:'asterisk',43:'plus',44:'comma',45:'hyphen',
 46:'period',47:'slash',48:'zero',49:'one',50:'two',51:'three',52:'four',53:'five',54:'six',
 55:'seven',56:'eight',57:'nine',58:'colon',59:'semicolon',60:'less',61:'equal',62:'greater',
 63:'question',64:'at',65:'A',66:'B',67:'C',68:'D',69:'E',70:'F',71:'G',72:'H',73:'I',74:'J',
 75:'K',76:'L',77:'M',78:'N',79:'O',80:'P',81:'Q',82:'R',83:'S',84:'T',85:'U',86:'V',87:'W',
 88:'X',89:'Y',90:'Z',91:'bracketleft',92:'backslash',93:'bracketright',94:'asciicircum',
 95:'underscore',96:'grave',97:'a',98:'b',99:'c',100:'d',101:'e',102:'f',103:'g',104:'h',
 105:'i',106:'j',107:'k',108:'l',109:'m',110:'n',111:'o',112:'p',113:'q',114:'r',115:'s',
 116:'t',117:'u',118:'v',119:'w',120:'x',121:'y',122:'z',123:'braceleft',124:'bar',
 125:'braceright',126:'asciitilde',169:'copyright',183:'periodcentered',8211:'endash',
 8212:'emdash',8220:'quotedblleft',8221:'quotedblright',8226:'bullet',8230:'ellipsis',
 8594:'arrowright',8377:'rupee',8722:'minus',8216:'quoteleft',8217:'quoteright',
}

KERN = [
 ('C','A',-40),('C','V',-42),('C','W',-38),('C','T',-52),('C','Y',-38),
 ('G','A',-24),('G','T',-34),('G','W',-22),
 ('L','T',-72),('L','V',-60),('L','W',-52),('L','Y',-60),('L','A',-32),
 ('A','T',-48),('H','T',-44),('N','T',-44),('U','T',-44),('O','T',-44),
 ('D','T',-44),('E','T',-44),('R','T',-38),('S','T',-38),('P','T',-38),
 ('B','T',-38),('M','T',-38),('F','T',-44),('J','T',-44),
 ('Q','T',-44),('V','T',-34),('W','T',-34),('Y','T',-34),('Z','T',-38),
 ('T','A',-30),('T','O',-16),('T','U',-16),('T','V',-32),('T','W',-30),('T','Y',-30),
 ('F','A',-30),('P','A',-22),('Y','A',-24),('V','A',-30),('W','A',-24),
 ('o','t',-28),('e','t',-22),('a','t',-22),('r','t',-22),('n','t',-22),('u','t',-22),
 ('T','o',-16),('T','a',-20),('L','e',-24),('L','o',-14),('C','a',-24),
]

WEIGHTS = {
 'Regular': dict(S=96, B=88),
 'Bold': dict(S=140, B=124),
}

def build_one(out_ttf, family, style, ps, weight_key, mono=False):
    w = WEIGHTS[weight_key]
    lsb = LSB_SANS
    ctx = Ctx(S=w['S'], B=w['B'], LSB=0 if mono else lsb)
    DRAW, WIDTH = define_glyphs(ctx)
    seen = set(['.notdef', 'space']); rest = []
    for g in list(DRAW.keys()) + list(CMAP.values()):
        if g not in seen:
            seen.add(g); rest.append(g)
    rest = sorted(rest, key=lambda x: (len(x), x))
    order = ['.notdef', 'space'] + rest
    for g in list(CMAP.values()):
        if g not in DRAW and g != 'space':
            WIDTH[g] = 400
            gg = g
            DRAW[gg] = lambda pen, _g=gg: ctx.dot(pen, 100, 100, 80)
    for g in order:
        if g not in WIDTH: WIDTH[g] = 600
    fb = FontBuilder(UPM, isTTF=True)
    glyphs = {}; metrics = {}
    for gname in order:
        pen = TTGlyphPen(None)
        if gname in DRAW:
            try: DRAW[gname](pen)
            except Exception as e: print('ERR', gname, e)
        elif gname == '.notdef':
            ctx2 = ctx
            ctx2.emit(pen, C([(70,0),(70,700),(530,700),(530,0)]))
            ctx2.emit(pen, C([(200,130),(200,570),(400,570),(400,130)]), hole=True)
        glyphs[gname] = pen.glyph()
        if mono:
            adv = ADV_MONO
            lsb_use = 0  # fixed below after bounds
        else:
            adv = WIDTH.get(gname, 600) + lsb * 2 if gname != 'space' else 340
            if gname == '.notdef': adv = 700
            lsb_use = lsb if gname != 'space' else 0
        metrics[gname] = (adv, lsb_use)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({u: g for u, g in CMAP.items()})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASC, descent=DESC)
    full = f'{family} {style}'
    fb.setupNameTable({'familyName': family, 'styleName': style,
        'uniqueFontIdentifier': f'{ps}-1.0', 'fullName': full,
        'psName': ps, 'version': 'Version 1.0',
        'designer': 'DestroCorp Studio',
        'description': 'Seatline: upright grotesk, ellipse bowls, flat-cut terminals, double-storey a/g, slashed zero, tabular figures. Original code-generated letterforms for DestroCorp (Seat=Kirvyn 16, Line=AuditScan file:line).',
        'manufacturer': 'DestroCorp'})
    fb.setupOS2(sTypoAscender=ASC, sTypoDescender=DESC, usWinAscent=ASC, usWinDescent=-DESC,
        sxHeight=XH, sCapHeight=CAP)
    fb.setupPost(); fb.setupHead(unitsPerEm=UPM); fb.setupMaxp()
    try:
        from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
        fea = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;', 'feature kern {']
        for l, r, v in KERN:
            if l in glyphs and r in glyphs: fea.append(f'  pos {l} {r} {v};')
        fea.append('} kern;')
        addOpenTypeFeaturesFromString(fb.font, '\n'.join(fea))
    except Exception as e:
        print('kern skipped:', e)
    fb.save(out_ttf)
    from fontTools.ttLib import TTFont
    f = TTFont(out_ttf)
    glyf = f['glyf']; hmtx = f['hmtx']
    for name, gl in glyf.glyphs.items():
        if name in ('space', '.notdef') or getattr(gl, 'numberOfContours', 0) == 0: continue
        gl.recalcBounds(glyf)
        ww = gl.xMax - gl.xMin
        if mono:
            hmtx[name] = (ADV_MONO, (ADV_MONO - ww) // 2 - gl.xMin)
        else:
            hmtx[name] = (ww + 2 * lsb, lsb - gl.xMin)
    f.save(out_ttf)
    print('saved', out_ttf)


def convert(out_ttf):
    from fontTools.ttLib import TTFont
    base, _ = os.path.splitext(out_ttf)
    f = TTFont(out_ttf)
    f.flavor = 'woff'; f.save(base + '.woff'); print('saved', base + '.woff')
    f.flavor = 'woff2'; f.save(base + '.woff2'); print('saved', base + '.woff2')

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    jobs = [
        (os.path.join(here, 'DestroSeatlineSans-Regular.ttf'), 'Destro Seatline Sans', 'Regular', 'DestroSeatlineSans-Regular', 'Regular', False),
        (os.path.join(here, 'DestroSeatlineSans-Bold.ttf'), 'Destro Seatline Sans', 'Bold', 'DestroSeatlineSans-Bold', 'Bold', False),
        (os.path.join(here, 'DestroSeatlineMono-Regular.ttf'), 'Destro Seatline Mono', 'Regular', 'DestroSeatlineMono-Regular', 'Regular', True),
    ]
    for out, fam, sty, ps, wk, mono in jobs:
        build_one(out, fam, sty, ps, wk, mono)
        convert(out)
