# 🎙️ MicroToggle

Un petit utilitaire Python pour couper et réactiver ses microphones avec un raccourci clavier, sans revenir sur le bureau.

Pensé pour une utilisation pendant les jeux, les appels ou les sessions de travail.

> Projet Windows en cours de test. Le fonctionnement du raccourci peut varier selon les claviers, les jeux et les logiciels utilisés.

## ✨ Fonctionnalités

- Raccourci global : `Shift + 9 du pavé numérique`.
- Coupure et réactivation de tous les microphones actifs détectés.
- Fonctionnement en arrière-plan, sans fenêtre de console.
- Icône de statut dans la zone de notification Windows.
- Menu pour couper ou réactiver les microphones manuellement.
- Démarrage automatique à la connexion Windows, activable dans le menu.
- Journal d’erreurs pour faciliter le dépannage.
- Protection contre le lancement de plusieurs instances dans une même session.

## 📋 Prérequis

- Windows 10 ou Windows 11.
- Python installé avec le lanceur `py`.
- Une connexion Internet pour installer les dépendances.
- L’accès au microphone autorisé dans les paramètres Windows.

Python 3.11 ou 3.12 est conseillé pour commencer. La compatibilité avec toutes les versions de Python n’a pas été vérifiée.

## 🚀 Installation rapide

1. Télécharge le projet et extrais-le dans un dossier permanent.
2. Double-clique sur `installer_et_lancer.bat`.
3. Patiente pendant l’installation des dépendances.
4. Retrouve l’icône du microphone dans la zone de notification, près de l’horloge.

L’installateur crée un environnement Python local dans `.venv`, installe les dépendances, puis lance l’application.

> Si l’icône n’apparaît pas directement, regarde dans les icônes masquées de la barre des tâches.

### Installation manuelle

Ouvre un terminal dans le dossier du projet :

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\pythonw.exe microtoggle.py
```

## ⌨️ Utilisation

Appuie sur :

```text
Shift + 9 du pavé numérique
```

- Première pression : coupe les microphones actifs détectés.
- Deuxième pression : les réactive.

Utilise le `9` du pavé numérique, pas celui situé au-dessus des lettres.

### Indicateurs

| Icône | Signification |
| :--- | :--- |
| 🟢 Verte | Au moins un microphone détecté est actif |
| 🔴 Rouge | Tous les microphones détectés sont coupés |
| ⚪ Grise | Initialisation ou erreur |

### Menu de l’application

Fais un clic droit sur l’icône pour accéder aux commandes :

| Option | Action |
| :--- | :--- |
| Couper / réactiver | Bascule l’état des microphones |
| Couper tous les micros | Coupe les microphones actifs détectés |
| Réactiver tous les micros | Réactive les microphones actifs détectés |
| Démarrer avec Windows | Active ou désactive le lancement automatique |
| Ouvrir le journal | Affiche le fichier de diagnostic |
| Quitter | Ferme l’application sans modifier l’état des microphones |

> Quitter l’application ne réactive pas automatiquement les microphones. Pour les laisser actifs, sélectionne « Réactiver tous les micros » avant de quitter.

## 🔄 Démarrage automatique

Pour lancer MicroToggle à chaque connexion Windows :

1. Lance l’application.
2. Fais un clic droit sur son icône.
3. Coche `Démarrer avec Windows`.

Décoche cette option pour désactiver le lancement automatique.

L’option utilise la clé de démarrage du compte Windows courant :

```text
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
```

L’entrée créée porte le nom `MicroToggle`.

> Garde le projet et son environnement `.venv` dans le même dossier. Si tu déplaces le projet, désactive puis réactive le démarrage automatique depuis son nouvel emplacement.

## 🔒 Fonctionnement et confidentialité

MicroToggle modifie l’état de sourdine des périphériques d’entrée audio via les interfaces audio Windows.

Il ne modifie pas le réglage de confidentialité « Accès au micro ».

Le code du projet :

- n’enregistre pas le son ;
- ne sauvegarde aucun fichier audio ;
- n’envoie aucun son à un serveur ;
- utilise un écouteur clavier pour détecter le raccourci, sans écrire les frappes dans le journal.

L’accès au microphone doit rester autorisé dans :

```text
Paramètres → Confidentialité et sécurité → Microphone
```

> MicroToggle est un outil pratique de coupure audio, pas un verrou de confidentialité ni une déconnexion matérielle du microphone.

## ⚠️ Limites connues

- Le fonctionnement dans tous les jeux n’est pas garanti.
- Certains anti-triches ou logiciels exécutés avec des privilèges différents peuvent empêcher la détection du raccourci.
- Le raccourci n’est pas intercepté exclusivement : l’application au premier plan peut également le recevoir.
- La détection de `Shift + 9 du pavé numérique` doit être vérifiée sur ton clavier, notamment selon son comportement avec Verr Num.
- Un microphone branché après une coupure n’est pas automatiquement coupé.
- Une autre application peut modifier l’état de sourdine des microphones.
- La réactivation concerne tous les microphones actifs détectés : elle ne restaure pas leur état individuel précédent.
- La syntaxe du script a été vérifiée, mais son fonctionnement complet n’a pas encore été validé sur une machine Windows.

Avant de t’y fier, teste la coupure dans les paramètres audio Windows ou dans ton application de communication.

## 🛠️ Dépannage

### L’installation ne démarre pas

Vérifie que Python et le lanceur `py` sont installés :

```powershell
py --version
```

Si la commande n’est pas reconnue, vérifie ton installation de Python.

### Le microphone reste inutilisable après réactivation

Vérifie :

1. L’autorisation d’accès au microphone dans Windows.
2. Le périphérique d’entrée sélectionné dans ton application.
3. Le bouton de sourdine propre à ton casque ou à ton microphone.
4. Le réglage de sourdine de ton application de communication.

### Le raccourci ne fonctionne pas

- Utilise bien le `9` du pavé numérique.
- Maintiens `Shift`, puis appuie sur le `9`.
- Teste d’abord depuis le bureau, sans jeu ouvert.
- Essaie avec Verr Num activé, puis désactivé.
- Utilise le menu de l’icône pour vérifier que la coupure manuelle fonctionne.

### Consulter les erreurs

Dans le menu de l’application, sélectionne `Ouvrir le journal`.

Le fichier se trouve dans :

```text
%LOCALAPPDATA%\MicroToggle\microtoggle.log
```

## 📁 Structure du projet

```text
MicroToggle/
├── microtoggle.py
├── requirements.txt
├── installer_et_lancer.bat
├── LISEZMOI.txt
└── README.md
```

Le dossier `.venv` est créé localement pendant l’installation. Il ne doit pas être ajouté au dépôt Git.

## 📦 Dépendances

| Bibliothèque | Utilisation |
| :--- | :--- |
| `pycaw` | Accès aux périphériques audio Windows |
| `comtypes` | Communication avec les interfaces COM Windows |
| `keyboard` | Détection du raccourci clavier |
| `pystray` | Icône et menu dans la zone de notification |
| `Pillow` | Génération des icônes |

Les dépendances sont listées dans `requirements.txt`.

## 🗑️ Désinstallation

1. Décoche `Démarrer avec Windows`.
2. Réactive les microphones si nécessaire.
3. Quitte l’application.
4. Supprime le dossier du projet.

Pour supprimer également les journaux, supprime ce dossier :

```text
%LOCALAPPDATA%\MicroToggle
```

## 🤝 Signaler un problème

Ouvre une issue en indiquant :

- ta version de Windows ;
- ta version de Python ;
- ton type de clavier ;
- si le problème apparaît sur le bureau ou uniquement dans un jeu ;
- les étapes permettant de reproduire le problème ;
- les lignes pertinentes du journal, après avoir retiré toute information personnelle.

## 📄 Licence

Aucune licence n’est définie pour le moment.
