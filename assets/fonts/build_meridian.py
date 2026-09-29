"""Destro Meridian — a wholly new invented typeface for DestroCorp (v4 line).
Replaces the GatherScan experiment entirely. Different design philosophy:
no cuts, no chisels, no stencil joints. Smoothness first.
Identity comes from three original systems:
  SLANT AXIS   every vertical leans 4 degrees forward (motion, optimism)
  SQUIRCLE     bowls/counters are superellipses (exp 2.6) - not circles, not rects
  ROUND ENDS   every stroke terminates in a full round terminal (trust, softness)
Plus: tall x-height (520), single-storey a/g, dot-in-zero for code contexts.
All letterforms generated from centerline skeletons + superellipse bands here.
No existing font data, no tracing.
"""
import math
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

UPM=1000; ASC=740; DESC=-220; CAP=690; XH=520
S=116; B=100; BW=112
SHEAR=0.07
LSB=46
SQN=2.6

class C:
    def __init__(self, pts, closed=True):
        self.pts=list(pts); self.closed=closed
    def reversed(self):
        return C(list(reversed(self.pts)), self.closed)

def area(pts):
    s=0; n=len(pts)
    for i in range(n):
        x0,y0=pts[i]; x1,y1=pts[(i+1)%n]
        s+=x0*y1-x1*y0
    return s/2

def emit(pen, cont, hole=False):
    poly=cont.pts
    a=area(poly)
    if hole and a<0: cont=cont.reversed()
    if not hole and a>0: cont=cont.reversed()
    pts=[(x+SHEAR*y+LSB, y) for x,y in cont.pts]
    pen.moveTo(pts[0])
    for p in pts[1:]: pen.lineTo(p)
    pen.closePath()

def sqpt(cx,cy,rx,ry,t):
    e=2.0/SQN
    c=math.cos(t); s=math.sin(t)
    x=rx*math.copysign(abs(c)**e, c)
    y=ry*math.copysign(abs(s)**e, s)
    return (cx+x, cy+y)

def sqarc(cx,cy,rx,ry,a0,a1,segs=None):
    a0=math.radians(a0); a1=math.radians(a1)
    if segs is None:
        segs=max(6,int(abs(a1-a0)/(math.pi/24)+0.999))
    return [sqpt(cx,cy,rx,ry,a0+(a1-a0)*i/segs) for i in range(segs+1)]

def band(cx,cy,rxo,ryo,rxi,ryi,a0,a1):
    outer=sqarc(cx,cy,rxo,ryo,a0,a1)
    inner=sqarc(cx,cy,rxi,ryi,a0,a1)
    return C(outer+list(reversed(inner)))

def ring(cx,cy,rxo,ryo,rxi,ryi):
    o=sqarc(cx,cy,rxo,ryo,0,360,64)[:-1]
    i=sqarc(cx,cy,rxi,ryi,0,360,64)[:-1]
    return C(o), C(i)

def oring(pen,cx,cy,rxo,ryo,rxi,ryi):
    o,i=ring(cx,cy,rxo,ryo,rxi,ryi)
    emit(pen,o); emit(pen,i,hole=True)

def stroke(pts, w, cap0='round', cap1='round'):
    n=len(pts); left=[]; right=[]
    for i in range(n):
        if i==0: dx,dy=pts[1][0]-pts[0][0], pts[1][1]-pts[0][1]
        elif i==n-1: dx,dy=pts[-1][0]-pts[-2][0], pts[-1][1]-pts[-2][1]
        else: dx,dy=pts[i+1][0]-pts[i-1][0], pts[i+1][1]-pts[i-1][1]
        L=math.hypot(dx,dy) or 1
        nx,ny=-dy/L*w/2, dx/L*w/2
        left.append((pts[i][0]+nx, pts[i][1]+ny))
        right.append((pts[i][0]-nx, pts[i][1]-ny))
    body=[]
    if cap0=='round':
        d=math.atan2(pts[1][1]-pts[0][1], pts[1][0]-pts[0][0])
        a=d-math.pi/2
        for t in range(7):
            ang=a-math.pi*t/6
            body.append((pts[0][0]+w/2*math.cos(ang), pts[0][1]+w/2*math.sin(ang)))
        body+=left[1:]
    else:
        body=left[:]
    if cap1=='round':
        d=math.atan2(pts[-1][1]-pts[-2][1], pts[-1][0]-pts[-2][0])
        a=d+math.pi/2
        for t in range(7):
            ang=a-math.pi*t/6
            body.append((pts[-1][0]+w/2*math.cos(ang), pts[-1][1]+w/2*math.sin(ang)))
        body+=right[-2:0:-1]
    else:
        body+=right[::-1]
    return C(body)

def sp(pen, pts, w, c0='round', c1='round'):
    emit(pen, stroke(pts,w,c0,c1))

def dot(pen,cx,cy,r,n=20):
    pts=[(cx+r*math.cos(2*math.pi*i/n), cy+r*math.sin(2*math.pi*i/n)) for i in range(n)]
    emit(pen, C(pts))

def cub(p0,c1,c2,p1,n=24):
    out=[]
    for i in range(n+1):
        t=i/n; u=1-t
        out.append((u*u*u*p0[0]+3*u*u*t*c1[0]+3*u*t*t*c2[0]+t*t*t*p1[0],
                    u*u*u*p0[1]+3*u*u*t*c1[1]+3*u*t*t*c2[1]+t*t*t*p1[1]))
    return out

def quad(p0,c,p1,n=16):
    out=[]
    for i in range(n+1):
        t=i/n; u=1-t
        out.append((u*u*p0[0]+2*u*t*c[0]+t*t*p1[0], u*u*p0[1]+2*u*t*c[1]+t*t*p1[1]))
    return out

DRAW={}; WIDTH={}
def glyph(name,width,fn):
    WIDTH[name]=width; DRAW[name]=fn

def stem(pen,x,y0,y1,w=S):
    sp(pen,[(x,y0+w/2),(x,y1-w/2)],w)
def bar(pen,x0,x1,y,w=B):
    sp(pen,[(x0+w/2,y),(x1-w/2,y)],w)

# ---------- UPPERCASE ----------
def g_A(p):
    sp(p,[(70,0),(330,690)],S); sp(p,[(590,0),(330,690)],S)
    bar(p,160,500,240)
glyph('A',660,g_A)
def g_B(p):
    stem(p,58,0,690)
    emit(p,band(58,516,400,174,284,58,90,-90))
    emit(p,band(58,174,412,174,296,58,90,-90))
glyph('B',620,g_B)
def g_C(p): emit(p,band(320,345,300,353,184,249,40,320))
glyph('C',640,g_C)
def g_D(p):
    stem(p,58,0,690)
    emit(p,band(58,345,420,353,304,249,90,-90))
glyph('D',680,g_D)
def g_E(p):
    stem(p,58,0,690); bar(p,58,470,640); bar(p,58,400,345); bar(p,58,470,50)
glyph('E',540,g_E)
def g_F(p):
    stem(p,58,0,690); bar(p,58,450,640); bar(p,58,380,345)
glyph('F',520,g_F)
def g_G(p):
    emit(p,band(320,345,300,353,184,249,40,320))
    sp(p,[(560,120),(560,300)],S)
    bar(p,330,560,250)
glyph('G',660,g_G)
def g_H(p):
    stem(p,58,0,690); stem(p,560,0,690); bar(p,58,560,345,B)
glyph('H',660,g_H)
def g_I(p): stem(p,58,0,690)
glyph('I',160,g_I)
def g_J(p):
    stem(p,470,150,690)
    emit(p,band(290,180,232,188,116,72,180,360))
glyph('J',540,g_J)
def g_K(p):
    stem(p,58,0,690)
    sp(p,[(110,330),(520,660)],S)
    sp(p,[(200,320),(540,30)],S)
glyph('K',640,g_K)
def g_L(p): stem(p,58,0,690); bar(p,58,450,50)
glyph('L',520,g_L)
def g_M(p):
    stem(p,58,0,690); stem(p,640,0,690)
    sp(p,[(80,640),(350,120)],110); sp(p,[(620,640),(350,120)],110)
glyph('M',760,g_M)
def g_N(p):
    stem(p,58,0,690); stem(p,560,0,690)
    sp(p,[(80,620),(580,70)],112)
glyph('N',660,g_N)
def g_O(p): oring(p,330,345,310,353,194,249)
glyph('O',680,g_O)
def g_P(p):
    stem(p,58,0,690)
    emit(p,band(58,516,400,174,284,58,90,-90))
glyph('P',600,g_P)
def g_Q(p):
    oring(p,330,345,310,353,194,249)
    sp(p,[(400,120),(600,-40)],104)
glyph('Q',680,g_Q)
def g_R(p):
    stem(p,58,0,690)
    emit(p,band(58,516,400,174,284,58,90,-90))
    sp(p,[(250,320),(540,30)],S)
glyph('R',620,g_R)
def g_S(p):
    pts=cub((492,576),(430,678),(258,702),(168,632),20)+cub((168,632),(84,566),(102,442),(212,394),20)[1:]+cub((212,394),(300,356),(330,342),(392,302),14)[1:]+cub((392,302),(492,238),(512,118),(408,54),20)[1:]+cub((408,54),(312,-4),(150,16),(84,106),20)[1:]
    emit(p, stroke(pts,112))
glyph('S',600,g_S)
def g_T(p):
    bar(p,60,540,640); stem(p,300,0,640)
glyph('T',600,g_T)
def g_U(p):
    stem(p,58,140,690); stem(p,560,140,690)
    emit(p,band(310,180,252,188,136,72,180,360))
glyph('U',660,g_U)
def g_V(p):
    sp(p,[(70,660),(320,40)],S); sp(p,[(570,660),(320,40)],S)
glyph('V',640,g_V)
def g_W(p):
    sp(p,[(60,660),(240,40)],110); sp(p,[(240,40),(430,460)],110)
    sp(p,[(430,460),(620,40)],110); sp(p,[(620,40),(800,660)],110)
glyph('W',860,g_W)
def g_X(p):
    sp(p,[(60,660),(560,30)],S); sp(p,[(60,30),(560,660)],S)
glyph('X',620,g_X)
def g_Y(p):
    sp(p,[(60,660),(310,320)],S); sp(p,[(560,660),(310,320)],S)
    stem(p,310,0,330)
glyph('Y',620,g_Y)
def g_Z(p):
    bar(p,60,500,640); sp(p,[(460,600),(100,90)],110); bar(p,60,500,50)
glyph('Z',560,g_Z)

# ---------- LOWERCASE ----------
def g_a(p):
    oring(p,250,260,240,268,124,164)
    stem(p,430,0,520)
glyph('a',560,g_a)
def g_b(p):
    stem(p,58,0,740)
    oring(p,320,260,240,268,124,164)
glyph('b',600,g_b)
def g_c(p): emit(p,band(270,260,240,268,124,164,40,320))
glyph('c',540,g_c)
def g_d(p):
    oring(p,250,260,240,268,124,164)
    stem(p,430,0,740)
glyph('d',600,g_d)
def g_e(p):
    emit(p,band(270,260,244,268,128,164,8,310))
    bar(p,60,450,270,B)
glyph('e',560,g_e)
def g_f(p):
    stem(p,240,0,600)
    emit(p,band(240,600,170,140,66,36,90,0))
    bar(p,60,360,280,96)
glyph('f',440,g_f)
def g_g(p):
    oring(p,250,260,240,268,124,164)
    stem(p,430,-160,520)
    emit(p,band(250,-100,240,130,124,26,200,340))
glyph('g',600,g_g)
def g_h(p):
    stem(p,58,0,740)
    emit(p,band(280,270,222,250,106,146,180,0))
    stem(p,460,0,300)
glyph('h',600,g_h)
def g_i(p):
    stem(p,58,0,520); dot(p,58,640,62)
glyph('i',160,g_i)
def g_j(p):
    stem(p,180,-160,520); dot(p,180,640,62)
glyph('j',280,g_j)
def g_k(p):
    stem(p,58,0,740)
    sp(p,[(110,240),(430,480)],110)
    sp(p,[(190,230),(450,30)],110)
glyph('k',560,g_k)
def g_l(p): stem(p,58,0,740)
glyph('l',160,g_l)
def g_m(p):
    stem(p,58,0,520)
    emit(p,band(270,270,212,250,96,146,180,0))
    stem(p,440,0,300)
    emit(p,band(610,270,200,250,84,146,180,0))
    stem(p,770,0,300)
glyph('m',880,g_m)
def g_n(p):
    stem(p,58,0,520)
    emit(p,band(280,270,222,250,106,146,180,0))
    stem(p,460,0,300)
glyph('n',600,g_n)
def g_o(p): oring(p,280,260,264,268,148,164)
glyph('o',580,g_o)
def g_p(p):
    stem(p,58,-220,520)
    oring(p,320,260,240,268,124,164)
glyph('p',600,g_p)
def g_q(p):
    oring(p,250,260,240,268,124,164)
    stem(p,430,-220,520)
glyph('q',600,g_q)
def g_r(p):
    stem(p,58,0,520)
    emit(p,band(250,270,220,250,104,146,180,60))
glyph('r',440,g_r)
def g_s(p):
    pts=cub((430,420),(380,500),(240,518),(160,460),18)+cub((160,460),(90,410),(105,320),(190,286),18)[1:]+cub((190,286),(260,258),(285,248),(330,218),12)[1:]+cub((330,218),(405,168),(420,80),(340,32),18)[1:]+cub((340,32),(265,-12),(140,4),(88,74),18)[1:]
    emit(p, stroke(pts,104))
glyph('s',520,g_s)
def g_t(p):
    pts=[(200,600),(200,160)]+quad((200,160),(200,60),(320,60),12)[1:]
    emit(p, stroke(pts,110))
    bar(p,60,330,300,96)
glyph('t',420,g_t)
def g_u(p):
    stem(p,58,160,520)
    emit(p,band(300,170,242,178,126,74,180,360))
    stem(p,480,0,520)
glyph('u',600,g_u)
def g_v(p):
    sp(p,[(60,490),(270,40)],110); sp(p,[(480,490),(270,40)],110)
glyph('v',540,g_v)
def g_w(p):
    sp(p,[(50,490),(200,40)],104); sp(p,[(200,40),(380,350)],104)
    sp(p,[(380,350),(560,40)],104); sp(p,[(560,40),(710,490)],104)
glyph('w',760,g_w)
def g_x(p):
    sp(p,[(50,490),(470,30)],110); sp(p,[(50,30),(470,490)],110)
glyph('x',520,g_x)
def g_y(p):
    sp(p,[(60,490),(270,40)],110); sp(p,[(480,490),(190,-200)],110)
glyph('y',540,g_y)
def g_z(p):
    bar(p,60,440,470); sp(p,[(400,430),(100,90)],104); bar(p,60,440,50)
glyph('z',500,g_z)

# ---------- DIGITS ----------
def g_0(p):
    oring(p,310,345,290,353,174,249)
    dot(p,310,345,58)
glyph('zero',640,g_0)
def g_1(p):
    stem(p,240,0,690); sp(p,[(240,640),(90,500)],B)
glyph('one',420,g_1)
def g_2(p):
    emit(p,band(290,500,240,190,124,86,170,10))
    sp(p,[(500,430),(90,90)],110)
    bar(p,60,500,50)
glyph('two',560,g_2)
def g_3(p):
    emit(p,band(290,510,240,175,124,71,150,-60))
    emit(p,band(290,180,250,185,134,81,60,-170))
glyph('three',560,g_3)
def g_4(p):
    sp(p,[(330,660),(70,240)],110)
    bar(p,40,560,240)
    stem(p,430,0,690)
glyph('four',620,g_4)
def g_5(p):
    bar(p,80,470,640)
    stem(p,80,360,690)
    bar(p,80,330,360)
    emit(p,band(300,200,240,195,124,91,80,-160))
glyph('five',560,g_5)
def g_6(p):
    sp(p,cub((450,650),(300,630),(150,480),(130,300),20),110)
    oring(p,300,190,260,205,144,101)
glyph('six',620,g_6)
def g_7(p):
    bar(p,60,520,640); sp(p,[(480,600),(180,40)],110)
glyph('seven',560,g_7)
def g_8(p):
    oring(p,300,510,230,175,114,71)
    oring(p,300,180,255,195,139,91)
glyph('eight',620,g_8)
def g_9(p):
    oring(p,300,500,260,205,144,101)
    stem(p,450,0,500)
glyph('nine',620,g_9)

# ---------- PUNCTUATION ----------
def g_space(p): pass
glyph('space',340,g_space)
def g_period(p): dot(p,58,58,58)
glyph('period',200,g_period)
def g_comma(p):
    dot(p,58,58,58); sp(p,[(58,58),(10,-90)],96)
glyph('comma',200,g_comma)
def g_colon(p): dot(p,58,110,56); dot(p,58,390,56)
glyph('colon',200,g_colon)
def g_semi(p):
    dot(p,95,390,56); dot(p,95,110,56); sp(p,[(95,110),(47,-40)],96)
glyph('semicolon',240,g_semi)
def g_excl(p): stem(p,58,180,690,104); dot(p,58,60,62)
glyph('exclam',200,g_excl)
def g_ques(p):
    emit(p,band(280,470,230,200,114,96,-50,210))
    sp(p,[(280,300),(260,150)],104)
    dot(p,255,45,62)
glyph('question',560,g_ques)
def g_hyphen(p): bar(p,60,320,290)
glyph('hyphen',380,g_hyphen)
def g_minus(p): bar(p,60,540,345)
glyph('minus',600,g_minus)
def g_endash(p): bar(p,40,560,290)
glyph('endash',600,g_endash)
def g_emdash(p): bar(p,40,860,290)
glyph('emdash',900,g_emdash)
def g_slash(p): sp(p,[(400,-40),(90,730)],104)
glyph('slash',480,g_slash)
def g_bslash(p): sp(p,[(70,-40),(420,730)],104)
glyph('backslash',480,g_bslash)
def g_lpar(p): sp(p,cub((300,710),(60,470),(60,230),(300,-10),24),108)
glyph('parenleft',360,g_lpar)
def g_rpar(p): sp(p,cub((60,710),(300,470),(300,230),(60,-10),24),108)
glyph('parenright',360,g_rpar)
def g_qdbl(p):
    sp(p,[(60,660),(100,460)],92); sp(p,[(210,660),(250,460)],92)
glyph('quotedbl',340,g_qdbl)
def g_apos(p): sp(p,[(60,660),(100,460)],92)
glyph('quotesingle',190,g_apos)
def g_amp(p):
    oring(p,240,170,190,175,84,71)
    sp(p,[(60,640),(470,0)],108)
    bar(p,60,400,520)
glyph('ampersand',620,g_amp)
def g_at(p):
    oring(p,300,250,280,285,164,169)
    sp(p,[(390,130),(390,430)],104)
    oring(p,330,300,100,120,30,50)
glyph('at',700,g_at)
def g_hash(p):
    sp(p,[(150,0),(150,690)],100); sp(p,[(390,0),(390,690)],100)
    bar(p,40,520,240,96); bar(p,40,520,440,96)
glyph('numbersign',560,g_hash)
def g_dollar(p):
    g_S(p); sp(p,[(300,-60),(300,750)],100)
glyph('dollar',600,g_dollar)
def g_pct(p):
    oring(p,140,540,135,135,55,55)
    oring(p,440,150,135,135,55,55)
    sp(p,[(480,690),(100,0)],92)
glyph('percent',660,g_pct)
def g_star(p):
    sp(p,[(280,60),(280,660)],96)
    sp(p,[(90,190),(470,530)],96); sp(p,[(90,530),(470,190)],96)
glyph('asterisk',560,g_star)
def g_plus(p): sp(p,[(300,80),(300,620)],100); bar(p,60,540,350,100)
glyph('plus',600,g_plus)
def g_eq(p): bar(p,60,540,220,100); bar(p,60,540,430,100)
glyph('equal',600,g_eq)
def g_lt(p): sp(p,[(450,640),(90,340)],108); sp(p,[(90,340),(450,40)],108)
glyph('less',540,g_lt)
def g_gt(p): sp(p,[(90,640),(450,340)],108); sp(p,[(450,340),(90,40)],108)
glyph('greater',540,g_gt)
def g_lb(p):
    bar(p,60,320,50,100); sp(p,[(110,50),(110,650)],100); bar(p,60,320,650,100)
glyph('bracketleft',360,g_lb)
def g_rb(p):
    bar(p,40,300,50,100); sp(p,[(250,50),(250,650)],100); bar(p,40,300,650,100)
glyph('bracketright',360,g_rb)
def g_lbr(p):
    bar(p,90,340,600,96); sp(p,[(140,600),(140,420)],96); sp(p,[(140,280),(140,100)],96); bar(p,90,340,100,96); sp(p,[(140,420),(140,280)],70)
glyph('braceleft',400,g_lbr)
def g_rbr(p):
    bar(p,60,310,600,96); sp(p,[(260,600),(260,420)],96); sp(p,[(260,280),(260,100)],96); bar(p,60,310,100,96); sp(p,[(260,420),(260,280)],70)
glyph('braceright',400,g_rbr)
def g_us(p): bar(p,40,520,-40,96)
glyph('underscore',560,g_us)
def g_caret(p):
    sp(p,[(60,360),(220,560)],96); sp(p,[(220,560),(380,360)],96)
glyph('asciicircum',440,g_caret)
def g_grave(p): sp(p,[(140,660),(60,500)],92)
glyph('grave',200,g_grave)
def g_bar(p): sp(p,[(120,-220),(120,740)],100)
glyph('bar',280,g_bar)
def g_tilde(p):
    sp(p,cub((50,290),(150,420),(250,180),(350,310),16)+[(350,310)],92)
glyph('asciitilde',420,g_tilde)
def g_middot(p): dot(p,58,260,56)
glyph('periodcentered',200,g_middot)
def g_copy(p):
    oring(p,320,260,290,295,174,179)
    emit(p,band(320,260,124,124,54,54,45,315))
glyph('copyright',700,g_copy)
def g_bull(p): dot(p,150,260,100)
glyph('bullet',340,g_bull)
def g_hellip(p): dot(p,55,55,55); dot(p,255,55,55); dot(p,455,55,55)
glyph('ellipsis',560,g_hellip)
def g_qll(p):
    sp(p,[(60,560),(100,360)],92); sp(p,[(210,560),(250,360)],92)
glyph('quotedblleft',340,g_qll)
def g_qr(p): sp(p,[(60,660),(100,460)],92)
glyph('quoteright',190,g_qr)
def g_ql(p): sp(p,[(60,660),(100,460)],92)
glyph('quoteleft',190,g_ql)
def g_qrr(p):
    sp(p,[(60,560),(100,360)],92); sp(p,[(210,560),(250,360)],92)
glyph('quotedblright',340,g_qrr)
def g_arrow(p):
    bar(p,40,560,290,100)
    sp(p,[(400,500),(620,290)],112); sp(p,[(620,290),(400,80)],112)
glyph('arrowright',700,g_arrow)
def g_rupee(p):
    bar(p,60,500,640); bar(p,60,500,360)
    sp(p,[(120,360),(500,0)],112)
    stem(p,60,0,690)
glyph('rupee',600,g_rupee)

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
 ('C','A',-50),('C','V',-50),('C','W',-45),('C','T',-60),('C','Y',-45),
 ('G','A',-30),('G','T',-40),('G','W',-26),
 ('L','T',-90),('L','V',-75),('L','W',-65),('L','Y',-75),('L','A',-40),
 ('A','T',-60),('H','T',-55),('N','T',-55),('U','T',-55),('O','T',-55),
 ('D','T',-55),('E','T',-55),('R','T',-48),('S','T',-48),('P','T',-48),
 ('B','T',-48),('M','T',-48),('F','T',-55),('I','T',-48),('J','T',-55),
 ('Q','T',-55),('V','T',-42),('W','T',-42),('Y','T',-42),('Z','T',-48),
 ('T','A',-36),('T','O',-20),('T','U',-20),('T','V',-40),('T','W',-36),('T','Y',-36),
 ('F','A',-36),('P','A',-28),('Y','A',-30),('V','A',-36),('W','A',-30),
 ('hyphen','T',-45),('hyphen','C',-35),
 ('o','t',-35),('e','t',-28),('a','t',-28),('r','t',-28),('n','t',-28),('u','t',-28),
 ('T','o',-20),('T','a',-24),('L','e',-30),('L','o',-18),('C','a',-30),
]

def build(out_ttf):
    seen=set(['.notdef','space']); rest=[]
    for g in list(DRAW.keys())+list(CMAP.values()):
        if g not in seen:
            seen.add(g); rest.append(g)
    rest=sorted(rest,key=lambda x:(len(x),x))
    order=['.notdef','space']+rest
    for g in list(CMAP.values()):
        if g not in DRAW and g!='space':
            WIDTH[g]=400
            DRAW[g]=lambda pen: dot(pen,100,100,80)
    for g in order:
        if g not in WIDTH: WIDTH[g]=600
    fb=FontBuilder(UPM,isTTF=True)
    glyphs={}; metrics={}
    for gname in order:
        pen=TTGlyphPen(None)
        if gname in DRAW:
            try: DRAW[gname](pen)
            except Exception as e: print('ERR',gname,e)
        elif gname=='.notdef':
            emit(pen,C([(70,0),(70,700),(530,700),(530,0)]))
            emit(pen,C([(200,130),(200,570),(400,570),(400,130)]),hole=True)
        glyphs[gname]=pen.glyph()
        adv=WIDTH.get(gname,600)+LSB*2 if gname!='space' else 340
        if gname=='.notdef': adv=700
        metrics[gname]=(adv, LSB if gname!='space' else 0)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({u:g for u,g in CMAP.items()})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASC,descent=DESC)
    fb.setupNameTable({'familyName':'Destro Meridian','styleName':'Regular',
        'uniqueFontIdentifier':'DestroMeridian-1.0','fullName':'Destro Meridian Regular',
        'psName':'DestroMeridian-Regular','version':'Version 1.0',
        'designer':'DestroCorp Studio','description':'Invented sans: 4-degree slant axis, superellipse squircle bowls, fully round stroke terminals, tall x-height, dot-in-zero. Original letterforms generated in code for DestroCorp.',
        'manufacturer':'DestroCorp'})
    fb.setupOS2(sTypoAscender=ASC,sTypoDescender=DESC,usWinAscent=ASC,usWinDescent=-DESC,
        sxHeight=XH,sCapHeight=CAP)
    fb.setupPost(); fb.setupHead(unitsPerEm=UPM); fb.setupMaxp()
    try:
        from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
        fea=['languagesystem DFLT dflt;','languagesystem latn dflt;','feature kern {']
        for l,r,v in KERN:
            if l in glyphs and r in glyphs: fea.append(f'  pos {l} {r} {v};')
        fea.append('} kern;')
        addOpenTypeFeaturesFromString(fb.font,'\n'.join(fea))
    except Exception as e:
        print('kern skipped:',e)
    fb.save(out_ttf)
    from fontTools.ttLib import TTFont
    f=TTFont(out_ttf)
    glyf=f['glyf']; hmtx=f['hmtx']
    for name,gl in glyf.glyphs.items():
        if name in ('space','.notdef') or getattr(gl,'numberOfContours',0)==0: continue
        gl.recalcBounds(glyf)
        w=gl.xMax-gl.xMin
        hmtx[name]=(w+2*LSB, LSB-gl.xMin)
    f.save(out_ttf)
    print('saved',out_ttf)

if __name__=='__main__':
    import sys
    build(sys.argv[1] if len(sys.argv)>1 else 'DestroMeridian.ttf')
