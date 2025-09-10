import os
import shutil
import hashlib
from pathlib import Path

def hash_arquivo(caminho_arquivo, chunk_size=8192):
    """Calcula o hash SHA256 de um arquivo para detectar duplicatas."""
    hash_sha = hashlib.sha256()
    with open(caminho_arquivo, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()


def processar_pasta(pasta_origem, pasta_destino=None):
    """
    Copia/move arquivos de pasta_origem para pasta_destino (se informado),
    detectando e movendo duplicatas para subpasta 'duplicata'.
    """
    hash_map = {}  # hash -> caminho do arquivo original

    for root, _, files in os.walk(pasta_origem):
        for nome_arquivo in files:
            caminho_arquivo = Path(root) / nome_arquivo

            if not caminho_arquivo.is_file():
                continue

            hash_valor = hash_arquivo(caminho_arquivo)

            # Calcula destino final (se tiver pasta_destino)
            if pasta_destino:
                caminho_relativo = Path(root).relative_to(pasta_origem)
                destino_final = Path(pasta_destino) / caminho_relativo / nome_arquivo
                destino_final.parent.mkdir(parents=True, exist_ok=True)
            else:
                destino_final = caminho_arquivo

            if hash_valor in hash_map:
                # Já existe um arquivo igual → mover para duplicata
                duplicata_dir = destino_final.parent / "duplicata"
                duplicata_dir.mkdir(parents=True, exist_ok=True)

                destino_duplicata = duplicata_dir / nome_arquivo
                shutil.move(str(caminho_arquivo), str(destino_duplicata))
                print(f"🔁 Duplicata movida: {caminho_arquivo} -> {destino_duplicata}")
            else:
                hash_map[hash_valor] = destino_final
                if pasta_destino:
                    shutil.copy2(str(caminho_arquivo), str(destino_final))
                    print(f"📂 Copiado: {caminho_arquivo} -> {destino_final}")


def mesclar_pastas(pasta1, pasta2, pasta_destino):
    """Mescla duas pastas (com subpastas) em uma terceira, eliminando duplicatas."""
    print("📁 Processando primeira pasta...")
    processar_pasta(pasta1, pasta_destino)
    print("📁 Processando segunda pasta...")
    processar_pasta(pasta2, pasta_destino)
    print("✅ Mesclagem concluída!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mesclar pastas e remover duplicatas de imagens.")
    parser.add_argument("pasta1", help="Caminho da primeira pasta")
    parser.add_argument("pasta2", nargs="?", help="Caminho da segunda pasta (opcional)")
    parser.add_argument("--destino", help="Caminho da pasta destino (apenas se usar duas pastas)")

    args = parser.parse_args()

    if args.pasta2:
        if not args.destino:
            print("⚠️ É necessário informar --destino ao mesclar duas pastas.")
        else:
            mesclar_pastas(args.pasta1, args.pasta2, args.destino)
    else:
        print("📁 Verificando duplicatas dentro da própria pasta...")
        processar_pasta(args.pasta1)
        print("✅ Processamento concluído!")
