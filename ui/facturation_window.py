# ui/facturation_window.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date
import math
from database import SessionLocal
import crud
import services.accounting as accounting

class FacturationWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        # Frame pour les boutons d'action
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(action_frame, text="Générer une facture", command=self.generate_invoice).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Enregistrer un règlement", command=self.add_reglement).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Exporter PDF", command=self.export_to_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Actualiser", command=self.load_data).pack(side=tk.RIGHT, padx=5)
        
        # Frame pour les filtres
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Filtre par client
        ttk.Label(filter_frame, text="Client:").pack(side=tk.LEFT, padx=5)
        self.client_var = tk.StringVar()
        self.client_combobox = ttk.Combobox(filter_frame, textvariable=self.client_var, width=30)
        self.client_combobox.pack(side=tk.LEFT, padx=5)
        self.client_combobox.bind("<<ComboboxSelected>>", lambda event: self.filter_invoices())
        
        # Filtre par statut
        ttk.Label(filter_frame, text="Statut:").pack(side=tk.LEFT, padx=(20, 5))
        self.status_var = tk.StringVar(value="Tous")
        self.status_combobox = ttk.Combobox(filter_frame, textvariable=self.status_var, width=15)
        self.status_combobox["values"] = ["Tous", "EN_ATTENTE", "PARTIELLEMENT_PAYEE", "PAYEE"]
        self.status_combobox.pack(side=tk.LEFT, padx=5)
        self.status_combobox.bind("<<ComboboxSelected>>", lambda event: self.filter_invoices())
        
        # Frame pour le tableau des factures
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Créer un Treeview
        columns = ("id", "numero", "date", "client", "ht", "tva", "ttc", "dt", "net", "statut")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Configurer les colonnes
        self.tree.heading("id", text="ID")
        self.tree.heading("numero", text="N° Facture")
        self.tree.heading("date", text="Date")
        self.tree.heading("client", text="Client")
        self.tree.heading("ht", text="HT")
        self.tree.heading("tva", text="TVA")
        self.tree.heading("ttc", text="TTC")
        self.tree.heading("dt", text="DT")
        self.tree.heading("net", text="Net à payer")
        self.tree.heading("statut", text="Statut")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("numero", width=120, anchor=tk.CENTER)
        self.tree.column("date", width=100, anchor=tk.CENTER)
        self.tree.column("client", width=200)
        self.tree.column("ht", width=100, anchor=tk.E)
        self.tree.column("tva", width=100, anchor=tk.E)
        self.tree.column("ttc", width=100, anchor=tk.E)
        self.tree.column("dt", width=80, anchor=tk.E)
        self.tree.column("net", width=120, anchor=tk.E)
        self.tree.column("statut", width=150, anchor=tk.CENTER)
        
        # Ajouter une scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Événement de double-clic
        self.tree.bind("<Double-1>", lambda event: self.view_invoice_details())
    
    def load_data(self):
        try:
            db = SessionLocal()
            
            # Charger les clients pour le filtre
            clients = crud.get_clients(db)
            self.client_combobox["values"] = ["Tous"] + [c.nom for c in clients]
            self.client_var.set("Tous")
            
            # Charger les factures
            self.invoices = crud.get_factures(db)
            
            db.close()
            
            # Effacer les anciennes données
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Ajouter les nouvelles données
            for invoice in self.invoices:
                self.tree.insert("", tk.END, values=(
                    invoice.id,
                    invoice.numero_facture,
                    invoice.date_facture.strftime("%Y-%m-%d"),
                    invoice.client.nom if invoice.client else "",
                    f"{invoice.montant_ht:.2f}",
                    f"{invoice.montant_tva:.2f}",
                    f"{invoice.montant_ttc:.2f}",
                    f"{invoice.droit_timbre:.2f}",
                    f"{invoice.montant_net_payer:.2f}",
                    invoice.statut.replace("_", " ")
                ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les factures: {str(e)}")
    
    def filter_invoices(self):
        selected_client = self.client_var.get()
        selected_status = self.status_var.get()
        
        # Effacer les anciennes données
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajouter les données filtrées
        for invoice in self.invoices:
            client_match = (selected_client == "Tous" or 
                           (invoice.client and invoice.client.nom == selected_client))
            
            status_match = (selected_status == "Tous" or 
                           invoice.statut == selected_status)
            
            if client_match and status_match:
                self.tree.insert("", tk.END, values=(
                    invoice.id,
                    invoice.numero_facture,
                    invoice.date_facture.strftime("%Y-%m-%d"),
                    invoice.client.nom if invoice.client else "",
                    f"{invoice.montant_ht:.2f}",
                    f"{invoice.montant_tva:.2f}",
                    f"{invoice.montant_ttc:.2f}",
                    f"{invoice.droit_timbre:.2f}",
                    f"{invoice.montant_net_payer:.2f}",
                    invoice.statut.replace("_", " ")
                ))
    
    def generate_invoice(self):
        # Ouvrir une fenêtre pour sélectionner un client et une période
        form = tk.Toplevel(self)
        form.title("Générer une facture")
        form.geometry("500x300")
        form.grab_set()
        
        db = SessionLocal()
        
        # Formulaire
        form_frame = ttk.Frame(form, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Client
        ttk.Label(form_frame, text="Client:").grid(row=0, column=0, sticky=tk.W, pady=10)
        client_var = tk.StringVar()
        client_combobox = ttk.Combobox(form_frame, textvariable=client_var, width=30)
        clients = crud.get_clients(db)
        client_combobox["values"] = [c.nom for c in clients]
        client_combobox.grid(row=0, column=1, sticky=tk.W, pady=10)
        
        # Période
        ttk.Label(form_frame, text="Période:").grid(row=1, column=0, sticky=tk.W, pady=10)
        
        ttk.Label(form_frame, text="Du:").grid(row=1, column=1, sticky=tk.W, pady=10)
        date_debut_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-01"))
        ttk.Entry(form_frame, textvariable=date_debut_var, width=12).grid(row=1, column=2, sticky=tk.W, pady=10)
        
        ttk.Label(form_frame, text="Au:").grid(row=2, column=1, sticky=tk.W, pady=10)
        date_fin_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(form_frame, textvariable=date_fin_var, width=12).grid(row=2, column=2, sticky=tk.W, pady=10)
        
        # Boutons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        def process_invoice():
            try:
                # Valider la sélection du client
                if not client_var.get():
                    messagebox.showwarning("Avertissement", "Veuillez sélectionner un client")
                    return
                
                # Trouver l'ID du client
                client_id = None
                for client in clients:
                    if client.nom == client_var.get():
                        client_id = client.id
                        break
                
                if not client_id:
                    messagebox.showerror("Erreur", "Client introuvable")
                    return
                
                # Valider les dates
                date_debut = datetime.strptime(date_debut_var.get(), "%Y-%m-%d").date()
                date_fin = datetime.strptime(date_fin_var.get(), "%Y-%m-%d").date()
                
                if date_debut > date_fin:
                    messagebox.showerror("Erreur", "La date de début ne peut pas être postérieure à la date de fin")
                    return
                
                # Générer la facture
                self.create_invoice_from_bl(db, client_id, date_debut, date_fin)
                
                form.destroy()
                self.load_data()
                messagebox.showinfo("Succès", "Facture générée avec succès")
            except ValueError as e:
                messagebox.showerror("Erreur", f"Format de date invalide: {str(e)}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de générer la facture: {str(e)}")
            finally:
                db.close()
        
        ttk.Button(button_frame, text="Générer", command=process_invoice).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annuler", command=form.destroy).pack(side=tk.LEFT, padx=5)
    
    def create_invoice_from_bl(self, db, client_id, date_debut, date_fin):
        """Génère une facture à partir des BL non facturés pour un client dans une période donnée"""
        # Récupérer les BL non facturés pour ce client dans la période
        bls = db.query(models.JournalQuotidien).filter(
            models.JournalQuotidien.client_id == client_id,
            models.JournalQuotidien.type_journal == "VENTE",
            models.JournalQuotidien.date_operation >= date_debut,
            models.JournalQuotidien.date_operation <= date_fin,
            models.JournalQuotidien.facture_id == None
        ).all()
        
        if not bls:
            messagebox.showinfo("Information", "Aucun BL éligible pour la facturation dans cette période")
            return
        
        # Calculer les montants
        montant_ht = sum(bl.montant_ht for bl in bls)
        montant_tva = sum(bl.montant_tva for bl in bls)
        montant_ttc = sum(bl.montant_ttc for bl in bls)
        droit_timbre = crud.calcul_droit_timbre(montant_ttc)
        montant_net_payer = montant_ttc + droit_timbre
        
        # Créer la facture
        invoice_data = {
            "client_id": client_id,
            "date_facture": date.today(),
            "montant_ht": montant_ht,
            "montant_tva": montant_tva,
            "montant_ttc": montant_ttc,
            "droit_timbre": droit_timbre,
            "montant_net_payer": montant_net_payer,
            "date_echeance": date.today() + timedelta(days=30),
            "statut": "EN_ATTENTE"
        }
        
        invoice = crud.create_facture(db, invoice_data)
        
        # Ajouter les lignes de facture
        for bl in bls:
            ligne_data = {
                "facture_id": invoice.id,
                "produit_id": bl.produit_id,
                "quantite": bl.quantite,
                "prix_unitaire": bl.prix_unitaire,
                "montant_ht": bl.montant_ht,
                "taux_tva": bl.taux_tva,
                "montant_tva": bl.montant_tva
            }
            crud.add_ligne_facture(db, ligne_data)
            
            # Mettre à jour le BL pour indiquer qu'il est facturé
            bl.facture_id = invoice.id
            db.commit()
        
        return invoice
    
    def add_reglement(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner une facture")
            return
        
        invoice_id = self.tree.item(selected_item)["values"][0]
        invoice = None
        
        try:
            db = SessionLocal()
            invoice = crud.get_facture(db, invoice_id)
            
            if not invoice:
                messagebox.showerror("Erreur", "Facture introuvable")
                return
            
            # Ouvrir une fenêtre pour saisir le règlement
            form = tk.Toplevel(self)
            form.title(f"Règlement - {invoice.numero_facture}")
            form.geometry("400x300")
            form.grab_set()
            
            # Formulaire
            form_frame = ttk.Frame(form, padding=20)
            form_frame.pack(fill=tk.BOTH, expand=True)
            
            # Montant restant dû
            ttk.Label(form_frame, text="Montant restant dû:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=10)
            ttk.Label(form_frame, text=f"{invoice.montant_net_payer:.2f} DA", font=("Arial", 10, "bold")).grid(row=0, column=1, sticky=tk.W, pady=10)
            
            # Montant réglé
            ttk.Label(form_frame, text="Montant réglé:").grid(row=1, column=0, sticky=tk.W, pady=10)
            montant_var = tk.StringVar(value=f"{invoice.montant_net_payer:.2f}")
            ttk.Entry(form_frame, textvariable=montant_var, width=15).grid(row=1, column=1, sticky=tk.W, pady=10)
            
            # Mode de règlement
            ttk.Label(form_frame, text="Mode de règlement:").grid(row=2, column=0, sticky=tk.W, pady=10)
            mode_var = tk.StringVar(value="ESPÈCES")
            mode_combobox = ttk.Combobox(form_frame, textvariable=mode_var, width=15)
            mode_combobox["values"] = ["ESPÈCES", "CHÈQUE", "VIREMENT"]
            mode_combobox.grid(row=2, column=1, sticky=tk.W, pady=10)
            
            # Numéro de chèque (si applicable)
            ttk.Label(form_frame, text="N° Chèque:").grid(row=3, column=0, sticky=tk.W, pady=10)
            cheque_var = tk.StringVar()
            ttk.Entry(form_frame, textvariable=cheque_var, width=15).grid(row=3, column=1, sticky=tk.W, pady=10)
            
            # Boutons
            button_frame = ttk.Frame(form_frame)
            button_frame.grid(row=4, column=0, columnspan=2, pady=20)
            
            def save_reglement():
                try:
                    montant = float(montant_var.get())
                    if montant <= 0:
                        messagebox.showerror("Erreur", "Le montant doit être positif")
                        return
                    
                    if montant > invoice.montant_net_payer:
                        messagebox.showerror("Erreur", "Le montant réglé ne peut pas dépasser le montant dû")
                        return
                    
                    reglement_data = {
                        "facture_id": invoice_id,
                        "montant": montant,
                        "mode": mode_var.get(),
                        "numero_cheque": cheque_var.get() if mode_var.get() == "CHÈQUE" else None,
                        "date_reglement": date.today()
                    }
                    
                    crud.create_reglement(db, reglement_data)
                    
                    form.destroy()
                    self.load_data()
                    messagebox.showinfo("Succès", "Règlement enregistré avec succès")
                except ValueError:
                    messagebox.showerror("Erreur", "Montant invalide")
            
            ttk.Button(button_frame, text="Enregistrer", command=save_reglement).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Annuler", command=form.destroy).pack(side=tk.LEFT, padx=5)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger la facture: {str(e)}")
        finally:
            if db:
                db.close()
    
    def export_to_pdf(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner une facture")
            return
        
        invoice_id = self.tree.item(selected_item)["values"][0]
        
        # Ici, vous implémenteriez l'export PDF
        # Pour l'exemple, on affiche juste un message
        messagebox.showinfo("Export PDF", f"Export de la facture {invoice_id} en cours...")
    
    def view_invoice_details(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        invoice_id = self.tree.item(selected_item)["values"][0]
        
        try:
            db = SessionLocal()
            invoice = crud.get_facture(db, invoice_id)
            
            if not invoice:
                messagebox.showerror("Erreur", "Facture introuvable")
                return
            
            # Créer une nouvelle fenêtre pour les détails
            details_window = tk.Toplevel(self)
            details_window.title(f"Détails de la facture {invoice.numero_facture}")
            details_window.geometry("800x600")
            
            # Frame principale
            main_frame = ttk.Frame(details_window, padding=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # En-tête
            header_frame = ttk.Frame(main_frame)
            header_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(header_frame, text="FACTURE", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
            ttk.Label(header_frame, text=invoice.numero_facture, font=("Arial", 16)).pack(side=tk.LEFT, padx=20)
            
            # Informations client
            client_frame = ttk.LabelFrame(main_frame, text="Client")
            client_frame.pack(fill=tk.X, pady=10, padx=5)
            
            if invoice.client:
                ttk.Label(client_frame, text=f"Nom: {invoice.client.nom}").pack(anchor=tk.W, padx=10, pady=5)
                ttk.Label(client_frame, text=f"Adresse: {invoice.client.adresse}").pack(anchor=tk.W, padx=10, pady=5)
                ttk.Label(client_frame, text=f"NIF: {invoice.client.nif}").pack(anchor=tk.W, padx=10, pady=5)
            
            # Dates
            dates_frame = ttk.Frame(main_frame)
            dates_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(dates_frame, text=f"Date de facture: {invoice.date_facture}").grid(row=0, column=0, sticky=tk.W, padx=10)
            ttk.Label(dates_frame, text=f"Échéance: {invoice.date_echeance}").grid(row=0, column=1, sticky=tk.W, padx=10)
            ttk.Label(dates_frame, text=f"Statut: {invoice.statut.replace('_', ' ')}").grid(row=0, column=2, sticky=tk.W, padx=10)
            
            # Tableau des lignes de facture
            lines_frame = ttk.LabelFrame(main_frame, text="Détails")
            lines_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            
            # Créer un Treeview
            columns = ("designation", "quantite", "prix_unitaire", "montant_ht", "tva", "montant_tva")
            tree = ttk.Treeview(lines_frame, columns=columns, show="headings")
            
            # Configurer les colonnes
            tree.heading("designation", text="Désignation")
            tree.heading("quantite", text="Quantité")
            tree.heading("prix_unitaire", text="P.U.")
            tree.heading("montant_ht", text="Montant HT")
            tree.heading("tva", text="TVA (%)")
            tree.heading("montant_tva", text="Montant TVA")
            
            tree.column("designation", width=250)
            tree.column("quantite", width=80, anchor=tk.E)
            tree.column("prix_unitaire", width=100, anchor=tk.E)
            tree.column("montant_ht", width=100, anchor=tk.E)
            tree.column("tva", width=80, anchor=tk.E)
            tree.column("montant_tva", width=100, anchor=tk.E)
            
            # Ajouter une scrollbar
            scrollbar = ttk.Scrollbar(lines_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Ajouter les lignes
            for ligne in invoice.lignes:
                tree.insert("", tk.END, values=(
                    ligne.produit.designation if ligne.produit else "",
                    f"{ligne.quantite:.2f}",
                    f"{ligne.prix_unitaire:.2f}",
                    f"{ligne.montant_ht:.2f}",
                    f"{ligne.taux_tva:.2f}",
                    f"{ligne.montant_tva:.2f}"
                ))
            
            # Résumé
            summary_frame = ttk.Frame(main_frame)
            summary_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(summary_frame, text="Montant HT:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.E, padx=10, pady=5)
            ttk.Label(summary_frame, text=f"{invoice.montant_ht:.2f} DA").grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
            
            ttk.Label(summary_frame, text="Montant TVA:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.E, padx=10, pady=5)
            ttk.Label(summary_frame, text=f"{invoice.montant_tva:.2f} DA").grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
            
            ttk.Label(summary_frame, text="Droit de timbre:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.E, padx=10, pady=5)
            ttk.Label(summary_frame, text=f"{invoice.droit_timbre:.2f} DA").grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
            
            ttk.Label(summary_frame, text="Net à payer:", font=("Arial", 10, "bold"), foreground="blue").grid(row=3, column=0, sticky=tk.E, padx=10, pady=10)
            ttk.Label(summary_frame, text=f"{invoice.montant_net_payer:.2f} DA", font=("Arial", 10, "bold"), foreground="blue").grid(row=3, column=1, sticky=tk.W, padx=10, pady=10)
            
            # Règlements
            if invoice.reglements:
                payments_frame = ttk.LabelFrame(main_frame, text="Règlements")
                payments_frame.pack(fill=tk.X, pady=10)
                
                # Créer un Treeview
                columns = ("date", "mode", "montant", "cheque")
                payments_tree = ttk.Treeview(payments_frame, columns=columns, show="headings")
                
                # Configurer les colonnes
                payments_tree.heading("date", text="Date")
                payments_tree.heading("mode", text="Mode")
                payments_tree.heading("montant", text="Montant")
                payments_tree.heading("cheque", text="N° Chèque")
                
                payments_tree.column("date", width=100, anchor=tk.CENTER)
                payments_tree.column("mode", width=100, anchor=tk.CENTER)
                payments_tree.column("montant", width=100, anchor=tk.E)
                payments_tree.column("cheque", width=100, anchor=tk.CENTER)
                
                # Ajouter une scrollbar
                scrollbar = ttk.Scrollbar(payments_frame, orient=tk.VERTICAL, command=payments_tree.yview)
                payments_tree.configure(yscrollcommand=scrollbar.set)
                
                payments_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                # Ajouter les règlements
                for reglement in invoice.reglements:
                    payments_tree.insert("", tk.END, values=(
                        reglement.date_reglement.strftime("%Y-%m-%d"),
                        reglement.mode,
                        f"{reglement.montant:.2f}",
                        reglement.numero_cheque or ""
                    ))
            
            # Boutons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(button_frame, text="Exporter PDF", command=lambda: self.export_to_pdf()).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Fermer", command=details_window.destroy).pack(side=tk.RIGHT, padx=5)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les détails de la facture: {str(e)}")
        finally:
            db.close()
