from sqlalchemy.orm import Session
from models import JournalQuotidien, EcritureComptable, Operation, Stock
from crud import *
import services.accounting as accounting
import services.production as production
from datetime import datetime



def process_journal_entry(db: Session, journal_entry: JournalQuotidien):
    """
    Traite une écriture de journal et génère les écritures comptables correspondantes
    """
    if journal_entry.comptabilisee:
        return {"status": "error", "message": "Cette écriture est déjà comptabilisée"}
    
    ecritures = []
    
    try:
        if journal_entry.type_journal == "ACHAT":
            ecritures = _process_achat(db, journal_entry)
        elif journal_entry.type_journal == "VENTE":
            ecritures = _process_vente(db, journal_entry)
        elif journal_entry.type_journal == "CAISSE":
            ecritures = _process_caisse(db, journal_entry)
        elif journal_entry.type_journal == "PRODUCTION":
            ecritures = _process_production(db, journal_entry)
        elif journal_entry.type_journal == "CONSOMMATION":
            ecritures = _process_consommation(db, journal_entry)
        
        # Marquer comme comptabilisé
        journal_entry.comptabilisee = True
        db.commit()
        
        return {
            "status": "success", 
            "message": f"{len(ecritures)} écritures comptables générées",
            "ecritures": ecritures
        }
        
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

def _process_achat(db: Session, journal: JournalQuotidien):
    """Traite un achat"""
    ecritures = []
    
    # Récupérer le produit et le fournisseur
    produit = get_produit(db, journal.produit_id)
    fournisseur = get_fournisseur(db, journal.fournisseur_id)
    
    if not produit or not fournisseur:
        raise ValueError("Produit ou fournisseur introuvable")
    
    # Écriture principale : Débit Stock / Crédit Fournisseur
    ecriture_stock = create_ecriture_comptable(db, {
        "journal_id": journal.id,
        "date_comptable": journal.date_operation,
        "journal": "ACHATS",
        "libelle": f"Achat {journal.quantite} {produit.unite_mesure} {produit.designation}",
        "compte_debit": produit.compte_stock or "311000",
        "compte_credit": fournisseur.compte_comptable,
        "montant": journal.montant_ht,
        "produit_id": journal.produit_id,
        "fournisseur_id": journal.fournisseur_id,
        "quantite": journal.quantite,
        "unite_mesure": produit.unite_mesure,
        "numero_facture": journal.numero_piece
    })
    ecritures.append(ecriture_stock)
    
    # Écriture TVA si applicable
    if journal.montant_tva > 0:
        ecriture_tva = create_ecriture_comptable(db, {
            "journal_id": journal.id,
            "date_comptable": journal.date_operation,
            "journal": "ACHATS",
            "libelle": f"TVA déductible sur achat {produit.designation}",
            "compte_debit": "4456",  # TVA déductible
            "compte_credit": fournisseur.compte_comptable,
            "montant": journal.montant_tva,
            "fournisseur_id": journal.fournisseur_id,
            "taux_tva": journal.taux_tva,
            "numero_facture": journal.numero_piece
        })
        ecritures.append(ecriture_tva)
    
    # Mettre à jour le stock
    _update_stock_achat(db, journal, produit)
    
    # Créer l'opération correspondante
    _create_operation_from_journal(db, journal, "achat")
    
    return ecritures

def _process_vente(db: Session, journal: JournalQuotidien):
    """Traite une vente avec gestion TVA et droit de timbre"""
    ecritures = []
    
    # Ne comptabiliser que si c'est une FACTURE
    if journal.type_document == "BL":
        return ecritures  # Pas de comptabilisation pour les BL
    
    # Récupérer le produit et le client
    produit = get_produit(db, journal.produit_id)
    client = get_client(db, journal.client_id)
    
    if not produit or not client:
        raise ValueError("Produit ou client introuvable")
    
    # Écriture principale : Débit Client / Crédit Vente
    libelle_detaille = f"Vente {journal.quantite} {produit.unite_mesure} {produit.designation} - {journal.libelle}"
    
    ecriture_vente = create_ecriture_comptable(db, {
        "journal_id": journal.id,
        "date_comptable": journal.date_operation,
        "journal": "VENTES",
        "libelle": libelle_detaille,
        "compte_debit": client.compte_comptable,
        "compte_credit": produit.compte_vente or "701000",
        "montant": journal.montant_ht,
        "produit_id": journal.produit_id,
        "client_id": journal.client_id,
        "quantite": journal.quantite,
        "unite_mesure": produit.unite_mesure,
        "numero_facture": journal.numero_piece
    })
    ecritures.append(ecriture_vente)
    
    # Écriture TVA si applicable
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
            "taux_tva": journal.taux_tva,
            "numero_facture": journal.numero_piece
        })
        ecritures.append(ecriture_tva)
    
    # Écriture droit de timbre si applicable
    if journal.dt_applicable and journal.droit_timbre > 0:
        ecriture_dt = create_ecriture_comptable(db, {
            "journal_id": journal.id,
            "date_comptable": journal.date_operation,
            "journal": "VENTES",
            "libelle": f"Droit de timbre - {journal.libelle}",
            "compte_debit": client.compte_comptable,
            "compte_credit": "4458",  # Compte droit de timbre
            "montant": journal.droit_timbre,
            "client_id": journal.client_id,
            "numero_facture": journal.numero_piece
        })
        ecritures.append(ecriture_dt)
    
    # Écriture de sortie de stock (coût des ventes)
    stock_actuel = get_stock_actuel(db, journal.produit_id, journal.unite_production)
    if stock_actuel and stock_actuel.quantite >= journal.quantite:
        cout_sortie = journal.quantite * stock_actuel.cout_unitaire_moyen
        
        ecriture_cout = create_ecriture_comptable(db, {
            "journal_id": journal.id,
            "date_comptable": journal.date_operation,
            "journal": "VENTES",
            "libelle": f"Coût des ventes {produit.designation} - {journal.libelle}",
            "compte_debit": "601000",
            "compte_credit": produit.compte_stock or "311000",
            "montant": cout_sortie,
            "produit_id": journal.produit_id,
            "quantite": journal.quantite,
            "unite_mesure": produit.unite_mesure
        })
        ecritures.append(ecriture_cout)
        
        # Mettre à jour le stock
        _update_stock_sortie(db, journal, produit, cout_sortie)
    
    # Créer l'opération correspondante
    _create_operation_from_journal(db, journal, "vente")
    
    return ecritures

def _process_caisse(db: Session, journal: JournalQuotidien):
    """Traite une opération de caisse"""
    ecritures = []
    
    # Déterminer le sens de l'opération (recette ou dépense)
    if journal.montant_ttc > 0:
        # Recette : Débit Caisse / Crédit compte de produit
        compte_contrepartie = "758000"  # Produits divers
        if journal.client_id:
            client = get_client(db, journal.client_id)
            compte_contrepartie = client.compte_comptable
        
        ecriture = create_ecriture_comptable(db, {
            "journal_id": journal.id,
            "date_comptable": journal.date_operation,
            "journal": "CAISSE",
            "libelle": journal.libelle,
            "compte_debit": "530000",  # Caisse
            "compte_credit": compte_contrepartie,
            "montant": abs(journal.montant_ttc),
            "client_id": journal.client_id,
            "numero_facture": journal.numero_piece
        })
    else:
        # Dépense : Débit compte de charge / Crédit Caisse
        compte_contrepartie = "658000"  # Charges diverses
        if journal.fournisseur_id:
            fournisseur = get_fournisseur(db, journal.fournisseur_id)
            compte_contrepartie = fournisseur.compte_comptable
        
        ecriture = create_ecriture_comptable(db, {
            "journal_id": journal.id,
            "date_comptable": journal.date_operation,
            "journal": "CAISSE",
            "libelle": journal.libelle,
            "compte_debit": compte_contrepartie,
            "compte_credit": "530000",  # Caisse
            "montant": abs(journal.montant_ttc),
            "fournisseur_id": journal.fournisseur_id,
            "numero_facture": journal.numero_piece
        })
    
    ecritures.append(ecriture)
    return ecritures

def _process_production(db: Session, journal: JournalQuotidien):
    """Traite une production avec libellé détaillé"""
    ecritures = []
    
    produit = get_produit(db, journal.produit_id)
    if not produit:
        raise ValueError("Produit introuvable")
    
    # Calculer le coût de production basé sur le stock actuel des MP
    cout_production = _calculate_production_cost(db, journal)
    
    # Mettre à jour le montant HT avec le coût calculé
    journal.montant_ht = cout_production
    journal.montant_ttc = cout_production  # Pas de TVA sur production interne
    
    libelle_detaille = f"Production {journal.quantite} {produit.unite_mesure} {produit.designation} - {journal.libelle}"
    
    # Écriture : Débit Stock produit / Crédit Production stockée
    ecriture = create_ecriture_comptable(db, {
        "journal_id": journal.id,
        "date_comptable": journal.date_operation,
        "journal": "PRODUCTION",
        "libelle": libelle_detaille,
        "compte_debit": produit.compte_stock or "311000",
        "compte_credit": "713000",
        "montant": cout_production,
        "produit_id": journal.produit_id,
        "quantite": journal.quantite,
        "unite_mesure": produit.unite_mesure
    })
    ecritures.append(ecriture)
    
    # Mettre à jour le stock
    _update_stock_production(db, journal, produit)
    
    # Créer l'opération correspondante
    _create_operation_from_journal(db, journal, "production")
    
    return ecritures

def _process_consommation(db: Session, journal: JournalQuotidien):
    """Traite une consommation avec libellé détaillé"""
    ecritures = []
    
    produit = get_produit(db, journal.produit_id)
    if not produit:
        raise ValueError("Produit introuvable")
    
    # Calculer le coût de consommation basé sur le CUMP
    stock_actuel = get_stock_actuel(db, journal.produit_id, journal.unite_production)
    if not stock_actuel:
        raise ValueError(f"Pas de stock disponible pour {produit.designation}")
    
    cout_consommation = journal.quantite * stock_actuel.cout_unitaire_moyen
    
    # Mettre à jour le montant HT avec le coût calculé
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
        "unite_mesure": produit.unite_mesure
    })
    ecritures.append(ecriture)
    
    # Mettre à jour le stock
    _update_stock_consommation(db, journal, produit)
    
    # Créer l'opération correspondante
    _create_operation_from_journal(db, journal, "consommation")
    
    return ecritures

def _calculate_production_cost(db: Session, journal: JournalQuotidien):
    """Calcule le coût de production basé sur les consommations"""
    # Pour simplifier, on peut utiliser un coût standard ou calculer basé sur les MP consommées
    # Ici, on utilise un coût moyen des matières premières
    
    # Récupérer les MP de la même unité de production
    mp_stocks = db.query(Stock).join(Produit).filter(
        and_(
            Produit.famille == "MP",
            Stock.unite_production == journal.unite_production
        )
    ).all()
    
    if mp_stocks:
        cout_moyen_mp = sum(s.cout_unitaire_moyen for s in mp_stocks) / len(mp_stocks)
        # Facteur de transformation (à ajuster selon votre logique métier)
        facteur_transformation = 1.2  # 20% de coût de transformation
        return journal.quantite * cout_moyen_mp * facteur_transformation
    
    return 0

def _update_stock_achat(db: Session, journal: JournalQuotidien, produit: Produit):
    """Met à jour le stock pour un achat"""
    stock_actuel = get_stock_actuel(db, produit.id, journal.unite_production)
    
    if stock_actuel:
        # Calculer le nouveau coût moyen pondéré (CUMP)
        # Formule CUMP: (stock_initial * cump_initial + qte_entree * prix_achat) / (stock_initial + qte_entree)
        ancienne_valeur_totale = stock_actuel.quantite * stock_actuel.cout_unitaire_moyen
        
        nouvelle_quantite = stock_actuel.quantite + journal.quantite
        nouvelle_valeur_totale = ancienne_valeur_totale + journal.montant_ht
        
        nouveau_cout_moyen = nouvelle_valeur_totale / nouvelle_quantite if nouvelle_quantite > 0 else 0
        
        # Mettre à jour l'entrée de stock existante ou la plus récente
        stock_actuel.quantite = nouvelle_quantite
        stock_actuel.cout_unitaire_moyen = nouveau_cout_moyen
        stock_actuel.valeur_stock = nouvelle_valeur_totale
        stock_actuel.date = journal.date_operation # Date de l'opération
    else:
        # Créer une nouvelle entrée de stock si le stock n'existe pas pour ce produit/unité
        nouveau_stock = Stock(
            produit_id=produit.id,
            date=journal.date_operation,
            quantite=journal.quantite,
            cout_unitaire_moyen=journal.prix_unitaire if journal.prix_unitaire else (journal.montant_ht / journal.quantite if journal.quantite > 0 else 0),
            valeur_stock=journal.montant_ht,
            unite_production=journal.unite_production
        )
        db.add(nouveau_stock)
    
    db.commit()

def _update_stock_sortie(db: Session, journal: JournalQuotidien, produit: Produit, cout_sortie: float):
    """Met à jour le stock pour une sortie (vente ou consommation)"""
    stock_actuel = get_stock_actuel(db, produit.id, journal.unite_production)
    
    if not stock_actuel or stock_actuel.quantite < journal.quantite:
        raise ValueError(f"Stock insuffisant pour le produit {produit.designation} dans l'unité {journal.unite_production}")
    
    # Diminuer la quantité et la valeur du stock
    stock_actuel.quantite -= journal.quantite
    stock_actuel.valeur_stock -= cout_sortie
    # Le coût unitaire moyen reste le même pour les sorties
    
    db.commit()

def _update_stock_production(db: Session, journal: JournalQuotidien, produit: Produit):
    """Met à jour le stock pour une production (ajout de PF/SF)"""
    stock_actuel = get_stock_actuel(db, produit.id, journal.unite_production)
    
    if stock_actuel:
        # Mettre à jour l'entrée de stock existante
        ancienne_valeur_totale = stock_actuel.quantite * stock_actuel.cout_unitaire_moyen
        
        nouvelle_quantite = stock_actuel.quantite + journal.quantite
        nouvelle_valeur_totale = ancienne_valeur_totale + journal.montant_ht # Coût de production
        
        nouveau_cout_moyen = nouvelle_valeur_totale / nouvelle_quantite if nouvelle_quantite > 0 else 0
        
        stock_actuel.quantite = nouvelle_quantite
        stock_actuel.cout_unitaire_moyen = nouveau_cout_moyen
        stock_actuel.valeur_stock = nouvelle_valeur_totale
        stock_actuel.date = journal.date_operation
    else:
        # Créer une nouvelle entrée de stock
        nouveau_stock = Stock(
            produit_id=produit.id,
            date=journal.date_operation,
            quantite=journal.quantite,
            cout_unitaire_moyen=journal.montant_ht / journal.quantite if journal.quantite > 0 else 0, # Coût de production unitaire
            valeur_stock=journal.montant_ht,
            unite_production=journal.unite_production
        )
        db.add(nouveau_stock)
    
    db.commit()

def _update_stock_consommation(db: Session, journal: JournalQuotidien, produit: Produit):
    """Met à jour le stock pour une consommation (diminution de MP)"""
    # La consommation est une sortie de stock, donc la fonction _update_stock_sortie peut être réutilisée
    # Il faut déterminer le coût de sortie pour la consommation.
    stock_actuel = get_stock_actuel(db, produit.id, journal.unite_production)
    
    if not stock_actuel or stock_actuel.quantite < journal.quantite:
        raise ValueError(f"Stock insuffisant pour le produit {produit.designation} dans l'unité {journal.unite_production}")
    
    cout_sortie = journal.quantite * stock_actuel.cout_unitaire_moyen # Utiliser le CUMP du stock
    
    _update_stock_sortie(db, journal, produit, cout_sortie)
    db.commit()

def _create_operation_from_journal(db: Session, journal: JournalQuotidien, op_type: str):
    """Crée une entrée dans la table Operations à partir d'une entrée de JournalQuotidien"""
    
    operation_data = {
        "journal_id": journal.id,
        "date_comptable": journal.date_operation,
        "unite_production": journal.unite_production if journal.unite_production else "GENERAL", # Peut être null pour achat/vente/caisse
        "type_operation": op_type,
        "produit_id": journal.produit_id,
        "client_id": journal.client_id,
        "fournisseur_id": journal.fournisseur_id,
        "quantite": journal.quantite,
        "cout_unitaire": journal.prix_unitaire,
        "montant": journal.montant_ttc, # Ou montant_ht selon la nature de l'opération
        "libelle": journal.libelle,
        "validee": True # L'opération est validée si elle vient d'un journal traité
    }
    
    # Ajustement du montant pour les opérations internes (consommation/production) qui ne sont pas TTC
    if op_type in ["consommation", "production"]:
        operation_data["montant"] = journal.montant_ht
    
    # Générer une référence unique pour l'opération
    op_ref_base = f"{op_type.upper()}-{journal.date_operation.strftime('%Y%m%d')}"
    # Trouver le prochain numéro de séquence pour la référence
    existing_ops_count = db.query(Operation).filter(Operation.reference.like(f"{op_ref_base}%")).count()
    operation_data["reference"] = f"{op_ref_base}-{existing_ops_count + 1:04d}"

    db_operation = Operation(**operation_data)
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    return db_operation
