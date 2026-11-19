# CONSERVA — site + base de données + connexion/inscription + application installable

Interface : Tabler (Bootstrap 5, MIT). Base : Supabase (PostgreSQL). Rien à installer sur votre ordinateur.

## Contenu du dossier
- `index.html`, `assets/`, `config.js` : le site.
- `manifest.webmanifest`, `sw.js`, `icons/` : permettent de l'installer comme une application.
- `supabase/01_schema.sql` : tables, règles de capacité, droits par rôle, réception des capteurs.
- `supabase/02_exemple.sql` : données d'exemple (facultatif).
- `supabase/03_mesures_usb.sql` : autorisation sécurisée des mesures envoyées par USB (administrateur seulement).
- `arduino_mega_usb.ino` : programme pour Arduino Mega 2560 + DHT11 + buzzer, liaison USB directe.
- `bridge_serial.py` : pont local Python qui lit le port série et transmet les mesures à Supabase.
- `requirements.txt` : dépendance Python du pont série (`pyserial`).
- `esp32/conserva_capteur.ino` : programme du capteur.
- `esp32/conserva_capteur_usb.ino` : variante de transmission USB vers le navigateur.

## Essayer tout de suite (sans base)
Ouvrez `index.html`. Tant que `config.js` est vide, le site tourne en mode démonstration (rien n'est enregistré).

## Brancher la vraie base (environ 10 minutes)
1. Créez un compte gratuit sur supabase.com, puis « New project ». Notez le mot de passe de la base.
2. Menu **SQL Editor** > New query : collez tout `supabase/01_schema.sql`, puis **Run**.
   (Facultatif : faites pareil avec `supabase/02_exemple.sql` pour avoir des produits d'exemple.)
3. Menu **Project Settings > API** : copiez « Project URL » et la clé « anon public ».
   Collez-les dans `config.js` (entre les guillemets). La clé anon est faite pour être publique.
4. Ouvrez le site (`config.js` rempli), onglet **Créer un compte**, et inscrivez-vous avec votre e-mail.
   **Le premier compte créé devient administrateur** et est validé d'office.
   (Si Supabase demande de confirmer l'e-mail, cliquez sur le lien reçu. Vous pouvez aussi créer le compte dans
   Authentication > Users > Add user, en cochant « Auto Confirm User ».)
5. Les producteurs s'inscrivent eux-mêmes depuis la même page : ils indiquent le nom de leur GIE ou de leur exploitation.
   Leur compte reste **en attente** : ils ne voient aucune donnée tant que vous ne l'avez pas validé.
   Vous le validez dans la page « Producteurs » (carte « Comptes à valider »), après avoir vérifié le producteur
   auquel le rattacher. Le nom saisi crée le producteur s'il n'existe pas ; s'il existe déjà, le compte est proposé
   pour ce producteur existant : vérifiez avant de valider.
6. Un producteur validé ne voit que ses produits et ses réservations. Il ne peut pas modifier la capacité.
7. Si vous ne voulez pas d'inscription ouverte, désactivez-la dans les réglages Authentication de Supabase et créez
   les comptes vous-même (Add user) : ils arrivent aussi « en attente », vous les rattachez à un producteur au moment de valider.

## Règles appliquées par la base
- Capacité de 100 kg à 1 tonne, modifiable par l'administrateur (jamais sous le stock actuel).
- Une réservation est refusée si, sur sa période, produits + réservations dépasseraient la capacité.
- Alertes automatiques si la température sort de 2–8 °C ou l'humidité de 70–90 % (une alerte par type toutes les 30 min).
  Seuils modifiables dans la table `chambres` (colonnes `temp_min`, `temp_max`, `hum_min`, `hum_max`).

## Capteur ESP32
1. Dans le SQL Editor : `select cle from public.cles_capteurs;` pour lire la clé du capteur.
2. Ouvrez `esp32/conserva_capteur.ino` dans l'IDE Arduino, remplissez la zone « À REMPLIR », téléversez.
3. Les mesures apparaissent sur le tableau de bord (actualisation toutes les 10 s). Le code n'a pas été testé sur du matériel.

### Utiliser l'USB pour envoyer les mesures à l'application
1. Après `01_schema.sql`, exécutez aussi `supabase/03_mesures_usb.sql` dans le SQL Editor.
2. Pour l'Arduino Mega 2560 + DHT11 + buzzer, ouvrez `arduino_mega_usb.ino`, sélectionnez « Arduino Mega or Mega 2560 » et téléversez. Le DHT11 doit être sur la broche 2 et le buzzer sur la broche 8. Le programme transmet les deux mesures en JSON par USB à 9600 bauds.
3. Ouvrez l'application sur HTTPS (Netlify convient) ou `localhost` dans Chrome ou Edge, puis connectez-vous avec le compte administrateur.
4. Sur le tableau de bord, cliquez sur « Connecter le capteur USB », choisissez le port de la carte et laissez l'onglet ouvert. Les mesures sont enregistrées dans Supabase et affichées dans l'application.

La liaison Web Serial nécessite Chrome ou Edge et une connexion USB autorisée par le navigateur. Fermez le Moniteur série Arduino avant de cliquer sur le bouton de connexion. Le programme USB ne requiert pas de Wi-Fi, mais le PC doit avoir Internet pour enregistrer les mesures dans Supabase. L'onglet doit rester ouvert et connecté. Pour l'option ESP32 + DHT22 par USB, utilisez `esp32/conserva_capteur_usb.ino` et changez `SERIAL_BAUD` dans `config.js` à `115200`. Pour un fonctionnement autonome sans ordinateur, utilisez plutôt `esp32/conserva_capteur.ino` et le Wi-Fi. Le Mega est connecté directement au PC dans le scénario USB ; sa liaison `Serial1` vers l'ESP32 n'est pas nécessaire.

### Variante : pont local Python (sans Web Serial du navigateur)
Cette option convient si vous préférez que Python ouvre le port USB. Elle envoie les mesures directement à la fonction Supabase `enregistrer_mesure`; le tableau de bord les récupère ensuite par son actualisation habituelle.
1. Installez Python, puis dans le dossier du projet lancez `py -m pip install -r requirements.txt`.
2. Vérifiez que `config.js` contient l'URL Supabase, la clé publishable/anon et `SERIAL_BAUD: 9600`.
3. Téléversez `arduino_mega_usb.ino` sur le Mega. Fermez le Moniteur série Arduino.
4. Lancez `py bridge_serial.py`, choisissez le port `COM` affiché et saisissez la clé capteur récupérée dans Supabase avec `select cle from public.cles_capteurs;`. La clé est demandée sans être affichée et n'est pas stockée dans le script.
5. Gardez cette fenêtre de terminal ouverte. Les mesures envoyées seront visibles dans le tableau de bord après connexion au compte.

Avec cette variante, ne cliquez pas en même temps sur « Connecter le capteur USB » dans l'application : un seul programme peut ouvrir le port série à la fois. Le pont local utilise HTTPS pour envoyer les mesures à Supabase, donc le site peut être ouvert dans n'importe quel navigateur. Le PC, le pont et l'accès Internet doivent rester actifs. Vous pouvez arrêter le pont avec Ctrl+C.

## Mettre en ligne gratuitement
Le site est statique. Le fichier `netlify.toml` prépare une publication Netlify et copie uniquement les fichiers du site dans `dist/` (sans les scripts Arduino/Python ni le SQL).
1. Placez le dossier du projet dans un dépôt GitHub privé ou public et envoyez-y les fichiers, notamment `netlify.toml`.
2. Sur Netlify, choisissez **Add new site > Import an existing project**, connectez GitHub et sélectionnez le dépôt CONSERVA.
3. Laissez Netlify lire la configuration du fichier `netlify.toml`, puis lancez le déploiement. Le site sera publié à une adresse `https://....netlify.app`.
4. Dans Supabase, ouvrez **Authentication > URL Configuration**. Remplacez **Site URL** par l'adresse Netlify et ajoutez cette adresse à **Redirect URLs**. Si vous utilisez aussi une URL de prévisualisation Netlify, ajoutez-la également.
5. Ouvrez l'adresse Netlify, testez la connexion, puis testez le lien WhatsApp et, si nécessaire, la connexion USB dans Chrome/Edge.

Les paramètres Supabase/WhatsApp du site restent dans `config.js`. Seule la clé publishable/anon peut être utilisée côté navigateur : ne mettez jamais une clé `service_role` ou une clé secrète dans ce fichier. L'installation comme application et le fonctionnement hors ligne nécessitent HTTPS (fourni par Netlify).

## Installer comme application
- Android (Chrome) : menu ⋮ > « Installer l'application » (ou « Ajouter à l'écran d'accueil »).
- iPhone (Safari) : bouton Partager > « Sur l'écran d'accueil ».
Hors ligne, l'application s'ouvre mais les données viennent de la base : il faut du réseau pour les voir à jour.

## Limites connues
- Pas d'annulation de réservation ni de modification de produit dans l'interface (la base le permettrait plus tard).
- Pas de « mot de passe oublié » dans le site pour l'instant. Un compte peut être réinitialisé depuis Supabase (Authentication > Users).
- Pas de bouton « Refuser » : un compte non voulu reste en attente (vous pouvez le supprimer dans Authentication > Users).
- Aperçu de la page de connexion en mode démonstration : lien « Aperçu de la page de connexion » dans le menu, ou `index.html#connexion`.
- Le site et le SQL ont été testés ici sur un faux Supabase et un vrai PostgreSQL local ; le branchement sur votre projet Supabase reste à vérifier à la première connexion.
