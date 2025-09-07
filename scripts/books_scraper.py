#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper do site https://books.toscrape.com/ usando requests + BeautifulSoup4.

Melhorias de performance:
- Coleta de detalhes dos livros em paralelo por página (ThreadPoolExecutor)
- Parser 'lxml' (fallback automático para 'html.parser' se ausente)
- Reuso do HTML do catálogo (evita baixar 2x)
- Pool de conexões maior + gzip
- Sleep apenas entre páginas
- availability como int; price_* e tax como float

Execução (exemplos):
    python books_scraper.py
    python books_scraper.py --out data/raw/books.csv --delay 0.1 --workers 12
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from dataclasses import dataclass, asdict
from typing import Generator, Iterable, List, Optional, Tuple
from urllib.parse import urljoin
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import re
import unicodedata
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry


# -------- Config --------
BASE_URL = "https://books.toscrape.com/"
CATALOGUE_FIRST = urljoin(BASE_URL, "catalogue/page-1.html")
OUTPUT_DEFAULT = Path("data/raw/books.csv")

# Regex pré-compiladas
RE_DIGITS = re.compile(r"(\d+)")
# permite dígitos, ponto, vírgula, sinais +/-, parênteses (para formatos contábeis)
RE_PRICE = re.compile(r"[^\d,.\-()+]")


def _get_parser() -> str:
    """Escolhe parser mais rápido disponível."""
    try:
        import lxml  # noqa: F401
        return "lxml"
    except Exception:
        return "html.parser"


@dataclass
class BookRecord:
    """Estrutura de dados (linha) para o CSV."""
    title: str
    category: str
    product_type: str
    price_excl_tax: float   # float normalizado
    price_incl_tax: float   # float normalizado
    tax: float              # <- agora garantidamente float limpo
    availability: int       # somente o número de peças
    number_of_reviews: str


class BookScraper:
    """
    Scraper responsável por:
    - Percorrer páginas do catálogo
    - Extrair links de produtos
    - Visitar cada produto em paralelo para coletar campos detalhados
    - Persistir em CSV
    """

    def __init__(self, out_csv: Path | str = OUTPUT_DEFAULT, delay: float = 0.1, max_workers: int = 12) -> None:
        self.out_csv = Path(out_csv)
        self.delay = delay
        self.max_workers = max_workers
        self.session = self._build_session()
        self.parser = _get_parser()

    @staticmethod
    def _build_session() -> requests.Session:
        """Cria sessão HTTP com cabeçalhos, gzip e política de retry."""
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/119.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )
        retries = Retry(
            total=4,
            backoff_factor=0.25,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=50, pool_maxsize=50)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _get_soup(self, url: str) -> BeautifulSoup:
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, self.parser)

    def _iter_catalogue_pages(self) -> Generator[Tuple[str, BeautifulSoup], None, None]:
        """Gera (url_da_página, soup_da_página) do catálogo, reutilizando o HTML."""
        next_url = CATALOGUE_FIRST
        while next_url:
            soup = self._get_soup(next_url)
            yield next_url, soup
            next_link = soup.select_one("ul.pager li.next a")
            next_url = urljoin(next_url, next_link["href"]) if (next_link and next_link.get("href")) else None

    @staticmethod
    def _extract_product_links_from_soup(catalogue_url: str, soup: BeautifulSoup) -> List[str]:
        links: List[str] = []
        for a in soup.select("article.product_pod h3 a"):
            href = a.get("href")
            if href:
                product_url = urljoin(catalogue_url, href)
                links.append(product_url)
        return links

    # ---------- Helpers de normalização ----------
    @staticmethod
    def _extract_digits(s: str) -> int:
        """Extrai o primeiro número inteiro de s; 0 se não houver."""
        if not s:
            return 0
        m = RE_DIGITS.search(s)
        return int(m.group(1)) if m else 0

    @staticmethod
    def _to_float(price_str: str) -> float:
        """
        Converte strings monetárias variadas em float.
        Exemplos:
            '£51.77'     -> 51.77
            'R$ 1.234,56'-> 1234.56
            '(€12,34)'   -> -12.34
        Remove símbolos de moeda/letras, NBSP, lida com parênteses (negativo),
        vírgula como decimal e múltiplos pontos.
        """
        if not price_str:
            return 0.0

        # Normaliza unicode e remove NBSP/espaços
        s = unicodedata.normalize("NFKC", str(price_str))
        neg = "(" in s and ")" in s  # formato contábil: (valor) = negativo
        s = s.replace("\xa0", "").replace(" ", "")

        # Remove tudo que não for dígito, ., ,, +, -, parênteses
        cleaned = RE_PRICE.sub("", s)

        # Remove parênteses (sinal já foi marcado)
        cleaned = cleaned.replace("(", "").replace(")", "")

        # Troca vírgula decimal por ponto
        cleaned = cleaned.replace(",", ".")

        # Se houver múltiplos pontos, mantém só o último como separador decimal
        if cleaned.count(".") > 1:
            parts = cleaned.split(".")
            cleaned = "".join(parts[:-1]) + "." + parts[-1]

        # Normaliza casos como ".99", "-.99", "+.99"
        if cleaned.startswith("."):
            cleaned = "0" + cleaned
        elif cleaned.startswith("-."):
            cleaned = "-0" + cleaned[1:]
        elif cleaned.startswith("+."):
            cleaned = "+0" + cleaned[1:]

        try:
            val = float(cleaned)
        except ValueError:
            return 0.0

        return -val if neg else val

    def _parse_book_page(self, product_url: str) -> Optional[BookRecord]:
        soup = self._get_soup(product_url)

        title_tag = soup.select_one("div.product_main h1")
        title = title_tag.get_text(strip=True) if title_tag else ""

        category_tag = soup.select_one("ul.breadcrumb li:nth-of-type(3) a")
        category = category_tag.get_text(strip=True) if category_tag else ""

        data_map = {}
        for row in soup.select("table.table.table-striped tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                data_map[th.get_text(strip=True)] = td.get_text(strip=True)

        # Disponibilidade (tabela -> fallback no parágrafo superior)
        availability_text = data_map.get("Availability", "")
        if not availability_text:
            av_p = soup.select_one("div.product_main p.availability")
            availability_text = av_p.get_text(strip=True) if av_p else ""
        availability_num = self._extract_digits(availability_text)

        # Preços normalizados
        price_excl = self._to_float(data_map.get("Price (excl. tax)", ""))
        price_incl = self._to_float(data_map.get("Price (incl. tax)", ""))
        tax_clean = self._to_float(data_map.get("Tax", ""))

        return BookRecord(
            title=title,
            category=category,
            product_type=data_map.get("Product Type", ""),
            price_excl_tax=price_excl,
            price_incl_tax=price_incl,
            tax=tax_clean,
            availability=availability_num,
            number_of_reviews=data_map.get("Number of reviews", ""),
        )

    def run(self) -> None:
        # Garante diretório de saída
        self.out_csv.parent.mkdir(parents=True, exist_ok=True)

        # --- início da medição ---
        t0 = time.perf_counter()

        fieldnames = [f.name for f in BookRecord.__dataclass_fields__.values()]
        total = 0

        with open(self.out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for page_url, page_soup in self._iter_catalogue_pages():
                product_urls = self._extract_product_links_from_soup(page_url, page_soup)

                # Coleta em paralelo os detalhes dos produtos desta página
                results: List[BookRecord] = []
                with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                    futures = [ex.submit(self._parse_book_page, u) for u in product_urls]
                    for fut in as_completed(futures):
                        try:
                            rec = fut.result()
                            if rec:
                                results.append(rec)
                        except requests.RequestException as exc:
                            print(f"[WARN] Falha ao processar: {exc}", file=sys.stderr)
                        except Exception as exc:
                            print(f"[WARN] Erro inesperado: {exc}", file=sys.stderr)

                # Escreve em lote após a página terminar
                for rec in results:
                    writer.writerow(asdict(rec))
                    total += 1

                # Polidez: pequeno intervalo entre PÁGINAS (não por produto)
                time.sleep(max(0.05, self.delay * 0.25))

        # --- fim da medição ---
        elapsed = time.perf_counter() - t0
        speed = (total / elapsed) if elapsed > 0 else 0.0

        # Imprime no formato pedido + taxa opcional
        print(f"[OK] Concluído em {elapsed:.2f}s ({speed:.1f} livros/s). {total} livros salvos em: {self.out_csv}")



def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scraper do Books to Scrape (requests + BeautifulSoup)."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=OUTPUT_DEFAULT,
        help=f"Caminho do CSV de saída (padrão: {OUTPUT_DEFAULT})",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Pequeno atraso entre páginas (padrão: 0.1s).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=12,
        help="Número de threads para baixar páginas de produto (padrão: 12).",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    scraper = BookScraper(out_csv=args.out, delay=args.delay, max_workers=args.workers)
    scraper.run()


if __name__ == "__main__":
    main()
