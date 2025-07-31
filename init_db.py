# init_db.py
import os
from datetime import datetime, date
from database import SessionLocal, engine
import models
import crud

# Créer toutes les tables
models.Base.metadata.create_all(bind=engine)


def init_database():
    db = SessionLocal()
    try:
        print("=== Initialisation de la base de données bois_m v2 ===")
        print(f"Date et heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 1. Vérifier si le plan comptable existe déjà
        if not crud.get_all_comptes(db):
            print("- Création du plan comptable algérien (classes 1 à 8)...")

            # Classe 1 : Capital
            crud.create_compte(db, {
                "compte": "10", "libelle": "Capital", "classe": 1, "type_compte": "CAPITAL", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "11", "libelle": "Réserves", "classe": 1, "type_compte": "CAPITAL", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "12", "libelle": "Report à nouveau", "classe": 1, "type_compte": "CAPITAL", "niveau": 1
            })

            # Classe 2 : Immobilisations
            crud.create_compte(db, {
                "compte": "20", "libelle": "Immobilisations incorporelles", "classe": 2, "type_compte": "ACTIF", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "21", "libelle": "Immobilisations corporelles", "classe": 2, "type_compte": "ACTIF", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "23", "libelle": "Immobilisations en cours", "classe": 2, "type_compte": "ACTIF", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "27", "libelle": "Ecarts de conversion - Actif", "classe": 2, "type_compte": "ACTIF", "niveau": 1
            })

            # Classe 3 : Stocks et en-cours
            crud.create_compte(db, {
                "compte": "31", "libelle": "Matières premières", "classe": 3, "type_compte": "ACTIF", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "35", "libelle": "Produits finis", "classe": 3, "type_compte": "ACTIF", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "38", "libelle": "Autres approvisionnements", "classe": 3, "type_compte": "ACTIF", "niveau": 1
            })

            # Classes 4 et 5 : Tiers et Trésorerie
            crud.create_compte(db, {
                "compte": "41", "libelle": "Clients", "classe": 4, "type_compte": "ACTIF", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "40", "libelle": "Fournisseurs", "classe": 4, "type_compte": "PASSIF", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "51", "libelle": "Banques", "classe": 5, "type_compte": "ACTIF", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "53", "libelle": "Caisses", "classe": 5, "type_compte": "ACTIF", "niveau": 1
            })

            # Comptes détaillés
            # Clients par défaut
            crud.create_compte(db, {
                "compte": "411000", "libelle": "Clients - Ventes", "classe": 4, "type_compte": "ACTIF", "niveau": 2
            })
            # Fournisseurs par défaut
            crud.create_compte(db, {
                "compte": "401000", "libelle": "Fournisseurs - Achats", "classe": 4, "type_compte": "PASSIF", "niveau": 2
            })
            # Caisse par défaut
            crud.create_compte(db, {
                "compte": "530000", "libelle": "Caisse principale", "classe": 5, "type_compte": "ACTIF", "niveau": 2
            })

            # TVA
            crud.create_compte(db, {
                "compte": "4456", "libelle": "TVA déductible sur achats", "classe": 4, "type_compte": "ACTIF", "niveau": 2
            })
            crud.create_compte(db, {
                "compte": "4457", "libelle": "TVA collectée", "classe": 4, "type_compte": "PASSIF", "niveau": 2
            })
            # Droit de timbre
            crud.create_compte(db, {
                "compte": "4458", "libelle": "Droit de Timbre", "classe": 4, "type_compte": "PASSIF", "niveau": 2
            })

            # Classe 6 : Charges
            crud.create_compte(db, {
                "compte": "60", "libelle": "Achats", "classe": 6, "type_compte": "CHARGE", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "61", "libelle": "Services extérieurs", "classe": 6, "type_compte": "CHARGE", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "62", "libelle": "Autres services extérieurs", "classe": 6, "type_compte": "CHARGE", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "64", "libelle": "Charges de personnel", "classe": 6, "type_compte": "CHARGE", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "68", "libelle": "Dotations aux amortissements", "classe": 6, "type_compte": "CHARGE", "niveau": 1
            })

            # Classe 7 : Produits
            crud.create_compte(db, {
                "compte": "70", "libelle": "Ventes", "classe": 7, "type_compte": "PRODUIT", "niveau": 1
            })
            crud.create_compte(db, {
                "compte": "71", "libelle": "Production stockée", "classe": 7, "type_compte": "PRODUIT", "niveau": 1
            })

            print("✅ Plan comptable créé avec succès.")
        else:
            print("- Plan comptable déjà existant. Skipping.")

        # 2. Initialiser les paramètres
        if not db.query(models.Parametres).filter(models.Parametres.type_param == "famille_produit").first():
            print("- Création des familles de produits...")
            familles = [
                ("famille_produit", "MP", "Matière première"),
                ("famille_produit", "SF", "Semi-fini"),
                ("famille_produit", "PF", "Produit fini"),
                ("famille_produit", "déchet", "Déchet"),
            ]
            for type_param, valeur, description in familles:
                crud.create_parametre(db, {
                    "type_param": type_param,
                    "valeur": valeur,
                    "description": description
                })
            print("✅ Familles de produits créées.")

        if not db.query(models.Parametres).filter(models.Parametres.type_param == "unite_production").first():
            print("- Création des unités de production...")
            unites = [
                ("unite_production", "Scierie", "Unité de sciage du bois"),
                ("unite_production", "Déroulage", "Unité de déroulage"),
                ("unite_production", "Atelier Nord", "Atelier de finition"),
                ("unite_production", "Broyeur", "Unité de broyage des déchets"),
            ]
            for type_param, valeur, description in unites:
                crud.create_parametre(db, {
                    "type_param": type_param,
                    "valeur": valeur,
                    "description": description
                })
            print("✅ Unités de production créées.")

        if not db.query(models.Parametres).filter(models.Parametres.type_param == "unite_mesure").first():
            print("- Création des unités de mesure...")
            unites_mesure = [
                ("unite_mesure", "m³", "mètre cube"),
                ("unite_mesure", "pièces", "unité"),
                ("unite_mesure", "kg", "kilogramme"),
                ("unite_mesure", "planches", "planches"),
            ]
            for type_param, valeur, description in unites_mesure:
                crud.create_parametre(db, {
                    "type_param": type_param,
                    "valeur": valeur,
                    "description": description
                })
            print("✅ Unités de mesure créées.")

        # 3. Créer une séquence pour les factures si elle n'existe pas
        current_year = datetime.now().year
        if not db.query(models.Sequence).filter(models.Sequence.annee == current_year).first():
            db_sequence = models.Sequence(annee=current_year, dernier_numero=0)
            db.add(db_sequence)
            db.commit()
            print(f"✅ Séquence de facturation initialisée pour {current_year}.")

        # 4. Ajouter des données de test si la base est vide
        if not crud.get_produits(db):
            print("- Ajout des produits de test...")
            produits = [
                {
                    "code": "MP001",
                    "designation": "Bois de Chêne",
                    "famille": "MP",
                    "unite_mesure": "m³",
                    "prix_achat": 500,
                    "prix_vente": 700,
                    "taux_tva": 19,
                    "compte_stock": "311001",
                    "compte_achat": "601001",
                    "compte_vente": "701001"
                },
                {
                    "code": "MP002",
                    "designation": "Bois de Pin",
                    "famille": "MP",
                    "unite_mesure": "m³",
                    "prix_achat": 300,
                    "prix_vente": 450,
                    "taux_tva": 19,
                    "compte_stock": "311001",
                    "compte_achat": "601001",
                    "compte_vente": "701001"
                },
                {
                    "code": "SF001",
                    "designation": "Planches sciées",
                    "famille": "SF",
                    "unite_mesure": "planches",
                    "prix_vente": 200,
                    "taux_tva": 19,
                    "compte_stock": "351001",
                    "compte_vente": "701004"
                },
                {
                    "code": "PF001",
                    "designation": "Table en Chêne",
                    "famille": "PF",
                    "unite_mesure": "pièces",
                    "prix_vente": 1200,
                    "taux_tva": 19,
                    "compte_stock": "351002",
                    "compte_vente": "701002"
                },
                {
                    "code": "PF002",
                    "designation": "Chaise en Pin",
                    "famille": "PF",
                    "unite_mesure": "pièces",
                    "prix_vente": 350,
                    "taux_tva": 19,
                    "compte_stock": "351002",
                    "compte_vente": "701002"
                },
                {
                    "code": "DECH001",
                    "designation": "Copeaux de bois",
                    "famille": "déchet",
                    "unite_mesure": "kg",
                    "prix_vente": 10,
                    "taux_tva": 19,
                    "compte_stock": "351003",
                    "compte_vente": "701003"
                }
            ]
            for prod in produits:
                crud.create_produit(db, prod)
            print("✅ Produits de test ajoutés.")

        # 5. Ajouter des clients de test
        if not crud.get_clients(db):
            print("- Ajout des clients de test...")
            clients = [
                {
                    "nom": "EURL Menuiserie Pro",
                    "adresse": "123 Rue de l'Artisanat, Alger",
                    "telephone": "0550123456",
                    "email": "contact@menuiseriepro.dz",
                    "nif": "1234567890123",
                    "nis": "123456789",
                    "rc": "ALG-123456",
                    "compte_comptable": "411000"
                },
                {
                    "nom": "SARL Bois & Design",
                    "adresse": "456 Av. des Pins, Oran",
                    "telephone": "0770987654",
                    "email": "info@boisdesign.dz",
                    "nif": "2345678901234",
                    "nis": "234567890",
                    "rc": "ORAN-789012",
                    "compte_comptable": "411000"
                }
            ]
            for client in clients:
                crud.create_client(db, client)
            print("✅ Clients de test ajoutés.")

        # 6. Ajouter des fournisseurs de test
        if not crud.get_fournisseurs(db):
            print("- Ajout des fournisseurs de test...")
            fournisseurs = [
                {
                    "nom": "Scierie du Nord",
                    "adresse": "789 Route Forestière, Tizi Ouzou",
                    "telephone": "0660112233",
                    "email": "scierie.nord@djezair.dz",
                    "nif": "3456789012345",
                    "nis": "345678901",
                    "rc": "TIZI-345678",
                    "compte_comptable": "401000"
                },
                {
                    "nom": "Bois & Cie",
                    "adresse": "321 Rue des Arbres, Constantine",
                    "telephone": "0555998877",
                    "email": "bois.cie@constantine.dz",
                    "nif": "4567890123456",
                    "nis": "456789012",
                    "rc": "CONST-987654",
                    "compte_comptable": "401000"
                }
            ]
            for fournisseur in fournisseurs:
                crud.create_fournisseur(db, fournisseur)
            print("✅ Fournisseurs de test ajoutés.")

        # 7. Initialiser le stock pour les produits MP
        produits_mp = db.query(models.Produit).filter(models.Produit.famille == "MP").all()
        for produit in produits_mp:
            if not crud.get_stock_actuel(db, produit.id, "GENERAL"):
                crud.update_stock(db, produit.id, "GENERAL", 100, produit.prix_achat or 0)
        print("✅ Stock initialisé pour les matières premières.")

        print("=== Initialisation terminée avec succès ! ===")

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
