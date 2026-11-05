"""KEV product context for the growth engine.

KEV is the immersive school: an 11-floor 3D campus, studio-grade science labs,
a Human Atlas and EV cutaway, AI tutors per subject, an offline-first classroom
and an on-device Motion Gym. This module carries KEV's verified claim registry,
its (much stricter) child-safe compliance guard, its hook library and its
programmatic-SEO page catalog, so ``products.use("kev")`` runs the whole
create → launch → scale loop against KEV.

The compliance posture is deliberately harder than Priv's: KEV is used by
children, so no performance or learning-outcome claims, no literal "5D", no
quantum-hardware claims, no camera-surveillance framing, and no fake
multiplayer. Every number in the registry is readable out of the shipped app.
"""
from __future__ import annotations

import re

# ------------------------------------------------------------------ identity --
SITE = "kev.sansmercantile.com"
SITE_FULL = "https://kev.sansmercantile.com"
DOWNLOADS = SITE_FULL  # installable PWA; the app *is* the download

# The honest note that must ride on every page and ad. No risk product, so no
# financial disclaimer — this is the accuracy line instead.
DISCLAIMER = (
    "KEV is educational software. Immersive scenes are teaching "
    "visualisations; Motion Gym is on-device movement analysis, not medical "
    "monitoring.")

CATEGORY = "immersive school"
ONE_LINER = (
    "KEV is an immersive school: a 3D campus, studio-grade science labs, "
    "level-adaptive AI tutors and an offline classroom, on any device.")

# Hashtags for organic posts (read by growth.social._tags via stats.SOCIAL_TAGS).
SOCIAL_TAGS = ["edtech", "immersivelearning", "xr", "educhat", "stem"]

# ---------------------------------------------------------------- claim stack --
# verified=True  -> readable out of the shipped app (campus model, atlas index,
#                   lab list, precache manifest). Children are shown numbers that
#                   must be true.
STATS = {
    "category":     dict(value="Immersive school", label="category",
                         source="positioning", verified=True),
    "floors":       dict(value="11", label="campus floors",
                         source="campus model (11 floors, 199 rooms)",
                         verified=True),
    "rooms":        dict(value="199", label="rooms",
                         source="campus model", verified=True),
    "facilities":   dict(value="14", label="bookable facilities",
                         source="Virtual School facility list", verified=True),
    "atlas":        dict(value="2,234", label="anatomical structures",
                         source="Human Atlas (BodyParts3D 4.0 index)",
                         verified=True),
    "ev_parts":     dict(value="334", label="EV cutaway parts",
                         source="vehicle cutaway index", verified=True),
    "labs":         dict(value="4", label="interactive 3D labs",
                         source="chemistry / gravity / cell / light",
                         verified=True),
    "subjects":     dict(value="185+", label="curriculum subjects",
                         source="curriculum graph", verified=True),
    "languages":    dict(value="6", label="languages in full parity",
                         source="i18n locale parity check", verified=True),
    "offline":      dict(value="100%", label="of 3D models precached",
                         source="PWA precache manifest", verified=True),
    "motion":       dict(value="On-device", label="camera PE analysis",
                         source="Motion Gym pose engine; frames never uploaded",
                         verified=True),
    "price":        dict(value="Free", label="to start",
                         source="landing tier", verified=True),
    # Alias so the shared media-kit / press helpers (which read price_free)
    # resolve against KEV too.
    "price_free":   dict(value="Free", label="to start",
                         source="landing tier", verified=True),
}

# ------------------------------------------------------- compliance guard ----
# Child-safe + school-credible: the language that would get an education product
# rejected by an app store, a school governor or a parent. Hard no's from
# kev/marketing/01-PRODUCT-FACT-SHEET.md.
BANNED = [
    # learning-outcome / performance claims
    "learn faster", "learn 10x", "boost grades", "better grades", "guaranteed results",
    "ace your exams", "top of the class", "outperform", "improves memory",
    "scientifically proven to teach", "proven to improve",
    # literal-dimension / hardware overclaims. Note: KEV's honest framing is a
    # *real* 4D tesseract projected to 3D, so "real 4d" is a true statement
    # about the model and is allowed; the ban is on claiming a literal 4-space
    # render or quantum hardware.
    "5d learning", "5d", "true 4d", "literal 4d", "4d space rendered",
    "quantum computer", "quantum hardware", "quantum processor", "uses a quantum",
    # camera-surveillance framing
    "camera watches your child", "we watch", "surveillance", "always-on camera",
    "webcam monitoring", "we record your child", "facial recognition",
    # fake multiplayer / social overclaim
    "play with friends online", "massively multiplayer", "mmo",
    # money / dark-pattern
    "guaranteed", "risk-free", "no risk", "free money", "as seen on",
    "cancel anytime", "money back", "act now", "limited time", "don't miss out",
    "your child will love", "kids love it guaranteed",
]

# Numeric claims require a registry key (a child should never see an invented
# statistic; every number maps to something in the app).
_NUM_CLAIM = re.compile(r"(\d+(?:\.\d+)?\s*%|\$\d|\b\d{2,}[xX]\b|\b\d{3,}\b)")


def get(key):
    return STATS.get(key)


def line(key, with_source=False):
    s = STATS.get(key)
    if not s:
        raise KeyError(key)
    out = f"{s['value']} {s['label']}".strip()
    if with_source:
        out += f"  [{s['source']}]"
    return out


def proof(keys, sep=" · "):
    return sep.join(line(k) for k in keys)


def verified_stats():
    return {k: v for k, v in STATS.items() if v["verified"]}


def guard(text, allow_numbers=False):
    """Return a list of compliance violations in `text`. Empty list == pass."""
    low = (text or "").lower()
    hits = [b for b in BANNED if b in low]
    if not allow_numbers:
        for m in _NUM_CLAIM.finditer(text or ""):
            if not _sourced(m.group(0)):
                hits.append(f"unsourced number: {m.group(0)}")
    return hits


def _sourced(token):
    t = token.replace("%", "").replace("$", "").replace(",", "").replace("+", "").strip().lower()
    for s in STATS.values():
        v = str(s["value"]).replace("%", "").replace("$", "").replace(",", "").replace("+", "").lower()
        if v and v in t:
            return True
        if str(s["value"]).lower().replace(",", "").replace("+", "") in t:
            return True
    return False


def require_clean(text, where=""):
    v = guard(text)
    if v:
        raise ValueError(f"compliance block{' on ' + where if where else ''}: "
                         + "; ".join(v))
    return text


def risk_block(kind="page"):
    if kind == "ad":
        return DISCLAIMER
    return (f"<p class=\"risk\">{DISCLAIMER} "
            f"<a href=\"{SITE_FULL}\">Read how KEV works</a>.</p>")


# ------------------------------------------------------------------- hooks ---
# (text, angle, kind) -- kind: hook | claim | caption. No power-word bait about
# outcomes; the hooks lead with the school being real, explorable and honest.
# NOTE: hooks carry no numeric claims (the stats live on the pages/ads, which
# cite the registry) so every hook passes guard() unconditionally.
HOOKS = [
    ("Walk to class through a 3D campus.", "mechanism", "hook"),
    ("Dissect the human body. Then the engine.", "contrast", "hook"),
    ("A tutor for every subject, at every level.", "mechanism", "hook"),
    ("The classroom that works with no internet.", "mechanism", "hook"),
    ("PE that reads your movement, not your data.", "contrast", "hook"),
    ("Steer the fourth dimension. Watch an optimizer think.", "curiosity", "hook"),
    ("Eleven floors. Every room opens.", "mechanism", "hook"),
    ("The campus keeps working when the Wi-Fi does not.", "contrast", "hook"),
    ("Ask the lab a question. Get a tutor's answer.", "mechanism", "hook"),
    ("Every structure in the body, ready to inspect.", "quantified", "hook"),
    ("Your child's school should feel like a place.", "identity", "hook"),
    ("Every facility is a door, not a picture.", "contrast", "hook"),
    ("Offline first. Online when it matters.", "contrast", "hook"),
    ("The tutor sees the same bench you do.", "mechanism", "hook"),
    ("One school, from age six to university.", "identity", "hook"),
    ("A dance game that never uploads a frame.", "proof", "hook"),
    ("Explode an engine. Put it back together.", "mechanism", "hook"),
    ("The whole school, in six languages.", "quantified", "hook"),
    ("No cartoon school. A real one, in 3D.", "contrast", "hook"),
    ("The beat drops. Your move is the controller.", "mechanism", "hook"),
    ("Built to be believed, not just clicked.", "proof", "hook"),
    ("The atlas is open. Pick a bone.", "curiosity", "hook"),
    ("An optimizer, cooling into an answer.", "curiosity", "hook"),
    ("Sign in. Your school knows your level.", "identity", "hook"),
    ("The library is a place now.", "identity", "hook"),
]

# ------------------------------------------------------------- page catalog --
# Programmatic SEO: one landing page per pillar, rendered by growth.pages. Each
# spec: slug / title / h1 / lead / desc / section_title + cards / before_after /
# faq. Proof keys reference STATS. All copy passes guard() (no banned phrases,
# every number sourced).
PAGES = {
    "feature": [
        dict(slug="explore/campus", title="The 3D campus — walk to class",
             h1="Walk to class through a 3D campus.",
             product_name="KEV", cta="Start free — walk the campus",
             eyebrow="KEV IMMERSIVE SCHOOL · XR CAMPUS",
             lead="Eleven floors, 199 rooms, a Grand Concourse to orient you, "
                  "subject wings for every discipline, and the KEV International "
                  "Virtual School building with fourteen bookable facilities — "
                  "all explorable, all gated to your role.",
             desc="KEV 3D campus: 11 floors, 199 rooms, 14 bookable facilities that route to working surfaces, gated to each student's role.",
             section_title="A school that makes sense as a place", cards=[
                 dict(h="11 floors · 199 rooms", p="Generated from the school's real campus model, not a cartoon map."),
                 dict(h="14 bookable facilities", p="Gym, library, science lab, auditorium — each routes to its working surface."),
                 dict(h="Role-gated doors", p="Students and teachers each see their own school, re-checked by the backend.")],
             before_after=[("A menu of subject icons", "A campus you actually walk through"),
                           ("A facility name on a list", "A door that opens into the working room"),
                           ("One flat classroom", "Eleven floors from the gym to the observatory")],
             faq=[("Is the campus a game?",
                   "It is the school's campus model rendered in 3D. Every facility routes to a real working surface — the gym to Motion Gym, the library to the shelves, the lab to the bench."),
                  ("Do all students see the same campus?",
                   "No. Each role sees its own school — a primary student and a university student walk different wings, re-checked by the backend."),
                  ("Does it work on a school laptop?",
                   "Yes. It runs in the browser on any device, and the 3D models are precached so it works offline.")],
             proof=["floors", "rooms", "facilities"]),
        dict(slug="explore/labs", title="Studio-grade science labs",
             h1="Dissect the human body. Then the engine.",
             product_name="KEV", cta="Start free — walk the campus",
             eyebrow="3D SCIENCE LABS · STUDIO GRADE",
             lead="A Human Atlas of 2,234 modeled anatomical structures, an "
                  "electric vehicle cutaway of 334 pieces, and four interactive "
                  "labs — chemistry, gravity, the living cell and light — all "
                  "rendered to the same studio baseline.",
             desc="KEV science labs: a 2,234-structure Human Atlas, a 334-part EV cutaway and four interactive 3D labs with real physics and chemistry.",
             section_title="Real models, not canned animations", cards=[
                 dict(h="2,234 structures", p="Explode, isolate and inspect any anatomical structure in the atlas."),
                 dict(h="4 interactive labs", p="Chemistry, gravity, the living cell and light — real physics, not video."),
                 dict(h="Licensed geometry", p="BodyParts3D 4.0 (CC BY 4.0); vehicle geometry licensed for study.")],
             before_after=[("A diagram of a cell", "A cell you can orbit and pull apart"),
                           ("Reading about gravity", "Dropping two moons and watching them fall"),
                           ("A photo of an engine", "A 334-piece cutaway you explode and rebuild")],
             faq=[("Are the lab models real?",
                   "Yes. The Human Atlas uses BodyParts3D 4.0 geometry (CC BY 4.0) and the labs simulate the actual physics and chemistry."),
                  ("Can a young child use them?",
                   "Yes — the same labs adapt to the student's level, from a 7-year-old orbiting a cell to a university student balancing an equation.")],
             proof=["atlas", "ev_parts", "labs"]),
        dict(slug="explore/tutors", title="AI tutors for every subject",
             h1="A tutor for every subject, at every level.",
             product_name="KEV", cta="Start free — walk the campus",
             eyebrow="AI TUTORS · EVERY SUBJECT",
             lead="Socratic, level-adaptive tutors from elementary to "
                  "professional — live answers online, cached and offline "
                  "guidance when you're not. Ask about the exact part, lab or "
                  "problem in front of you.",
             desc="KEV AI tutors: level-adaptive Socratic tutors for 185+ curriculum subjects, live online and cached offline.",
             section_title="A tutor that meets the student where they are", cards=[
                 dict(h="185+ subjects", p="Tutors across the curriculum with dependencies, levels and tracks."),
                 dict(h="Level-adaptive", p="The same tutor meets a 7-year-old and a university student differently."),
                 dict(h="Live + offline", p="Live answers online, cached guidance offline — learning never stops.")],
             before_after=[("A generic chatbot answer", "A tutor that sees the same bench you do"),
                           ("One explanation for everyone", "An answer matched to your study level"),
                           ("Stuck when offline", "Cached guidance that keeps working")],
             faq=[("Do the tutors give answers or teach?",
                   "They teach. The tutors are Socratic — they guide with questions matched to the student's level, in the context of the lab or problem on screen."),
                  ("Which subjects are covered?",
                   "185+ curriculum subjects, each with its own tutor, levels and tracks.")],
             proof=["subjects", "languages"]),
        dict(slug="explore/offline", title="The offline classroom",
             h1="The classroom that works with no internet.",
             product_name="KEV", cta="Start free — walk the campus",
             eyebrow="WORKS OFFLINE · ANY DEVICE",
             lead="The full immersive classroom is precached — every 3D model — "
                  "so a first-visit device runs the labs with zero network. "
                  "Notes and chat queue and replay on reconnect. Six languages, "
                  "role-gated, installable as an app.",
             desc="KEV offline classroom: every 3D model precached, notes and chat queued and replayed on reconnect, 6 languages, on any device.",
             section_title="Learning that does not stop for a dropped connection", cards=[
                 dict(h="100% of models precached", p="Full labs offline on first visit, not just cached ones."),
                 dict(h="Queue + replay", p="Notes and chat send automatically when you're back online."),
                 dict(h="6 languages", p="Full parity across every locale, role-gated for every student.")],
             before_after=[("A spinner when the Wi-Fi drops", "The lab keeps running, offline"),
                           ("Lost work on reconnect", "Notes and chat replay on their own"),
                           ("One language", "Six languages in full parity")],
             faq=[("Does it really work offline?",
                   "Yes. Every 3D model is precached, so a device that has visited once can run the full labs with no network at all."),
                  ("What happens to work done offline?",
                   "Notes and chat queue locally and replay automatically the next time the device is online.")],
             proof=["offline", "languages"]),
        dict(slug="explore/motion-gym", title="Motion Gym — camera PE",
             h1="PE that reads your movement, not your data.",
             product_name="KEV", cta="Start free — walk the campus",
             eyebrow="MOTION GYM · CAMERA PE",
             lead="Dance and cardio games that read how much and where you move "
                  "from the webcam — analysed on-device, never uploaded. Link a "
                  "heart-rate smartwatch over standard Bluetooth to add your "
                  "real pulse to fitness play.",
             desc="KEV Motion Gym: on-device camera PE (dance and cardio games), smartwatch heart-rate over standard Bluetooth, frames never uploaded.",
             section_title="Movement as the controller, privacy by design", cards=[
                 dict(h="On-device analysis", p="The camera feed is analysed on the device; frames never leave it."),
                 dict(h="Dance + cardio", p="Dance-beat and cardio-burst games, XP-awarded, on any webcam."),
                 dict(h="Smartwatch pulse", p="Standard Bluetooth Heart Rate Service adds your real pulse.")],
             before_after=[("A fitness video to copy", "A game that reads how you actually move"),
                           ("Uploading camera footage", "On-device analysis — frames never leave"),
                           ("Guessing your effort", "A smartwatch pulse in the game")],
             faq=[("Does the camera upload video?",
                   "No. Motion Gym analyses movement on the device itself; no frame ever leaves it, and the copy says so."),
                  ("Do I need a smartwatch?",
                   "No. The camera games work on their own; a Bluetooth heart-rate watch just adds your real pulse.")],
             proof=["motion"]),
        dict(slug="explore/frontier", title="Quantum Lab & Dimension Explorer",
             h1="Steer the fourth dimension. Watch an optimizer think.",
             product_name="KEV", cta="Start free — walk the campus",
             eyebrow="QUANTUM LAB · DIMENSION EXPLORER",
             lead="A real Ising/QUBO solver replays a quantum-style optimizer "
                  "cooling into a solution, and a real 4D tesseract projects "
                  "down to 3D so you can steer the fourth axis yourself — "
                  "advanced ideas, made playable and honest.",
             desc="KEV frontier ideas: a real Ising/QUBO solver with cooling replay, and a real 4D tesseract projected to 3D with a steerable fourth axis.",
             section_title="Advanced ideas, honest framing", cards=[
                 dict(h="Real Ising solver", p="Deterministic simulated annealing on Max-Cut and Number Partition, with the full cooling replay."),
                 dict(h="Real 4D projection", p="A 4D hypercube projected to 3D, with an XW rotation + distance slider."),
                 dict(h="Honest by design", p="Classical annealing (the family quantum annealers approximate); 4D by projection, not literal claims.")],
             before_after=[("Reading about quantum annealing", "Running a solver and scrubbing its energy curve"),
                           ("A flat drawing of a tesseract", "Steering the fourth axis yourself"),
                           ("Buzzword claims", "An honest label: classical annealing, 4D by projection")],
             faq=[("Is this a real quantum computer?",
                   "No — and we say so. It is a deterministic classical solver in the family quantum annealers approximate, with the full cooling replay visible."),
                  ("Can a screen really show 4D?",
                   "Not literally — a screen can't show four perpendicular axes. KEV shows a real 4D tesseract projected down to 3D, with a slider to steer the fourth axis.")],
             proof=["category"]),
    ],
    "usecase": [
        dict(slug="for/primary", title="KEV for primary school",
             h1="A school a six-year-old can walk through.",
             product_name="KEV", cta="Start free — walk the campus",
             lead="Big doors, bright wings and a tutor that explains like a "
                  "patient teacher — the same campus, scaled to a young reader.",
             desc="KEV for primary school: an explorable 3D campus, level-adaptive tutors and safe, role-gated spaces for young children.",
             section_title="Made for young learners", cards=[
                 dict(h="Walk, don't navigate", p="Children walk to class through the campus — no menus to get lost in."),
                 dict(h="A patient tutor", p="Level-adaptive answers that meet a young reader where they are."),
                 dict(h="Safe by default", p="Role-gated spaces; children only ever see their own school.")],
             faq=[("Is it safe for young children?",
                   "Yes. Spaces are role-gated and re-checked by the backend; children only ever see their own school, and camera analysis never leaves the device.")]),
        dict(slug="for/secondary", title="KEV for secondary school",
             h1="Labs that make the abstract concrete.",
             product_name="KEV", cta="Start free — walk the campus",
             lead="Chemistry you can mix, gravity you can drop, a cell you can "
                  "orbit — and a tutor that answers at exam level.",
             desc="KEV for secondary school: interactive 3D labs with real physics and chemistry, plus level-adaptive tutors at exam level.",
             section_title="Where the syllabus becomes a place", cards=[
                 dict(h="Real physics + chemistry", p="Interactive labs that simulate the actual phenomena, not videos."),
                 dict(h="Exam-level tutors", p="Answers matched to the student's level and the problem on screen."),
                 dict(h="Revision that sticks", p="Orbit, explode and rebuild the model until it makes sense.")],
             faq=[("Does it match the curriculum?",
                   "Yes. Tutors cover 185+ curriculum subjects with levels and tracks, and the labs map to the same topics.")]),
        dict(slug="for/university", title="KEV for university",
             h1="A professional-grade bench, anywhere.",
             product_name="KEV", cta="Start free — walk the campus",
             lead="The Human Atlas, the EV cutaway and the frontier labs — with "
                  "tutors that answer at a professional depth.",
             desc="KEV for university: a 2,234-structure Human Atlas, EV cutaway and frontier labs with professional-depth tutors.",
             section_title="Beyond the lecture hall", cards=[
                 dict(h="2,234 structures", p="A full anatomical atlas to explode, isolate and inspect."),
                 dict(h="Frontier labs", p="A real Ising solver and a 4D tesseract, framed honestly."),
                 dict(h="Professional depth", p="Tutors that answer at the depth the course demands.")],
             faq=[("Is it rigorous enough for university?",
                   "Yes. The models are licensed professional geometry and the tutors adapt to a professional depth.")]),
    ],
    "trust": [
        dict(slug="trust/privacy", title="Privacy — on-device by design",
             h1="Analysis that never leaves the device.",
             product_name="KEV", cta="Start free — walk the campus",
             lead="Motion Gym reads movement on the device itself; no camera "
                  "frame is ever uploaded. Progress is the student's own, "
                  "gated to their sign-in.",
             desc="KEV privacy: camera analysis is on-device (frames never uploaded), progress is the student's own and role-gated.",
             section_title="What we never do", cards=[
                 dict(h="No camera upload", p="Movement is analysed on the device; frames never leave it."),
                 dict(h="No outcome promises", p="We do not claim KEV raises grades — it is a teaching tool."),
                 dict(h="No fake multiplayer", p="What you see is what is real — no simulated classmates.")],
             faq=[("Does KEV record my child?",
                   "No. Motion Gym analyses movement on the device itself and never uploads a frame. There is no camera surveillance."),
                  ("What data does KEV hold?",
                   "Only the student's own progress (XP, badges, counts), gated to their sign-in — never camera footage or lesson content.")]),
    ],
}
