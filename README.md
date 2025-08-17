# FolderMonitor
Monitoramento de pasta com cópia e versionamento por data de alteração

Arquivo config.json editar os caminhos da pasta de origin e backup

Funções:

- Ao inicializar sincroniza as pastas "origin" e "backup";
- Monitora pasta "origin" realizando cópia/sincronização com pasta "backup";
- Alterações em "origin" cópia criada em "backup" renomeando anterior com a data e hora da modificação;
- Novos arquivos copiados para "backup".
