# services/production.py
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from models import *
from crud import *
from decimal import Decimal


def init_parameters(db: Session):
    """
    Initialise les paramètres spécifiques à la production.
    À appeler une fois au démarrage.
    """
    # Unités de production
    unites_production = [
        ("unite_production", "Scierie", "Unité de sciage du bois"),
        ("unite_production", "Déroulage", "Unité de déroulage"),
        ("unite_production", "Atelier Nord", "Atelier de finition"),
        ("unite_production", "Broyeur", "Unité de broyage des déchets"),
    ]

    # Familles de produits
    familles_produit = [
        ("famille_produit", "MP", "Matière première"),
        ("famille_produit", "SF", "Semi-fini"),
        ("famille_produit", "PF", "Produit fini"),
        ("famille_produit", "déchet", "Déchet"),
    ]

    # Types d'opération
    types_operation = [
        ("type_operation", "achat", "Achat de matières premières"),
        ("type_operation", "consommation", "Consommation de matières"),
        ("type_operation", "production", "Production de produits"),
        ("type_operation", "transfert", "Transfert entre unités"),
        ("type_operation", "vente", "Vente de produits"),
        ("type_operation", "charge", "Charge de production"),
    ]

    # Créer les paramètres s'ils n'existent pas
    for type_param, valeur, description in unites_production + familles_produit + types_operation:
        if not db.query(Parametres).filter(
            Parametres.type_param == type_param,
            Parametres.valeur == valeur
        ).first():
            create_parametre(db, {
                "type_param": type_param,
                "valeur": valeur,
                "description": description
            })


def _calculate_production_cost(db: Session, journal: JournalQuotidien) -> float:
    """
    Calcule le coût de production d'un produit fini ou semi-fini.
    Basé sur :
    1. Le coût des matières premières consommées (CUMP)
    2. Une répartition des charges de production (simplifiée ici à 20% du coût MP)
    """
    # Exemple de recette (à terme, cette donnée devrait être dans une table "Recette")
    recette = {
        "PF001": {"MP001": 2.5},  # 2.5 m³ de Bois de Chêne pour 1 Table en Chêne
        "SF001": {"MP001": 1.2},  # 1.2 m³ pour 1 lot de Planches sciées
        "PF002": {"MP002": 0.8},  # 0.8 m³ de Bois de Pin pour 1 Chaise
    }

    produit = get_produit(db, journal.produit_id)
    if not produit or produit.code not in recette:
        # Si pas de recette, utiliser le prix d'achat comme coût unitaire
        return float(journal.quantite * (produit.prix_achat or 0))

    cout_total = Decimal('0.0')
    for code_mp, quantite_mp in recette[produit.code].items():
        mp = db.query(Produit).filter(Produit.code == code_mp).first()
        if mp:
            # Récupérer le coût unitaire moyen du stock dans l'unité de production
            stock_mp = get_stock_actuel(db, mp.id, journal.unite_production or "GENERAL")
            cout_unitaire_mp = stock_mp.cout_unitaire_moyen if stock_mp else mp.prix_achat or 0
            cout_total += Decimal(str(quantite_mp)) * Decimal(str(cout_unitaire_mp)) * Decimal(str(journal.quantite))

    # Ajouter les charges de production (ex: 20% du coût des matières)
    # À terme, cette valeur devrait être calculée à partir des écritures de charges
    cout_total *= Decimal('1.2')

    return float(cout_total)


def _update_stock_production(db: Session, journal: JournalQuotidien, produit: Produit):
    """
    Met à jour le stock lors d'une production (ajout de PF ou SF).
    Utilise le CMP (coût moyen pondéré) pour valoriser le stock.
    """
    stock_actuel = get_stock_actuel(db, produit.id, journal.unite_production or "GENERAL")
    cout_production = _calculate_production_cost(db, journal)
    cout_unitaire = cout_production / journal.quantite if journal.quantite > 0 else 0

    if stock_actuel:
        # CMP : (stock_actuel * prix_actuel + quantite_nouvelle * prix_nouveau) / total
        ancienne_valeur = stock_actuel.quantite * stock_actuel.cout_unitaire_moyen
        nouvelle_valeur = journal.quantite * cout_unitaire
        nouvelle_quantite = stock_actuel.quantite + journal.quantite
        if nouvelle_quantite > 0:
            stock_actuel.cout_unitaire_moyen = (ancienne_valeur + nouvelle_valeur) / nouvelle_quantite
        stock_actuel.quantite = nouvelle_quantite
        stock_actuel.valeur_stock = stock_actuel.quantite * stock_actuel.cout_unitaire_moyen
    else:
        # Créer un nouveau stock
        stock_actuel = Stock(
            produit_id=produit.id,
            unite_production=journal.unite_production or "GENERAL",
            quantite=journal.quantite,
            cout_unitaire_moyen=cout_unitaire,
            valeur_stock=journal.quantite * cout_unitaire,
            date_derniere_operation=datetime.now()
        )
        db.add(stock_actuel)

    stock_actuel.date_derniere_operation = datetime.now()
    db.commit()
    db.refresh(stock_actuel)


def _update_stock_consommation(db: Session, journal: JournalQuotidien, produit: Produit):
    """
    Met à jour le stock lors d'une consommation (sortie de MP).
    Utilise le CUMP du stock pour valoriser la sortie.
    """
    stock_actuel = get_stock_actuel(db, produit.id, journal.unite_production or "GENERAL")
    if not stock_actuel or stock_actuel.quantite < journal.quantite:
        raise ValueError(f"Stock insuffisant pour {produit.designation} dans {journal.unite_production}")

    # Valorisation au CUMP
    cout_sortie = journal.quantite * stock_actuel.cout_unitaire_moyen

    # Diminuer la quantité
    stock_actuel.quantite -= journal.quantite
    stock_actuel.valeur_stock -= cout_sortie

    # Le coût unitaire moyen reste inchangé pour les sorties
    if stock_actuel.quantite <= 0:
        stock_actuel.quantite = 0
        stock_actuel.valeur_stock = 0
        stock_actuel.cout_unitaire_moyen = 0

    stock_actuel.date_derniere_operation = datetime.now()
    db.commit()
    db.refresh(stock_actuel)


def _create_operation_from_journal(db: Session, journal: JournalQuotidien, op_type: str):
    """
    Crée une entrée dans la table Operations à partir d'une entrée de JournalQuotidien.
    Cette table est utilisée pour le calcul des métriques du tableau de bord.
    """
    operation_data = {
        "journal_id": journal.id,
        "date_comptable": journal.date_operation,
        "unite_production": journal.unite_production or "GENERAL",
        "type_operation": op_type,
        "produit_id": journal.produit_id,
        "client_id": journal.client_id,
        "fournisseur_id": journal.fournisseur_id,
        "quantite": journal.quantite,
        "cout_unitaire": journal.prix_unitaire,
        "montant": journal.montant_ttc,
        "libelle": journal.libelle,
        "validee": True
    }
    db_operation = Operation(**operation_data)
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    return db_operation


def calculate_daily_metrics(db: Session, date_ref: date = None):
    """
    Calcule les métriques quotidiennes pour le tableau de bord.
    Retourne un dictionnaire avec les données de production, consommation, rendement, etc.
    """
    if not date_ref:
        date_ref = date.today()

    start_date = datetime.combine(date_ref, datetime.min.time())
    end_date = datetime.combine(date_ref, datetime.max.time())

    # Récupérer toutes les opérations du jour
    operations = db.query(Operation).filter(
        Operation.date_comptable >= start_date,
        Operation.date_comptable <= end_date
    ).all()

    # Initialiser les métriques
    metrics = {
        "date": date_ref,
        "bois_consomme": 0.0,
        "produits_finis": 0.0,
        "semi_finis": 0.0,
        "dechets": 0.0,
        "cout_total_consommation": 0.0,
        "cout_total_production": 0.0,
        "rendement_moyen": 0.0,
        "total_operations": len(operations),
        "details_unites": {}
    }

    # Initialiser les unités de production
    unites = get_parametres_by_type(db, "unite_production")
    for unit in unites:
        metrics["details_unites"][unit.valeur] = {
            "bois_consomme": 0.0,
            "produits_finis": 0.0,
            "semi_finis": 0.0,
            "dechets": 0.0,
            "cout_consommation": 0.0,
            "cout_production": 0.0,
            "rendement": 0.0
        }

    # Calculer les métriques
    for op in operations:
        unit_name = op.unite_production or "GENERAL"
        if unit_name not in metrics["details_unites"]:
            metrics["details_unites"][unit_name] = {
                "bois_consomme": 0.0, "produits_finis": 0.0, "semi_finis": 0.0,
                "dechets": 0.0, "cout_consommation": 0.0, "cout_production": 0.0,
                "rendement": 0.0
            }

        unit_data = metrics["details_unites"][unit_name]

        # Consommation de matières premières (MP)
        if op.type_operation == "consommation" and op.produit and op.produit.famille == "MP":
            metrics["bois_consomme"] += op.quantite
            unit_data["bois_consomme"] += op.quantite
            metrics["cout_total_consommation"] += op.montant
            unit_data["cout_consommation"] += op.montant

        # Production de produits
        elif op.type_operation == "production" and op.produit:
            metrics["cout_total_production"] += op.montant
            unit_data["cout_production"] += op.montant

            if op.produit.famille == "PF":
                metrics["produits_finis"] += op.quantite
                unit_data["produits_finis"] += op.quantite
            elif op.produit.famille == "SF":
                metrics["semi_finis"] += op.quantite
                unit_data["semi_finis"] += op.quantite
            elif op.produit.famille == "déchet":
                metrics["dechets"] += op.quantite
                unit_data["dechets"] += op.quantite

    # Calcul du rendement global
    total_output = metrics["produits_finis"] + metrics["semi_finis"] + metrics["dechets"]
    if metrics["bois_consomme"] > 0:
        metrics["rendement_moyen"] = (total_output / metrics["bois_consomme"]) * 100

    # Calcul du rendement par unité
    for unit_name, unit_data in metrics["details_unites"].items():
        total_output_unit = unit_data["produits_finis"] + unit_data["semi_finis"] + unit_data["dechets"]
        if unit_data["bois_consomme"] > 0:
            unit_data["rendement"] = (total_output_unit / unit_data["bois_consomme"]) * 100

    return metrics


def calculate_production_costs(db: Session, date_ref: date = None):
    """
    Calcule les coûts de production détaillés par unité de production.
    """
    if not date_ref:
        date_ref = date.today()

    start_date = datetime.combine(date_ref, datetime.min.time())
    end_date = datetime.combine(date_ref, datetime.max.time())

    unites = get_parametres_by_type(db, "unite_production")
    report = []

    for unit_param in unites:
        unit_name = unit_param.valeur

        # Récupérer les opérations de la journée pour cette unité
        operations = db.query(Operation).filter(
            Operation.date_comptable >= start_date,
            Operation.date_comptable <= end_date,
            Operation.unite_production == unit_name
        ).all()

        total_wood_consumed = sum(
            op.quantite for op in operations
            if op.type_operation == "consommation" and op.produit and op.produit.famille == "MP"
        )
        total_consumption_cost = sum(
            op.montant for op in operations
            if op.type_operation == "consommation" and op.produit and op.produit.famille == "MP"
        )
        total_produced_quantity = sum(
            op.quantite for op in operations
            if op.type_operation == "production" and op.produit and op.produit.famille in ["PF", "SF", "déchet"]
        )
        total_production_value = sum(
            op.montant for op in operations
            if op.type_operation == "production" and op.produit and op.produit.famille in ["PF", "SF", "déchet"]
        )

        cost_per_unit = total_production_value / total_produced_quantity if total_produced_quantity > 0 else 0
        rendement = (total_produced_quantity / total_wood_consumed) * 100 if total_wood_consumed > 0 else 0

        report.append({
            "unite_production": unit_name,
            "date": str(date_ref),
            "bois_consomme": total_wood_consumed,
            "cout_total_consommation": total_consumption_cost,
            "quantite_produite": total_produced_quantity,
            "valeur_production_totale": total_production_value,
            "cout_unitaire_moyen": cost_per_unit,
            "rendement": rendement
        })

    return report
