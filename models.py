# models.py
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship, backref
from database import Base
from datetime import datetime


class PlanComptable(Base):
    __tablename__ = "plan_comptable"

    id = Column(Integer, primary_key=True, index=True)
    compte = Column(String(10), unique=True, index=True, nullable=False)
    libelle = Column(String(255), nullable=False)
    classe = Column(Integer, nullable=False)  # 1 à 8
    type_compte = Column(String(20))  # ACTIF, PASSIF, CHARGE, PRODUIT, MIXTE
    niveau = Column(Integer)  # 1: classe, 2: sous-classe, 3: compte détaillé

    # Relations inversées pour les écritures
    ecritures_debit = relationship(
        "EcritureComptable",
        foreign_keys="EcritureComptable.compte_debit",
        back_populates="compte_debit_rel"
    )
    ecritures_credit = relationship(
        "EcritureComptable",
        foreign_keys="EcritureComptable.compte_credit",
        back_populates="compte_credit_rel"
    )

    def __repr__(self):
        return f"<PlanComptable(compte={self.compte}, libelle={self.libelle})>"


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True)
    nom = Column(String(100), nullable=False)
    adresse = Column(Text)
    telephone = Column(String(20))
    email = Column(String(100))
    nif = Column(String(20))
    nis = Column(String(20))
    rc = Column(String(20))
    compte_comptable = Column(String(15), default="411000")
    actif = Column(Boolean, default=True)
    date_creation = Column(DateTime, default=datetime.now)

    # Relations
    factures = relationship("Facture", back_populates="client")
    ecritures = relationship("EcritureComptable", back_populates="client")
    operations = relationship("JournalQuotidien", back_populates="client")
    
    # ✅ CORRECTION : Relation vers les règlements
    reglements = relationship(
        "Reglement", 
        back_populates="client",
        foreign_keys="Reglement.client_id"
    )


class Fournisseur(Base):
    __tablename__ = "fournisseurs"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True)
    nom = Column(String(100), nullable=False)
    adresse = Column(Text)
    telephone = Column(String(20))
    email = Column(String(100))
    nif = Column(String(20))
    nis = Column(String(20))
    rc = Column(String(20))
    compte_comptable = Column(String(15), default="401000")
    actif = Column(Boolean, default=True)
    date_creation = Column(DateTime, default=datetime.now)

    # Relations
    ecritures = relationship("EcritureComptable", back_populates="fournisseur")
    operations = relationship("JournalQuotidien", back_populates="fournisseur")
    
    # ✅ CORRECTION : Relation vers les règlements
    reglements = relationship(
        "Reglement", 
        back_populates="fournisseur",
        foreign_keys="Reglement.fournisseur_id"
    )

class FamilleProduit(Base):
    __tablename__ = "familles_produit"

    id = Column(Integer, primary_key=True, index=True)
    designation = Column(String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<FamilleProduit(designation={self.designation})>"

class Produit(Base):
    __tablename__ = "produits"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    designation = Column(String(255), nullable=False)
    famille = Column(String(10))  # MP, SF, PF, déchet
    unite_mesure = Column(String(20))  # m³, pièces, kg, etc.
    prix_achat = Column(Numeric(15, 2))
    prix_vente = Column(Numeric(15, 2))
    taux_tva = Column(Numeric(5, 2), default=19.0)
    compte_stock = Column(String(10))  # ex: 311001
    compte_achat = Column(String(10))  # ex: 601001
    compte_vente = Column(String(10))  # ex: 701001
    actif = Column(Boolean, default=True)
    date_creation = Column(DateTime, default=datetime.now)

    # Relations
    lignes_facture = relationship("LigneFacture", back_populates="produit")
    operations = relationship("JournalQuotidien", back_populates="produit")
    stocks = relationship("Stock", back_populates="produit")

    def __repr__(self):
        return f"<Produit(designation={self.designation}, code={self.code}, famille={self.famille})>"


class Parametres(Base):
    __tablename__ = "parametres"

    id = Column(Integer, primary_key=True, index=True)
    type_param = Column(String(50), index=True)  # famille_produit, unite_production, etc.
    valeur = Column(String(50))
    description = Column(String(255))

    def __repr__(self):
        return f"<Parametres(type={self.type_param}, valeur={self.valeur})>"


class Facture(Base):
    __tablename__ = "factures"

    id = Column(Integer, primary_key=True, index=True)
    numero_facture = Column(String(50), unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"))
    date_facture = Column(Date, nullable=False)
    montant_ht = Column(Numeric(15, 2), default=0)
    montant_tva = Column(Numeric(15, 2), default=0)
    montant_ttc = Column(Numeric(15, 2), default=0)
    droit_timbre = Column(Numeric(15, 2), default=0)
    montant_net_payer = Column(Numeric(15, 2), default=0)
    date_echeance = Column(Date)
    statut = Column(String(20), default="EN_ATTENTE")  # EN_ATTENTE, PAYEE, PARTIELLEMENT_PAYEE
    mode_reglement = Column(String(20))
    numero_cheque = Column(String(50))
    date_reglement = Column(Date)

    # Relations
    client = relationship("Client", back_populates="factures")
    lignes = relationship("LigneFacture", back_populates="facture")
    reglements = relationship("Reglement", back_populates="facture")
    
    # ✅ CORRECTION : Ajout de la relation manquante
    operations = relationship("JournalQuotidien", back_populates="facture")

    def __repr__(self):
        return f"<Facture(numero={self.numero_facture}, client_id={self.client_id}, ttc={self.montant_ttc})>"


class LigneFacture(Base):
    __tablename__ = "lignes_facture"

    id = Column(Integer, primary_key=True, index=True)
    facture_id = Column(Integer, ForeignKey("factures.id"))
    produit_id = Column(Integer, ForeignKey("produits.id"))
    quantite = Column(Float, nullable=False)
    prix_unitaire = Column(Numeric(15, 2), nullable=False)
    montant_ht = Column(Numeric(15, 2), nullable=False)
    taux_tva = Column(Numeric(5, 2), default=19.0)
    montant_tva = Column(Numeric(15, 2), nullable=False)

    # Relations
    facture = relationship("Facture", back_populates="lignes")
    produit = relationship("Produit", back_populates="lignes_facture")


class JournalQuotidien(Base):
    __tablename__ = "journal_quotidien"

    id = Column(Integer, primary_key=True, index=True)
    date_operation = Column(DateTime, default=datetime.now)
    type_journal = Column(String(20), nullable=False)  # ACHAT, VENTE, CAISSE, PRODUCTION, CONSOMMATION, CHARGES
    type_document = Column(String(20))  # BL, FACTURE, AVOIR
    numero_piece = Column(String(50), nullable=False)
    libelle = Column(String(255), nullable=False)
    produit_id = Column(Integer, ForeignKey("produits.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    fournisseur_id = Column(Integer, ForeignKey("fournisseurs.id"), nullable=True)
    unite_production = Column(String(50))  # Atelier, Scierie, Broyeur
    quantite = Column(Float, default=0.0)
    prix_unitaire = Column(Numeric(15, 2), default=0)
    montant_ht = Column(Numeric(15, 2), default=0)
    taux_tva = Column(Numeric(5, 2), default=19.0)
    montant_tva = Column(Numeric(15, 2), default=0)
    montant_ttc = Column(Numeric(15, 2), default=0)
    tva_applicable = Column(Boolean, default=True)
    dt_applicable = Column(Boolean, default=True)
    droit_timbre = Column(Numeric(15, 2), default=0)
    facture_id = Column(Integer, ForeignKey("factures.id"), nullable=True)
    avoir_origine_id = Column(Integer, ForeignKey("journal_quotidien.id"), nullable=True)
    comptabilisee = Column(Boolean, default=False)
    date_comptabilisation = Column(DateTime, nullable=True)

    # Champs transport
    adresse_livraison = Column(Text, nullable=True)
    matricule_camion = Column(String(20), nullable=True)

    # Champs charges
    type_charge = Column(String(50), nullable=True)  # MO, Électricité, Amortissement
    centre_production = Column(String(50), nullable=True)

    # Relations
    client = relationship("Client", back_populates="operations")
    fournisseur = relationship("Fournisseur", back_populates="operations")
    produit = relationship("Produit", back_populates="operations")
    facture = relationship("Facture", back_populates="operations")
    avoir_origine = relationship("JournalQuotidien", remote_side=[id])

    def __repr__(self):
        return f"<JournalQuotidien(type={self.type_journal}, piece={self.numero_piece}, montant={self.montant_ttc})>"


class EcritureComptable(Base):
    __tablename__ = "ecritures_comptables"

    id = Column(Integer, primary_key=True, index=True)
    journal_id = Column(Integer, ForeignKey("journal_quotidien.id"), nullable=True)
    date_comptable = Column(Date, nullable=False)
    journal = Column(String(50), nullable=False)
    reference = Column(String(50))
    libelle = Column(String(255), nullable=False)
    compte_debit = Column(String(10), ForeignKey("plan_comptable.compte"), nullable=False)
    compte_credit = Column(String(10), ForeignKey("plan_comptable.compte"), nullable=False)
    montant = Column(Numeric(15, 2), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    fournisseur_id = Column(Integer, ForeignKey("fournisseurs.id"), nullable=True)
    numero_facture = Column(String(50))
    date_creation = Column(DateTime, default=datetime.now)

    # Relations
    journal = relationship("JournalQuotidien")
    client = relationship("Client", back_populates="ecritures")
    fournisseur = relationship("Fournisseur", back_populates="ecritures")
    compte_debit_rel = relationship("PlanComptable", foreign_keys=[compte_debit])
    compte_credit_rel = relationship("PlanComptable", foreign_keys=[compte_credit])

    def __repr__(self):
        return f"<EcritureComptable(debit={self.compte_debit}, credit={self.compte_credit}, montant={self.montant})>"


class Tresorerie(Base):
    __tablename__ = "tresorerie"

    id = Column(Integer, primary_key=True, index=True)
    date_operation = Column(Date, nullable=False)
    type_operation = Column(String(20))  # ENCAISSEMENT, DECAISSEMENT
    libelle = Column(String(255), nullable=False)
    montant = Column(Numeric(15, 2), nullable=False)
    mode_paiement = Column(String(20))  # ESPECES, CHEQUE, VIREMENT
    numero_piece = Column(String(50))
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    fournisseur_id = Column(Integer, ForeignKey("fournisseurs.id"), nullable=True)
    date_creation = Column(DateTime, default=datetime.now)

    # Relations
    client = relationship("Client")
    fournisseur = relationship("Fournisseur")


class Production(Base):
    __tablename__ = "production"

    id = Column(Integer, primary_key=True, index=True)
    date_production = Column(Date, nullable=False)
    unite_production = Column(String(50))  # Atelier, Scierie
    produit_id = Column(Integer, ForeignKey("produits.id"))
    quantite_produite = Column(Float, nullable=False)
    cout_total = Column(Numeric(15, 2), default=0)
    responsable = Column(String(100))
    observations = Column(Text)
    date_creation = Column(DateTime, default=datetime.now)

    # Relations
    produit = relationship("Produit")


class Reglement(Base):
    __tablename__ = "reglements"

    id = Column(Integer, primary_key=True, index=True)
    facture_id = Column(Integer, ForeignKey("factures.id"), nullable=False)
    montant = Column(Numeric(15, 2), nullable=False)
    mode = Column(String(20), nullable=False)  # ESPÈCES, CHÈQUE, VIREMENT
    numero_cheque = Column(String(50))
    date_reglement = Column(Date, nullable=False)
    commentaire = Column(Text)
    
    # ✅ CORRECTION : Colonnes ajoutées pour résoudre l'erreur
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    fournisseur_id = Column(Integer, ForeignKey("fournisseurs.id"), nullable=True)

    # Relations
    facture = relationship("Facture", back_populates="reglements")
    client = relationship("Client", back_populates="reglements")
    fournisseur = relationship("Fournisseur", back_populates="reglements")


class Sequence(Base):
    __tablename__ = "sequences"

    id = Column(Integer, primary_key=True)
    annee = Column(Integer, unique=True, nullable=False)
    dernier_numero = Column(Integer, default=0)


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True)
    produit_id = Column(Integer, ForeignKey("produits.id"))
    unite_production = Column(String(50), nullable=False)
    quantite = Column(Float, default=0.0)
    cout_unitaire_moyen = Column(Numeric(15, 2), default=0)
    valeur_stock = Column(Numeric(15, 2), default=0)
    date_derniere_operation = Column(DateTime, default=datetime.now)

    # Relations
    produit = relationship("Produit", back_populates="stocks")
