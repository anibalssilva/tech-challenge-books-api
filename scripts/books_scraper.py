#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper do site https://books.toscrape.com/ usando requests + BeautifulSoup4.

Coleta de cada livro:
- Título
- Categoria
- Product Type
- Price (excl. tax)
- Price (incl. tax)
- Tax
- Availability
- Number of reviews

Navega por todas as páginas do catálogo e visita a página de cada livro
para obter os detalhes. Salva em CSV local (data/raw/books.csv).

Execução (exemplos):
    python scrape_books.py
    python scrape_books.py --out data/raw/books.csv --delay 0.5
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from dataclasses import dataclass, asdict
from typing import Generator, Iterable, List, Optional
from urllib.parse import urljoin
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_FIRST = urljoin(BASE_URL, "catalogue/page-1.html")
OUTPUT_DEFAULT = Path("data/raw/books.csv")


@dataclass
class BookRecord:
    """Estrutura de dados (linha) para o CSV."""
    title: str
    category: str
    product_type: str
    price_excl_tax: str
    price_incl_tax: str
    tax: str
    availability: str
    number_of_reviews: str


class BookScraper:
    """
    Scraper responsável por:
    - Percorrer todas as páginas do catálogo
    - Extrair links de produtos
    - Visitar cada produto para coletar campos detalhados
    - Persistir em CSV
    """

    def __init__(self, out_csv: str = OUTPUT_DEFAULT, delay: float = 0.3) -> None:
        self.out_csv = out_csv
        self.delay = delay
        self.session = self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        """Cria uma sessão HTTP com cabeçalhos e política de retry robusta."""
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
                "Connection": "keep-alive",
            }
        )
        retries = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _get_soup(self, url: str) -> BeautifulSoup:
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    def _iter_catalogue_pages(self) -> Generator[str, None, None]:
        next_url = CATALOGUE_FIRST
        while next_url:
            yield next_url
            soup = self._get_soup(next_url)
            next_link = soup.select_one("ul.pager li.next a")
            if next_link and next_link.get("href"):
                next_url = urljoin(next_url, next_link["href"])
            else:
                next_url = None

    def _extract_product_links(self, catalogue_url: str) -> List[str]:
        soup = self._get_soup(catalogue_url)
        links = []
        for a in soup.select("article.product_pod h3 a"):
            href = a.get("href")
            if href:
                product_url = urljoin(catalogue_url, href)
                links.append(product_url)
        return links

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

        return BookRecord(
            title=title,
            category=category,
            product_type=data_map.get("Product Type", ""),
            price_excl_tax=data_map.get("Price (excl. tax)", ""),
            price_incl_tax=data_map.get("Price (incl. tax)", ""),
            tax=data_map.get("Tax", ""),
            availability=data_map.get("Availability", ""),
            number_of_reviews=data_map.get("Number of reviews", ""),
        )

    def run(self) -> None:
        fieldnames = [f.name for f in BookRecord.__dataclass_fields__.values()]
        total = 0

        with open(self.out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for page_url in self._iter_catalogue_pages():
                for product_url in self._extract_product_links(page_url):
                    try:
                        record = self._parse_book_page(product_url)
                        if record:
                            writer.writerow(asdict(record))
                            total += 1
                    except requests.RequestException as exc:
                        print(f"[WARN] Falha ao processar {product_url}: {exc}", file=sys.stderr)

                    time.sleep(self.delay + random.uniform(0, self.delay / 2))

        print(f"[OK] Concluído. {total} livros salvos em: {self.out_csv}")


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
        default=0.3,
        help="Atraso (segundos) entre requisições (padrão: 0.3s).",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    scraper = BookScraper(out_csv=args.out, delay=args.delay)
    scraper.run()


if __name__ == "__main__":
    main()
