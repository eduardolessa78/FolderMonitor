from json import load
from os import path, makedirs, walk
from datetime import datetime
from shutil import move, copy2
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from time import sleep, time

# VARAIVEIS
CONFIG_FILE = "config.json"

# FUNÇÔES
## CARREGA AS INFORMAÇÔES DE CONFIGURAÇÕES
def carregar_config():
    if path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = load(f)
            return data.get("origin", ""), data.get("backup", "")
    return "", ""

## FAZ COPIA DOS ARQUIVOS COM CONTROLE DE VERSÃO
def copyVersioning(filePath, origin, destination):
    if not path.isfile(filePath):
        return
    
    relativePath = path.relpath(filePath, origin)
    fileDestination = path.join(destination, relativePath)
    fileDir = path.dirname(fileDestination)

    if not path.exists(fileDir):
        makedirs(fileDir)

    fileName = path.basename(filePath)

    if path.exists(fileDestination):
        dateTime = datetime.now().strftime("%y-%m-%d_%H-%M-%S")
        name, ext = path.splitext(fileName)
        newName = f"{name}_{dateTime}{ext}"
        renamedOriginalFile = path.join(fileDir, newName)
        move(fileDestination, renamedOriginalFile)
        print("[{}] 🟡 Alterado [{}]".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), normalizePath(filePath)))

    copy2(filePath, fileDestination)
    print("[{}] 🟢 Sincronizado [{}]".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), normalizePath(fileDestination)))

## BACKUP INICIAL COMPARANDO AS PASTAS E SINCRONIZANDO
def initializeBackup(origin, destination):
    print('\n[{}] Backup incial...'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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
                print("[{}] 🟢 Sincronizado [{}]".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), normalizePath(fileDestination)))
    print('[{}] ...Finalizado\n'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

## FORMATA AS BARRAS DE EXIBIÇÃO PARA O LOG
def normalizePath(p):
    return p.replace("\\", "/")

# HANDLER DO WATCHDOG
class MonitorHandler(FileSystemEventHandler):
    def __init__(self, origin, destination):
        self.origin = origin
        self.destination = destination
        self.last_event = {}

    def process(self, filePath):
        now = time()
        last_time = self.last_event.get(filePath, 0)

        # Só processa se passaram pelo menos 0.5 segundos do último evento
        if now - last_time > 0.5:
            copyVersioning(filePath, self.origin, self.destination)
            self.last_event[filePath] = now

    def on_modified(self, event):
        if not event.is_directory:
            self.process(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self.process(event.src_path)

# INICIA O MONITORAMENTO
def startMonitoring(origin, destination):
    if not path.exists(destination):
        makedirs(destination)

    initializeBackup(origin, destination)
    eventHandler = MonitorHandler(origin, destination)
    observer = Observer()
    observer.schedule(eventHandler, origin, recursive=True)
    observer.start()
    print("📂 Monitorando: {}".format(origin))
    print("💾 Backup: {}".format(destination))
    print("🚀 Serviço iniciado. Pressione CTRL+C para parar.\n")

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Monitoramento interrompido pelo usuário.")
    observer.join()

if __name__ == "__main__":
    origin, backup = carregar_config()
    if not origin or not backup:
        print("❌ Erro: Configure 'origin' e 'backup' no arquivo config.json")
    else:
        startMonitoring(origin, backup)
    