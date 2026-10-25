import os
import shutil
import sys
import argparse

parser = argparse.ArgumentParser(
    description=(
        "Remonte tous les fichiers des sous-répertoires vers le dossier racine et "
        "supprime les dossiers vides ensuite."
    ),
    epilog=(
        "Exemples:\n"
        "  py flatten_directory.py C:/path/to/folder\n"
        "  py flatten_directory.py ./downloads"
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument("dossier", nargs="?", help="Dossier à traiter")
args = parser.parse_args()

if not args.dossier:
    parser.print_help()
    sys.exit(0)

dossier = os.path.abspath(args.dossier)

for racine, sous_dossiers, fichiers in os.walk(dossier, topdown=False):
    for fichier in fichiers:
        src = os.path.join(racine, fichier)
        dst = os.path.join(dossier, fichier)
        i = 1
        while os.path.exists(dst):
            nom, ext = os.path.splitext(fichier)
            dst = os.path.join(dossier, f"{nom}_{i}{ext}")
            i += 1
        shutil.move(src, dst)

    if racine != dossier and not os.listdir(racine):
        os.rmdir(racine)
