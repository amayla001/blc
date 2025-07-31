# ui/client_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from database import SessionLocal
import crud

class ClientWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        # Frame pour les boutons d'action
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(action_frame, text="Nouveau client", command=self.add_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Modifier", command=self.edit_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Supprimer", command=self.delete_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Actualiser", command=self.load_data).pack(side=tk.RIGHT, padx=5)
        
        # Frame pour la recherche
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Rechercher:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda event: self.search_clients())
        
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
        self.tree.bind("<Double-1>", lambda event: self.edit_client())
    
    def load_data(self):
        try:
            db = SessionLocal()
            self.clients = crud.get_clients(db)
            
            # Effacer les anciennes données
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Ajouter les nouvelles données
            for client in self.clients:
                self.tree.insert("", tk.END, values=(
                    client.id,
                    client.code,
                    client.nom,
                    client.telephone,
                    client.email,
                    client.nif
                ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les clients: {str(e)}")
        finally:
            db.close()
    
    def search_clients(self):
        search_term = self.search_var.get().lower()
        
        # Effacer les anciennes données
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajouter les données filtrées
        for client in self.clients:
            if (search_term in client.code.lower() or
                search_term in client.nom.lower() or
                search_term in (client.telephone or "").lower() or
                search_term in (client.email or "").lower() or
                search_term in (client.nif or "").lower()):
                self.tree.insert("", tk.END, values=(
                    client.id,
                    client.code,
                    client.nom,
                    client.telephone,
                    client.email,
                    client.nif
                ))
    
    def add_client(self):
        self.open_client_form()
    
    def edit_client(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un client à modifier")
            return
        
        client_id = self.tree.item(selected_item)["values"][0]
        self.open_client_form(client_id)
    
    def delete_client(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un client à supprimer")
            return
        
        client_id = self.tree.item(selected_item)["values"][0]
        client_name = self.tree.item(selected_item)["values"][2]
        
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer le client '{client_name}'?"):
            try:
                db = SessionLocal()
                crud.delete_produit(db, client_id)
                db.close()
                self.load_data()
                messagebox.showinfo("Succès", "Client supprimé avec succès")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer le client: {str(e)}")
    
    def open_client_form(self, client_id=None):
        form = tk.Toplevel(self)
        form.title("Client" if client_id is None else "Modifier le client")
        form.geometry("500x400")
        form.grab_set()  # Bloquer la fenêtre principale
        
        db = SessionLocal()
        client = None
        if client_id:
            client = crud.get_client(db, client_id)
        
        # Formulaire
        form_frame = ttk.Frame(form, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Code
        ttk.Label(form_frame, text="Code:").grid(row=0, column=0, sticky=tk.W, pady=5)
        code_var = tk.StringVar(value=client.code if client else "")
        ttk.Entry(form_frame, textvariable=code_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Nom
        ttk.Label(form_frame, text="Nom:").grid(row=1, column=0, sticky=tk.W, pady=5)
        nom_var = tk.StringVar(value=client.nom if client else "")
        ttk.Entry(form_frame, textvariable=nom_var, width=30).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Adresse
        ttk.Label(form_frame, text="Adresse:").grid(row=2, column=0, sticky=tk.W, pady=5)
        adresse_var = tk.StringVar(value=client.adresse if client else "")
        ttk.Entry(form_frame, textvariable=adresse_var, width=30).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Téléphone
        ttk.Label(form_frame, text="Téléphone:").grid(row=3, column=0, sticky=tk.W, pady=5)
        telephone_var = tk.StringVar(value=client.telephone if client else "")
        ttk.Entry(form_frame, textvariable=telephone_var, width=30).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Email
        ttk.Label(form_frame, text="Email:").grid(row=4, column=0, sticky=tk.W, pady=5)
        email_var = tk.StringVar(value=client.email if client else "")
        ttk.Entry(form_frame, textvariable=email_var, width=30).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # NIF
        ttk.Label(form_frame, text="NIF:").grid(row=5, column=0, sticky=tk.W, pady=5)
        nif_var = tk.StringVar(value=client.nif if client else "")
        ttk.Entry(form_frame, textvariable=nif_var, width=30).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # NIS
        ttk.Label(form_frame, text="NIS:").grid(row=6, column=0, sticky=tk.W, pady=5)
        nis_var = tk.StringVar(value=client.nis if client else "")
        ttk.Entry(form_frame, textvariable=nis_var, width=30).grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # RC
        ttk.Label(form_frame, text="RC:").grid(row=7, column=0, sticky=tk.W, pady=5)
        rc_var = tk.StringVar(value=client.rc if client else "")
        ttk.Entry(form_frame, textvariable=rc_var, width=30).grid(row=7, column=1, sticky=tk.W, pady=5)
        
        # Boutons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=15)
        
        def save_client():
            client_data = {
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
                if client_id:
                    crud.update_client(db, client_id, client_data)
                    message = "Client modifié avec succès"
                else:
                    crud.create_client(db, client_data)
                    message = "Client ajouté avec succès"
                
                db.commit()
                form.destroy()
                self.load_data()
                messagebox.showinfo("Succès", message)
            except Exception as e:
                db.rollback()
                messagebox.showerror("Erreur", f"Impossible de sauvegarder le client: {str(e)}")
            finally:
                db.close()
        
        ttk.Button(button_frame, text="Enregistrer", command=save_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annuler", command=form.destroy).pack(side=tk.LEFT, padx=5)
