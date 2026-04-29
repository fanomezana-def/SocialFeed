"""
reset_db.py — À lancer UNE SEULE FOIS si vous avez une ancienne base de données v1.
Supprime l'ancienne DB et recrée tout proprement.

Usage:
    python reset_db.py
"""
import os
import sys

db_path = os.path.join(os.path.dirname(__file__), 'socialfeed.db')

if os.path.exists(db_path):
    confirm = input(f"⚠️  Supprimer '{db_path}' et recréer la base ? (oui/non) : ").strip().lower()
    if confirm in ('oui', 'o', 'yes', 'y'):
        os.remove(db_path)
        print("✅ Ancienne base supprimée.")
    else:
        print("Annulé.")
        sys.exit(0)
else:
    print("Aucune base existante trouvée.")

# Importer l'app pour créer la nouvelle base
print("Création de la nouvelle base de données...")
from app import app, db, seed
import app as app_module

with app.app_context():
    for sub in ['images', 'videos', 'audios']:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], sub), exist_ok=True)
    db.create_all()
    app_module.seed()
    print("✅ Base de données créée avec succès !")
    print("\nComptes de démonstration :")
    print("  alice@demo.mg  / password123  (Admin)")
    print("  bob@demo.mg    / password123")
    print("  clara@demo.mg  / password123")
    print("\nLancez maintenant : python app.py")
