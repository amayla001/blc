# ui/tresorerie_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from database import SessionLocal
import crud
from models import Tresorerie  # Importer la classe Tresorerie

class TresorerieWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        # Frame pour les boutons d'action
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(action_frame, text="Nouvelle opération", command=self.add_operation).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Actualiser", command=self.load_data).pack(side=tk.RIGHT, padx=5)
        
        # Frame pour les filtres
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Période
        ttk.Label(filter_frame, text="Période:").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_frame, text="Du:").pack(side=tk.LEFT, padx=5)
        self.date_debut_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-01"))
        ttk.Entry(filter_frame, textvariable=self.date_debut_var, width=12).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_frame, text="Au:").pack(side=tk.LEFT, padx=5)
        self.date_fin_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(filter_frame, textvariable=self.date_fin_var, width=12).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="Filtrer", command=self.filter_operations).pack(side=tk.LEFT, padx=5)
        
        # Frame pour les métriques
        metrics_frame = ttk.Frame(self)
        metrics_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Solde trésorerie
        self.create_metric_card(metrics_frame, "Solde Trésorerie", "0.00 DA", "solde", 0)
        
        # Encaissements
        self.create_metric_card(metrics_frame, "Encaissements", "0.00 DA", "encaissements", 1)
        
        # Décaissements
        self.create_metric_card(metrics_frame, "Décaissements", "0.00 DA", "decaissements", 2)
        
        # Frame pour le tableau
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Créer un Treeview
        columns = ("id", "date", "type", "mode", "montant", "libelle", "tiers", "piece")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Configurer les colonnes
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("type", text="Type")
        self.tree.heading("mode", text="Mode")
        self.tree.heading("montant", text="Montant")
        self.tree.heading("libelle", text="Libellé")
        self.tree.heading("tiers", text="Tiers")
        self.tree.heading("piece", text="N° Pièce")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("date", width=100, anchor=tk.CENTER)
        self.tree.column("type", width=100, anchor=tk.CENTER)
        self.tree.column("mode", width=100, anchor=tk.CENTER)
        self.tree.column("montant", width=100, anchor=tk.E)
        self.tree.column("libelle", width=200)
        self.tree.column("tiers", width=150)
        self.tree.column("piece", width=100, anchor=tk.CENTER)
        
        # Ajouter une scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Événement de double-clic
        self.tree.bind("<Double-1>", lambda event: self.edit_operation())
    
    def create_metric_card(self, parent, title, value, metric_key, column):
        card = ttk.LabelFrame(parent, text=title)
        card.grid(row=0, column=column, padx=5, pady=5, sticky="nsew")
        
        value_label = ttk.Label(card, text=value, font=("Arial", 16, "bold"))
        value_label.pack(pady=10, padx=10)
        
        # Stocker la référence pour mise à jour
        setattr(self, f"{metric_key}_label", value_label)
    
    def load_data(self):
        try:
            db = SessionLocal()
            
            # Charger les opérations
            self.operations = db.query(Tresorerie).order_by(Tresorerie.date_operation.desc()).all()
            
            # Calculer les métriques
            self.update_metrics(db)
            
            # Effacer les anciennes données
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Ajouter les nouvelles données
            for op in self.operations:
                client_fournisseur = ""
                if op.client_id:
                    client = crud.get_client(db, op.client_id)
                    client_fournisseur = client.nom if client else ""
                elif op.fournisseur_id:
                    fournisseur = crud.get_fournisseur(db, op.fournisseur_id)
                    client_fournisseur = fournisseur.nom if fournisseur else ""
                
                self.tree.insert("", tk.END, values=(
                    op.id,
                    op.date_operation.strftime("%Y-%m-%d"),
                    op.type_operation,
                    op.mode_paiement,
                    f"{op.montant:.2f}",
                    op.libelle,
                    client_fournisseur,
                    op.numero_piece
                ))
            
            db.close()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les opérations: {str(e)}")
    
    def update_metrics(self, db):
        # Calculer les encaissements et décaissements
        encaissements = sum(op.montant for op in self.operations if op.type_operation == "ENCAISSEMENT")
        decaissements = sum(op.montant for op in self.operations if op.type_operation == "DECAISSEMENT")
        solde = encaissements - decaissements
        
        # Mettre à jour les métriques
        self.solde_label.config(text=f"{solde:.2f} DA")
        self.encaissements_label.config(text=f"{encaissements:.2f} DA")
        self.decaissements_label.config(text=f"{decaissements:.2f} DA")
    
    def filter_operations(self):
        try:
            # Parser les dates
            date_debut = datetime.strptime(self.date_debut_var.get(), "%Y-%m-%d").date()
            date_fin = datetime.strptime(self.date_fin_var.get(), "%Y-%m-%d").date()
            
            if date_debut > date_fin:
                messagebox.showerror("Erreur", "La date de début ne peut pas être postérieure à la date de fin")
                return
            
            # Filtrer les opérations
            filtered_ops = [
                op for op in self.operations
                if date_debut <= op.date_operation.date() <= date_fin
            ]
            
            # Effacer les anciennes données
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Ajouter les données filtrées
            for op in filtered_ops:
                client_fournisseur = ""
                if op.client_id:
                    client = crud.get_client(db, op.client_id)
                    client_fournisseur = client.nom if client else ""
                elif op.fournisseur_id:
                    fournisseur = crud.get_fournisseur(db, op.fournisseur_id)
                    client_fournisseur = fournisseur.nom if fournisseur else ""
                
                self.tree.insert("", tk.END, values=(
                    op.id,
                    op.date_operation.strftime("%Y-%m-%d"),
                    op.type_operation,
                    op.mode_paiement,
                    f"{op.montant:.2f}",
                    op.libelle,
                    client_fournisseur,
                    op.numero_piece
                ))
        except ValueError:
            messagebox.showerror("Erreur", "Format de date invalide")
    
    def add_operation(self):
        self.open_operation_form()
    
    def edit_operation(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner une opération à modifier")
            return
        
        operation_id = self.tree.item(selected_item)["values"][0]
        self.open_operation_form(operation_id)
    
    def open_operation_form(self, operation_id=None):
        try:
            form = tk.Toplevel(self)
            form.title("Nouvelle opération" if operation_id is None else "Modifier l'opération")
            form.geometry("500x400")
            form.grab_set()
            
            db = SessionLocal()
            operation = None
            try:
                if operation_id:
                    operation = db.query(Tresorerie).filter(Tresorerie.id == operation_id).first()
                
                # Formulaire
                form_frame = ttk.Frame(form, padding=20)
                form_frame.pack(fill=tk.BOTH, expand=True)
                
                # Date - CORRECTION : Ajout de 'form' comme premier argument
                ttk.Label(form_frame, text="Date:").grid(row=0, column=0, sticky=tk.W, pady=5)
                date_var = tk.StringVar(form, value=operation.date_operation.strftime("%Y-%m-%d") if operation else datetime.now().strftime("%Y-%m-%d"))
                ttk.Entry(form_frame, textvariable=date_var, width=15).grid(row=0, column=1, sticky=tk.W, pady=5)
                
                # Type d'opération - CORRECTION : Ajout de 'form' comme premier argument
                ttk.Label(form_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
                type_var = tk.StringVar(form, value=operation.type_operation if operation else "ENCAISSEMENT")
                type_combobox = ttk.Combobox(form_frame, textvariable=type_var, width=20)
                type_combobox["values"] = ["ENCAISSEMENT", "DECAISSEMENT"]
                type_combobox.grid(row=1, column=1, sticky=tk.W, pady=5)
                
                # Mode de paiement - CORRECTION : Ajout de 'form' comme premier argument
                ttk.Label(form_frame, text="Mode:").grid(row=2, column=0, sticky=tk.W, pady=5)
                mode_var = tk.StringVar(form, value=operation.mode_paiement if operation else "ESPÈCES")
                mode_combobox = ttk.Combobox(form_frame, textvariable=mode_var, width=20)
                mode_combobox["values"] = ["ESPÈCES", "CHÈQUE", "VIREMENT"]
                mode_combobox.grid(row=2, column=1, sticky=tk.W, pady=5)
                
                # Montant - CORRECTION : Ajout de 'form' comme premier argument
                ttk.Label(form_frame, text="Montant:").grid(row=3, column=0, sticky=tk.W, pady=5)
                montant_var = tk.StringVar(form, value=f"{operation.montant:.2f}" if operation else "")
                ttk.Entry(form_frame, textvariable=montant_var, width=15).grid(row=3, column=1, sticky=tk.W, pady=5)
                
                # Libellé - CORRECTION : Ajout de 'form' comme premier argument
                ttk.Label(form_frame, text="Libellé:").grid(row=4, column=0, sticky=tk.W, pady=5)
                libelle_var = tk.StringVar(form, value=operation.libelle if operation else "")
                ttk.Entry(form_frame, textvariable=libelle_var, width=40).grid(row=4, column=1, sticky=tk.W, pady=5)
                
                # Tiers (client/fournisseur) - CORRECTION : Ajout de 'form' comme premier argument
                ttk.Label(form_frame, text="Client/Fournisseur:").grid(row=5, column=0, sticky=tk.W, pady=5)
                tiers_var = tk.StringVar(form)
                tiers_combobox = ttk.Combobox(form_frame, textvariable=tiers_var, width=30)
                
                # Charger les clients et fournisseurs
                clients = crud.get_clients(db)
                fournisseurs = crud.get_fournisseurs(db)
                
                tiers_options = []
                for c in clients:
                    tiers_options.append(f"C|{c.id}|{c.nom}")
                for f in fournisseurs:
                    tiers_options.append(f"F|{f.id}|{f.nom}")
                
                tiers_combobox["values"] = tiers_options
                tiers_combobox.grid(row=5, column=1, sticky=tk.W, pady=5)
                
                if operation:
                    if operation.client_id:
                        for c in clients:
                            if c.id == operation.client_id:
                                tiers_combobox.set(f"C|{c.id}|{c.nom}")
                                break
                    elif operation.fournisseur_id:
                        for f in fournisseurs:
                            if f.id == operation.fournisseur_id:
                                tiers_combobox.set(f"F|{f.id}|{f.nom}")
                                break
                
                # Numéro de pièce - CORRECTION : Ajout de 'form' comme premier argument
                ttk.Label(form_frame, text="N° Pièce:").grid(row=6, column=0, sticky=tk.W, pady=5)
                piece_var = tk.StringVar(form, value=operation.numero_piece if operation else "")
                ttk.Entry(form_frame, textvariable=piece_var, width=15).grid(row=6, column=1, sticky=tk.W, pady=5)
                
                # Boutons
                button_frame = ttk.Frame(form_frame)
                button_frame.grid(row=7, column=0, columnspan=2, pady=15)
                
                def save_operation():
                    try:
                        # Convertir les valeurs
                        date_op = datetime.strptime(date_var.get(), "%Y-%m-%d").date()
                        montant = float(montant_var.get())
                        
                        if montant <= 0:
                            messagebox.showerror("Erreur", "Le montant doit être positif")
                            return
                        
                        # Extraire les informations du tiers
                        client_id = None
                        fournisseur_id = None
                        
                        if tiers_var.get():
                            parts = tiers_var.get().split("|")
                            if parts[0] == "C":
                                client_id = int(parts[1])
                            elif parts[0] == "F":
                                fournisseur_id = int(parts[1])
                        
                        operation_data = {
                            "date_operation": date_op,
                            "type_operation": type_var.get(),
                            "mode_paiement": mode_var.get(),
                            "montant": montant,
                            "libelle": libelle_var.get(),
                            "client_id": client_id,
                            "fournisseur_id": fournisseur_id,
                            "numero_piece": piece_var.get()
                        }
                        
                        if operation_id:
                            # Mettre à jour l'opération existante
                            for key, value in operation_data.items():
                                setattr(operation, key, value)
                            db.commit()
                            message = "Opération mise à jour avec succès"
                        else:
                            # Créer une nouvelle opération
                            new_op = Tresorerie(**operation_data)
                            db.add(new_op)
                            db.commit()
                            message = "Opération ajoutée avec succès"
                        
                        form.destroy()
                        self.load_data()
                        messagebox.showinfo("Succès", message)
                    except ValueError as e:
                        messagebox.showerror("Erreur", f"Valeur invalide: {str(e)}")
                    except Exception as e:
                        db.rollback()
                        messagebox.showerror("Erreur", f"Impossible de sauvegarder l'opération: {str(e)}")
                    finally:
                        db.close()
                
                ttk.Button(button_frame, text="Enregistrer", command=save_operation).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Annuler", command=form.destroy).pack(side=tk.LEFT, padx=5)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger l'opération: {str(e)}")
                db.rollback()
                form.destroy()
            finally:
                db.close()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur inattendue: {str(e)}")
