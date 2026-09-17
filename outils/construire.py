#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
construire.py — fabrique une page du site a partir d'un markdown de l'agent.

Usage :
    python outils/construire.py sources/BC_EP01_sources_et_methode.md ep01/sources

Le site est statique : cette conversion se fait ici, sur la machine, et c'est
du HTML deja fabrique qui part dans le depot. Aucune page ne charge de script,
ni local ni distant.

Regles de la chaine appliquees a la conversion :
  - aucun tiret cadratin ni demi-cadratin : la conversion echoue s'il y en a ;
  - aucune image du projet video : seul le logo de la charte est utilise ;
  - les adresses ecrites en clair dans le markdown deviennent des liens, et le
    texte du lien reste l'adresse, pour qu'une page imprimee reste lisible.

Markdown reconnu : titres # a ###, listes a tirets avec lignes de continuation,
regles horizontales ---, gras **texte**, italique *texte*, adresses http(s).
"""

import html
import os
import re
import sys

CADRATINS = {"—": "tiret cadratin", "–": "tiret demi-cadratin"}

# Consignes de fabrication laissees dans le markdown par l'agent : elles
# s'adressent a nous, pas au lecteur, et ne partent donc pas en ligne.
MENTIONS_INTERNES = (
    re.compile(r"^Adresse pr[ée]vue\s*:"),
    re.compile(r"^Aucun tiret cadratin"),
)

MODELE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre_page}</title>
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
{corps}
</main>
<footer>
<p>Béton &amp; Capital, une publication de Sanaga Land International LLC.
Contact : <a href="mailto:betoncapital.contact@gmail.com">betoncapital.contact@gmail.com</a></p>
<p><a href="{racine}">Accueil</a></p>
</footer>
</div>
</body>
</html>
"""


def verifie_tirets(texte, origine):
    for c, nom in CADRATINS.items():
        if c in texte:
            ligne = texte[:texte.index(c)].count("\n") + 1
            raise SystemExit("%s : %s ligne %d, interdit par la charte"
                             % (origine, nom, ligne))


def en_ligne(t):
    """Gras, italique, adresses. Le texte est echappe avant toute balise."""
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\*\w])\*([^\*]+?)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"(?<!\")(https?://[^\s<)]+[^\s<).,])",
               r'<a href="\1">\1</a>', t)
    t = re.sub(r"(?<![\w@.])([\w.+-]+@[\w-]+\.[\w.]+)",
               r'<a href="mailto:\1">\1</a>', t)
    return t


def convertit(md):
    """Markdown -> corps HTML. Renvoie (titre, sous-titre, corps)."""
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
            ferme_paragraphe()
            ferme_item()
            continue
        if any(m.match(nu) for m in MENTIONS_INTERNES):
            ferme_paragraphe()
            ferme_item()
            continue
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
            ferme_paragraphe()
            ferme_item()
            item.append(nu[2:])
        elif item:
            item.append(nu)          # ligne de continuation d'un item
        else:
            ferme_liste()
            paragraphe.append(nu)
    ferme_paragraphe(); ferme_liste()
    return titre, sous_titre, "\n".join(corps)


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__.strip())
    source, dossier = argv
    md = open(source, encoding="utf-8").read()
    verifie_tirets(md, source)
    titre, sous_titre, corps = convertit(md)
    entete = "<h1>%s</h1>" % html.escape(titre or "Béton & Capital")
    if sous_titre:
        entete += '\n<p class="sous-titre">%s</p>' % html.escape(sous_titre)
    racine = "../" * (dossier.strip("/").count("/") + 1)
    page = MODELE.format(
        titre_page=html.escape("%s : %s" % (titre, sous_titre) if sous_titre else titre),
        description=html.escape("Sources et méthode de l'épisode, Béton & Capital."),
        racine=racine, corps=entete + "\n" + corps)
    verifie_tirets(page, "page produite")
    os.makedirs(dossier, exist_ok=True)
    cible = os.path.join(dossier, "index.html")
    open(cible, "w", encoding="utf-8", newline="\n").write(page)
    print("%s -> %s (%d octets)" % (source, cible, len(page.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
