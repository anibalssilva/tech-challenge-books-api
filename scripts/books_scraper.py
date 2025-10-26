#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Scraper para Books to Scrape
================================

Este script realiza web scraping do site books.toscrape.com para extrair informações
sobre livros e salvá-las em um arquivo CSV. Utiliza paralelização com ThreadPoolExecutor
para melhorar a performance.

Funcionalidades:
- Extração de dados de livros (título, categoria, preço, avaliação, etc.)
- Processamento paralelo com múltiplas threads
- Tratamento de erros e retry automático
- Saída em formato CSV com encoding UTF-8

Autor: Tech Challenge - Fase 1
"""

from __future__ import annotations

# Imports padrão do Python
import argparse  # Para parsing de argumentos da linha de comando
import csv      # Para manipulação de arquivos CSV
import sys      # Para acesso ao stderr
import time     # Para medição de tempo de execução

# Imports para estruturas de dados e tipos
from dataclasses import dataclass, asdict  # Para criar classes de dados e conversão para dict
from typing import Generator, List, Optional, Tuple  # Para type hints

# Imports para manipulação de URLs e caminhos
from urllib.parse import urljoin  # Para construção de URLs absolutas
from pathlib import Path  # Para manipulação de caminhos de arquivo

# Imports para paralelização
from concurrent.futures import ThreadPoolExecutor, as_completed  # Para execução paralela
from threading import local  # Para armazenamento thread-local

# Imports para processamento de texto e regex
import re  # Para expressões regulares
import unicodedata  # Para normalização de caracteres Unicode

# Imports para requisições HTTP e parsing HTML
import requests  # Para fazer requisições HTTP
from bs4 import BeautifulSoup  # Para parsing de HTML
from requests.adapters import HTTPAdapter, Retry  # Para configuração de sessão HTTP

# Imports para logging estruturado
sys.path.append(str(Path(__file__).parent.parent))
import structlog
from logs.setup_logging import setup_logging

# =============================================================================
# CONFIGURAÇÕES E CONSTANTES
# =============================================================================

# Path do log do books_scrapper e configurando o log
LOG_PATH = Path("./logs/scrapper.log")
setup_logging(LOG_PATH)
logger = structlog.get_logger("web_scraper")

# URL base do site que será feito o scraping
BASE_URL = "https://books.toscrape.com/"

# URL da primeira página do catálogo de livros
CATALOGUE_FIRST = urljoin(BASE_URL, "catalogue/page-1.html")

# Caminho padrão para o arquivo CSV de saída
OUTPUT_DEFAULT = Path("../data/raw/books.csv")

# =============================================================================
# EXPRESSÕES REGULARES PRÉ-COMPILADAS
# =============================================================================

# Regex para extrair números de strings (ex: "22 available" -> 22)
RE_DIGITS = re.compile(r"(\d+)")

# Regex para limpar preços: remove tudo exceto dígitos, ponto, vírgula, 
# sinais +/-, parênteses (para valores negativos como (12,34))
RE_PRICE = re.compile(r"[^\d,.\-()+]")

# =============================================================================
# FUNÇÕES AUXILIARES DE CONFIGURAÇÃO
# =============================================================================

def _get_parser() -> str:
    """
    Determina qual parser HTML usar baseado na disponibilidade do lxml.
    
    Returns:
        str: Nome do parser a ser usado ('lxml' ou 'html.parser')
    """
    try:
        import lxml  # noqa: F401
        return "lxml"  # Parser mais rápido se disponível
    except Exception:
        return "html.parser"  # Parser padrão do Python

# =============================================================================
# MAPEAMENTOS E CONSTANTES DE DADOS
# =============================================================================

# Mapeamento das classes CSS de rating para valores numéricos
# O site usa classes como "star-rating One", "star-rating Two", etc.
RATING_MAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

# =============================================================================
# CLASSES DE DADOS
# =============================================================================

@dataclass
class BookRecord:
    """
    Representa os dados de um livro extraídos do site.
    
    Esta classe define a estrutura de dados que será extraída de cada página
    de produto e salva no arquivo CSV.
    
    Attributes:
        title (str): Título do livro
        category (str): Categoria do livro (ex: Fiction, Poetry, etc.)
        image_url (str): URL da imagem de capa do livro
        description (str): Descrição/sinopse do livro
        rating (int): Avaliação em estrelas (1-5)
        upc (str): Código UPC do produto
        product_type (str): Tipo do produto (geralmente "Books")
        price_excl_tax (float): Preço sem impostos
        price_incl_tax (float): Preço com impostos
        tax (float): Valor do imposto
        availability (int): Quantidade disponível em estoque
    """
    # Informações principais do livro
    title: str          # Título do livro
    category: str       # Categoria (Fiction, Poetry, etc.)
    image_url: str      # URL da imagem de capa
    description: str    # Descrição/sinopse
    rating: int         # Avaliação em estrelas (1-5)
    
    # Informações da tabela "Product Information"
    upc: str            # Código UPC único do produto
    product_type: str   # Tipo do produto (geralmente "Books")
    price_excl_tax: float  # Preço sem impostos
    price_incl_tax: float  # Preço com impostos incluídos
    tax: float          # Valor do imposto
    availability: int   # Quantidade disponível em estoque
    
    # Campo comentado: número de avaliações (não usado atualmente)
    # number_of_reviews: int

# =============================================================================
# CLASSE PRINCIPAL DO SCRAPER
# =============================================================================

class BookScraper:
    """
    Classe principal para realizar web scraping do site books.toscrape.com.
    
    Esta classe gerencia todo o processo de scraping, incluindo:
    - Configuração de sessões HTTP com retry automático
    - Navegação pelas páginas do catálogo
    - Extração de dados de cada livro
    - Processamento paralelo com múltiplas threads
    - Salvamento dos dados em arquivo CSV
    
    Attributes:
        out_csv (Path): Caminho do arquivo CSV de saída
        delay (float): Atraso entre requisições (não usado no modo paralelo)
        max_workers (int): Número máximo de threads para processamento paralelo
        verbose (bool): Se deve exibir informações de progresso
        parser (str): Parser HTML a ser usado
        _tls (local): Armazenamento thread-local para sessões HTTP
    """
    
    def __init__(self, out_csv: Path | str = OUTPUT_DEFAULT, delay: float = 0.1, max_workers: int = 12, verbose: bool = False) -> None:
        """
        Inicializa o scraper com as configurações especificadas.
        
        Args:
            out_csv (Path | str): Caminho do arquivo CSV de saída
            delay (float): Atraso entre requisições (ignorado no modo paralelo)
            max_workers (int): Número de threads para processamento paralelo
            verbose (bool): Se deve exibir informações de progresso
        """
        self.out_csv = Path(out_csv)      # Caminho do arquivo de saída
        self.delay = delay               # Atraso entre requisições (não usado)
        self.max_workers = max_workers   # Número de threads paralelas
        self.verbose = verbose           # Modo verboso para debug
        self.parser = _get_parser()      # Parser HTML a ser usado
        
        # Armazenamento thread-local: cada thread terá sua própria sessão HTTP
        self._tls = local()

    # =============================================================================
    # GERENCIAMENTO DE SESSÕES HTTP
    # =============================================================================
    
    @staticmethod
    def _build_session() -> requests.Session:
        """
        Cria uma nova sessão HTTP configurada com headers e retry automático.
        
        Configura:
        - Headers para simular um navegador real
        - Retry automático para códigos de erro específicos
        - Pool de conexões para melhor performance
        
        Returns:
            requests.Session: Sessão HTTP configurada
        """
        session = requests.Session()
        
        # Headers para simular um navegador real e evitar bloqueios
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
        
        # Configuração de retry automático para códigos de erro comuns
        retries = Retry(
            total=4,                    # Máximo de 4 tentativas
            backoff_factor=0.25,        # Atraso exponencial entre tentativas
            status_forcelist=(429, 500, 502, 503, 504),  # Códigos para retry
            allowed_methods=frozenset(["GET"]),           # Apenas GET
            raise_on_status=False,      # Não levantar exceção em códigos de erro
        )
        
        # Adapter com pool de conexões para melhor performance
        adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=20)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def _thread_session(self) -> requests.Session:
        """
        Obtém ou cria uma sessão HTTP específica para a thread atual.
        
        Usa thread-local storage para garantir que cada thread tenha sua própria
        sessão HTTP, evitando problemas de concorrência.
        
        Returns:
            requests.Session: Sessão HTTP da thread atual
        """
        # Verifica se já existe uma sessão para esta thread
        s = getattr(self._tls, "session", None)
        if s is None:
            # Cria uma nova sessão se não existir
            s = self._build_session()
            self._tls.session = s
        return s

    # =============================================================================
    # MÉTODOS DE REQUISIÇÕES HTTP E PARSING
    # =============================================================================
    
    def _get_soup(self, url: str) -> BeautifulSoup:
        """
        Faz uma requisição HTTP e retorna o HTML parseado como BeautifulSoup.
        
        Args:
            url (str): URL para fazer a requisição
            
        Returns:
            BeautifulSoup: Objeto BeautifulSoup com o HTML parseado
            
        Raises:
            requests.RequestException: Se a requisição falhar
        """
        # Faz a requisição HTTP com timeout de 15 segundos
        resp = self._thread_session().get(url, timeout=15)
        resp.raise_for_status()  # Levanta exceção se status não for 2xx
        
        # Retorna o HTML parseado usando o parser configurado
        return BeautifulSoup(resp.text, self.parser)

    def _iter_catalogue_pages(self) -> Generator[Tuple[str, BeautifulSoup], None, None]:
        """
        Itera através de todas as páginas do catálogo de livros.
        
        Navega automaticamente pelas páginas seguindo os links "Next" até
        não haver mais páginas disponíveis.
        
        Yields:
            Tuple[str, BeautifulSoup]: Tupla contendo (URL_da_página, HTML_parseado)
        """
        next_url = CATALOGUE_FIRST  # Começa pela primeira página
        
        while next_url:
            # Faz requisição e parse da página atual
            soup = self._get_soup(next_url)
            yield next_url, soup
            
            # Procura pelo link "Next" para ir para a próxima página
            next_link = soup.select_one("ul.pager li.next a")
            
            # Se encontrar link "Next", constrói a URL da próxima página
            # Caso contrário, next_url será None e o loop termina
            next_url = urljoin(next_url, next_link["href"]) if (next_link and next_link.get("href")) else None

    @staticmethod
    def _extract_product_links_from_soup(catalogue_url: str, soup: BeautifulSoup) -> List[str]:
        """
        Extrai todos os links de produtos de uma página do catálogo.
        
        Args:
            catalogue_url (str): URL da página do catálogo (para construir URLs absolutas)
            soup (BeautifulSoup): HTML parseado da página do catálogo
            
        Returns:
            List[str]: Lista de URLs absolutas dos produtos encontrados
        """
        links: List[str] = []
        
        # Procura por todos os links de produtos na página
        # Cada produto está em um <article class="product_pod"> com <h3><a>
        for a in soup.select("article.product_pod h3 a"):
            href = a.get("href")
            if href:
                # Constrói URL absoluta combinando a URL da página com o href relativo
                product_url = urljoin(catalogue_url, href)
                links.append(product_url)
        
        return links

    # =============================================================================
    # MÉTODOS AUXILIARES (HELPERS)
    # =============================================================================
    
    @staticmethod
    def _extract_digits(s: str) -> int:
        """
        Extrai o primeiro número encontrado em uma string.
        
        Útil para extrair quantidades de estoque de strings como "22 available".
        
        Args:
            s (str): String de onde extrair o número
            
        Returns:
            int: Primeiro número encontrado, ou 0 se não encontrar nenhum
        """
        if not s:
            return 0
        
        # Usa regex pré-compilada para encontrar o primeiro número
        m = RE_DIGITS.search(s)
        return int(m.group(1)) if m else 0

    @staticmethod
    def _to_float(price_str: str) -> float:
        """
        Converte uma string de preço para float, lidando com diferentes formatos.
        
        Trata formatos como:
        - "£51.77" -> 51.77
        - "£12.84" -> 12.84
        - "(12.34)" -> -12.34 (valores negativos)
        
        Args:
            price_str (str): String contendo o preço
            
        Returns:
            float: Valor numérico do preço, ou 0.0 se não conseguir converter
        """
        if not price_str:
            return 0.0
        
        # Normaliza caracteres Unicode (remove acentos, etc.)
        s = unicodedata.normalize("NFKC", str(price_str))
        
        # Detecta se é um valor negativo (entre parênteses)
        neg = "(" in s and ")" in s
        
        # Remove espaços e caracteres especiais
        s = s.replace("\xa0", "").replace(" ", "")
        
        # Remove tudo exceto dígitos, pontos, vírgulas e sinais
        cleaned = RE_PRICE.sub("", s)
        cleaned = cleaned.replace("(", "").replace(")", "")
        
        # Converte vírgulas para pontos (formato europeu -> americano)
        cleaned = cleaned.replace(",", ".")
        
        # Trata múltiplos pontos (ex: "1.234.567" -> "1234567")
        if cleaned.count(".") > 1:
            parts = cleaned.split(".")
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        
        # Adiciona zero antes do ponto se necessário
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
        
        # Retorna valor negativo se estava entre parênteses
        return -val if neg else val

    # =============================================================================
    # MÉTODOS DE PARSING ESPECÍFICOS
    # =============================================================================
    
    @staticmethod
    def _parse_description(soup: BeautifulSoup) -> str:
        """
        Extrai a descrição do livro da página de produto.
        
        Procura pela seção com id "product_description" e extrai o texto
        do parágrafo seguinte.
        
        Args:
            soup (BeautifulSoup): HTML parseado da página de produto
            
        Returns:
            str: Descrição do livro, ou string vazia se não encontrar
        """
        # Procura pelo elemento com id "product_description"
        h = soup.select_one("#product_description")
        if not h:
            return ""
        
        # Procura pelo parágrafo seguinte (que contém a descrição)
        p = h.find_next_sibling("p")
        return p.get_text(strip=True) if p else ""

    @staticmethod
    def _parse_image_url(soup: BeautifulSoup) -> str:
        """
        Extrai a URL da imagem de capa do livro.
        
        Tenta diferentes seletores CSS para encontrar a imagem, em ordem
        de prioridade, e constrói a URL absoluta.
        
        Args:
            soup (BeautifulSoup): HTML parseado da página de produto
            
        Returns:
            str: URL absoluta da imagem, ou string vazia se não encontrar
        """
        # Tenta diferentes seletores CSS em ordem de prioridade
        img = (
            soup.select_one("article.product_page img")      # Imagem principal da página
            or soup.select_one("div.thumbnail img")          # Imagem no thumbnail
            or soup.select_one("div.item.active img")       # Imagem ativa em carousel
            or soup.select_one("img")                       # Qualquer imagem como fallback
        )
        
        if not img or not img.get("src"):
            return ""
        
        # Constrói URL absoluta combinando com a URL base
        return urljoin(BASE_URL, img["src"])

    @staticmethod
    def _parse_rating(soup: BeautifulSoup) -> int:
        """
        Extrai a avaliação em estrelas do livro.
        
        Procura pelo elemento com classe "star-rating" e determina
        quantas estrelas baseado nas classes CSS adicionais.
        
        Args:
            soup (BeautifulSoup): HTML parseado da página de produto
            
        Returns:
            int: Número de estrelas (1-5), ou 0 se não encontrar
        """
        # Procura pelo elemento de rating
        tag = soup.select_one("p.star-rating")
        if not tag:
            return 0
        
        # Extrai todas as classes CSS exceto "star-rating"
        classes = [c.lower() for c in tag.get("class", []) if c.lower() != "star-rating"]
        
        # Procura por uma classe que corresponda ao mapeamento de rating
        for c in classes:
            val = RATING_MAP.get(c)
            if val:
                return val
        
        return 0

    # =============================================================================
    # MÉTODO PRINCIPAL DE PARSING DE PÁGINA DE PRODUTO
    # =============================================================================
    
    def _parse_book_page(self, product_url: str) -> Optional[BookRecord]:
        """
        Extrai todos os dados de um livro de sua página de produto.
        
        Este é o método principal que coordena a extração de todos os dados
        de uma página de produto individual, utilizando os métodos auxiliares
        de parsing específicos.
        
        Args:
            product_url (str): URL da página de produto do livro
            
        Returns:
            Optional[BookRecord]: Objeto BookRecord com os dados extraídos,
                                ou None se houver erro na extração
        """
        # Faz requisição e parse da página de produto
        soup = self._get_soup(product_url)

        # =============================================================================
        # EXTRAÇÃO DE INFORMAÇÕES PRINCIPAIS
        # =============================================================================
        
        # Extrai título do livro
        title_tag = soup.select_one("div.product_main h1")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Extrai categoria do breadcrumb (navegação)
        category_tag = soup.select_one("ul.breadcrumb li:nth-of-type(3) a")
        category = category_tag.get_text(strip=True) if category_tag else ""

        # Extrai informações adicionais usando métodos auxiliares
        image_url = self._parse_image_url(soup)
        description = self._parse_description(soup)
        rating = self._parse_rating(soup)

        # =============================================================================
        # EXTRAÇÃO DE DADOS DA TABELA "PRODUCT INFORMATION"
        # =============================================================================
        
        # Cria um dicionário com os dados da tabela de informações do produto
        data_map = {}
        for row in soup.select("table.table.table-striped tr"):
            th = row.find("th")  # Cabeçalho da linha
            td = row.find("td")  # Dados da linha
            if th and td:
                # Mapeia cabeçalho -> valor
                data_map[th.get_text(strip=True)] = td.get_text(strip=True)

        # Extrai dados específicos da tabela
        upc = data_map.get("UPC", "")
        product_type = data_map.get("Product Type", "")

        # =============================================================================
        # PROCESSAMENTO DE DISPONIBILIDADE
        # =============================================================================
        
        # Tenta extrair disponibilidade da tabela primeiro
        availability_text = data_map.get("Availability", "")
        
        # Se não encontrar na tabela, procura em outro local
        if not availability_text:
            av_p = soup.select_one("div.product_main p.availability")
            availability_text = av_p.get_text(strip=True) if av_p else ""
        
        # Converte texto de disponibilidade para número
        availability_num = self._extract_digits(availability_text)

        # =============================================================================
        # PROCESSAMENTO DE PREÇOS
        # =============================================================================
        
        # Extrai e converte preços usando o método auxiliar
        price_excl = self._to_float(data_map.get("Price (excl. tax)", ""))
        price_incl = self._to_float(data_map.get("Price (incl. tax)", ""))
        tax_clean = self._to_float(data_map.get("Tax", ""))

        # =============================================================================
        # INFORMAÇÕES ADICIONAIS (NÃO USADAS ATUALMENTE)
        # =============================================================================
        
        # Extrai número de avaliações (campo comentado no BookRecord)
        num_reviews = self._extract_digits(data_map.get("Number of reviews", ""))

        # =============================================================================
        # CRIAÇÃO DO OBJETO DE RETORNO
        # =============================================================================
        
        # Cria e retorna o objeto BookRecord com todos os dados extraídos
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
            # number_of_reviews=num_reviews,  # Campo comentado
        )

    # =============================================================================
    # MÉTODOS DE COLETA E PROCESSAMENTO
    # =============================================================================
    
    def _gather_all_product_urls(self) -> List[str]:
        """
        Coleta todas as URLs de produtos de todas as páginas do catálogo.
        
        Itera através de todas as páginas do catálogo e extrai os links
        de todos os produtos encontrados, mantendo a ordem global.
        
        Returns:
            List[str]: Lista de todas as URLs de produtos encontradas
        """
        urls: List[str] = []
        
        # Itera através de todas as páginas do catálogo
        for page_url, page_soup in self._iter_catalogue_pages():
            # Extrai links de produtos da página atual
            page_urls = self._extract_product_links_from_soup(page_url, page_soup)
            urls.extend(page_urls)
        
        return urls

    # =============================================================================
    # MÉTODO PRINCIPAL DE EXECUÇÃO
    # =============================================================================
    
    def run(self) -> None:
        """
        Executa o processo completo de web scraping.
        
        Este é o método principal que coordena todo o processo:
        1. Coleta todas as URLs de produtos
        2. Processa os produtos em paralelo usando ThreadPoolExecutor
        3. Mantém a ordem original dos produtos
        4. Salva os resultados em arquivo CSV
        5. Exibe estatísticas de performance
        
        O processamento é feito em paralelo para melhor performance,
        mas os resultados são salvos na ordem original do catálogo.
        """
        # Cria o diretório de saída se não existir
        logger.info(f"Creating output directory if not exists: {self.out_csv.parent}", title=None, duration=None)
        self.out_csv.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicia cronômetro para medir performance
        t0 = time.perf_counter()

        # =============================================================================
        # FASE 1: COLETA DE URLs
        # =============================================================================
        
        # Coleta todas as URLs de produtos de todas as páginas
        logger.info("Gathering all product URLs from catalogue...", title=None, duration=time.perf_counter()-t0)
        product_urls = self._gather_all_product_urls()
        total_urls = len(product_urls)
        logger.info(f"Found {total_urls} product URLs.", title=None, duration=time.perf_counter()-t0)
        
        if self.verbose:
            logger.info(f"[INFO] {total_urls} produtos encontrados. Disparando com {self.max_workers} workers...", title=None, duration=time.perf_counter()-t0)

        # =============================================================================
        # FASE 2: PREPARAÇÃO PARA PROCESSAMENTO PARALELO
        # =============================================================================
        
        # Obtém os nomes dos campos da classe BookRecord para o CSV
        fieldnames = [f.name for f in BookRecord.__dataclass_fields__.values()]
        
        # Lista para manter os resultados na ordem original
        # Usa None como placeholder para produtos que falharam
        ordered_results: List[Optional[BookRecord]] = [None] * total_urls
        completed = 0

        # =============================================================================
        # FASE 3: PROCESSAMENTO PARALELO
        # =============================================================================
        
        # Usa ThreadPoolExecutor para processar múltiplos produtos simultaneamente
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            # Cria um mapeamento de future -> índice para manter a ordem
            future_to_idx = {
                ex.submit(self._parse_book_page, u): idx
                for idx, u in enumerate(product_urls)
            }
            
            # Processa os resultados conforme ficam prontos
            for fut in as_completed(future_to_idx):
                idx = future_to_idx[fut]
                try:
                    # Obtém o resultado do parsing
                    rec = fut.result()
                    if rec:
                        # Armazena na posição correta para manter a ordem
                        logger.info('Processed book: ', title=rec.title, duration=time.perf_counter()-t0)
                        ordered_results[idx] = rec
                except requests.RequestException as exc:
                    # Trata erros de requisição HTTP
                    logger.warn(f'Falha ao processar: {exc}', title=rec.title, duration=time.perf_counter()-t0)
                except Exception as exc:
                    # Trata outros erros inesperados
                    logger.warn(f'Erro inesperado: {exc}', title=rec.title, duration=time.perf_counter()-t0)
                finally:
                    completed += 1
                    # Exibe progresso a cada 20 produtos processados (se verbose)
                    if self.verbose and completed % 20 == 0:
                        logger.info(f'{completed}/{total_urls} concluídos', title=None, duration=time.perf_counter()-t0)

        # =============================================================================
        # FASE 4: SALVAMENTO EM CSV
        # =============================================================================
        
        # Salva os resultados em arquivo CSV mantendo a ordem original
        logger.info(f'Saving results {self.out_csv} ...', title=None, duration=None)
        with open(self.out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()  # Escreve cabeçalho do CSV
            
            total = 0
            for rec in ordered_results:
                if rec:  # Ignora produtos que falharam (None)
                    writer.writerow(asdict(rec))  # Converte dataclass para dict
                    total += 1
        logger.info(f'Process completed, total of lines writed: {total}', title=None, duration=time.perf_counter()-t0)
        # =============================================================================
        # FASE 5: ESTATÍSTICAS FINAIS
        # =============================================================================
        
        # Calcula e exibe estatísticas de performance
        elapsed = time.perf_counter() - t0
        speed = (total / elapsed) if elapsed > 0 else 0.0
        logger.info(f'Process completed in {elapsed:.2f}s ({speed:.1f} livros/s). {total} livros salvos em: {self.out_csv}', title=None, duration=elapsed)
# =============================================================================
# FUNÇÕES PRINCIPAIS E INTERFACE DE LINHA DE COMANDO
# =============================================================================

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Configura e processa os argumentos da linha de comando.
    
    Define todos os parâmetros opcionais que podem ser passados para o script,
    incluindo valores padrão e descrições de ajuda.
    
    Args:
        argv (Optional[List[str]]): Lista de argumentos (None para usar sys.argv)
        
    Returns:
        argparse.Namespace: Objeto contendo os argumentos parseados
    """
    parser = argparse.ArgumentParser(description="Scraper do Books to Scrape (requests + BeautifulSoup).")
    
    # Argumento para especificar arquivo de saída
    parser.add_argument("--out", type=Path, default=OUTPUT_DEFAULT,
                        help=f"Caminho do CSV de saída (padrão: {OUTPUT_DEFAULT})")
    
    # Argumento para delay entre requisições (não usado no modo paralelo)
    parser.add_argument("--delay", type=float, default=0.1,
                        help="(Ignorado no modo global) Atraso entre páginas.")
    
    # Argumento para número de threads paralelas
    parser.add_argument("--workers", type=int, default=12,
                        help="Número de threads (padrão: 12).")
    
    # Argumento para modo verboso (exibe progresso)
    parser.add_argument("--verbose", action="store_true",
                        help="Exibe progresso para visualizar o paralelismo.")
    
    return parser.parse_args(argv)

def main() -> None:
    """
    Função principal do script.
    
    Esta é a função de entrada do programa que:
    1. Processa os argumentos da linha de comando
    2. Cria uma instância do BookScraper com as configurações
    3. Executa o processo de scraping
    
    Exemplo de uso:
        python books_scraper.py --workers 8 --verbose --out dados/livros.csv
    """
    # Processa argumentos da linha de comando
    args = parse_args()
    
    # Cria instância do scraper com as configurações especificadas
    scraper = BookScraper(
        out_csv=args.out,           # Arquivo de saída
        delay=args.delay,           # Delay entre requisições (não usado)
        max_workers=args.workers,   # Número de threads
        verbose=args.verbose        # Modo verboso
    )
    
    # Executa o processo de scraping
    scraper.run()

# =============================================================================
# PONTO DE ENTRADA DO SCRIPT
# =============================================================================

if __name__ == "__main__":
    """
    Ponto de entrada quando o script é executado diretamente.
    
    Este bloco garante que a função main() seja chamada apenas quando
    o script é executado diretamente, não quando importado como módulo.
    """
    main()