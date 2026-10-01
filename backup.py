"""Consistent local SQLite backup. Protect the output as sensitive data."""
import argparse, sqlite3
from pathlib import Path
import server

parser=argparse.ArgumentParser();parser.add_argument('destination',type=Path);args=parser.parse_args()
destination=args.destination.resolve()
if destination==server.DB.resolve() or destination.exists():raise SystemExit('Escolha um arquivo novo, diferente do banco ativo.')
if not server.DB.exists():raise SystemExit('Banco de origem não encontrado.')
destination.parent.mkdir(parents=True,exist_ok=True)
source=sqlite3.connect(f'{server.DB.resolve().as_uri()}?mode=ro',uri=True)
target=sqlite3.connect(destination)
try:
    source.backup(target)
    if target.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise SystemExit('Falha na integridade do backup.')
finally:target.close();source.close()
print('Backup consistente criado. Proteja o arquivo: ele contém os dados do aplicativo.')
