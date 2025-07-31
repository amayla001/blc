# ui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
from database import SessionLocal, engine
import crud
import services.accounting as accounting
import services.production as production
from ui.client_window import ClientWindow
from ui.fournisseur_window import FournisseurWindow
from ui.product_window import ProductWindow
from ui.journal_window import JournalWindow
from ui.facturation_window import FacturationWindow
from ui.dashboard_window import DashboardWindow
from ui.stock_window import StockWindow
from ui.tresorerie_window import TresorerieWindow

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestion Comptable Bois_M - Application de Bureau")
        self.geometry("1200x800")
        
        # Configurer le style
        self.style = ttk.Style()
        self.style.configure("TNotebook", tabposition="n")
        self.style.configure("TNotebook.Tab", font=("Arial", 10, "bold"), padding=[10, 5])
        
        # Créer un menu
        self.create_menu()
        
        # Créer un notebook (onglets)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Créer les onglets
        self.dashboard_tab = DashboardWindow(self.notebook)
        self.clients_tab = ClientWindow(self.notebook)
        self.fournisseurs_tab = FournisseurWindow(self.notebook)
        self.products_tab = ProductWindow(self.notebook)
        self.journal_tab = JournalWindow(self.notebook)
        self.facturation_tab = FacturationWindow(self.notebook)
        self.stock_tab = StockWindow(self.notebook)
        self.tresorerie_tab = TresorerieWindow(self.notebook)
        
        # Ajouter les onglets
        self.notebook.add(self.dashboard_tab, text="Tableau de bord")
        self.notebook.add(self.clients_tab, text="Clients")
        self.notebook.add(self.fournisseurs_tab, text="Fournisseurs")
        self.notebook.add(self.products_tab, text="Produits")
        self.notebook.add(self.journal_tab, text="Journal de saisie")
        self.notebook.add(self.facturation_tab, text="Facturation")
        self.notebook.add(self.stock_tab, text="Stocks")
        self.notebook.add(self.tresorerie_tab, text="Trésorerie")
        
        # Sélectionner l'onglet par défaut
        self.notebook.select(self.dashboard_tab)
        
        # Barre de statut
        self.status_var = tk.StringVar()
        self.status_var.set("Prêt")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Charger les données initiales
        self.load_initial_data()
    
    def create_menu(self):
        menu_bar = tk.Menu(self)
        
        # Menu Fichier
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Nouveau", command=self.new_file)
        file_menu.add_command(label="Ouvrir", command=self.open_file)
        file_menu.add_command(label="Enregistrer", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit_app)
        menu_bar.add_cascade(label="Fichier", menu=file_menu)
        
        # Menu Édition
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Annuler", command=self.undo)
        edit_menu.add_command(label="Rétablir", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Copier", command=self.copy)
        edit_menu.add_command(label="Coller", command=self.paste)
        menu_bar.add_cascade(label="Édition", menu=edit_menu)
        
        # Menu Aide
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="À propos", command=self.about)
        menu_bar.add_cascade(label="Aide", menu=help_menu)
        
        self.config(menu=menu_bar)
    
    def load_initial_data(self):
        # Charger les données initiales si nécessaire
        pass
    
    # Méthodes du menu Fichier
    def new_file(self):
        pass
    
    def open_file(self):
        pass
    
    def save_file(self):
        pass
    
    def quit_app(self):
        self.destroy()
    
    # Méthodes du menu Édition
    def undo(self):
        pass
    
    def redo(self):
        pass
    
    def copy(self):
        pass
    
    def paste(self):
        pass
    
    # Méthodes du menu Aide
    def about(self):
        messagebox.showinfo("À propos", "Gestion Comptable Bois_M\nVersion 1.0\nApplication de bureau pour la gestion comptable et de production dans le secteur de la transformation du bois")
