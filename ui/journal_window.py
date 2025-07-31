# ui/journal_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import SessionLocal
import crud
import services.accounting as accounting
from models import JournalQuotidien
from tkcalendar import DateEntry


class JournalWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Frame pour la date et le type
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        # Date
        ttk.Label(top_frame, text="Date:").pack(side=tk.LEFT, padx=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        # Dans create_widgets() - Configuration du DateEntry
        self.date_entry = DateEntry(
            top_frame,
            textvariable=self.date_var,
            date_pattern="dd/mm/yyyy",  # Format visuel pour l'utilisateur
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2
        )
        # Initialiser la valeur au format YYYY-MM-DD (pour la DB)
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        
        # Type de journal
        ttk.Label(top_frame, text="Type:").pack(side=tk.LEFT, padx=(20, 5))
        self.type_var = tk.StringVar()
        self.type_combobox = ttk.Combobox(top_frame, textvariable=self.type_var, width=20)
        self.type_combobox["values"] = ["ACHAT", "VENTE", "CAISSE", "PRODUCTION", "CONSOMMATION", "CHARGES"]
        self.type_combobox.pack(side=tk.LEFT, padx=5)
        self.type_combobox.bind("<<ComboboxSelected>>", self.filter_by_type)
        
        # Boutons
        ttk.Button(top_frame, text="Nouvelle opération", command=self.add_operation).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Actualiser", command=self.load_data).pack(side=tk.RIGHT, padx=5)
        
        # Frame pour les filtres
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Rechercher:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda event: self.filter_operations())
        
        # Frame pour le tableau
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Créer un Treeview
        columns = ("id", "date", "type", "piece", "libelle", "client_fournisseur", "produit", "quantite", "montant")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Configurer les colonnes
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("type", text="Type")
        self.tree.heading("piece", text="Pièce")
        self.tree.heading("libelle", text="Libellé")
        self.tree.heading("client_fournisseur", text="Client/Fournisseur")
        self.tree.heading("produit", text="Produit")
        self.tree.heading("quantite", text="Quantité")
        self.tree.heading("montant", text="Montant TTC")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("date", width=100, anchor=tk.CENTER)
        self.tree.column("type", width=100, anchor=tk.CENTER)
        self.tree.column("piece", width=100, anchor=tk.CENTER)
        self.tree.column("libelle", width=200)
        self.tree.column("client_fournisseur", width=150)
        self.tree.column("produit", width=150)
        self.tree.column("quantite", width=80, anchor=tk.E)
        self.tree.column("montant", width=100, anchor=tk.E)
        
        # Ajouter une scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Événement de double-clic
        self.tree.bind("<Double-1>", lambda event: self.edit_operation())
    
    def load_data(self):
        try:
            db = SessionLocal()
            self.operations = crud.get_journal_entries(db)
            
            # Effacer les anciennes données
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Ajouter les nouvelles données
            for op in self.operations:
                client_fournisseur = ""
                if op.client_id:
                    client_fournisseur = op.client.nom if op.client else ""
                elif op.fournisseur_id:
                    client_fournisseur = op.fournisseur.nom if op.fournisseur else ""
                
                produit = op.produit.designation if op.produit else ""
                
                self.tree.insert("", tk.END, values=(
                    op.id,
                    op.date_operation.strftime("%Y-%m-%d"),
                    op.type_journal,
                    op.numero_piece,
                    op.libelle,
                    client_fournisseur,
                    produit,
                    f"{op.quantite:.2f}",
                    f"{op.montant_ttc:.2f}"
                ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les opérations: {str(e)}")
        finally:
            db.close()
    
    def filter_operations(self):
        search_term = self.search_var.get().lower()
        
        # Effacer les anciennes données
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajouter les données filtrées
        for op in self.operations:
            client_fournisseur = ""
            if op.client_id:
                client_fournisseur = op.client.nom if op.client else ""
            elif op.fournisseur_id:
                client_fournisseur = op.fournisseur.nom if op.fournisseur else ""
            
            produit = op.produit.designation if op.produit else ""
            
            if (search_term in op.numero_piece.lower() or
                search_term in op.libelle.lower() or
                search_term in client_fournisseur.lower() or
                search_term in produit.lower()):
                self.tree.insert("", tk.END, values=(
                    op.id,
                    op.date_operation.strftime("%Y-%m-%d"),
                    op.type_journal,
                    op.numero_piece,
                    op.libelle,
                    client_fournisseur,
                    produit,
                    f"{op.quantite:.2f}",
                    f"{op.montant_ttc:.2f}"
                ))
    
    def filter_by_type(self, event=None):
        """Filtre les opérations par type sélectionné"""
        selected_type = self.type_var.get()
        
        # Effacer les anciennes données
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajouter les données filtrées
        for op in self.operations:
            if selected_type == "" or op.type_journal == selected_type:
                client_fournisseur = ""
                if op.client_id:
                    client_fournisseur = op.client.nom if op.client else ""
                elif op.fournisseur_id:
                    client_fournisseur = op.fournisseur.nom if op.fournisseur else ""
                
                produit = op.produit.designation if op.produit else ""
                
                self.tree.insert("", tk.END, values=(
                    op.id,
                    op.date_operation.strftime("%Y-%m-%d"),
                    op.type_journal,
                    op.numero_piece,
                    op.libelle,
                    client_fournisseur,
                    produit,
                    f"{op.quantite:.2f}",
                    f"{op.montant_ttc:.2f}"
                ))
    
    def add_operation(self):
        self.open_operation_form()
    
    def edit_operation(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner une opération à modifier")
            return
        
        operation_id = self.tree.item(selected_item)["values"][0]
        self.open_operation_form(operation_id)
    
    def update_operation_form(self, type_journal):
        """Met à jour la visibilité des champs selon le type d'opération sélectionné"""
        # Cacher tous les groupes
        if hasattr(self, 'client_group') and self.client_group:
            self.client_group.grid_remove()
        if hasattr(self, 'fournisseur_group') and self.fournisseur_group:
            self.fournisseur_group.grid_remove()
        if hasattr(self, 'produit_group') and self.produit_group:
            self.produit_group.grid_remove()
        if hasattr(self, 'unite_group') and self.unite_group:
            self.unite_group.grid_remove()
        if hasattr(self, 'transport_group') and self.transport_group:
            self.transport_group.grid_remove()
        if hasattr(self, 'charge_group') and self.charge_group:
            self.charge_group.grid_remove()
        if hasattr(self, 'tva_group') and self.tva_group:
            self.tva_group.grid_remove()
        
        # Afficher les groupes selon le type
        if type_journal == "ACHAT":
            if hasattr(self, 'fournisseur_group') and self.fournisseur_group:
                self.fournisseur_group.grid(row=6, column=0, columnspan=2, sticky="ew")
            if hasattr(self, 'produit_group') and self.produit_group:
                self.produit_group.grid(row=7, column=0, columnspan=2, sticky="ew")
            if hasattr(self, 'tva_group') and self.tva_group:
                self.tva_group.grid()
        
        elif type_journal == "VENTE":
            if hasattr(self, 'client_group') and self.client_group:
                self.client_group.grid(row=5, column=0, columnspan=2, sticky="ew")
            if hasattr(self, 'produit_group') and self.produit_group:
                self.produit_group.grid(row=7, column=0, columnspan=2, sticky="ew")
            if hasattr(self, 'tva_group') and self.tva_group:
                self.tva_group.grid()
            if hasattr(self, 'transport_group') and self.transport_group:
                self.transport_group.grid(row=0, column=0, sticky="ew")
        
        elif type_journal == "PRODUCTION":
            # Pas de client dans la production
            if hasattr(self, 'produit_group') and self.produit_group:
                self.produit_group.grid(row=7, column=0, columnspan=2, sticky="ew")
            if hasattr(self, 'unite_group') and self.unite_group:
                self.unite_group.grid(row=8, column=0, columnspan=2, sticky="ew")
        
        elif type_journal == "CONSOMMATION":
            if hasattr(self, 'produit_group') and self.produit_group:
                self.produit_group.grid(row=7, column=0, columnspan=2, sticky="ew")
            if hasattr(self, 'unite_group') and self.unite_group:
                self.unite_group.grid(row=8, column=0, columnspan=2, sticky="ew")
        
        elif type_journal == "CHARGES":
            if hasattr(self, 'charge_group') and self.charge_group:
                self.charge_group.grid(row=0, column=0, sticky="ew")
        
        # Pour la caisse, afficher selon le sens de l'opération
        elif type_journal == "CAISSE":
            if hasattr(self, 'client_group') and self.client_group:
                self.client_group.grid(row=5, column=0, columnspan=2, sticky="ew")
            if hasattr(self, 'fournisseur_group') and self.fournisseur_group:
                self.fournisseur_group.grid(row=6, column=0, columnspan=2, sticky="ew")
    
    def open_operation_form(self, operation_id=None):
        try:
            form = tk.Toplevel(self)
            form.title("Nouvelle opération" if operation_id is None else "Modifier l'opération")
            form.geometry("800x600")
            form.grab_set()  # Bloquer la fenêtre principale
            
            db = SessionLocal()
            operation = None
            try:
                if operation_id:
                    operation = db.query(JournalQuotidien).filter(JournalQuotidien.id == operation_id).first()
                
                # Formulaire
                self.form_frame = ttk.Frame(form, padding=20)
                self.form_frame.pack(fill=tk.BOTH, expand=True)
                
                # Date
                ttk.Label(self.form_frame, text="Date:").grid(row=0, column=0, sticky=tk.W, pady=5)
                date_var = tk.StringVar(form, value=operation.date_operation.strftime("%Y-%m-%d") if operation else datetime.now().strftime("%Y-%m-%d"))
                ttk.Entry(self.form_frame, textvariable=date_var, width=15).grid(row=0, column=1, sticky=tk.W, pady=5)
                
                # Type de journal
                ttk.Label(self.form_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
                type_var = tk.StringVar(form, value=operation.type_journal if operation else "")
                type_combobox = ttk.Combobox(self.form_frame, textvariable=type_var, width=25)
                type_combobox["values"] = ["ACHAT", "VENTE", "CAISSE", "PRODUCTION", "CONSOMMATION", "CHARGES"]
                type_combobox.grid(row=1, column=1, sticky=tk.W, pady=5)
                
                # Liaison de l'événement pour mise à jour en temps réel
                type_combobox.bind("<<ComboboxSelected>>", lambda event: self.update_operation_form(type_var.get()))
                
                # Type de document
                ttk.Label(self.form_frame, text="Type de document:").grid(row=2, column=0, sticky=tk.W, pady=5)
                doc_var = tk.StringVar(form, value=operation.type_document if operation else "BL")
                doc_combobox = ttk.Combobox(self.form_frame, textvariable=doc_var, width=25)
                doc_combobox["values"] = ["BL", "FACTURE", "AVOIR", "BC"]
                doc_combobox.grid(row=2, column=1, sticky=tk.W, pady=5)
                
                # Numéro de pièce
                ttk.Label(self.form_frame, text="Numéro pièce:").grid(row=3, column=0, sticky=tk.W, pady=5)
                numero_var = tk.StringVar(form, value=operation.numero_piece if operation else "")
                ttk.Entry(self.form_frame, textvariable=numero_var, width=30).grid(row=3, column=1, sticky=tk.W, pady=5)
                
                # Libellé
                ttk.Label(self.form_frame, text="Libellé:").grid(row=4, column=0, sticky=tk.W, pady=5)
                libelle_var = tk.StringVar(form, value=operation.libelle if operation else "")
                ttk.Entry(self.form_frame, textvariable=libelle_var, width=50).grid(row=4, column=1, sticky=tk.W, pady=5)
                
                # Client (dans un groupe)
                self.client_group = ttk.Frame(self.form_frame)
                ttk.Label(self.client_group, text="Client:").grid(row=0, column=0, sticky=tk.W, pady=5)
                client_var = tk.StringVar(form)
                client_combobox = ttk.Combobox(self.client_group, textvariable=client_var, width=40)
                clients = crud.get_clients(db)
                client_combobox["values"] = [f"{c.id} - {c.nom}" for c in clients]
                client_combobox.grid(row=0, column=1, sticky=tk.W, pady=5)
                if operation and operation.client_id:
                    client_combobox.set(f"{operation.client_id} - {operation.client.nom}")
                
                # Fournisseur (dans un groupe)
                self.fournisseur_group = ttk.Frame(self.form_frame)
                ttk.Label(self.fournisseur_group, text="Fournisseur:").grid(row=0, column=0, sticky=tk.W, pady=5)
                fournisseur_var = tk.StringVar(form)
                fournisseur_combobox = ttk.Combobox(self.fournisseur_group, textvariable=fournisseur_var, width=40)
                fournisseurs = crud.get_fournisseurs(db)
                fournisseur_combobox["values"] = [f"{f.id} - {f.nom}" for f in fournisseurs]
                fournisseur_combobox.grid(row=0, column=1, sticky=tk.W, pady=5)
                if operation and operation.fournisseur_id:
                    fournisseur_combobox.set(f"{operation.fournisseur_id} - {operation.fournisseur.nom}")
                
                # Produit (dans un groupe)
                self.produit_group = ttk.Frame(self.form_frame)
                ttk.Label(self.produit_group, text="Produit:").grid(row=0, column=0, sticky=tk.W, pady=5)
                product_var = tk.StringVar(form)
                product_combobox = ttk.Combobox(self.produit_group, textvariable=product_var, width=40)
                products = crud.get_produits(db)
                product_combobox["values"] = [f"{p.id} - {p.designation} ({p.code})" for p in products]
                product_combobox.grid(row=0, column=1, sticky=tk.W, pady=5)
                
                # Fonction pour mettre à jour le prix unitaire selon le type d'opération et le produit sélectionné
                def update_product_info():
                    if not product_var.get():
                        return
                    
                    # Trouver le produit sélectionné
                    product_id = int(product_var.get().split(" - ")[0])
                    product = crud.get_produit(db, product_id)
                    
                    if not product:
                        return
                    
                    # Déterminer le type d'opération
                    type_operation = type_var.get()
                    
                    # Mettre à jour le prix unitaire automatiquement
                    if type_operation == "ACHAT" and product.prix_achat is not None:
                        prix_var.set(f"{product.prix_achat:.2f}")
                    elif type_operation in ["VENTE", "PRODUCTION"] and product.prix_vente is not None:
                        prix_var.set(f"{product.prix_vente:.2f}")
                    
                    # Mettre à jour le taux de TVA
                    if product.taux_tva is not None:
                        tva_var.set(f"{product.taux_tva:.2f}")
                    
                    # Recalculer les montants
                    recalculate_amounts()
                
                # Lier l'événement de sélection du produit
                product_combobox.bind("<<ComboboxSelected>>", lambda event: update_product_info())
                
                if operation and operation.produit_id:
                    product_combobox.set(f"{operation.produit_id} - {operation.produit.designation} ({operation.produit.code})")
                
                # Unité de production (dans un groupe)
                self.unite_group = ttk.Frame(self.form_frame)
                ttk.Label(self.unite_group, text="Unité de production:").grid(row=0, column=0, sticky=tk.W, pady=5)
                unite_var = tk.StringVar(form)
                unite_combobox = ttk.Combobox(self.unite_group, textvariable=unite_var, width=40)
                unites = crud.get_unites_production(db)
                unite_combobox["values"] = [u.valeur for u in unites]
                unite_combobox.grid(row=0, column=1, sticky=tk.W, pady=5)
                if operation and operation.unite_production:
                    unite_combobox.set(operation.unite_production)
                
                # Quantité
                ttk.Label(self.form_frame, text="Quantité:").grid(row=9, column=0, sticky=tk.W, pady=5)
                quantite_var = tk.StringVar(form, value=f"{operation.quantite:.2f}" if operation else "1.00")
                quantite_entry = ttk.Entry(self.form_frame, textvariable=quantite_var, width=15)
                quantite_entry.grid(row=9, column=1, sticky=tk.W, pady=5)
                
                # Prix unitaire
                ttk.Label(self.form_frame, text="Prix unitaire:").grid(row=10, column=0, sticky=tk.W, pady=5)
                prix_var = tk.StringVar(form, value=f"{operation.prix_unitaire:.2f}" if operation and operation.prix_unitaire else "")
                prix_entry = ttk.Entry(self.form_frame, textvariable=prix_var, width=15)
                prix_entry.grid(row=10, column=1, sticky=tk.W, pady=5)
                
                # Taux TVA
                ttk.Label(self.form_frame, text="Taux TVA (%):").grid(row=11, column=0, sticky=tk.W, pady=5)
                tva_var = tk.StringVar(form, value=f"{operation.taux_tva:.2f}" if operation and operation.taux_tva else "19.00")
                tva_entry = ttk.Entry(self.form_frame, textvariable=tva_var, width=15)
                tva_entry.grid(row=11, column=1, sticky=tk.W, pady=5)
                
                # Montant HT
                ttk.Label(self.form_frame, text="Montant HT:").grid(row=12, column=0, sticky=tk.W, pady=5)
                montant_ht_var = tk.StringVar(form, value=f"{operation.montant_ht:.2f}" if operation else "")
                montant_ht_entry = ttk.Entry(self.form_frame, textvariable=montant_ht_var, width=15)
                montant_ht_entry.grid(row=12, column=1, sticky=tk.W, pady=5)
                
                # Montant TVA
                ttk.Label(self.form_frame, text="Montant TVA:").grid(row=13, column=0, sticky=tk.W, pady=5)
                montant_tva_var = tk.StringVar(form, value=f"{operation.montant_tva:.2f}" if operation else "")
                montant_tva_entry = ttk.Entry(self.form_frame, textvariable=montant_tva_var, width=15)
                montant_tva_entry.grid(row=13, column=1, sticky=tk.W, pady=5)
                
                # Montant TTC
                ttk.Label(self.form_frame, text="Montant TTC:").grid(row=14, column=0, sticky=tk.W, pady=5)
                montant_ttc_var = tk.StringVar(form, value=f"{operation.montant_ttc:.2f}" if operation else "")
                montant_ttc_entry = ttk.Entry(self.form_frame, textvariable=montant_ttc_var, width=15)
                montant_ttc_entry.grid(row=14, column=1, sticky=tk.W, pady=5)
                
                # Groupe TVA
                self.tva_group = ttk.Frame(self.form_frame)
                ttk.Label(self.tva_group, text="TVA applicable:").grid(row=0, column=0, sticky=tk.W, pady=5)
                tva_applicable_var = tk.BooleanVar(form, value=operation.tva_applicable if operation else True)
                tva_check = ttk.Checkbutton(self.tva_group, variable=tva_applicable_var)
                tva_check.grid(row=0, column=1, sticky=tk.W, pady=5)
                
                ttk.Label(self.tva_group, text="Droit de timbre applicable:").grid(row=1, column=0, sticky=tk.W, pady=5)
                dt_applicable_var = tk.BooleanVar(form, value=operation.dt_applicable if operation else True)
                dt_check = ttk.Checkbutton(self.tva_group, variable=dt_applicable_var)
                dt_check.grid(row=1, column=1, sticky=tk.W, pady=5)
                self.tva_group.grid(row=15, column=0, columnspan=2, sticky="ew")
                
                # Droit de timbre
                ttk.Label(self.form_frame, text="Droit de timbre:").grid(row=16, column=0, sticky=tk.W, pady=5)
                dt_var = tk.StringVar(form, value=f"{operation.droit_timbre:.2f}" if operation else "")
                dt_entry = ttk.Entry(self.form_frame, textvariable=dt_var, width=15)
                dt_entry.grid(row=16, column=1, sticky=tk.W, pady=5)
                
                # Informations supplémentaires dans un LabelFrame
                extra_frame = ttk.LabelFrame(self.form_frame, text="Informations supplémentaires")
                extra_frame.grid(row=17, column=0, columnspan=2, sticky="nsew", pady=10, padx=5)
                
                # Transport (dans un groupe)
                self.transport_group = ttk.Frame(extra_frame)
                ttk.Label(self.transport_group, text="Adresse de livraison:").grid(row=0, column=0, sticky=tk.W, pady=5)
                adresse_var = tk.StringVar(form, value=operation.adresse_livraison if operation else "")
                ttk.Entry(self.transport_group, textvariable=adresse_var, width=50).grid(row=0, column=1, sticky=tk.W, pady=5)
                
                ttk.Label(self.transport_group, text="Matricule camion:").grid(row=1, column=0, sticky=tk.W, pady=5)
                matricule_var = tk.StringVar(form, value=operation.matricule_camion if operation else "")
                ttk.Entry(self.transport_group, textvariable=matricule_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=5)
                
                # Charges (dans un groupe)
                self.charge_group = ttk.Frame(extra_frame)
                ttk.Label(self.charge_group, text="Type de charge:").grid(row=0, column=0, sticky=tk.W, pady=5)
                charge_var = tk.StringVar(form, value=operation.type_charge if operation else "")
                charge_combobox = ttk.Combobox(self.charge_group, textvariable=charge_var, width=25)
                charge_combobox["values"] = ["MO", "ELEC", "AMORT"]
                charge_combobox.grid(row=0, column=1, sticky=tk.W, pady=5)
                
                # Mettre à jour le formulaire selon le type d'opération
                self.update_operation_form(type_var.get())
                
                # Fonction pour recalculer les montants
                def recalculate_amounts():
                    # Ne pas recalculer pour CAISSE et CHARGES
                    type_operation = type_var.get()
                    if type_operation in ["CAISSE", "CHARGES"]:
                        return
                    
                    try:
                        # Récupérer les valeurs
                        quantite = float(quantite_var.get())
                        prix = float(prix_var.get()) if prix_var.get() else 0
                        taux_tva = float(tva_var.get()) if tva_var.get() else 19.0
                        
                        # Calculer le montant HT
                        montant_ht = quantite * prix
                        
                        # Calculer le montant TVA si applicable
                        montant_tva = 0
                        if tva_applicable_var.get():
                            montant_tva = montant_ht * taux_tva / 100
                        
                        # Calculer le montant TTC
                        montant_ttc = montant_ht + montant_tva
                        
                        # Calculer le droit de timbre si applicable
                        droit_timbre = 0
                        if dt_applicable_var.get():
                            droit_timbre = crud.calcul_droit_timbre(montant_ttc)
                        
                        # Mettre à jour les champs
                        montant_ht_var.set(f"{montant_ht:.2f}")
                        montant_tva_var.set(f"{montant_tva:.2f}")
                        montant_ttc_var.set(f"{montant_ttc:.2f}")
                        dt_var.set(f"{droit_timbre:.2f}")
                    except ValueError:
                        pass
                
                # Associer les événements pour recalculer automatiquement
                quantite_var.trace_add("write", lambda *args: recalculate_amounts())
                prix_var.trace_add("write", lambda *args: recalculate_amounts())
                tva_var.trace_add("write", lambda *args: recalculate_amounts())
                tva_applicable_var.trace_add("write", lambda *args: recalculate_amounts())
                dt_applicable_var.trace_add("write", lambda *args: recalculate_amounts())
                
                # Boutons d'action
                button_frame = ttk.Frame(self.form_frame)
                button_frame.grid(row=18, column=0, columnspan=2, pady=15)
                
                # Fonction pour sauvegarder l'opération
                def save_operation(close_after_save=True):
                    try:
                        # Convertir les valeurs
                        date_op = datetime.strptime(date_var.get(), "%Y-%m-%d")
                        quantite = float(quantite_var.get())
                        prix = float(prix_var.get()) if prix_var.get() else None
                        montant_ht = float(montant_ht_var.get()) if montant_ht_var.get() else None
                        taux_tva = float(tva_var.get()) if tva_var.get() else 19.0
                        montant_tva = float(montant_tva_var.get()) if montant_tva_var.get() else None
                        montant_ttc = float(montant_ttc_var.get()) if montant_ttc_var.get() else None
                        droit_timbre = float(dt_var.get()) if dt_var.get() else None
                        
                        # Extraire l'ID du client
                        client_id = None
                        if client_var.get():
                            client_id = int(client_var.get().split(" - ")[0])
                        
                        # Extraire l'ID du fournisseur
                        fournisseur_id = None
                        if fournisseur_var.get():
                            fournisseur_id = int(fournisseur_var.get().split(" - ")[0])
                        
                        # Extraire l'ID du produit
                        produit_id = None
                        if product_var.get():
                            produit_id = int(product_var.get().split(" - ")[0])
                        
                        # Déterminer le type d'opération
                        type_operation = type_var.get()
                        
                        # Pour CAISSE et CHARGES, utiliser le montant TTC saisi manuellement
                        if type_operation in ["CAISSE", "CHARGES"]:
                            # Si le montant TTC est saisi, utiliser ce montant
                            if montant_ttc is not None:
                                montant_ht = montant_ttc
                                montant_tva = 0
                                droit_timbre = 0
                            # Sinon, calculer à partir du montant HT
                            elif montant_ht is not None:
                                montant_ttc = montant_ht
                                montant_tva = 0
                                droit_timbre = 0
                        
                        operation_data = {
                            "date_operation": date_op,
                            "type_journal": type_var.get(),
                            "type_document": doc_var.get(),
                            "numero_piece": numero_var.get(),
                            "libelle": libelle_var.get(),
                            "client_id": client_id,
                            "fournisseur_id": fournisseur_id,
                            "produit_id": produit_id,
                            "unite_production": unite_var.get(),
                            "quantite": quantite,
                            "prix_unitaire": prix,
                            "montant_ht": montant_ht,
                            "taux_tva": taux_tva,
                            "montant_tva": montant_tva,
                            "montant_ttc": montant_ttc,
                            "tva_applicable": tva_applicable_var.get(),
                            "dt_applicable": dt_applicable_var.get(),
                            "droit_timbre": droit_timbre,
                            "adresse_livraison": adresse_var.get(),
                            "matricule_camion": matricule_var.get(),
                            "type_charge": charge_var.get()
                        }
                        
                        if operation_id:
                            # Mettre à jour l'opération existante
                            crud.update_journal_entry(db, operation_id, operation_data)
                            message = "Opération mise à jour avec succès"
                        else:
                            # Créer une nouvelle opération
                            crud.create_journal_entry(db, operation_data)
                            message = "Opération ajoutée avec succès"
                        
                        # Traiter les écritures comptables si nécessaire
                        if not operation_id:
                            # Récupérer la nouvelle opération
                            new_operation = crud.get_journal_entries(db, limit=1)[0]
                            # Générer les écritures comptables
                            accounting.process_journal_entry(db, new_operation)
                        
                        db.commit()
                        self.load_data()
                        messagebox.showinfo("Succès", message)
                        
                        # Si c'est une nouvelle opération et qu'on ne ferme pas la fenêtre
                        if not operation_id and not close_after_save:
                            # Réinitialiser le formulaire pour ajouter une nouvelle opération
                            date_var.set(datetime.now().strftime("%Y-%m-%d"))
                            type_var.set("")
                            doc_var.set("BL")
                            numero_var.set("")
                            libelle_var.set("")
                            client_var.set("")
                            fournisseur_var.set("")
                            product_var.set("")
                            unite_var.set("")
                            quantite_var.set("1.00")
                            prix_var.set("")
                            tva_var.set("19.00")
                            montant_ht_var.set("")
                            montant_tva_var.set("")
                            montant_ttc_var.set("")
                            tva_applicable_var.set(True)
                            dt_applicable_var.set(True)
                            dt_var.set("")
                            adresse_var.set("")
                            matricule_var.set("")
                            charge_var.set("")
                            
                            # Mettre à jour la visibilité des champs
                            self.update_operation_form("")
                        else:
                            # Fermer la fenêtre
                            form.destroy()
                    except ValueError as e:
                        messagebox.showerror("Erreur", f"Valeur invalide: {str(e)}")
                    except Exception as e:
                        db.rollback()
                        messagebox.showerror("Erreur", f"Impossible de sauvegarder l'opération: {str(e)}")
                
                # Boutons
                ttk.Button(button_frame, text="Ajouter et Continuer", 
                          command=lambda: save_operation(close_after_save=False)).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Valider et Quitter", 
                          command=lambda: save_operation(close_after_save=True)).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Annuler", 
                          command=form.destroy).pack(side=tk.LEFT, padx=5)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger l'opération: {str(e)}")
                db.rollback()
                form.destroy()
            finally:
                db.close()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur inattendue: {str(e)}")
