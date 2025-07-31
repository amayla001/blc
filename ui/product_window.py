import tkinter as tk
from tkinter import ttk, messagebox
from database import SessionLocal
import crud

class ProductWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        # Frame pour les boutons d'action
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(action_frame, text="Nouveau produit", command=self.add_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Modifier", command=self.edit_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Supprimer", command=self.delete_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Gérer Familles", command=self.manage_families).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Actualiser", command=self.load_data).pack(side=tk.RIGHT, padx=5)
        
        # Frame pour la recherche et filtre
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Rechercher:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda event: self.filter_products())
        
        # Frame pour le tableau
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Créer un Treeview
        columns = ("id", "code", "designation", "famille", "unite_mesure", "prix_achat", "prix_vente")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Configurer les colonnes
        self.tree.heading("id", text="ID")
        self.tree.heading("code", text="Code")
        self.tree.heading("designation", text="Désignation")
        self.tree.heading("famille", text="Famille")
        self.tree.heading("unite_mesure", text="Unité")
        self.tree.heading("prix_achat", text="Prix achat")
        self.tree.heading("prix_vente", text="Prix vente")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("code", width=100, anchor=tk.CENTER)
        self.tree.column("designation", width=200)
        self.tree.column("famille", width=80, anchor=tk.CENTER)
        self.tree.column("unite_mesure", width=80, anchor=tk.CENTER)
        self.tree.column("prix_achat", width=100, anchor=tk.E)
        self.tree.column("prix_vente", width=100, anchor=tk.E)
        
        # Ajouter une scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_data(self):
        try:
            db = SessionLocal()
            
            # Charger les produits
            self.products = crud.get_produits(db)
            
            # Effacer les anciennes données
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Ajouter les nouvelles données
            for product in self.products:
                self.tree.insert("", tk.END, values=(
                    product.id,
                    product.code,
                    product.designation,
                    product.famille,
                    product.unite_mesure,
                    f"{product.prix_achat:.2f}" if product.prix_achat else "",
                    f"{product.prix_vente:.2f}" if product.prix_vente else ""
                ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les produits: {str(e)}")
    
    def filter_products(self):
        search_term = self.search_var.get().lower()
        
        # Effacer les anciennes données
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajouter les données filtrées
        for product in self.products:
            if (search_term in product.code.lower() or
                search_term in product.designation.lower() or
                search_term in (product.famille or "").lower()):
                self.tree.insert("", tk.END, values=(
                    product.id,
                    product.code,
                    product.designation,
                    product.famille,
                    product.unite_mesure,
                    f"{product.prix_achat:.2f}" if product.prix_achat else "",
                    f"{product.prix_vente:.2f}" if product.prix_vente else ""
                ))
    
    def manage_families(self):
        # Ouvrir une nouvelle fenêtre pour gérer les familles de produits
        FamilyManagementWindow(self)

    def add_product(self):
        self.open_product_form()
    
    def edit_product(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un produit à modifier")
            return
        
        product_id = self.tree.item(selected_item)["values"][0]
        self.open_product_form(product_id)
    
    def delete_product(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un produit à supprimer")
            return
        
        product_id = self.tree.item(selected_item)["values"][0]
        product_name = self.tree.item(selected_item)["values"][2]
        
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer le produit '{product_name}'?"):
            try:
                db = SessionLocal()
                crud.delete_produit(db, product_id)
                db.close()
                self.load_data()
                messagebox.showinfo("Succès", "Produit supprimé avec succès")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer le produit: {str(e)}")
    
    def open_product_form(self, product_id=None):
        # Code pour ouvrir le formulaire de produit
        pass

class FamilyManagementWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gestion des Familles de Produits")
        self.geometry("400x300")
        self.create_widgets()
        self.load_families()
    
    def create_widgets(self):
        # Frame pour les boutons d'action
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(action_frame, text="Nouvelle Famille", command=self.add_family).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Modifier", command=self.edit_family).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Supprimer", command=self.delete_family).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Actualiser", command=self.load_families).pack(side=tk.RIGHT, padx=5)
        
        # Frame pour le tableau
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Créer un Treeview
        columns = ("id", "designation")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Configurer les colonnes
        self.tree.heading("id", text="ID")
        self.tree.heading("designation", text="Désignation")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("designation", width=300)
        
        # Ajouter une scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_families(self):
        try:
            db = SessionLocal()
            self.families = crud.get_familles_produit(db)
            
            # Effacer les anciennes données
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Ajouter les nouvelles données
            for family in self.families:
                self.tree.insert("", tk.END, values=(family.id, family.designation))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les familles: {str(e)}")
    
    def add_family(self):
        # Ouvrir une fenêtre pour ajouter une nouvelle famille
        family_name = simpledialog.askstring("Nouvelle Famille", "Entrez la désignation de la nouvelle famille:")
        if family_name:
            try:
                db = SessionLocal()
                crud.create_famille_produit(db, {"designation": family_name})
                db.commit()
                self.load_families()
                messagebox.showinfo("Succès", "Famille ajoutée avec succès")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ajouter la famille: {str(e)}")
    
    def edit_family(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner une famille à modifier")
            return
        
        family_id = self.tree.item(selected_item)["values"][0]
        family_name = simpledialog.askstring("Modifier Famille", "Entrez la nouvelle désignation de la famille:")
        if family_name:
            try:
                db = SessionLocal()
                crud.update_famille_produit(db, family_id, {"designation": family_name})
                db.commit()
                self.load_families()
                messagebox.showinfo("Succès", "Famille modifiée avec succès")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de modifier la famille: {str(e)}")
    
    def delete_family(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner une famille à supprimer")
            return
        
        family_id = self.tree.item(selected_item)["values"][0]
        family_name = self.tree.item(selected_item)["values"][1]
        
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer la famille '{family_name}'?"):
            try:
                db = SessionLocal()
                crud.delete_famille_produit(db, family_id)
                db.commit()
                self.load_families()
                messagebox.showinfo("Succès", "Famille supprimée avec succès")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer la famille: {str(e)}")
