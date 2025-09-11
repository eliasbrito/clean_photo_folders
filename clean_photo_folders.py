import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime

EXTENSOES_IMAGENS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"}


def hash_arquivo(caminho_arquivo, chunk_size=8192):
    """Calcula o hash SHA256 de um arquivo para detectar duplicatas."""
    hash_sha = hashlib.sha256()
    with open(caminho_arquivo, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()


class Relatorio:
    def __init__(self):
        self.total_arquivos = 0
        self.total_copiados = 0
        self.total_duplicados = 0
        self.total_erros = 0
        self.pastas_duplicatas = set()
        self.arquivos_com_erro = []

    def resumo(self):
        print("\n===== 📊 RELATÓRIO FINAL =====")
        print(f"📂 Total de arquivos analisados : {self.total_arquivos}")
        print(f"✅ Arquivos únicos/copied      : {self.total_copiados}")
        print(f"🔁 Arquivos duplicados         : {self.total_duplicados}")
        print(f"⚠️ Arquivos com erro           : {self.total_erros}")

        if self.pastas_duplicatas:
            print("\n📁 Pastas com duplicatas encontradas:")
            for pasta in sorted(self.pastas_duplicatas):
                print(f" - {pasta}")

        if self.arquivos_com_erro:
            print("\n❌ Arquivos que falharam:")
            for arquivo in self.arquivos_com_erro:
                print(f" - {arquivo}")

    def salvar_em_arquivo(self, pasta_saida):
        caminho_log = Path(pasta_saida) / f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(caminho_log, "w", encoding="utf-8") as f:
            f.write("===== 📊 RELATÓRIO FINAL =====\n")
            f.write(f"📂 Total de arquivos analisados : {self.total_arquivos}\n")
            f.write(f"✅ Arquivos únicos/copied      : {self.total_copiados}\n")
            f.write(f"🔁 Arquivos duplicados         : {self.total_duplicados}\n")
            f.write(f"⚠️ Arquivos com erro           : {self.total_erros}\n\n")

            if self.pastas_duplicatas:
                f.write("📁 Pastas com duplicatas encontradas:\n")
                for pasta in sorted(self.pastas_duplicatas):
                    f.write(f" - {pasta}\n")
                f.write("\n")

            if self.arquivos_com_erro:
                f.write("❌ Arquivos que falharam:\n")
                for arquivo in self.arquivos_com_erro:
                    f.write(f" - {arquivo}\n")
        print(f"\n📝 Relatório salvo em: {caminho_log}")


def processar_pasta(pasta_origem, pasta_destino=None, relatorio=None):
    """Copia/move arquivos, detectando duplicatas em imagens e movendo para subpasta 'duplicata'."""
    hash_map = {}

    for root, _, files in os.walk(pasta_origem):
        for nome_arquivo in files:
            caminho_arquivo = Path(root) / nome_arquivo

            if not caminho_arquivo.is_file():
                continue

            if relatorio:
                relatorio.total_arquivos += 1

            ext = caminho_arquivo.suffix.lower()

            # Se for imagem, calcula hash e verifica duplicata
            if ext in EXTENSOES_IMAGENS:
                try:
                    hash_valor = hash_arquivo(caminho_arquivo)
                except Exception as e:
                    print(f"❌ Erro ao calcular hash: {caminho_arquivo} ({e})")
                    if relatorio:
                        relatorio.total_erros += 1
                        relatorio.arquivos_com_erro.append(str(caminho_arquivo))
                    continue
            else:
                hash_valor = None  # outros arquivos não verificam duplicata

            if pasta_destino:
                caminho_relativo = Path(root).relative_to(pasta_origem)
                destino_final = Path(pasta_destino) / caminho_relativo / nome_arquivo
                destino_final.parent.mkdir(parents=True, exist_ok=True)
            else:
                destino_final = caminho_arquivo

            try:
                if ext in EXTENSOES_IMAGENS and hash_valor in hash_map:
                    # já existe → duplicata
                    duplicata_dir = destino_final.parent / "duplicata"
                    duplicata_dir.mkdir(parents=True, exist_ok=True)
                    destino_duplicata = duplicata_dir / nome_arquivo

                    shutil.move(str(caminho_arquivo), str(destino_duplicata))
                    print(f"🔁 Duplicata movida: {caminho_arquivo} -> {destino_duplicata}")

                    if relatorio:
                        relatorio.total_duplicados += 1
                        relatorio.pastas_duplicatas.add(str(duplicata_dir))
                else:
                    if hash_valor:
                        hash_map[hash_valor] = destino_final
                    if pasta_destino:
                        shutil.copy2(str(caminho_arquivo), str(destino_final))
                        print(f"📂 Copiado: {caminho_arquivo} -> {destino_final}")
                    if relatorio:
                        relatorio.total_copiados += 1
            except Exception as e:
                print(f"❌ Erro ao processar {caminho_arquivo}: {e}")
                if relatorio:
                    relatorio.total_erros += 1
                    relatorio.arquivos_com_erro.append(str(caminho_arquivo))


def mesclar_pastas(pasta1, pasta2, pasta_destino):
    relatorio = Relatorio()
    print("📁 Processando primeira pasta...")
    processar_pasta(pasta1, pasta_destino, relatorio)
    print("📁 Processando segunda pasta...")
    processar_pasta(pasta2, pasta_destino, relatorio)
    print("✅ Mesclagem concluída!")
    relatorio.resumo()
    relatorio.salvar_em_arquivo(pasta_destino)


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
        relatorio = Relatorio()
        processar_pasta(args.pasta1, relatorio=relatorio)
        print("✅ Processamento concluído!")
        relatorio.resumo()
        relatorio.salvar_em_arquivo(args.pasta1)
