ranger 2.1.4-1
============

<img src="https://ranger.github.io/ranger_logo.png" width="150">

[![Build Status](https://travis-ci.org/ranger/ranger.svg?branch=master)](https://travis-ci.org/ranger/ranger)
<a href="https://repology.org/metapackage/ranger/versions">
  <img src="https://repology.org/badge/latest-versions/ranger.svg" alt="latest packaged version(s)">
</a>

Ranger ces notes
----------------

ranger est un programme de prise de code de console avec liaisons de clés VI.
Il fournit un interface minimaliste et agréable de curses avec une vue sur tes
zettel. Il est livré avec `rifle`, un lanceur de fichiers qui est bon pour
trouver automatiquement d'utiliser quel programme pour modifier tes zettel.
C'est le moyen idéal pour gérer ton zettelkasten.

![capture d'écran](https://raw.githubusercontent.com/toonn/ranger/farnear/capturedecran.png)

Ce fichier décrit ranger et comment le faire fonctionner. Pour des instructions
sur l'utilisation, veuillez lire la page de man (`man ranger` dans un
terminal). Voir `HACKING.md` pour des informations spécifiques au
développement. 

Pour la configuration, vérifiez les fichiers dans `ranger/config/` ou copiez
la configuration par défaut à `~/.config/ranger` avec `ranger --copy-config` (Voir [Instructions](#getting-started)). 

Le répertoire `examples/` contient plusieurs scripts et plugins qui démontrent comment ranger peut être étendu ou combiné avec d'autres programmes. Ces fichiers peuvent être trouvé dans le référentiel git ou dans `/usr/share/doc/ranger`. 

Une note aux emballeurs: les versions destinées aux emballages sont
répertoriées dans le changelog  sur le site Internet. 


Au sujet de
-----
* Auteurs:          vois fichier `AUTHORS`
* Licence:          Licence Général Publique de GNU Version 3
* Site Internet:    https://ranger.github.io/
* Télécharger:      https://ranger.github.io/ranger-stable.tar.gz
* Rapports de bugs: https://github.com/ranger/ranger/issues
* git clone         https://github.com/ranger/ranger.git


Buts de conception
------------------
* Un programme de prise de notes facilement maintenu dans une langue de haut
  niveau
* Un moyen rapide de basculer et de parcourir tes zettel
* Gardez-le petit mais utile, fait une chose et fait-le bien
* Basé sur la console, avec une intégration lisse dans la coque UNIX 

Fonctionnalités
---------------
* Support UTF-8 (si votre copie Python prend en charge)
* Aperçu du fichier / répertoire sélectionné
* Opérations de fichier communes (créer/copier/supprimer/...)
* Renommer plusieurs fichiers à la fois
* Console et liaisons de type Vim
* Déterminer automatiquement les types de fichiers et les exécuter avec des
  programmes corrects
* Modifier le répertoire de votre coquille après avoir quitté Ranger
* Onglets, signets, support de souris ... 

Dépendances
-------------
* Python (`>=2.6` ou `>=3.1`) avec le module `curses` et (éventuellement)
  support de wide-unicode
* Un pager (`less` par défaut) 
* bat pour la colorisation des zettel

### Dépendances facultatives

Pour l'utilisation générale:

* `file` pour déterminer les types de fichiers
* `chardet` (package Python) pour une détection d'encodage améliorée des
  fichiers texte
* `sudo` utiliser la fonctionnalité "Exécuter en tant que root"
* `python-bidi` (package Python) pour afficher correctement les noms de fichier
  droit à gauche (Hébreu, arabe) 

Installation
-----------
Utilisez le gestionnaire de paquets de votre système d'exploitation pour
installer ranger. Vous pouvez également installer ranger via PYPI:
```pip install ranger-fm```. 

<details>
  <summary>
    Check current version:
    <sub>
      <a href="https://repology.org/metapackage/ranger/versions">
        <img src="https://repology.org/badge/tiny-repos/ranger.svg" alt="Packaging status">
      </a>
    </sub>
  </summary>
  <a href="https://repology.org/metapackage/ranger/versions">
    <img src="https://repology.org/badge/vertical-allrepos/ranger.svg" alt="Packaging status">
  </a>
</details>

### Installation d'un clone
Notez que vous *n'avez pas* d'installer ranger; vous pouvez simplement exécuter
`ranger.py`.

Pour installer ranger manuellement:
```
sudo make install
```

Cela se traduit à peu près à:
```
sudo python setup.py install --optimize=1 --record=install_log.txt
```

Cela enregistre également une liste de tous les fichiers installés à
`install_log.txt`, que vous pouvez utiliser pour désinstaller Ranger. 

Commencer
---------
Après avoir commencé Ranger, vous pouvez utiliser les touches fléchées ou `h`
`j` `k` `l` à naviguer, `Entrez` pour ouvrir un zettel ou `q` à cesser. La
deuxième colonne montre un aperçu du zettel actuel. La première le répertoire
de zettel.

ranger peut automatiquement copier des fichiers de configuration par défaut sur
`~/.config/ranger` si vous l'exécutez avec l'interrupteur `--copy-config = (rc
| scope | ... | all)`.  Voir `ranger --help` pour une description de cet
interrupteur. Aussi vérifier `ranger/config/` pour la configuration par défaut. 

Aller plus loin
---------------
* Pour tirer le meilleur parti de ranger, lisez le [Guide de l'utilisateur
  officiel](https://github.com/ranger/ranger/wiki/Official-user-guide).
* Pour les questions fréquemment posées, voir la
  [FAQ](https://github.com/ranger/ranger/wiki/faq%3A-Frequently-Asked-Questions).
* Pour plus d'informations sur la personnalisation, voir le
  [wiki](https://github.com/ranger/ranger/wiki). 


Communauté
----------
Pour l'aide, le soutien ou si vous voulez juste sortir avec nous, vous pouvez
nous trouver ici:
* **irc**: canal **#ranger** sur
  [freenode](https://freenode.net/kb/answer/chat)
* **Reddit**: [r/ranger](https://www.reddit.com/r/ranger/) 
