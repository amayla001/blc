# services/accounting.py
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from models import *
from crud import *
import math


def process_journal_entry(db: Session, journal: JournalQuotidien):
    """
    Traite une entrée du journal et génère les écritures comptables associées.
    """
    if journal.type_journal == "ACHAT":
        return _process_achat(db, journal)
    elif journal.type_journal == "VENTE":
        return _process_vente(db, journal)
    elif journal.type_journal == "CAISSE":
        return _process_caisse(db, journal)
    elif journal.type_journal == "PRODUCTION":
        return _process_production(db, journal)
    elif journal.type_journal == "CONSOMMATION":
        return _process_consommation(db, journal)
    elif journal.type_journal == "CHARGES":
        return _process_charges(db, journal)
    else:
        raise ValueError(f"Type de journal inconnu : {journal.type_journal}")


def _process_achat(db: Session, journal: JournalQuotidien):
    """Traite un achat avec écritures : Stock (débit) / Fournisseur (crédit) + TVA"""
    ecritures = []
    produit = get_produit(db, journal.produit_id)
    fournisseur = get_fournisseur(db, journal.fournisseur_id)
    if not produit or not fournisseur:
        raise ValueError("Produit ou fournisseur introuvable")

    # Compte de débit selon la famille
    compte_debit = "311000"  # Stock MP
    if produit.famille == "PF":
        compte_debit = "351000"  # Stock PF
    elif produit.famille == "SF":
        compte_debit = "351001"  # Stock SF
    else:
        compte_debit = produit.compte_stock or "311000"

    libelle_detaille = f"Achat {journal.quantite} {produit.unite_mesure} {produit.designation} - {journal.libelle}"

    # Écriture : Débit Stock / Crédit Fournisseur
    ecriture_stock = create_ecriture_comptable(db, {
        "journal_id": journal.id,
        "date_comptable": journal.date_operation,
        "journal": "ACHATS",
        "libelle": libelle_detaille,
        "compte_debit": compte_debit,
        "compte_credit": fournisseur.compte_comptable,
        "montant": journal.montant_ht,
        "fournisseur_id": journal.fournisseur_id,
        "numero_facture": journal.numero_piece
    })
    ecritures.append(ecriture_stock)

    # TVA déductible
    if journal.tva_applicable and journal.montant_tva > 0:
        ecriture_tva = create_ecriture_comptable(db, {
            "journal_id": journal.id,
            "date_comptable": journal.date_operation,
            "journal": "ACHATS",
            "libelle": f"TVA déductible {journal.taux_tva}% - {journal.libelle}",
            "compte_debit": "4456",  # TVA déductible
            "compte_credit": fournisseur.compte_comptable,
            "montant": journal.montant_tva,
            "fournisseur_id": journal.fournisseur_id,
            "numero_facture": journal.numero_piece
        })
        ecritures.append(ecriture_tva)

    # Mettre à jour le stock
    update_stock(db, journal.produit_id, journal.unite_production or "GENERAL", journal.quantite, journal.prix_unitaire)

    return ecritures


def _process_vente(db: Session, journal: JournalQuotidien):
    """Traite une vente avec écritures : Client (débit) / Vente (crédit) + TVA + DT"""
    ecritures = []
    produit = get_produit(db, journal.produit_id)
    client = get_client(db, journal.client_id)
    if not produit or not client:
        raise ValueError("Produit ou client introuvable")

    compte_credit = produit.compte_vente or "701000"
    libelle_detaille = f"Vente {journal.quantite} {produit.unite_mesure} {produit.designation} - {journal.libelle}"

    # Écriture : Débit Client / Crédit Ventes
    ecriture_vente = create_ecriture_comptable(db, {
        "journal_id": journal.id,
        "date_comptable": journal.date_operation,
        "journal": "VENTES",
        "libelle": libelle_detaille,
        "compte_debit": client.compte_comptable,
        "compte_credit": compte_credit,
        "montant": journal.montant_ht,
        "client_id": journal.client_id,
        "numero_facture": journal.numero_piece
    })
    ecritures.append(ecriture_vente)

    # TVA collectée
    if journal.tva_applicable and journal.montant_tva > 0:
        ecriture_tva = create_ecriture_comptable(db, {
            "journal_id": journal.id,
            "date_comptable": journal.date_operation,
            "journal": "VENTES",
            "libelle": f"TVA collectée {journal.taux_tva}% - {journal.libelle}",
            "compte_debit": client.compte_comptable,
            "compte_credit": "4457",  # TVA collectée
            "montant": journal.montant_tva,
            "client_id": journal.client_id,
            "numero_facture": journal.numero_piece
        })
        ecritures.append(ecriture_tva)

    # Droit de timbre
    if journal.dt_applicable and journal.droit_timbre > 0:
        ecriture_dt = create_ecriture_comptable(db, {
            "journal_id": journal.id,
            "date_comptable": journal.date_operation,
            "journal": "VENTES",
            "libelle": f"Droit de timbre - {journal.libelle}",
            "compte_debit": client.compte_comptable,
            "compte_credit": "4458",  # Droit de timbre
            "montant": journal.droit_timbre,
            "client_id": journal.client_id,
            "numero_facture": journal.numero_piece
        })
        ecritures.append(ecriture_dt)

    # Mettre à jour le stock
    update_stock(db, journal.produit_id, journal.unite_production or "GENERAL", -journal.quantite)

    return ecritures


def _process_caisse(db: Session, journal: JournalQuotidien):
    """Traite un règlement encaissé ou décaissé"""
    ecritures = []
    compte_contrepartie = "658000"  # Charges diverses

    if journal.client_id:
        client = get_client(db, journal.client_id)
        compte_contrepartie = client.compte_comptable
    elif journal.fournisseur_id:
        fournisseur = get_fournisseur(db, journal.fournisseur_id)
        compte_contrepartie = fournisseur.compte_comptable

    libelle = f"Règlement {journal.mode_paiement} - {journal.libelle}"

    # Écriture : Débit Compte tiers / Crédit Caisse (ou inverse)
    debit, credit = ("530000", compte_contrepartie) if journal.type_operation == "ENCAISSEMENT" else (compte_contrepartie, "530000")

    ecriture = create_ecriture_comptable(db, {
        "journal_id": journal.id,
        "date_comptable": journal.date_operation,
        "journal": "CAISSE",
        "libelle": libelle,
        "compte_debit": debit,
        "compte_credit": credit,
        "montant": abs(journal.montant_ttc),
        "client_id": journal.client_id,
        "fournisseur_id": journal.fournisseur_id,
        "numero_facture": journal.numero_piece
    })
    ecritures.append(ecriture)

    return ecritures


def _process_production(db: Session, journal: JournalQuotidien):
    """Traite une production (PF, SF, déchet) avec coût calculé"""
    ecritures = []
    produit = get_produit(db, journal.produit_id)
    if not produit:
        raise ValueError("Produit introuvable")

    # Calculer le coût de production (matières + charges)
    cout_production = _calculate_production_cost(db, journal)
    journal.montant_ht = cout_production
    journal.montant_ttc = cout_production

    # Compte de crédit selon la famille
    compte_credit = "713000"  # Production stockée
    if produit.famille == "déchet":
        compte_credit = "701003"  # Ventes de déchets
    elif produit.famille == "SF":
        compte_credit = "701004"  # Ventes de semi-finis

    libelle_detaille = f"Production {journal.quantite} {produit.unite_mesure} {produit.designation} - {journal.libelle}"

    # Écriture : Débit Stock / Crédit Production
    ecriture = create_ecriture_comptable(db, {
        "journal_id": journal.id,
        "date_comptable": journal.date_operation,
        "journal": "PRODUCTION",
        "libelle": libelle_detaille,
        "compte_debit": produit.compte_stock or "311000",
        "compte_credit": compte_credit,
        "montant": cout_production,
        "produit_id": journal.produit_id,
        "quantite": journal.quantite,
        "unite_production": journal.unite_production
    })
    ecritures.append(ecriture)

    # Mettre à jour le stock
    update_stock(db, journal.produit_id, journal.unite_production or "GENERAL", journal.quantite, cout_production / journal.quantite if journal.quantite > 0 else 0)

    return ecritures


def _process_consommation(db: Session, journal: JournalQuotidien):
    """Traite une consommation de matière première"""
    ecritures = []
    produit = get_produit(db, journal.produit_id)
    if not produit:
        raise ValueError("Produit introuvable")

    # Récupérer le coût unitaire moyen du stock
    stock = get_stock_actuel(db, journal.produit_id, journal.unite_production or "GENERAL")
    cout_unitaire = stock.cout_unitaire_moyen if stock else produit.prix_achat or 0
    cout_consommation = journal.quantite * cout_unitaire

    journal.montant_ht = cout_consommation
    journal.montant_ttc = cout_consommation

    libelle_detaille = f"Consommation {journal.quantite} {produit.unite_mesure} {produit.designation} - {journal.libelle}"

    # Écriture : Débit Consommation / Crédit Stock
    ecriture = create_ecriture_comptable(db, {
        "journal_id": journal.id,
        "date_comptable": journal.date_operation,
        "journal": "PRODUCTION",
        "libelle": libelle_detaille,
        "compte_debit": produit.compte_achat or "601000",
        "compte_credit": produit.compte_stock or "311000",
        "montant": cout_consommation,
        "produit_id": journal.produit_id,
        "quantite": journal.quantite,
        "unite_production": journal.unite_production
    })
    ecritures.append(ecriture)

    # Mettre à jour le stock
    update_stock(db, journal.produit_id, journal.unite_production or "GENERAL", -journal.quantite)

    return ecritures


def _process_charges(db: Session, journal: JournalQuotidien):
    """Traite les charges de production (MO, électricité, amortissement)"""
    ecritures = []
    compte_charge = "611000"  # Charges de production

    if journal.type_charge == "MO":
        compte_charge = "641000"  # Main d'œuvre
    elif journal.type_charge == "ELEC":
        compte_charge = "606100"  # Énergie
    elif journal.type_charge == "AMORT":
        compte_charge = "681100"  # Amortissements

    libelle = f"Charge de production - {journal.libelle}"

    ecriture = create_ecriture_comptable(db, {
        "journal_id": journal.id,
        "date_comptable": journal.date_operation,
        "journal": "CHARGES",
        "libelle": libelle,
        "compte_debit": compte_charge,
        "compte_credit": "401000",  # Fournisseur
        "montant": journal.montant_ttc,
        "unite_production": journal.unite_production,
        "type_charge": journal.type_charge
    })
    ecritures.append(ecriture)

    return ecritures


def _calculate_production_cost(db: Session, journal: JournalQuotidien) -> float:
    """
    Calcule le coût de production d'un produit fini ou semi-fini.
    Pour l'instant, basé sur les matières consommées.
    À améliorer avec charges de production.
    """
    # Exemple simplifié : 2.5 m³ de MP001 pour 1 PF001
    recette = {
        "PF001": {"MP001": 2.5},
        "SF001": {"MP001": 1.2}
    }

    produit = get_produit(db, journal.produit_id)
    if not produit or produit.code not in recette:
        return journal.quantite * (produit.prix_achat or 0)

    cout_total = 0
    for code_mp, quantite_mp in recette[produit.code].items():
        mp = db.query(Produit).filter(Produit.code == code_mp).first()
        if mp:
            stock_mp = get_stock_actuel(db, mp.id, journal.unite_production or "GENERAL")
            cout_unitaire_mp = stock_mp.cout_unitaire_moyen if stock_mp else mp.prix_achat or 0
            cout_total += quantite_mp * cout_unitaire_mp * journal.quantite

    # Ajouter 20% pour charges indirectes (à remplacer par répartition réelle)
    cout_total *= 1.2
    return cout_total


def get_dashboard_metrics(db: Session, date_reference: date = None):
    """Calcule les métriques du tableau de bord"""
    if not date_reference:
        date_reference = date.today()

    date_debut = datetime.combine(date_reference, datetime.min.time())
    date_fin = datetime.combine(date_reference, datetime.max.time())

    metrics_today = _calculate_daily_metrics(db, date_reference)
    yesterday = date_reference - timedelta(days=1)
    metrics_yesterday = _calculate_daily_metrics(db, yesterday)

    variations = {}
    for key in ["bois_consomme", "produits_finis", "semi_finis", "dechets", "cout_total_consommation", "cout_total_production"]:
        today_val = metrics_today.get(key, 0)
        yesterday_val = metrics_yesterday.get(key, 0)
        if yesterday_val > 0:
            variations[key] = ((today_val - yesterday_val) / yesterday_val) * 100
        else:
            variations[key] = 100 if today_val > 0 else 0

    return {
        "today": metrics_today,
        "yesterday": metrics_yesterday,
        "variations": variations,
        "date": str(date_reference)
    }


def _calculate_daily_metrics(db: Session, date_ref: date):
    """Calcule les métriques quotidiennes"""
    from sqlalchemy import func

    operations = db.query(JournalQuotidien).filter(
        JournalQuotidien.date_operation >= datetime.combine(date_ref, datetime.min.time()),
        JournalQuotidien.date_operation <= datetime.combine(date_ref, datetime.max.time())
    ).all()

    metrics = {
        "bois_consomme": 0,
        "produits_finis": 0,
        "semi_finis": 0,
        "dechets": 0,
        "cout_total_consommation": 0,
        "cout_total_production": 0,
        "rendement_moyen": 0,
        "total_operations": len(operations),
        "details_unites": {}
    }

    # Initialiser les unités
    units = get_parametres_by_type(db, "unite_production")
    for unit in units:
        metrics["details_unites"][unit.valeur] = {
            "bois_consomme": 0, "produits_finis": 0, "semi_finis": 0,
            "dechets": 0, "cout_consommation": 0, "cout_production": 0
        }

    for op in operations:
        unit_name = op.unite_production or "GENERAL"
        if unit_name not in metrics["details_unites"]:
            metrics["details_unites"][unit_name] = {
                "bois_consomme": 0, "produits_finis": 0, "semi_finis": 0,
                "dechets": 0, "cout_consommation": 0, "cout_production": 0
            }

        unit_data = metrics["details_unites"][unit_name]

        if op.type_journal == "CONSOMMATION" and op.produit and op.produit.famille == "MP":
            metrics["bois_consomme"] += op.quantite
            unit_data["bois_consomme"] += op.quantite
            metrics["cout_total_consommation"] += op.montant_ht
            unit_data["cout_consommation"] += op.montant_ht

        elif op.type_journal == "PRODUCTION" and op.produit:
            metrics["cout_total_production"] += op.montant_ht
            unit_data["cout_production"] += op.montant_ht

            if op.produit.famille == "PF":
                metrics["produits_finis"] += op.quantite
                unit_data["produits_finis"] += op.quantite
            elif op.produit.famille == "SF":
                metrics["semi_finis"] += op.quantite
                unit_data["semi_finis"] += op.quantite
            elif op.produit.famille == "déchet":
                metrics["dechets"] += op.quantite
                unit_data["dechets"] += op.quantite

    # Calcul du rendement
    total_output = metrics["produits_finis"] + metrics["semi_finis"] + metrics["dechets"]
    if metrics["bois_consomme"] > 0:
        metrics["rendement_moyen"] = (total_output / metrics["bois_consomme"]) * 100

    return metrics
