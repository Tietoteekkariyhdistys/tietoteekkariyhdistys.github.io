import json, math, os, sys
from collections import OrderedDict

OUT_HTML = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'layouts', '404.html')

data = json.load(open('frames5.json'))
f, meta = data['frames'], data['meta']
EPS = 0.004

# ---- timeline (seconds) -------------------------------------------------
win = OrderedDict()
marks = {}
t = 0.0


def show(name, dur):
    global t
    win.setdefault(name, []).append((t, t + dur))
    t += dur


NW, CYC, REPS = 12, 1.0, 7
for _ in range(REPS):
    for i in range(NW):
        show("w%d" % i, CYC / NW)
WALK = t                                   # beat 1: 0 - 7 s
show("settle", 0.3)                        # beat 2: stop
show("rest", 0.7)
marks["pocket"] = t                        # beat 3: cigarette from the pack
for n, d in (("pk1", .18), ("pk2", .18), ("pk3", .18), ("pk4", .2), ("pk5", .13), ("restc", .13)):
    show(n, d)
marks["light"] = t                         # beat 4: lighter, red tip, first puff
for n, d in (("lt1", .15), ("lt2", .15), ("lt3", .15), ("fA", .1), ("fB", .1), ("fA", .1),
             ("fD", .1), ("fC", .1), ("fD", .1), ("fC", .1), ("fD", .1), ("ld1", .15)):
    show(n, d)
marks["puffP"] = t
show("ld2", .15)
show("litrest", .45)
marks["turn"] = t                          # beat 5: turn in three steps
show("t1", .33)
show("t2", .33)
show("idle", .64)
marks["smoke"] = t                         # beat 6: three drags and one tap
PUFFS = []


def drag(lens, first_raise):
    for n, d in first_raise:
        show(n, d)
    for L_ in lens:
        show("mB%d" % L_, 0.55 if L_ == lens[0] else 0.5)


drag((24, 21, 18), [("pm", .2)])
PUFFS.append(t)
show("cm18", .2); show("cl18", .5)
show("tapA", .25); show("tapB", .2); show("tapC", .25); show("cl18", .35)
drag((18, 15, 12), [("cm18", .2)])
PUFFS.append(t)
show("cm12", .2); show("cl12", .6)
drag((12, 9, 6), [("cm12", .2)])
PUFFS.append(t)
show("cm6", .2); show("cl6", .6)
marks["throw"] = t                         # beat 7: throw the butt
show("thr1", .3)
BUTT0 = t
show("thr2", .15)
show("thr3", .7)
show("end", .3)
marks["stomp"] = t                         # beat 8: three stomps with a twist
for name, dur in (("stU", .3), ("stM", .08), ("stD", .13), ("stU", .2), ("stM", .08), ("stD", .13), ("stU", .2), ("stM", .08), ("stD", .13)):
    show(name, dur)
TWIST0 = t
for name, dur in (("stT1", .14), ("stT2", .14), ("stT1", .14), ("stD", .15)):
    show(name, dur)
STOMP_END = t
END0 = t
FLIGHT = 0.8
D = END0 + 0.6                             # beat 9: held by an explicit 100% keyframe
win["end"].append((END0, D))
FL_N = 8
for i in range(FL_N):
    win["bf%d" % i] = [(BUTT0 + FLIGHT * i / FL_N, BUTT0 + FLIGHT * (i + 1) / FL_N)]
win["bl"] = [(BUTT0 + FLIGHT, TWIST0)]
win["bg"] = [(TWIST0, D)]

# ---- html -----------------------------------------------------------------
esc = lambda name: "\n".join(f[name]).replace("{", "&#123;")
pre = lambda name, cls, extra="": '<pre class="%s"%s aria-hidden="true">%s</pre>' % (cls, extra, esc(name))


def keyframes(name):
    out = []
    for a, b in win[name]:
        pa, pb = a / D * 100, b / D * 100
        if a > 0:
            out.append("%.4f%%{visibility:hidden}" % max(0, pa - EPS))
        out.append("%.4f%%{visibility:visible}" % pa)
        if b < D - 1e-9:
            out.append("%.4f%%{visibility:visible}" % max(0, pb - EPS))
            out.append("%.4f%%{visibility:hidden}" % pb)
        else:
            out.append("100%{visibility:visible}")   # final pose: explicit end state, never falls back to hidden
    if win[name][0][0] > 0:
        out.insert(0, "0%{visibility:hidden}")
    return "@keyframes kf-%s{%s}" % (name, "".join(out))


kf = "\n".join(keyframes(n) for n in win)
frames_html = "\n      ".join('<pre class="fr f-%s" style="animation-name:kf-%s" aria-hidden="true">%s</pre>' % (n, n, esc(n)) for n in win)

bx0, by0 = meta["butt_start"]
bx1, by1 = meta["butt_end"]
cvt = lambda x, y: ("%.1fch" % (x / 2), "%.1fem" % ((280 - y) / (10 / 3)))
(bl0, bb0), (bl1, bb1) = cvt(bx0, by0), cvt(bx1, by1)
BW = 3.9   # half the butt width in ch
bl0, bl1 = "%.1fch" % (bx0 / 2 - BW), "%.1fch" % (bx1 / 2 - BW)
bmid_l, bmid_b = "%.1fch" % ((bx0 + bx1) / 4 - BW + 3), "%.1fem" % ((280 - by0) / (10 / 3) + 16)

puffs = [pre("puffP", "puff", ' style="animation-delay:%.3fs"' % marks["puffP"])]
for pt in PUFFS:
    puffs.append(pre("puffF", "puff", ' style="animation-delay:%.3fs"' % pt))
puffs_html = "\n      ".join(puffs)

page = '''{{ define "head" }}
<style>
.stage { --walk: %.2fs; --total: %.3fs; }
%s
</style>
{{ end }}

{{ define "main" }}
{{- /* One 404 page serves every language, so the text is shown in all three.
       The scene is generated ASCII art (a bus stop sign and a stick figure with a kitty head) animated with CSS only:
       the figure walks out from behind the sidebar, takes a cigarette from a pack in her pocket, lights it,
       turns to face the viewer, smokes it down, throws the butt on the ground, stomps it out and keeps standing there.
       Every frame has its own visibility keyframes on one shared timeline; the last one ends on an explicit 100%%
       keyframe so she stays visible. Reduced motion shows the final pose. */ -}}
<article class="page notfound">
  <h1>404 <span class="nf-sub">site not reached</span></h1>
  <div class="stage" role="img" aria-label="A stick figure with a kitty head waits at a bus stop sign that reads BUS 404, smokes a cigarette, throws the butt on the ground and stomps it out.">
    %s
    <div class="walker" aria-hidden="true">
      %s
      %s
      <span class="bwisp" style="left:%s;animation-delay:%.3fs">'<br>)<br>'</span>
    </div>
  </div>
  <p><strong>Sivua ei löytynyt.</strong> Se on voinut siirtyä tai poistua.</p>
  <p><strong>Page not found.</strong> It may have moved or been removed.</p>
  <p><strong>Sidan hittades inte.</strong> Den kan ha flyttats eller tagits bort.</p>
  <p class="notfound-links">
    <a class="btn" href="{{ "" | relURL }}">Etusivu</a>
    <a class="btn" href="{{ "en/" | relURL }}">Home</a>
    <a class="btn" href="{{ "sv/" | relURL }}">Startsida</a>
  </p>
</article>
{{ end }}
''' % (WALK, D, kf,
       pre("sign", "sign"), frames_html, puffs_html,
       "%.1fch" % (bx1 / 2 - 1), TWIST0 + 0.2)
open(OUT_HTML, 'w', encoding='utf-8', newline='\n').write(page)

print("walk %.2f pocket %.2f light %.2f turn %.2f smoke %.2f throw %.2f stomp %.2f end %.2f total %.2f, frames %d" % (
    WALK, marks["pocket"], marks["light"], marks["turn"], marks["smoke"], marks["throw"], marks["stomp"], END0, D, len(win)))
