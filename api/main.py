from fastapi  import FastAPI,HTTPException
from pydantic import BaseModel
from pathlib  import Path
import pandas as     pd 


class Books(BaseModel):
    title:             str
    category:          str
    product_type:      str
    price_excl_tax:    float
    price_incl_tax:    float
    tax:               float
    availability:      int
    number_of_reviews: int


app = FastAPI()
#Salvado o caminho para ser utilizado na criação do Dataframe
pasta_dados  = Path(__file__).parent.parent
caminho_dados= pasta_dados/'data'/'raw'/'books.csv'
df =pd.read_csv(caminho_dados)

#Alguns titulos estão vindo com o Add a comment como categoria 
mascara = df['category'] == 'Add a comment'
linha_problematica = df[mascara]
print(linha_problematica)


@app.get('/api/v1/books',response_model=list[Books])
def retornar_livros():
    df_books = df.to_dict(orient='records')
    return df_books


@app.get('/api/v1/books/search',response_model=list[Books])
def pesquisar_livros_titulo_categoria(title: str = None ,category:str = None):
    df_book = df.copy()
    if title:
        df_book = df_book[df_book['title'] == title]

    if category:
        df_book  = df_book[df_book['category'] == category]
    
    return df_book.to_dict(orient='records')
    
    
@app.get('/api/v1/categories')
def retornar_categorias():
    df_books = list(set(df['category']))
    return df_books
    
    
@app.get('/api/v1/health')
def retorna_saude():
    if df is not None and not df.empty:
        return{
            'status':'ok',
            'messagem':f'O Dataframe foi carregado com sucesso e possui {len(df)} livros' }
    else:
        raise HTTPException(
            status_code=503,
            detail='Serviço indisponível: O Dataframe com os livros não foram carregados corretamente.'
        )
        
#Endpoints opcionais 
        
@app.get('/api/v1/stats/categories') 
def estatica_detalhada():
    return df.describe().to_dict()
        
        
@app.get('/api/v1/books/top-rated')
def livros_mais_avaliado():
    df_book = df[['title']].copy()
    df_book['reviews'] = 0
    return df_book.to_dict(orient='records')

@app.get('/api/v1/books/price-range',response_model=list[Books])
def filtrar_preco(min:int,max:int):
    filtro = df['price_incl_tax'].between(min,max)
    df_book=df[filtro]
    return df_book.to_dict(orient='records')
        

#Esta é uma função dinamica e de ficar abaixo das que não são ,se não dá erro 
@app.get('/api/v1/books/{id}',response_model=Books)
def pesquisar_livros_id(id:int):
    coluna   = df.iloc[id]
    df_books = coluna.to_dict()
    return df_books