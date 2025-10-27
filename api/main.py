from fastapi  import FastAPI,HTTPException,Request, Depends
from pydantic import BaseModel,HttpUrl
from pathlib  import Path
import pandas as     pd
import time
import sys
import uuid
from typing import Annotated

# Imports para logging estruturado
sys.path.append(str(Path(__file__).parent.parent))
import structlog
from logs.setup_logging import setup_logging

# Imports para autenticação JWT
from db.user import User
from api.security import (
    get_current_active_user,
    get_current_active_user_admin,
    SessionDep,
    login_for_access_token,
    refresh_access_token,
    register_user,
    update_admin,
    update_disable,
    create_db_and_tables
)
from model.create_user import CreateUser
from model.token import Token
from model.refresh_token import RefreshToken
from model.request_token import RequestToken
from model.update_user import UpdateUser

# Configuração do logging estruturado
raiz = Path(__file__).parent.parent
LOG_PATH = raiz/'logs'/'api.log'
setup_logging(LOG_PATH)
logger = structlog.get_logger("api")


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


@app.on_event('startup')
def on_startup():
    create_db_and_tables()


#Salvado o caminho para ser utilizado na criação do Dataframe
pasta_dados  = Path(__file__).parent.parent
caminho_dados= pasta_dados/'data'/'processed'/'books.csv'
#Dataframe que será utilizado na api
df =pd.read_csv(caminho_dados)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para logar informações sobre cada requisição.
    """
    request_id = str(uuid.uuid4())
    # Cria um logger específico para esta requisição, com o ID e informações do request
    request_logger = logger.bind(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_host=request.client.host
    )

    request_logger.info("request_started")
    start_time = time.time()

    try:
        # Prossegue com a execução da rota
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Loga a resposta bem-sucedida
        request_logger.info(
            "request_finished",
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2) # Converte para milissegundos
        )
        response.headers["X-Request-ID"] = request_id
        return response

    except Exception as e:
        # Se ocorrer um erro não tratado, loga como erro crítico
        process_time = time.time() - start_time
        request_logger.error(
            "request_failed_unhandled_exception",
            status_code=500,
            process_time_ms=round(process_time * 1000, 2),
            exception=str(e),
            exc_info=True # Adiciona o traceback completo ao log
        )
        # É importante relançar a exceção para que o FastAPI possa lidar com ela
        # e retornar uma resposta de erro 500.
        raise


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


# Endpoints de autenticação JWT

@app.post('/api/v1/auth/register')
def register(user: CreateUser, session: SessionDep):
    """Registra um novo usuário"""
    return register_user(user, session)


@app.post('/api/v1/auth/login', response_model=Token)
def login(user_request: RequestToken, session: SessionDep):
    """Faz login e retorna um token JWT"""
    return login_for_access_token(user_request, session)


@app.post('/api/v1/auth/refresh', response_model=Token)
def refresh_token(token: RefreshToken, session: SessionDep):
    """Atualiza o token JWT"""
    return refresh_access_token(token, session)


@app.get('/api/v1/auth/me')
def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Retorna informações do usuário atual autenticado"""
    return current_user


@app.put('/api/v1/auth/update/admin')
def update_user_admin(
    user: UpdateUser,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user_admin)]
):
    """Torna um usuário administrador (requer permissão de admin)"""
    return update_admin(user, session)


@app.put('/api/v1/auth/update/disable')
def update_user_disable(
    user: UpdateUser,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user_admin)]
):
    """Desabilita um usuário (requer permissão de admin)"""
    return update_disable(user, session)


#Esta é uma função dinamica e de ficar abaixo das que não são ,se não dá erro
#Retorna o livro pelo seu id no Dataframe ,o id do Dataframe começa com 0
@app.get('/api/v1/books/{id}',response_model=Books)
def pesquisar_livros_id(current_user: Annotated[User, Depends(get_current_active_user)], id:int):
    coluna   = df.iloc[id]
    df_books = coluna.to_dict()
    return df_books


