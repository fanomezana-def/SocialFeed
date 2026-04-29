
# SocialFeed

# SocialFeed Madagascar 🇲🇬

Plateforme sociale complète avec fil d'actualité, suggestions produits intelligentes, e-commerce intégré, et tableau de bord analytics.

---

## 🚀 Installation rapide

```bash
# 1. Extraire le zip et entrer dans le dossier
cd socialfeed2

# 2. Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer
python app.py
```

Ouvrir **http://localhost:5000**

---

## 🔑 Comptes de démonstration

| Email | Mot de passe | Rôle |
|-------|-------------|------|
| alice@demo.mg | password123 | **Admin** |
| bob@demo.mg | password123 | Utilisateur |
| clara@demo.mg | password123 | Utilisateur |

Le compte **alice** a accès au tableau de bord Admin.

---

## ✅ Fonctionnalités complètes

### 🔐 Authentification
- Inscription avec validation complète
- Connexion + "Se souvenir de moi"
- Déconnexion
- Mot de passe oublié (email avec token sécurisé, expire 1h)
- Réinitialisation de mot de passe
- Afficher/masquer le mot de passe

### 👤 Profil
- Page profil avec photo de couverture + avatar
- **Modification du profil** : nom, bio, localisation, site web
- Upload avatar et photo de couverture
- Changement de mot de passe depuis le profil
- Statistiques (publications, j'aime reçus)

### 📰 Fil d'actualité
- Publier texte, **photo**, **vidéo**, **audio** ou URL d'image
- Prévisualisation des médias avant publication
- Lecteur vidéo intégré dans le post
- Lecteur audio intégré dans le post
- Liker / unliker (AJAX — sans rechargement)
- Commenter (toggle visible/caché)
- Enregistrer (bookmarks)
- Supprimer ses propres publications
- Pagination

### 🛍️ Boutique & Suggestions
- **Suggestions dans le fil** : bannière produit + suggestions inline (toutes les X publications)
- **Sidebar droite** avec produits tendance + bouton ajouter direct
- Page boutique avec filtres par catégorie
- Affichage stock en temps réel
- Bouton "Ajouter au panier" AJAX (sans rechargement)

### 🛒 Panier fonctionnel
- Ajouter / retirer des produits
- **Modifier les quantités** (+ / −) en AJAX
- Total calculé automatiquement en **Ariary (Ar)**
- Commander → confirmation et création commande
- Historique des commandes

### 📊 Tableau de bord Admin
Accessible via `/admin` (compte alice uniquement) :
- **KPIs** : utilisateurs, publications, commandes, CA total
- **Stats par produit** : total clics, utilisateurs uniques, clics par source (feed / sidebar / bannière / boutique), dans combien de paniers
- **Timeline des derniers clics** (20 derniers)
- **Gestion des utilisateurs** : voir tous, accorder/retirer admin
- **Ajouter / supprimer des produits**
- **Historique des commandes**

### 🌙 Mode sombre / clair
- Toggle dans la sidebar
- Persistant via session Flask
- Transition fluide CSS

### 🔔 Autres
- Notifications (j'aime + commentaires)
- Recherche globale (publications, utilisateurs, produits)
- Publications enregistrées (bookmarks)

---

## 📧 Configuration Email (mot de passe oublié)

Dans `app.py`, remplacer :
```python
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_USERNAME'] = 'your_user'
app.config['MAIL_PASSWORD'] = 'your_pass'
```

Pour tester gratuitement : [mailtrap.io](https://mailtrap.io)

---

## 📁 Structure du projet

```
socialfeed2/
├── app.py                      # Application Flask principale
├── requirements.txt
├── static/
│   ├── css/style.css           # Design system complet (dark/light)
│   ├── js/app.js               # JS : AJAX, preview médias, thème
│   └── uploads/                # Médias uploadés (créé automatiquement)
│       ├── images/
│       ├── videos/
│       └── audios/
└── templates/
    ├── base.html               # Layout principal (sidebar + auth)
    ├── feed.html               # Fil d'actualité + suggestions
    ├── profile.html            # Page profil
    ├── edit_profile.html       # Modification du profil
    ├── products.html           # Boutique
    ├── cart.html               # Panier
    ├── orders.html             # Commandes
    ├── admin.html              # Dashboard admin
    ├── search.html             # Recherche
    ├── bookmarks.html          # Enregistrés
    ├── notifications.html      # Notifications
    ├── login.html
    ├── register.html
    ├── forgot_password.html
    └── reset_password.html
```

---

## ⚙️ Production

```python
# app.py — changer pour la production
app.config['SECRET_KEY'] = 'votre-cle-super-secrete-aleatoire'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@host/db'
# debug=False dans app.run()
```

