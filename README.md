# Site des sources, Béton & Capital

Site statique destiné à https://betoncapital.github.io/ (GitHub Pages, branche main, racine).
Aucun script, aucun traceur, aucune publicité, aucune ressource distante : une page charge
seulement `style.css` et `logo.svg`. Chaque page est bilingue FR/EN (sections `#fr` et `#en`).

    index.html                  accueil (chaîne, contact, inscription Kit)
    ep01/sources/index.html     Nachtigal, sources et méthode
    sources/                    markdown d'origine (EP01 : archive EP01_final, FR et traduction EN)
    episodes.json               catalogue des épisodes (titres, résumés, page)
    site.json                   kit_url (vide : bloc omis) ; episodes_en_ligne : les épisodes publiés
    outils/construire.py        fabrique toutes les pages : python outils/construire.py

La conversion refuse un tiret cadratin ou demi-cadratin, un crochet de gabarit non résolu,
et écarte les consignes de fabrication laissées dans le markdown.

Contact : betoncapital.contact@gmail.com
