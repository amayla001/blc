# app.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import os
from database import SessionLocal, engine
import models
import crud
import services.accounting as accounting
import services.production as production
from ui.main_window import MainWindow
from init_db import init_database

def main():
    # Initialiser la base de données
    try:
        init_database()
        print("Base de données initialisée avec succès")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
        messagebox.showerror("Erreur", f"Impossible d'initialiser la base de données: {str(e)}")
        return

    # Créer la fenêtre principale
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
