# ui/dashboard_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import crud
import services.accounting as accounting
from database import SessionLocal
import math

class DashboardWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        # Frame pour la date
        date_frame = ttk.Frame(self)
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(date_frame, text="Date:").pack(side=tk.LEFT, padx=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=12)
        self.date_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(date_frame, text="Actualiser", command=self.load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(date_frame, text="Hier", command=self.load_yesterday).pack(side=tk.LEFT, padx=5)
        ttk.Button(date_frame, text="Aujourd'hui", command=self.load_today).pack(side=tk.LEFT, padx=5)
        
        # Frame pour les métriques principales
        metrics_frame = ttk.Frame(self)
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Ventes
        self.create_metric_card(metrics_frame, "Ventes", "0.00 DA", "ventes", 0)
        
        # Achats
        self.create_metric_card(metrics_frame, "Achats", "0.00 DA", "achats", 1)
        
        # Trésorerie
        self.create_metric_card(metrics_frame, "Trésorerie", "0.00 DA", "tresorerie", 2)
        
        # Bois consommé
        self.create_metric_card(metrics_frame, "Bois consommé", "0.00 m³", "bois_consomme", 3)
        
        # Produits finis
        self.create_metric_card(metrics_frame, "Produits finis", "0 unités", "produits_finis", 4)
        
        # Rendement
        self.create_metric_card(metrics_frame, "Rendement", "0.00%", "rendement", 5)
        
        # Frame pour les détails par unité de production
        units_frame = ttk.LabelFrame(self, text="Détails par Unité de Production")
        units_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Créer un Treeview pour afficher les détails
        columns = ("unité", "bois_consommé", "produits_finis", "produits_semi", "déchets", "rendement")
        self.units_tree = ttk.Treeview(units_frame, columns=columns, show="headings")
        
        # Configurer les colonnes
        self.units_tree.heading("unité", text="Unité")
        self.units_tree.heading("bois_consommé", text="Bois consommé (m³)")
        self.units_tree.heading("produits_finis", text="PF produits")
        self.units_tree.heading("produits_semi", text="SF produits")
        self.units_tree.heading("déchets", text="Déchets")
        self.units_tree.heading("rendement", text="Rendement (%)")
        
        self.units_tree.column("unité", width=150)
        self.units_tree.column("bois_consommé", width=150, anchor=tk.E)
        self.units_tree.column("produits_finis", width=100, anchor=tk.E)
        self.units_tree.column("produits_semi", width=100, anchor=tk.E)
        self.units_tree.column("déchets", width=100, anchor=tk.E)
        self.units_tree.column("rendement", width=100, anchor=tk.E)
        
        # Ajouter une scrollbar
        scrollbar = ttk.Scrollbar(units_frame, orient=tk.VERTICAL, command=self.units_tree.yview)
        self.units_tree.configure(yscrollcommand=scrollbar.set)
        
        self.units_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame pour les graphiques
        charts_frame = ttk.Frame(self)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Créer les graphiques
        self.create_charts(charts_frame)
    
    def create_metric_card(self, parent, title, value, metric_key, column):
        card = ttk.LabelFrame(parent, text=title)
        card.grid(row=0, column=column, padx=5, pady=5, sticky="nsew")
        
        value_label = ttk.Label(card, text=value, font=("Arial", 16, "bold"))
        value_label.pack(pady=10, padx=10)
        
        # Ajouter une tendance (à remplacer par des données réelles)
        trend_label = ttk.Label(card, text="↑ 0.0% vs hier", foreground="green")
        trend_label.pack(pady=(0, 10))
        
        # Stocker la référence pour mise à jour
        setattr(self, f"{metric_key}_label", value_label)
        setattr(self, f"{metric_key}_trend", trend_label)
    
    def create_charts(self, parent):
        # Créer une frame pour les graphiques
        self.charts_frame = ttk.Frame(parent)
        self.charts_frame.pack(fill=tk.BOTH, expand=True)
        
        # Créer les graphiques
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Initialiser avec des données par défaut
        self.dashboard_metrics = {
            "today": {
                "produits_finis": 0,
                "semi_finis": 0,
                "dechets": 0,
                "rendement_moyen": 0
            }
        }
        
        # Initialiser les graphiques
        self.update_production_pie_chart()
        
        # Graphique 2: Évolution du rendement
        self.ax2.plot([], [])
        self.ax2.set_title("Évolution du rendement")
        self.ax2.set_xlabel("Date")
        self.ax2.set_ylabel("Rendement (%)")
        self.ax2.grid(True)
        
        # Intégrer les graphiques dans Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.charts_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_production_pie_chart(self):
        """Met à jour le graphique en camembert avec gestion des valeurs nulles"""
        # Données initiales
        total = (self.dashboard_metrics["today"]["produits_finis"] + 
                 self.dashboard_metrics["today"]["semi_finis"] + 
                 self.dashboard_metrics["today"]["dechets"])
        
        self.ax1.clear()
        
        if total > 0:
            sizes = [
                self.dashboard_metrics["today"]["produits_finis"],
                self.dashboard_metrics["today"]["semi_finis"],
                self.dashboard_metrics["today"]["dechets"]
            ]
            
            # Si la somme des tailles est nulle, on ne peut pas créer le graphique
            if sum(sizes) > 0:
                self.ax1.pie(sizes, labels=["PF", "SF", "Déchets"], autopct='%1.1f%%')
            else:
                self.ax1.text(0, 0, "Aucune production", 
                             ha='center', va='center', 
                             fontsize=12, color='gray')
        else:
            self.ax1.text(0, 0, "Aucune production", 
                         ha='center', va='center', 
                         fontsize=12, color='gray')
        
        self.ax1.set_title("Répartition de la production")
    
    def load_data(self):
        try:
            # Parser la date
            try:
                selected_date = datetime.strptime(self.date_var.get(), "%Y-%m-%d").date()
            except ValueError:
                selected_date = date.today()
                self.date_var.set(selected_date.strftime("%Y-%m-%d"))
            
            # Charger les métriques
            db = SessionLocal()
            self.dashboard_metrics = accounting.get_dashboard_metrics(db, selected_date)
            
            # Mettre à jour les métriques principales
            self.update_metric("ventes", self.dashboard_metrics["today"]["cout_total_production"], self.dashboard_metrics["variations"]["cout_total_production"])
            self.update_metric("achats", self.dashboard_metrics["today"]["cout_total_consommation"], self.dashboard_metrics["variations"]["cout_total_consommation"])
            self.update_metric("bois_consomme", self.dashboard_metrics["today"]["bois_consomme"], self.dashboard_metrics["variations"]["bois_consomme"])
            self.update_metric("produits_finis", self.dashboard_metrics["today"]["produits_finis"], self.dashboard_metrics["variations"]["produits_finis"])
            
            # Vérifier que rendement_moyen existe avant de l'utiliser
            rendement = self.dashboard_metrics["today"].get("rendement_moyen", 0)
            variation_rendement = self.dashboard_metrics["variations"].get("rendement_moyen", 0)
            self.update_metric("rendement", rendement, variation_rendement)
            
            # Mettre à jour les détails par unité
            details_unites = self.dashboard_metrics["today"].get("details_unites", {})
            self.update_units_details(details_unites)
            
            # Mettre à jour les graphiques
            self.update_production_pie_chart()
            self.update_trend_chart()
            
            # Mettre à jour la trésorerie
            balance_tresorerie = crud.get_balance_tresorerie(db)
            self.update_metric("tresorerie", balance_tresorerie, 0)  # Pas de variation pour la trésorerie
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les données: {str(e)}")
        finally:
            db.close()
    
    def update_trend_chart(self):
        """Met à jour le graphique d'évolution du rendement"""
        dates = [date.today() - timedelta(days=i) for i in range(7, 0, -1)]
        rendements = []
        
        db = SessionLocal()
        for d in dates:
            try:
                metrics = accounting.get_dashboard_metrics(db, d)
                rendements.append(metrics["today"]["rendement_moyen"])
            except:
                rendements.append(0)
        db.close()
        
        self.ax2.clear()
        
        # Filtrer les valeurs valides
        valid_dates = []
        valid_rendements = []
        
        for i in range(len(dates)):
            if not math.isnan(rendements[i]) and rendements[i] >= 0:
                valid_dates.append(dates[i])
                valid_rendements.append(rendements[i])
        
        if len(valid_dates) > 0:
            self.ax2.plot(valid_dates, valid_rendements, marker='o')
            self.ax2.set_title("Évolution du rendement")
            self.ax2.set_xlabel("Date")
            self.ax2.set_ylabel("Rendement (%)")
            self.ax2.grid(True)
        else:
            self.ax2.text(0.5, 0.5, "Aucune donnée", 
                         ha='center', va='center', 
                         transform=self.ax2.transAxes,
                         fontsize=12, color='gray')
            self.ax2.set_title("Évolution du rendement (aucune donnée)")
        
        # Mettre à jour le canvas
        self.canvas.draw()
    
    def update_metric(self, metric_key, value, variation):
        # Mettre à jour la valeur
        value_label = getattr(self, f"{metric_key}_label")
        
        # Formater la valeur selon le type de métrique
        if metric_key in ["ventes", "achats", "tresorerie"]:
            formatted_value = f"{value:.2f} DA"
        elif metric_key == "bois_consomme":
            formatted_value = f"{value:.2f} m³"
        elif metric_key == "produits_finis":
            formatted_value = f"{value:.0f} unités"
        else:  # rendement
            formatted_value = f"{value:.2f}%"
        
        value_label.config(text=formatted_value)
        
        # Mettre à jour la tendance
        trend_label = getattr(self, f"{metric_key}_trend")
        if variation > 0:
            trend_label.config(text=f"↑ {variation:.1f}% vs hier", foreground="green")
        elif variation < 0:
            trend_label.config(text=f"↓ {abs(variation):.1f}% vs hier", foreground="red")
        else:
            trend_label.config(text="→ Stable vs hier", foreground="black")
    
    def update_units_details(self, details_unites):
        # Effacer les anciennes données
        for item in self.units_tree.get_children():
            self.units_tree.delete(item)
        
        # Ajouter les nouvelles données
        for unite, data in details_unites.items():
            self.units_tree.insert("", tk.END, values=(
                unite,
                f"{data['bois_consomme']:.2f}",
                f"{data['produits_finis']:.0f}",
                f"{data['semi_finis']:.0f}",
                f"{data['dechets']:.0f}",
                f"{data['rendement']:.2f}" if data['rendement'] > 0 else "N/A"
            ))
    
    def load_yesterday(self):
        yesterday = date.today() - timedelta(days=1)
        self.date_var.set(yesterday.strftime("%Y-%m-%d"))
        self.load_data()
    
    def load_today(self):
        today = date.today()
        self.date_var.set(today.strftime("%Y-%m-%d"))
        self.load_data()
