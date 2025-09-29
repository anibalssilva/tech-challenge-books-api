#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass, asdict
from typing import Generator, List, Optional, Tuple
from urllib.parse import urljoin
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import local

import re
import unicodedata
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

#Teste de commit

# -------- Config --------
BASE_URL = "https://books.toscrape.com/"
CATALOGUE_FIRST = urljoin(BASE_URL, "catalogue/page-1.html")
OUTPUT_DEFAULT = Path("../data/raw/books.csv")

# Regex pré-compiladas
RE_DIGITS = re.compile(r"(\d+)")
# permite dígitos, ponto, vírgula, sinais +/-, parênteses (para (12,34) negativo)
RE_PRICE = re.compile(r"[^\d,.\-()+]")

def _get_parser() -> str:
    try:
        import lxml  # noqa: F401
        return "lxml"
    except Exception:
        return "html.parser"

RATING_MAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

@dataclass
class BookRecord:
    # Cabeçalho/infos principais
    title: str
    category: str
    image_url: str
    description: str
    rating: int
    # Tabela "Product Information"
    upc: str
    product_type: str
    price_excl_tax: float
    price_incl_tax: float
    tax: float
    availability: int
    # number_of_reviews: int

class BookScraper:
    def __init__(self, out_csv: Path | str = OUTPUT_DEFAULT, delay: float = 0.1, max_workers: int = 12, verbose: bool = False) -> None:
        self.out_csv = Path(out_csv)
        self.delay = delay
        self.max_workers = max_workers
        self.verbose = verbose
        self.parser = _get_parser()
        # cada thread terá sua própria session
        self._tls = local()

    # ---------- Sessão por thread ----------
    @staticmethod
    def _build_session() -> requests.Session:
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
        adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=20)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _thread_session(self) -> requests.Session:
        s = getattr(self._tls, "session", None)
        if s is None:
            s = self._build_session()
            self._tls.session = s
        return s

    # ---------- HTTP + parsing ----------
    def _get_soup(self, url: str) -> BeautifulSoup:
        resp = self._thread_session().get(url, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, self.parser)

    def _iter_catalogue_pages(self) -> Generator[Tuple[str, BeautifulSoup], None, None]:
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

    # ---------- Helpers ----------
    @staticmethod
    def _extract_digits(s: str) -> int:
        if not s:
            return 0
        m = RE_DIGITS.search(s)
        return int(m.group(1)) if m else 0

    @staticmethod
    def _to_float(price_str: str) -> float:
        if not price_str:
            return 0.0
        s = unicodedata.normalize("NFKC", str(price_str))
        neg = "(" in s and ")" in s
        s = s.replace("\xa0", "").replace(" ", "")
        cleaned = RE_PRICE.sub("", s)
        cleaned = cleaned.replace("(", "").replace(")", "")
        cleaned = cleaned.replace(",", ".")
        if cleaned.count(".") > 1:
            parts = cleaned.split(".")
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
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

    @staticmethod
    def _parse_description(soup: BeautifulSoup) -> str:
        h = soup.select_one("#product_description")
        if not h:
            return ""
        p = h.find_next_sibling("p")
        return p.get_text(strip=True) if p else ""

    @staticmethod
    def _parse_image_url(soup: BeautifulSoup) -> str:
        img = (
            soup.select_one("article.product_page img")
            or soup.select_one("div.thumbnail img")
            or soup.select_one("div.item.active img")
            or soup.select_one("img")
        )
        if not img or not img.get("src"):
            return ""
        return urljoin(BASE_URL, img["src"])

    @staticmethod
    def _parse_rating(soup: BeautifulSoup) -> int:
        tag = soup.select_one("p.star-rating")
        if not tag:
            return 0
        classes = [c.lower() for c in tag.get("class", []) if c.lower() != "star-rating"]
        for c in classes:
            val = RATING_MAP.get(c)
            if val:
                return val
        return 0

    # ---------- Parse de página de produto ----------
    def _parse_book_page(self, product_url: str) -> Optional[BookRecord]:
        soup = self._get_soup(product_url)

        title_tag = soup.select_one("div.product_main h1")
        title = title_tag.get_text(strip=True) if title_tag else ""
        category_tag = soup.select_one("ul.breadcrumb li:nth-of-type(3) a")
        category = category_tag.get_text(strip=True) if category_tag else ""

        image_url = self._parse_image_url(soup)
        description = self._parse_description(soup)
        rating = self._parse_rating(soup)

        data_map = {}
        for row in soup.select("table.table.table-striped tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                data_map[th.get_text(strip=True)] = td.get_text(strip=True)

        upc = data_map.get("UPC", "")
        product_type = data_map.get("Product Type", "")

        availability_text = data_map.get("Availability", "")
        if not availability_text:
            av_p = soup.select_one("div.product_main p.availability")
            availability_text = av_p.get_text(strip=True) if av_p else ""
        availability_num = self._extract_digits(availability_text)

        price_excl = self._to_float(data_map.get("Price (excl. tax)", ""))
        price_incl = self._to_float(data_map.get("Price (incl. tax)", ""))
        tax_clean = self._to_float(data_map.get("Tax", ""))

        num_reviews = self._extract_digits(data_map.get("Number of reviews", ""))

        return BookRecord(
            title=title,
            category=category,
            image_url=image_url,
            description=description,
            rating=rating,
            upc=upc,
            product_type=product_type,
            price_excl_tax=price_excl,
            price_incl_tax=price_incl,
            tax=tax_clean,
            availability=availability_num,
            # number_of_reviews=num_reviews,
        )

    # ---------- Coleta de URLs (ordem global) ----------
    def _gather_all_product_urls(self) -> List[str]:
        urls: List[str] = []
        for page_url, page_soup in self._iter_catalogue_pages():
            page_urls = self._extract_product_links_from_soup(page_url, page_soup)
            urls.extend(page_urls)
        return urls

    # ---------- Loop principal (paralelismo global) ----------
    def run(self) -> None:
        self.out_csv.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.perf_counter()

        product_urls = self._gather_all_product_urls()
        total_urls = len(product_urls)
        if self.verbose:
            print(f"[INFO] {total_urls} produtos encontrados. Disparando com {self.max_workers} workers...")

        fieldnames = [f.name for f in BookRecord.__dataclass_fields__.values()]
        ordered_results: List[Optional[BookRecord]] = [None] * total_urls
        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            future_to_idx = {
                ex.submit(self._parse_book_page, u): idx
                for idx, u in enumerate(product_urls)
            }
            for fut in as_completed(future_to_idx):
                idx = future_to_idx[fut]
                try:
                    rec = fut.result()
                    if rec:
                        ordered_results[idx] = rec
                except requests.RequestException as exc:
                    print(f"[WARN] Falha ao processar: {exc}", file=sys.stderr)
                except Exception as exc:
                    print(f"[WARN] Erro inesperado: {exc}", file=sys.stderr)
                finally:
                    completed += 1
                    if self.verbose and completed % 20 == 0:
                        print(f"[INFO] {completed}/{total_urls} concluídos")

        # grava em ORDEM GLOBAL do catálogo
        with open(self.out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            total = 0
            for rec in ordered_results:
                if rec:
                    writer.writerow(asdict(rec))
                    total += 1

        elapsed = time.perf_counter() - t0
        speed = (total / elapsed) if elapsed > 0 else 0.0
        print(f"[OK] Concluído em {elapsed:.2f}s ({speed:.1f} livros/s). {total} livros salvos em: {self.out_csv}")

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scraper do Books to Scrape (requests + BeautifulSoup).")
    parser.add_argument("--out", type=Path, default=OUTPUT_DEFAULT,
                        help=f"Caminho do CSV de saída (padrão: {OUTPUT_DEFAULT})")
    parser.add_argument("--delay", type=float, default=0.1,
                        help="(Ignorado no modo global) Atraso entre páginas.")
    parser.add_argument("--workers", type=int, default=12,
                        help="Número de threads (padrão: 12).")
    parser.add_argument("--verbose", action="store_true",
                        help="Exibe progresso para visualizar o paralelismo.")
    return parser.parse_args(argv)

def main() -> None:
    args = parse_args()
    scraper = BookScraper(out_csv=args.out, delay=args.delay, max_workers=args.workers, verbose=args.verbose)
    scraper.run()

if __name__ == "__main__":
    main()
