import sqlite3
from datetime import datetime
from banco import conectar

horario = datetime.now().strftime("%H:%M")

def menu_pedidos():
    while True:
        print("\nVocê está na aba pedidos!")