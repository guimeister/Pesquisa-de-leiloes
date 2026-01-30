# Pesquisa de Leilões - Watch Auction Scraper

Sistema de scraping para leilões de relógios que extrai dados estruturados e cria uma base de dados pesquisável.

## Funcionalidades

- **Scraping automatizado** de sites de leilão (modelo: leiloesbr.com.br)
- **Extração estruturada** de dados:
  - Descrição geral
  - Marca
  - Ano
  - Modelo
  - Especificação (movimento, tamanho, etc.)
  - Material (aço, ouro, ouro rosa, etc.)
  - Peso
  - Material da Pulseira
- **Banco de dados SQLite** com busca full-text
- **Interface CLI** amigável
- **Exportação** para CSV e JSON

## Instalação

```bash
# Clone o repositório
git clone https://github.com/guimeister/Pesquisa-de-leiloes.git
cd Pesquisa-de-leiloes

# Crie um ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt

# Instale o Playwright e os navegadores
playwright install chromium
```

## Uso

### Scraping

```bash
# Scrape com configurações padrão (5 páginas)
python main.py scrape

# Scrape mais páginas
python main.py scrape --max-pages 10

# Limitar número de itens
python main.py scrape --max-items 50

# Modo visual (não headless) para debug
python main.py scrape --no-headless
```

### Busca

```bash
# Busca por texto livre
python main.py search -q "rolex submariner"

# Filtrar por marca
python main.py search -b "omega"

# Filtrar por material
python main.py search -m "ouro"

# Filtrar por faixa de preço
python main.py search --min-price 5000 --max-price 50000

# Filtrar por ano
python main.py search --year-from 2010 --year-to 2020

# Combinar filtros
python main.py search -b "rolex" -m "aço" --min-price 10000
```

### Visualização

```bash
# Ver detalhes de um relógio
python main.py show 1

# Ver estatísticas do banco
python main.py stats

# Listar marcas
python main.py brands

# Listar materiais
python main.py materials
```

### Exportação

```bash
# Exportar para CSV
python main.py export --format csv -o meus_relogios

# Exportar para JSON
python main.py export --format json -o meus_relogios
```

## Estrutura do Projeto

```
Pesquisa-de-leiloes/
├── main.py              # CLI principal
├── requirements.txt     # Dependências Python
├── watches.db          # Banco de dados SQLite (criado após scraping)
└── src/
    ├── __init__.py
    ├── database.py     # Operações com banco de dados
    ├── models.py       # Modelos de dados
    ├── parser.py       # Parser de descrições
    └── scraper.py      # Web scraper
```

## Campos Extraídos

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `brand` | Marca do relógio | Rolex, Omega, Patek Philippe |
| `model` | Modelo/Referência | Submariner, 116500LN |
| `year` | Ano de fabricação | 2020 |
| `material` | Material da caixa | Aço, Ouro, Ouro rosa |
| `bracelet_material` | Material da pulseira | Aço, Couro, Borracha |
| `weight` | Peso total | 150g |
| `specification` | Especificações | Automático, 40mm, WR 100m |
| `current_price` | Preço atual/lance | 25000.00 |
| `description` | Descrição resumida | Título do lote |
| `raw_description` | Descrição completa | Texto original |

## Adicionando Novos Sites

Para adicionar suporte a outros sites de leilão, crie uma nova classe em `src/scraper.py` seguindo o padrão de `LeiloesBRScraper`:

```python
class NovoSiteScraper:
    BASE_URL = "https://novo-site.com.br"

    async def scrape_listing_page(self, page, url):
        # Implemente a extração da lista
        pass

    async def scrape_detail_page(self, page, url):
        # Implemente a extração de detalhes
        pass
```

## Licença

MIT License
