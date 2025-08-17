import os
from os import path, makedirs, walk
from datetime import datetime
from shutil import move, copy2
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import json

# CONFIGURAÇÃO
CONFIG_FILE = "config.json"

def carregar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("origin", ""), data.get("backup", "")
    return "", ""

def saveConfig(origin, backup):
    data = {"origin": origin, "backup": backup}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# FUNÇÕES
def copyVersioning(filePath, origin, destination):

    if not path.isfile(filePath):
        return
    
    relativePath = path.relpath(filePath, origin)
    fileDestination = path.join(destination, relativePath)
    fileDir = path.dirname(fileDestination)

    if not path.exists(fileDir):
        makedirs(fileDir)

    fileName = path.basename(filePath)

    # VERIFICA SE O ARQUIVO JÁ EXISTE E RENOMEIA
    if path.exists(fileDestination):
        dateTime = datetime.now().strftime("%y-%m-%d_%H-%M-%S")
        name, ext = path.splitext(fileName)
        newName = f"{name}_{dateTime}{ext}"
        renamedOriginalFile = path.join(fileDir, newName)
        move(fileDestination, renamedOriginalFile)

    # COPIA O ARQUIVO NOVO
    copy2(filePath, fileDestination)
    print(f'Arquivo Atualizado/Copiado: {fileDestination}')

def initializeBackup(origin, destination):
    for root, dirs, files in walk(origin):
        for file in files:
            filePath = path.join(root, file)
            relativePath = path.relpath(filePath, origin)
            fileDestination = path.join(destination, relativePath)
            fileDir = path.dirname(fileDestination)
            if not path.exists(fileDir):
                makedirs(fileDir)
            if not path.exists(fileDestination):
                copy2(filePath, fileDestination)
                print(f'Backup inicial criado: {fileDestination}')

class MonitorHandler(FileSystemEventHandler):
    def __init__(self, origin, destination):
        self.origin = origin
        self.destination = destination

    def on_modified(self, event):
        if not event.is_directory:
            copyVersioning(event.src_path, self.origin, self.destination)

    def on_created(self, event):
        if not event.is_directory:
            copyVersioning(event.src_path, self.origin, self.destination)

# CONTROLE DE MONITORAMENTO
observer = None
monitor_thread = None

def startMonitoring(origin, destination):
    global observer
    if not path.exists(destination):
        makedirs(destination)

    # INICIALIZA BACKUP DE ARQUIVO QUE NÃO EXISTEM
    initializeBackup(origin, destination)

    eventHandler = MonitorHandler(origin, destination)
    observer = Observer()
    observer.schedule(eventHandler, origin, recursive=True)
    observer.start()
    observer.join()

# GUI
def choiceOrigin():
    folder = filedialog.askdirectory()
    origin_var.set(folder)

def choiceDestination():
    folder = filedialog.askdirectory()
    destination_var.set(folder)

def start():
    global monitor_thread
    origin = origin_var.get()
    destination = destination_var.get()
    if not origin or not destination:
        messagebox.showerror("Erro", "Escolha as pastas de origin e backup")
        return

    saveConfig(origin, destination)

    def monitor():
        try:
            startMonitoring(origin, destination)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro no monitoramento:\n{e}")
        finally:
            statusVar.set("PARADO")
            btnStart.config(state="normal")
            btnStop.config(state="disabled")

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()

    statusVar.set("MONITORANDO")
    btnStart.config(state="disabled")
    btnStop.config(state="normal")

def stop():
    global observer
    if observer:
        observer.stop()
        observer.join()
        observer = None
    statusVar.set("PARADO")
    btnStart.config(state="normal")
    btnStop.config(state="disabled")

# CONSTRUÇÃO GUI
root = tk.Tk()
root.title("Monitor com Versionamento")

bold_font = ("TkDefaultFont", 10, "bold")
origin_var = tk.StringVar()
destination_var = tk.StringVar()
statusVar = tk.StringVar(value="PARADO")

# CARREGA CONFIGURAÇÃO
origin_inicial, backup_inicial = carregar_config()
origin_var.set(origin_inicial)
destination_var.set(backup_inicial)

tk.Label(root, text="Pasta Monitorada:", anchor="w", justify="left").pack(fill="x", padx=10, pady=(10,0))
frameOrigin = tk.Frame(root)
frameOrigin.pack(padx=10, pady=(0,5))
entryOrigin = tk.Entry(frameOrigin, textvariable=origin_var, width=50)
entryOrigin.pack(side="left", padx=(0,5))  # espaço entre Entry e botão
btnOrigin = tk.Button(frameOrigin, text="Escolher", command=choiceOrigin)
btnOrigin.pack(side="left")

tk.Label(root, text="Pasta Backup:", anchor="w", justify="left").pack(fill="x", padx=10, pady=(10,0))
frameBackup = tk.Frame(root)
frameBackup.pack(padx=10, pady=(0,5))
entryBackup = tk.Entry(frameBackup, textvariable=destination_var, width=50)
entryBackup.pack(side="left", padx=(0,5))
btnBackup = tk.Button(frameBackup, text="Escolher", command=choiceDestination)
btnBackup.pack(side="left")



frameButtons = tk.Frame(root)
frameButtons.pack(padx=10, pady=(0,20))

btnStart = tk.Button(frameButtons, text="INICIAR", command=start, bg="green", fg="white", font=bold_font)
btnStart.pack(side="left", padx=5)
btnStop = tk.Button(frameButtons, text="PARAR", command=stop, bg="red", fg="white", state="disabled", font=bold_font)
btnStop.pack(side="left", padx=5)
status = tk.Label(frameButtons, textvariable=statusVar, fg="blue", width=30, anchor="w")
status.pack(side="left", padx=5, fill="x")

root.mainloop()
