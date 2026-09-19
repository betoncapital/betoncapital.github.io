#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
construire.py : fabrique tout le site (accueil et pages Sources et méthode).

Usage, depuis la racine du dépôt :
    python outils/construire.py

Le site est statique : la conversion se fait ici, et c'est du HTML déjà fabriqué
qui part dans le dépôt. Aucune page ne charge de script, ni local ni distant, et
aucune ressource extérieure : seuls style.css et logo.svg sont servis.

Chaque page est bilingue : une section française (#fr), une section anglaise
(#en), et au besoin une section commune (#sources) pour ce qui est déjà écrit
dans les deux langues (listes de sources).

Règles appliquées à la conversion :
  - aucun tiret cadratin ni demi-cadratin : la conversion échoue s'il y en a ;
  - les consignes de fabrication laissées par l'agent dans le markdown
    (adresse prévue, rappel de style, signature de fin) ne partent pas en ligne ;
  - un crochet de gabarit « [ ... ] » non résolu fait échouer la conversion,
    sauf les mentions de suivi que la page assume (voir SUIVI) ;
  - le lien d'inscription Kit vient de site.json ; vide, le bloc est omis.

Markdown reconnu : titres # à ###, listes à tirets avec lignes de continuation,
règles ---, gras **texte**, italique *texte*, adresses http(s) et courriels.
"""

import html
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CADRATINS = {"—": "tiret cadratin", "–": "tiret demi-cadratin"}

MENTIONS_INTERNES = (
    re.compile(r"^Adresse pr[ée]vue\s*:"),
    re.compile(r"^Aucun tiret cadratin"),
    re.compile(r"^\*?B[ée]ton (&|et) Capital (est une publication|is published)"),
)

# Crochet assumé par la page : le suivi daté du résultat de l'offre (épisode 2).
SUIVI = re.compile(r"^\[(R[ée]sultat de l'offre[^\]]*)\]$")


def verifie_tirets(texte, origine):
    for c, nom in CADRATINS.items():
        if c in texte:
            ligne = texte[:texte.index(c)].count("\n") + 1
            raise SystemExit("%s : %s ligne %d, interdit par la charte"
                             % (origine, nom, ligne))


def en_ligne(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\*\w])\*([^\*]+?)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"(?<!\")(https?://[^\s<)]+[^\s<).,])",
               r'<a href="\1">\1</a>', t)
    t = re.sub(r"(?<![\w@.])([\w.+-]+@[\w-]+\.[\w.]+)",
               r'<a href="mailto:\1">\1</a>', t)
    return t


def convertit(md, origine):
    """Markdown -> (titre, sous_titre, corps HTML)."""
    lignes = md.replace("\r\n", "\n").split("\n")
    titre, sous_titre, corps = None, None, []
    paragraphe, liste, item = [], [], []

    def ferme_paragraphe():
        if paragraphe:
            corps.append("<p>%s</p>" % en_ligne(" ".join(paragraphe).strip()))
            paragraphe.clear()

    def ferme_item():
        if item:
            liste.append("<li>%s</li>" % en_ligne(" ".join(item).strip()))
            item.clear()

    def ferme_liste():
        ferme_item()
        if liste:
            corps.append("<ul>\n%s\n</ul>" % "\n".join(liste))
            liste.clear()

    for ligne in lignes:
        nu = ligne.strip()
        if not nu:
            ferme_paragraphe(); ferme_item()
            continue
        if any(m.match(nu) for m in MENTIONS_INTERNES):
            ferme_paragraphe(); ferme_item()
            continue
        suivi = SUIVI.match(nu)
        if suivi:
            ferme_paragraphe(); ferme_liste()
            corps.append("<p><em>%s</em></p>" % html.escape(suivi.group(1), quote=False))
            continue
        if re.search(r"\[[^\]]*(COMPL[ÉE]TER|TODO|XXX)[^\]]*\]", nu, re.I):
            raise SystemExit("%s : crochet de gabarit non résolu : %s" % (origine, nu))
        if nu.startswith("### "):
            ferme_paragraphe(); ferme_liste()
            corps.append("<h3>%s</h3>" % en_ligne(nu[4:]))
        elif nu.startswith("## "):
            ferme_paragraphe(); ferme_liste()
            corps.append("<h2>%s</h2>" % en_ligne(nu[3:]))
        elif nu.startswith("# "):
            ferme_paragraphe(); ferme_liste()
            if titre is None:
                titre = nu[2:].strip()
            elif sous_titre is None:
                sous_titre = nu[2:].strip()
            else:
                corps.append("<h2>%s</h2>" % en_ligne(nu[2:]))
        elif set(nu) == {"-"} and len(nu) >= 3:
            ferme_paragraphe(); ferme_liste()
            corps.append("<hr>")
        elif nu.startswith("- "):
            ferme_paragraphe(); ferme_item()
            item.append(nu[2:])
        elif item:
            item.append(nu)
        else:
            ferme_liste()
            paragraphe.append(nu)
    ferme_paragraphe(); ferme_liste()
    return titre, sous_titre, corps


def blocs(md, origine):
    """Découpe un markdown en (titre, sous_titre, préambule, [(intitulé, html)])."""
    titre, sous_titre, corps = convertit(md, origine)
    preambule, sections, courant = [], [], None
    for c in corps:
        if c == "<hr>":
            continue
        m = re.match(r"<h2>(.*)</h2>$", c)
        if m:
            courant = (m.group(1), [c])
            sections.append(courant)
        elif courant is None:
            preambule.append(c)
        else:
            courant[1].append(c)
    return titre, sous_titre, preambule, [(t, "\n".join(h)) for t, h in sections]


def lit(chemin):
    md = open(os.path.join(RACINE, chemin), encoding="utf-8").read()
    verifie_tirets(md, chemin)
    return md


def entete(racine, lang="fr"):
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre}</title>
<meta name="description" content="{description}">
<link rel="stylesheet" href="{racine}style.css">
<link rel="icon" href="{racine}logo.svg" type="image/svg+xml">
</head>
<body>
<div class="page">
<header class="marque">
<a href="{racine}"><img src="{racine}logo.svg" alt="Béton &amp; Capital"></a>
<div class="barre"></div>
</header>
<main>
"""


PIED = """</main>
<footer>
<p lang="fr">Béton &amp; Capital, une publication de Sanaga Land International LLC.
Contact : <a href="mailto:betoncapital.contact@gmail.com">betoncapital.contact@gmail.com</a></p>
<p lang="en">Béton &amp; Capital is published by Sanaga Land International LLC.
Contact: <a href="mailto:betoncapital.contact@gmail.com">betoncapital.contact@gmail.com</a></p>
<p><a href="{racine}">Accueil · Home</a></p>
</footer>
</div>
</body>
</html>
"""


KIT = ""     # lien d'inscription Kit, lu dans site.json par main()


def inscription(fr):
    """Bloc d'inscription, en fin de chaque section de langue ; omis si le lien est vide."""
    if not KIT:
        return ""
    if fr:
        return ('<h2>Recevoir les prochains épisodes</h2>\n'
                '<p><a href="%s">S\'inscrire à la lettre de la chaîne</a></p>' % html.escape(KIT))
    return ('<h2>Get the next episodes</h2>\n'
            '<p><a href="%s">Subscribe to the channel newsletter</a></p>' % html.escape(KIT))


def navigation(commune):
    liens = '<a href="#fr">Français</a> <a href="#en">English</a>'
    if commune:
        liens += ' <a href="#sources">Sources · Sources</a>'
    return '<nav class="langues" aria-label="Langue · Language">%s</nav>' % liens


def assemble(racine, titre_page, description, fr, en, commune="", notice=""):
    """fr et en : (titre, sous_titre, html)."""
    h = entete(racine).format(titre=html.escape(titre_page),
                              description=html.escape(description), racine=racine)
    h += '<h1 lang="fr">%s</h1>\n' % html.escape(fr[0])
    h += '<p class="titre-en" lang="en">%s</p>\n' % html.escape(en[0])
    h += navigation(bool(commune)) + "\n"
    if notice:
        h += '<div class="notice">\n%s\n</div>\n' % notice
    for lang, (t, st, corps) in (("fr", fr), ("en", en)):
        h += '<section id="%s" lang="%s">\n' % (lang, lang)
        if st:
            h += '<p class="sous-titre">%s</p>\n' % html.escape(st)
        h += corps + "\n" + inscription(lang == "fr") + "\n</section>\n"
    if commune:
        h += '<section id="sources">\n%s\n</section>\n' % commune
    h += PIED.format(racine=racine)
    verifie_tirets(h, "page produite")
    return h


def ecrit(dossier, contenu):
    cible = os.path.join(RACINE, dossier, "index.html")
    os.makedirs(os.path.dirname(cible), exist_ok=True)
    open(cible, "w", encoding="utf-8", newline="\n").write(contenu)
    print("%s (%d octets)" % (os.path.relpath(cible, RACINE), len(contenu.encode("utf-8"))))


def page_deux_fichiers(p):
    """Épisode dont la page existe en deux fichiers, un par langue.
    Si le fichier anglais n'est pas publié (traduction en relecture), la page
    porte le titre anglais et une mention en section #en."""
    t1, s1, p1, b1 = blocs(lit(p["fr"]), p["fr"])
    if os.path.exists(os.path.join(RACINE, p["en"])):
        t2, s2, p2, b2 = blocs(lit(p["en"]), p["en"])
    else:
        t2, s2, p2, b2 = p["titre_en"], "Sources and method", [
            "<p>%s</p>" % html.escape(p["attente_en"])], []
    corps = lambda pre, b: "\n".join(pre + [h for _, h in b])
    dossier = p["dossier"]
    racine = "../" * (dossier.strip("/").count("/") + 1)
    ecrit(dossier, assemble(
        racine, "%s · %s" % (t1, t2), p["description"],
        (t1, s1, corps(p1, b1)), (t2, s2, corps(p2, b2))))


def page_bilingue(p):
    """Épisode dont la page tient en un fichier : sections FR, EN et mixtes."""
    md_chemin, titres_fr, titres_en = p["md"], p["titres_fr"], p["titres_en"]
    t, st, pre, secs = blocs(lit(md_chemin), md_chemin)
    tf, te = [x.strip() for x in t.split(" · ")]
    sf, se = [x.strip() for x in st.split(" · ")]
    fr = [h for i, h in secs if i in titres_fr]
    en = [h for i, h in secs if i in titres_en]
    commune = [h for i, h in secs if i not in titres_fr and i not in titres_en]
    for i in list(titres_fr) + list(titres_en):
        if i not in [x for x, _ in secs]:
            raise SystemExit("%s : section attendue introuvable : %s" % (md_chemin, i))
    if not commune or not fr or not en:
        raise SystemExit("%s : découpage FR/EN incomplet" % md_chemin)
    dossier = p["dossier"]
    racine = "../" * (dossier.strip("/").count("/") + 1)
    ecrit(dossier, assemble(
        racine, "%s · %s" % (tf, te), p["description"],
        (tf, sf, "\n".join(fr)), (te, se, "\n".join(en)),
        commune="\n".join(commune),
        notice="\n".join(pre + ["<p>%s</p>" % p["mention"]])))


def episode_li(e, fr):
    l = "fr" if fr else "en"
    note = "" if fr else e.get("note_en", "")
    return ('<li>\n<div class="numero">%s</div>\n<div class="titre">%s</div>\n'
            '<p>%s\n<a href="%s">%s</a>%s</p>\n</li>'
            % (e["numero_" + l], e["titre_" + l], e["resume_" + l], e["lien_" + l],
               "Sources et méthode" if fr else "Sources and method", note))


def accueil(config, episodes):
    kit = KIT

    liste_fr = "\n".join(episode_li(e, True) for e in episodes)
    liste_en = "\n".join(episode_li(e, False) for e in episodes)

    fr = """<p class="chapo">Ce site porte les sources de chaque épisode : d'où vient chaque chiffre,
comment il a été vérifié, et ce que l'épisode ne dit pas.</p>

<h2>Épisodes</h2>
<ul class="episodes">
@@LISTE@@
</ul>

<h2>Notre règle</h2>
<p>Les chiffres viennent de sources publiques, et autant que possible de sources
primaires. Quand une source primaire et une source de presse se contredisent,
nous retenons la source primaire. Quand nous nous trompons, nous corrigeons sur
la page de l'épisode, en datant la correction, sans effacer la version d'origine.</p>

@@KIT@@

<h2>Nous corriger, nous écrire</h2>
<p>Si un chiffre est faux, écrivez-nous :
<a href="mailto:betoncapital.contact@gmail.com">betoncapital.contact@gmail.com</a></p>""".replace(
        "@@LISTE@@", liste_fr).replace("@@KIT@@", inscription(True))

    en = """<p class="chapo">This site carries the sources for each episode: where every figure
comes from, how it was checked, and what the episode does not say.</p>

<h2>Episodes</h2>
<ul class="episodes">
@@LISTE@@
</ul>

<h2>Our rule</h2>
<p>Figures come from public sources, and as far as possible from primary ones.
When a primary source and a press source contradict each other, we keep the
primary source. When we get something wrong, we correct it on the episode's
page, dating the correction, without erasing the original version.</p>

@@KIT@@

<h2>Correct us, write to us</h2>
<p>If a figure is wrong, write to us:
<a href="mailto:betoncapital.contact@gmail.com">betoncapital.contact@gmail.com</a></p>""".replace(
        "@@LISTE@@", liste_en).replace("@@KIT@@", inscription(False))

    titre_fr = "Comment se construisent et se financent les grandes infrastructures en Afrique"
    titre_en = "How Africa's major infrastructure is built and financed"
    h = entete("").format(titre="Béton &amp; Capital", racine="",
                          description="Comment se construisent et se financent les grandes "
                                      "infrastructures en Afrique. Sources et méthode de chaque épisode. "
                                      "How Africa's major infrastructure is built and financed.")
    h += '<h1 lang="fr">%s</h1>\n<p class="titre-en" lang="en">%s</p>\n' % (titre_fr, titre_en)
    h += navigation(False) + "\n"
    h += '<section id="fr" lang="fr">\n%s\n</section>\n<section id="en" lang="en">\n%s\n</section>\n' % (fr, en)
    h += PIED.format(racine="")
    verifie_tirets(h, "accueil")
    open(os.path.join(RACINE, "index.html"), "w", encoding="utf-8", newline="\n").write(h)
    print("index.html (%d octets)" % len(h.encode("utf-8")))
    if not kit:
        print("AVERTISSEMENT : kit_url vide dans site.json, bloc d'inscription omis.")


def main():
    """Les épisodes vivent dans episodes.json ; seuls ceux de episodes_en_ligne
    (site.json) sont fabriqués et listés. Un épisode absent de episodes.json
    ou de la liste n'existe pas dans le dépôt."""
    global KIT
    config = json.load(open(os.path.join(RACINE, "site.json"), encoding="utf-8"))
    KIT = (config.get("kit_url") or "").strip()
    if KIT and not KIT.startswith("https://"):
        raise SystemExit("site.json : kit_url doit commencer par https://")
    catalogue = json.load(open(os.path.join(RACINE, "episodes.json"), encoding="utf-8"))
    publies = config.get("episodes_en_ligne", [])
    inconnus = [i for i in publies if i not in catalogue]
    if inconnus:
        raise SystemExit("site.json : épisode absent de episodes.json : %s" % inconnus)
    episodes = [catalogue[i] for i in publies]
    accueil(config, episodes)
    for e in episodes:
        p = e["page"]
        (page_deux_fichiers if p["mode"] == "deux_fichiers" else page_bilingue)(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
