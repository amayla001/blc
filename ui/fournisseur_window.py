# ui/fournisseur_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from database import SessionLocal
import crud

class FournisseurWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        # Frame pour les boutons d'action
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(action_frame, text="Nouveau fournisseur", command=self.add_fournisseur).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Modifier", command=self.edit_fournisseur).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Supprimer", command=self.delete_fournisseur).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Actualiser", command=self.load_data).pack(side=tk.RIGHT, padx=5)
        
        # Frame pour la recherche
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Rechercher:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda event: self.search_fournisseurs())
        
        # Frame pour le tableau
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Créer un Treeview
        columns = ("id", "code", "nom", "telephone", "email", "nif")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Configurer les colonnes
        self.tree.heading("id", text="ID")
        self.tree.heading("code", text="Code")
        self.tree.heading("nom", text="Nom")
        self.tree.heading("telephone", text="Téléphone")
        self.tree.heading("email", text="Email")
        self.tree.heading("nif", text="NIF")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("code", width=100, anchor=tk.CENTER)
        self.tree.column("nom", width=200)
        self.tree.column("telephone", width=100, anchor=tk.CENTER)
        self.tree.column("email", width=200)
        self.tree.column("nif", width=100, anchor=tk.CENTER)
        
        # Ajouter une scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Événement de double-clic
        self.tree.bind("<Double-1>", lambda event: self.edit_fournisseur())
    
    def load_data(self):
        try:
            db = SessionLocal()
            self.fournisseurs = crud.get_fournisseurs(db)
            
            # Effacer les anciennes données
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Ajouter les nouvelles données
            for fournisseur in self.fournisseurs:
                self.tree.insert("", tk.END, values=(
                    fournisseur.id,
                    fournisseur.code,
                    fournisseur.nom,
                    fournisseur.telephone,
                    fournisseur.email,
                    fournisseur.nif
                ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les fournisseurs: {str(e)}")
        finally:
            db.close()
    
    def search_fournisseurs(self):
        search_term = self.search_var.get().lower()
        
        # Effacer les anciennes données
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajouter les données filtrées
        for fournisseur in self.fournisseurs:
            if (search_term in fournisseur.code.lower() or
                search_term in fournisseur.nom.lower() or
                search_term in (fournisseur.telephone or "").lower() or
                search_term in (fournisseur.email or "").lower() or
                search_term in (fournisseur.nif or "").lower()):
                self.tree.insert("", tk.END, values=(
                    fournisseur.id,
                    fournisseur.code,
                    fournisseur.nom,
                    fournisseur.telephone,
                    fournisseur.email,
                    fournisseur.nif
                ))
    
    def add_fournisseur(self):
        self.open_fournisseur_form()
    
    def edit_fournisseur(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un fournisseur à modifier")
            return
        
        fournisseur_id = self.tree.item(selected_item)["values"][0]
        self.open_fournisseur_form(fournisseur_id)
    
    def delete_fournisseur(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un fournisseur à supprimer")
            return
        
        fournisseur_id = self.tree.item(selected_item)["values"][0]
        fournisseur_name = self.tree.item(selected_item)["values"][2]
        
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer le fournisseur '{fournisseur_name}'?"):
            try:
                db = SessionLocal()
                crud.delete_produit(db, fournisseur_id)
                db.close()
                self.load_data()
                messagebox.showinfo("Succès", "Fournisseur supprimé avec succès")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer le fournisseur: {str(e)}")
    
    def open_fournisseur_form(self, fournisseur_id=None):
        form = tk.Toplevel(self)
        form.title("Fournisseur" if fournisseur_id is None else "Modifier le fournisseur")
        form.geometry("500x400")
        form.grab_set()  # Bloquer la fenêtre principale
        
        db = SessionLocal()
        fournisseur = None
        if fournisseur_id:
            fournisseur = crud.get_fournisseur(db, fournisseur_id)
        
        # Formulaire
        form_frame = ttk.Frame(form, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Code
        ttk.Label(form_frame, text="Code:").grid(row=0, column=0, sticky=tk.W, pady=5)
        code_var = tk.StringVar(value=fournisseur.code if fournisseur else "")
        ttk.Entry(form_frame, textvariable=code_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Nom
        ttk.Label(form_frame, text="Nom:").grid(row=1, column=0, sticky=tk.W, pady=5)
        nom_var = tk.StringVar(value=fournisseur.nom if fournisseur else "")
        ttk.Entry(form_frame, textvariable=nom_var, width=30).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Adresse
        ttk.Label(form_frame, text="Adresse:").grid(row=2, column=0, sticky=tk.W, pady=5)
        adresse_var = tk.StringVar(value=fournisseur.adresse if fournisseur else "")
        ttk.Entry(form_frame, textvariable=adresse_var, width=30).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Téléphone
        ttk.Label(form_frame, text="Téléphone:").grid(row=3, column=0, sticky=tk.W, pady=5)
        telephone_var = tk.StringVar(value=fournisseur.telephone if fournisseur else "")
        ttk.Entry(form_frame, textvariable=telephone_var, width=30).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Email
        ttk.Label(form_frame, text="Email:").grid(row=4, column=0, sticky=tk.W, pady=5)
        email_var = tk.StringVar(value=fournisseur.email if fournisseur else "")
        ttk.Entry(form_frame, textvariable=email_var, width=30).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # NIF
        ttk.Label(form_frame, text="NIF:").grid(row=5, column=0, sticky=tk.W, pady=5)
        nif_var = tk.StringVar(value=fournisseur.nif if fournisseur else "")
        ttk.Entry(form_frame, textvariable=nif_var, width=30).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # NIS
        ttk.Label(form_frame, text="NIS:").grid(row=6, column=0, sticky=tk.W, pady=5)
        nis_var = tk.StringVar(value=fournisseur.nis if fournisseur else "")
        ttk.Entry(form_frame, textvariable=nis_var, width=30).grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # RC
        ttk.Label(form_frame, text="RC:").grid(row=7, column=0, sticky=tk.W, pady=5)
        rc_var = tk.StringVar(value=fournisseur.rc if fournisseur else "")
        ttk.Entry(form_frame, textvariable=rc_var, width=30).grid(row=7, column=1, sticky=tk.W, pady=5)
        
        # Boutons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=15)
        
        def save_fournisseur():
            fournisseur_data = {
                "code": code_var.get(),
                "nom": nom_var.get(),
                "adresse": adresse_var.get(),
                "telephone": telephone_var.get(),
                "email": email_var.get(),
                "nif": nif_var.get(),
                "nis": nis_var.get(),
                "rc": rc_var.get()
            }
            
            try:
                if fournisseur_id:
                    crud.update_fournisseur(db, fournisseur_id, fournisseur_data)
                    message = "Fournisseur modifié avec succès"
                else:
                    crud.create_fournisseur(db, fournisseur_data)
                    message = "Fournisseur ajouté avec succès"
                
                db.commit()
                form.destroy()
                self.load_data()
                messagebox.showinfo("Succès", message)
            except Exception as e:
                db.rollback()
                messagebox.showerror("Erreur", f"Impossible de sauvegarder le fournisseur: {str(e)}")
            finally:
                db.close()
        
        ttk.Button(button_frame, text="Enregistrer", command=save_fournisseur).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annuler", command=form.destroy).pack(side=tk.LEFT, padx=5)
