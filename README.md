# Site des sources, Béton & Capital

Site statique publié par GitHub Pages : une page d'accueil et une page de
sources par épisode. Aucun script, aucun traceur, aucune publicité, aucune
dépendance distante. Les seules ressources chargées par une page sont sa
feuille de style et le logo, servis par ce dépôt.

## Ce que contient le dépôt

    index.html                 accueil
    style.css                  charte de la chaîne (couleurs de charte/palette.txt)
    logo.svg                   logo de la charte, métadonnées retirées
    sources/                   markdown d'origine, tel que livré par l'agent
    ep01/sources/index.html    page de l'épisode 1, générée depuis le markdown
    outils/construire.py       la conversion markdown vers page

Ce dépôt ne contient ni photo, ni rush, ni script du projet vidéo.

## Ajouter un épisode

    python outils/construire.py sources/BC_EP02_sources_et_methode.md ep02/sources

puis ajouter l'épisode à la liste dans `index.html`.

La conversion refuse un texte qui contient un tiret cadratin ou demi-cadratin,
conformément à la charte. Elle écarte aussi les consignes de fabrication que
l'agent laisse dans le markdown, comme l'adresse prévue de la page.

## Adresses

    https://betoncapital.github.io/            accueil
    https://betoncapital.github.io/ep01/sources/   épisode 1

Contact : betoncapital.contact@gmail.com
