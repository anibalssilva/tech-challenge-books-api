from fastapi  import FastAPI,HTTPException, Depends
from pydantic import BaseModel,HttpUrl
from pathlib  import Path
import pandas as     pd
from db.user import User
from typing import Annotated
from api.security import get_current_active_user, SessionDep, login_for_access_token, \
    RequestToken, refresh_access_token, RefreshToken, register_user, update_admin, update_disable, \
    get_current_active_user_admin, create_db_and_tables
from model.create_user import CreateUser
from model.token import Token
from model.update_user import UpdateUser


class Books(BaseModel):
    title:             str
    category:          str
    image_url:         HttpUrl
    description:       str
    rating:            int
    upc:               str
    product_type:      str
    price_excl_tax:    float
    price_incl_tax:    float
    tax:               float
    availability:      int
    


app = FastAPI()

# Criar banco de dados e tabelas ao iniciar
@app.on_event('startup')
def on_startup():
    create_db_and_tables()

#Salvado o caminho para ser utilizado na criação do Dataframe
pasta_dados  = Path(__file__).parent.parent
caminho_dados= pasta_dados/'data'/'processed'/'books.csv'
#Dataframe que será utilizado na api
df =pd.read_csv(caminho_dados)

#Retorna todos os livros com seus dados
@app.get('/api/v1/books',response_model=list[Books])
def retornar_livros(current_user: Annotated[User, Depends(get_current_active_user)]):
    df_books = df.to_dict(orient='records')
    return df_books

#Busca o livro pelo nome , pode buscar livros pela categoria também e pode buscar um livro por ambos
@app.get('/api/v1/books/search',response_model=list[Books])
def pesquisar_livros_titulo_categoria(current_user: Annotated[User, Depends(get_current_active_user)], title: str = None ,category:str = None):
    df_book = df.copy()
    if title:
        df_book = df_book[df_book['title'] == title]

    if category:
        df_book  = df_book[df_book['category'] == category]
    
    return df_book.to_dict(orient='records')
    
#Retorna uma lista com todas as categoria sem duplicatas 
@app.get('/api/v1/categories')
def retornar_categorias(current_user: Annotated[User, Depends(get_current_active_user)]):
    df_books = list(set(df['category']))
    return df_books
    
#Verifica se o Dataframe com os dados dos livros foi carregado com sucesso, retornando a quantidade de livros  
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


@app.get('/api/v1/stats/overview')
def estatistica_geral(current_user: Annotated[User, Depends(get_current_active_user)]):
    dict_estatistica_geral  = {'total_de_livros': len(df['title']),'preco_medio': round(df['price_incl_tax'].mean(),2)
                              , 'maior_preco': df['price_incl_tax'].max(),'menor_preco':df['price_incl_tax'].min(),}
    dict_estatistica_ratings= {'avaliacao_media':df['rating'].mean(),'distribuicao_de_avaliacoes':df['rating'].value_counts().to_dict() }
    
    return dict_estatistica_geral,dict_estatistica_ratings


#Gera estatísticas detalhadas por categoria 
@app.get('/api/v1/stats/categories') 
def estatica_detalhada(current_user: Annotated[User, Depends(get_current_active_user)]):
    dict_estatistica_categorias = {'total_de_categorias':df['category'].nunique() ,
                                   'quantidade_por_categoria':df['category'].value_counts().round(2).to_dict(),
                                   'preco_medio_categoria':df.groupby('category')['price_incl_tax'].mean().round(2).to_dict(),
                                   'avaliacao_por_categoria': df.groupby('category')['rating'].mean().round(2).to_dict()
                                   }
    return dict_estatistica_categorias    
        
#Retorna exatamento o nome e avaliação de todos livros por ordem da maior avaliação        
@app.get('/api/v1/books/top-rated')
def livros_mais_avaliado(current_user: Annotated[User, Depends(get_current_active_user)]):
    df_book = df[['title']].copy()
    df_book['rating'] = df['rating'].copy()
    df_book= df_book.sort_values(by='rating',ascending=False)
    return df_book.to_dict(orient='records')

#Retorna os livros através de um preço mínimo e máximo respectivamente
@app.get('/api/v1/books/price-range',response_model=list[Books])
def filtrar_preco(current_user: Annotated[User, Depends(get_current_active_user)], min:int,max:int):
    filtro = df['price_incl_tax'].between(min,max)
    df_book=df[filtro]
    return df_book.to_dict(orient='records')
        

#Esta é uma função dinamica e de ficar abaixo das que não são ,se não dá erro 
#Retorna o livro pelo seu id no Dataframe ,o id do Dataframe começa com 0
@app.get('/api/v1/books/{id}',response_model=Books)
def pesquisar_livros_id(current_user: Annotated[User, Depends(get_current_active_user)], id:int):
    coluna   = df.iloc[id]
    df_books = coluna.to_dict()
    return df_books

@app.post('/api/v1/users/register')
async def create_user(user: CreateUser, session: SessionDep):
    return register_user(user, session)

@app.post('/api/v1/users/admin')
async def user_admin(current_user: Annotated[User, Depends(get_current_active_user_admin)], user: UpdateUser, session: SessionDep):
    return update_admin(user, session)

@app.post('/api/v1/users/disable')
async def disable_user(current_user: Annotated[User, Depends(get_current_active_user_admin)], user: UpdateUser, session: SessionDep):
    return update_disable(user, session)

@app.post('/api/v1/auth/login')
async def login(request_token: RequestToken, session: SessionDep) -> Token:
    return login_for_access_token(request_token, session)

@app.post('/api/v1/auth/refresh')
async def refresh_token(token: RefreshToken, session: SessionDep) -> Token:
    return refresh_access_token(token, session)
