import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import SessionLocal
import crud
from tkcalendar import DateEntry  # Importer le widget DateEntry

class StockWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.load_data()
    
        def create_widgets(self):
            # Frame pour le filtre de période
            period_frame = ttk.Frame(self)
            period_frame.pack(fill=tk.X, padx=10, pady=5)

            # Date de début
            ttk.Label(period_frame, text="Du:").pack(side=tk.LEFT, padx=5)
            self.start_date_var = tk.StringVar(value="2025-01-01")  # Format interne YYYY-MM-DD
            self.start_date_entry = DateEntry(
                period_frame,
                textvariable=self.start_date_var,
                date_pattern="dd/mm/yyyy",  # Format visuel pour l'utilisateur
                width=12,
                background='darkblue',
                foreground='white',
                borderwidth=2
            )
            self.start_date_entry.pack(side=tk.LEFT, padx=5)

            # Date de fin
            ttk.Label(period_frame, text="Au:").pack(side=tk.LEFT, padx=5)
            self.end_date_var = tk.StringVar(value="2025-01-31")  # Format interne YYYY-MM-DD
            self.end_date_entry = DateEntry(
                period_frame,
                textvariable=self.end_date_var,
                date_pattern="dd/mm/yyyy",  # Format visuel pour l'utilisateur
                width=12,
                background='darkblue',
                foreground='white',
                borderwidth=2
            )
            self.end_date_entry.pack(side=tk.LEFT, padx=5)

            # Bouton de filtrage
            ttk.Button(period_frame, text="Filtrer", command=self.filter_stocks_by_period).pack(side=tk.LEFT, padx=5)
        # Frame pour le filtre de famille
        family_frame = ttk.Frame(self)
        family_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(family_frame, text="Sélectionner les familles:").pack(side=tk.LEFT, padx=5)

        # Charger les familles dans une liste de cases à cocher
        self.family_vars = {}
        self.load_families(family_frame)

        # Frame pour le tableau
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Créer un Treeview
        columns = ("numerotation", "id", "produit", "designation", "prix_u", "stock_initial", "production", "consommation", "vente", "stock_fin")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        # Configurer les colonnes
        self.tree.heading("numerotation", text="Numérotation")
        self.tree.heading("id", text="ID")
        self.tree.heading("produit", text="Produit")
        self.tree.heading("designation", text="Désignation")
        self.tree.heading("prix_u", text="Prix U")
        self.tree.heading("stock_initial", text="Stock Initial")
        self.tree.heading("production", text="Production")
        self.tree.heading("consommation", text="Consommation")
        self.tree.heading("vente", text="Vente")
        self.tree.heading("stock_fin", text="Stock Fin")

        self.tree.column("numerotation", width=50, anchor=tk.CENTER)
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("produit", width=100)
        self.tree.column("designation", width=200)
        self.tree.column("prix_u", width=100, anchor=tk.E)
        self.tree.column("stock_initial", width=100, anchor=tk.E)
        self.tree.column("production", width=100, anchor=tk.E)
        self.tree.column("consommation", width=100, anchor=tk.E)
        self.tree.column("vente", width=100, anchor=tk.E)
        self.tree.column("stock_fin", width=100, anchor=tk.E)

        # Ajouter une scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_families(self, frame):
        try:
            db = SessionLocal()
            families = crud.get_familles_produit(db)

            # Créer une case à cocher pour chaque famille
            for family in families:
                var = tk.BooleanVar()
                self.family_vars[family.designation] = var
                checkbox = ttk.Checkbutton(frame, text=family.designation, variable=var)
                checkbox.pack(side=tk.LEFT, padx=5)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les familles: {str(e)}")
        finally:
            db.close()

    def load_data(self):
        # Cette méthode sera modifiée pour charger les données selon les spécifications
        pass

    def filter_stocks_by_period(self):
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        
        # Convertir les dates en objets datetime
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erreur", "Format de date invalide. Utilisez YYYY-MM-DD.")
            return
        
        # Effacer les anciennes données
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajouter les données filtrées par période et par famille
        try:
            db = SessionLocal()
            products = crud.get_produits(db)

            family_selected = [family for family, var in self.family_vars.items() if var.get()]

            family_totals = {}
            for product in products:
                # Vérifier si la famille correspond à la sélection
                if family_selected and product.famille not in family_selected:
                    continue
                
                # Récupérer les opérations de production, consommation et vente pour chaque produit
                production = crud.get_production_for_product(db, product.id, start_date_obj, end_date_obj)
                consumption = crud.get_consumption_for_product(db, product.id, start_date_obj, end_date_obj)
                sales = crud.get_sales_for_product(db, product.id, start_date_obj, end_date_obj)
                
                # Calculer les quantités
                stock_initial = crud.get_initial_stock_for_product(db, product.id, start_date_obj)
                stock_final = stock_initial + production - consumption - sales
                
                # Regrouper par famille
                family = product.famille
                if family not in family_totals:
                    family_totals[family] = {
                        "sous_total": 0,
                        "quantite_initiale": 0,
                        "production": 0,
                        "consommation": 0,
                        "vente": 0
                    }
                
                # Ajouter les valeurs au tableau
                self.tree.insert("", tk.END, values=(
                    "",  # Numérotation
                    product.id,
                    product.code,
                    product.designation,
                    f"{product.prix_vente:.2f}",  # Prix U
                    f"{stock_initial:.2f}",  # Stock Initial
                    f"{production:.2f}",  # Production
                    f"{consumption:.2f}",  # Consommation
                    f"{sales:.2f}",  # Vente
                    f"{stock_final:.2f}"  # Stock Fin
                ))
                
                # Mettre à jour les totaux
                family_totals[family]["quantite_initiale"] += stock_initial
                family_totals[family]["production"] += production
                family_totals[family]["consommation"] += consumption
                family_totals[family]["vente"] += sales
                family_totals[family]["sous_total"] += product.prix_vente * stock_final
            
            # Afficher les sous-totaux par famille
            for family, totals in family_totals.items():
                self.tree.insert("", tk.END, values=(
                    "",  # ID vide pour le sous-total
                    "",  # Code vide pour le sous-total
                    family,  # Famille
                    "",  # Désignation vide pour le sous-total
                    "",  # Prix U vide pour le sous-total
                    f"{totals['quantite_initiale']:.2f}",  # Quantité initiale
                    f"{totals['production']:.2f}",  # Production
                    f"{totals['consommation']:.2f}",  # Consommation
                    f"{totals['vente']:.2f}",  # Vente
                    f"{totals['sous_total']:.2f}"  # Sous-total
                ))
            
            # Calculer le total général
            total_general = sum(totals["sous_total"] for totals in family_totals.values())
            self.tree.insert("", tk.END, values=(
                "",  # ID vide pour le total général
                "",  # Code vide pour le total général
                "Total Général",  # Label pour le total général
                "",  # Désignation vide pour le total général
                "",  # Prix U vide pour le total général
                "",  # Quantité vide pour le total général
                "",  # Production vide pour le total général
                "",  # Consommation vide pour le total général
                "",  # Vente vide pour le total général
                f"{total_general:.2f}"  # Total général
            ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les stocks: {str(e)}")
        finally:
            db.close()
