# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, select
from models import *
from datetime import datetime, date
import math
# ========================
# GESTION DES FAMILLES DE PRODUITS
# ========================
def get_familles_produit(db: Session):
    return db.query(FamilleProduit).all()

def create_famille_produit(db: Session, famille_data: dict):
    db_famille = FamilleProduit(**famille_data)
    db.add(db_famille)
    db.commit()
    db.refresh(db_famille)
    return db_famille

def update_famille_produit(db: Session, famille_id: int, famille_data: dict):
    db_famille = db.query(FamilleProduit).filter(FamilleProduit.id == famille_id).first()
    if db_famille:
        for key, value in famille_data.items():
            setattr(db_famille, key, value)
        db.commit()
        db.refresh(db_famille)
    return db_famille

def delete_famille_produit(db: Session, famille_id: int):
    db_famille = db.query(FamilleProduit).filter(FamilleProduit.id == famille_id).first()
    if db_famille:
        db.delete(db_famille)
        db.commit()
    return db_famille

# ========================
# GESTION DES PRODUITS
# ========================
def get_produits(db: Session):
    return db.query(Produit).all()

def create_produit(db: Session, produit_data: dict):
    db_produit = Produit(**produit_data)
    db.add(db_produit)
    db.commit()
    db.refresh(db_produit)
    return db_produit

def update_produit(db: Session, produit_id: int, produit_data: dict):
    db_produit = db.query(Produit).filter(Produit.id == produit_id).first()
    if db_produit:
        for key, value in produit_data.items():
            setattr(db_produit, key, value)
        db.commit()
        db.refresh(db_produit)
    return db_produit

def delete_produit(db: Session, produit_id: int):
    db_produit = db.query(Produit).filter(Produit.id == produit_id).first()
    if db_produit:
        db.delete(db_produit)
        db.commit()
    return db_produit

# ========================
# GESTION DES OPÉRATIONS DE PRODUCTION
# ========================
def get_production_for_product(db: Session, product_id: int, start_date: datetime, end_date: datetime):
    """Récupère la quantité produite pour un produit donné dans une période."""
    return db.query(func.sum(Production.quantite_produite)).filter(
        Production.produit_id == product_id,
        Production.date_production >= start_date,
        Production.date_production <= end_date
    ).scalar() or 0

def get_consumption_for_product(db: Session, product_id: int, start_date: datetime, end_date: datetime):
    """Récupère la quantité consommée pour un produit donné dans une période."""
    return db.query(func.sum(JournalQuotidien.quantite)).filter(
        JournalQuotidien.produit_id == product_id,
        JournalQuotidien.type_journal == "CONSOMMATION",
        JournalQuotidien.date_operation >= start_date,
        JournalQuotidien.date_operation <= end_date
    ).scalar() or 0

def get_sales_for_product(db: Session, product_id: int, start_date: datetime, end_date: datetime):
    """Récupère la quantité vendue pour un produit donné dans une période."""
    return db.query(func.sum(JournalQuotidien.quantite)).filter(
        JournalQuotidien.produit_id == product_id,
        JournalQuotidien.type_journal == "VENTE",
        JournalQuotidien.date_operation >= start_date,
        JournalQuotidien.date_operation <= end_date
    ).scalar() or 0

def get_initial_stock_for_product(db: Session, product_id: int, start_date: datetime):
    """Récupère le stock initial d'un produit donné au début d'une période."""
    return db.query(func.sum(Stock.quantite)).filter(
        Stock.produit_id == product_id,
        Stock.date_derniere_operation < start_date
    ).scalar() or 0

# ========================
# GESTION DES CLIENTS
# ========================
def get_clients(db: Session, actif_only=True):
    query = db.query(Client)
    if actif_only:
        query = query.filter(Client.actif == True)
    return query.all()


def get_client(db: Session, client_id: int):
    return db.query(Client).filter(Client.id == client_id).first()


def create_client(db: Session, client_data: dict):
    db_client = Client(**client_data)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def update_client(db: Session, client_id: int, client_data: dict):
    db_client = get_client(db, client_id)
    if db_client:
        for key, value in client_data.items():
            setattr(db_client, key, value)
        db.commit()
        db.refresh(db_client)
    return db_client


# ========================
# GESTION DES FOURNISSEURS
# ========================
def get_fournisseurs(db: Session, actif_only=True):
    query = db.query(Fournisseur)
    if actif_only:
        query = query.filter(Fournisseur.actif == True)
    return query.all()


def get_fournisseur(db: Session, fournisseur_id: int):
    return db.query(Fournisseur).filter(Fournisseur.id == fournisseur_id).first()


def create_fournisseur(db: Session, fournisseur_data: dict):
    db_fournisseur = Fournisseur(**fournisseur_data)
    db.add(db_fournisseur)
    db.commit()
    db.refresh(db_fournisseur)
    return db_fournisseur


def update_fournisseur(db: Session, fournisseur_id: int, fournisseur_data: dict):
    db_fournisseur = get_fournisseur(db, fournisseur_id)
    if db_fournisseur:
        for key, value in fournisseur_data.items():
            setattr(db_fournisseur, key, value)
        db.commit()
        db.refresh(db_fournisseur)
    return db_fournisseur


# ========================
# GESTION DES PARAMÈTRES
# ========================
def get_parametres_by_type(db: Session, type_param: str):
    return db.query(Parametres).filter(Parametres.type_param == type_param).all()


def create_parametre(db: Session, param_data: dict):
    db_param = Parametres(**param_data)
    db.add(db_param)
    db.commit()
    db.refresh(db_param)
    return db_param


# ========================
# GESTION DU PLAN COMPTABLE
# ========================
def get_all_comptes(db: Session):
    return db.query(PlanComptable).all()


def get_compte_by_code(db: Session, compte: str):
    return db.query(PlanComptable).filter(PlanComptable.compte == compte).first()


def create_compte(db: Session, compte_data: dict):
    db_compte = PlanComptable(**compte_data)
    db.add(db_compte)
    db.commit()
    db.refresh(db_compte)
    return db_compte


# ========================
# GESTION DU JOURNAL QUOTIDIEN
# ========================
def get_journal_entries(db: Session, date_debut: date = None, date_fin: date = None, comptabilisee: bool = None, limit: int = None):
    query = db.query(JournalQuotidien).order_by(desc(JournalQuotidien.date_operation))

    if date_debut:
        query = query.filter(JournalQuotidien.date_operation >= datetime.combine(date_debut, datetime.min.time()))
    if date_fin:
        query = query.filter(JournalQuotidien.date_operation <= datetime.combine(date_fin, datetime.max.time()))
    if comptabilisee is not None:
        query = query.filter(JournalQuotidien.comptabilisee == comptabilisee)

    if limit is not None:
        query = query.limit(limit)

    return query.all()


def create_journal_entry(db: Session, journal_data: dict):
    db_journal = JournalQuotidien(**journal_data)
    db.add(db_journal)
    db.commit()
    db.refresh(db_journal)
    return db_journal


# ========================
# GESTION DES ÉCRITURES COMPTABLES
# ========================
def get_ecritures_comptables(db: Session, date_debut: date = None, date_fin: date = None, limit: int = None):
    query = db.query(EcritureComptable).order_by(desc(EcritureComptable.date_comptable))

    if date_debut:
        query = query.filter(EcritureComptable.date_comptable >= date_debut)
    if date_fin:
        query = query.filter(EcritureComptable.date_comptable <= date_fin)

    if limit:
        query = query.limit(limit)

    return query.all()


def create_ecriture_comptable(db: Session, ecriture_data: dict):
    db_ecriture = EcritureComptable(**ecriture_data)
    db.add(db_ecriture)
    db.commit()
    db.refresh(db_ecriture)
    return db_ecriture


# ========================
# GESTION DES FACTURES
# ========================
def get_factures(db: Session, client_id: int = None, statut: str = None):
    query = db.query(Facture).order_by(desc(Facture.date_facture))
    if client_id:
        query = query.filter(Facture.client_id == client_id)
    if statut:
        query = query.filter(Facture.statut == statut)
    return query.all()


def get_facture(db: Session, facture_id: int):
    return db.query(Facture).filter(Facture.id == facture_id).first()


def generer_numero_facture(db: Session) -> str:
    """Génère un numéro de facture au format FACT-2025/0001"""
    annee = datetime.now().year
    seq = db.query(Sequence).filter(Sequence.annee == annee).first()
    if not seq:
        seq = Sequence(annee=annee, dernier_numero=0)
        db.add(seq)
        db.commit()
    seq.dernier_numero += 1
    db.commit()
    return f"FACT-{annee}/{seq.dernier_numero:04d}"


def create_facture(db: Session, facture_data: dict):
    # Générer automatiquement le numéro
    if "numero_facture" not in facture_data or not facture_data["numero_facture"]:
        facture_data["numero_facture"] = generer_numero_facture(db)

    db_facture = Facture(**facture_data)
    db.add(db_facture)
    db.commit()
    db.refresh(db_facture)
    return db_facture


def add_ligne_facture(db: Session, ligne_data: dict):
    db_ligne = LigneFacture(**ligne_data)
    db.add(db_ligne)
    db.commit()
    db.refresh(db_ligne)
    return db_ligne


# ========================
# GESTION DES RÈGLEMENTS
# ========================
def create_reglement(db: Session, reglement_data: dict):
    reglement = Reglement(**reglement_data)
    db.add(reglement)
    db.commit()
    db.refresh(reglement)

    # Mettre à jour le statut de la facture
    facture = get_facture(db, reglement.facture_id)
    total_reglements = sum(r.montant for r in facture.reglements)
    if total_reglements >= facture.montant_net_payer:
        facture.statut = "PAYEE"
    elif total_reglements > 0:
        facture.statut = "PARTIELLEMENT_PAYEE"
    else:
        facture.statut = "EN_ATTENTE"
    db.commit()
    return reglement


# ========================
# GESTION DES STOCKS
# ========================
def get_stock_actuel(db: Session, produit_id: int, unite_production: str = None):
    """Retourne le stock actuel d'un produit (CMP)"""
    query = db.query(Stock).filter(Stock.produit_id == produit_id)
    if unite_production:
        query = query.filter(Stock.unite_production == unite_production)
    return query.first()


def update_stock(db: Session, produit_id: int, unite_production: str, quantite: float, cout_unitaire: float = None):
    """Met à jour le stock avec CMP"""
    stock = get_stock_actuel(db, produit_id, unite_production)
    if not stock:
        stock = Stock(
            produit_id=produit_id,
            unite_production=unite_production,
            quantite=0,
            cout_unitaire_moyen=cout_unitaire or 0,
            valeur_stock=0
        )
        db.add(stock)

    ancienne_valeur = stock.quantite * stock.cout_unitaire_moyen
    nouvelle_quantite = stock.quantite + quantite
    nouvelle_valeur = ancienne_valeur + (quantite * cout_unitaire if cout_unitaire else 0)

    if nouvelle_quantite > 0:
        stock.cout_unitaire_moyen = nouvelle_valeur / nouvelle_quantite
    else:
        stock.cout_unitaire_moyen = 0

    stock.quantite = max(0, nouvelle_quantite)
    stock.valeur_stock = stock.quantite * stock.cout_unitaire_moyen
    stock.date_derniere_operation = datetime.now()

    db.commit()
    db.refresh(stock)
    return stock


# ========================
# GESTION DES UNITÉS DE PRODUCTION
# ========================
def get_unites_production(db: Session):
    return get_parametres_by_type(db, "unite_production")


# ========================
# CALCUL DU DROIT DE TIMBRE (Algérie)
# ========================
def calcul_droit_timbre(montant: float) -> float:
    """Calcule le droit de timbre selon la loi algérienne"""
    if montant <= 30000:
        tranches = math.ceil(montant / 100)
        droit = tranches * 1
    elif montant <= 100000:
        tranches = math.ceil(montant / 100)
        droit = tranches * 0.5
    else:
        tranches = math.ceil(montant / 100)
        droit = tranches * 0.25
    return max(droit, 5.0)  # Minimum 5 DA


# ========================
# GESTION DE LA TRÉSORERIE
# ========================
def get_balance_tresorerie(db: Session):
    """Calcule la balance de trésorerie (caisse + banque)"""
    encaissements = db.query(func.sum(EcritureComptable.montant)).filter(
        EcritureComptable.compte_debit.like('5%'),
        EcritureComptable.compte_credit.like('4%')
    ).scalar() or 0

    decaissements = db.query(func.sum(EcritureComptable.montant)).filter(
        EcritureComptable.compte_debit.like('4%'),
        EcritureComptable.compte_credit.like('5%')
    ).scalar() or 0

    return encaissements - decaissements


# ========================
# GESTION DES CRÉANCES ET DETTES
# ========================
def get_creances_clients(db: Session):
    """Retourne les créances clients (factures impayées)"""
    return db.query(Facture).filter(
        Facture.statut.in_(["EN_ATTENTE", "PARTIELLEMENT_PAYEE"])
    ).all()


def get_dettes_fournisseurs(db: Session):
    """Retourne les dettes fournisseurs (factures impayées)"""
    # Note : Dans notre modèle, les dettes fournisseurs seraient des factures fournisseurs impayées
    # Mais nous n'avons pas de modèle FactureFournisseur, donc nous utilisons juste les factures clients
    return []


# ========================
# GESTION DES OPÉRATIONS
# ========================
def get_operations(db: Session, date_debut: date = None, date_fin: date = None):
    query = db.query(JournalQuotidien).order_by(desc(JournalQuotidien.date_operation))
    if date_debut:
        query = query.filter(JournalQuotidien.date_operation >= date_debut)
    if date_fin:
        query = query.filter(JournalQuotidien.date_operation <= date_fin)
    return query.all()
