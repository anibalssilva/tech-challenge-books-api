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

#Esta função deve ficar acima da get id , ocorre um erro envolvendo FastAPI no caso contrário 
@app.get('/api/v1/books/search',response_model=list[Books])
def pesquisar_livros_titulo_categoria(title: str = None ,category:str = None):
    df_book = df.copy()
    if title:
        df_book = df_book[df_book['title'] == title]

    if category:
        df_book  = df_book[df_book['category'] == category]
    
    return df_book.to_dict(orient='records')

@app.get('/api/v1/books/{id}',response_model=Books)
def pesquisar_livros_id(id:int):
    coluna   = df.iloc[id]
    df_books = coluna.to_dict()
    return df_books
    

@app.get('/api/v1/categories',response_model=Books)
def retornar_categories():
    df_books = set(df['category'])
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
        
        
            
       
