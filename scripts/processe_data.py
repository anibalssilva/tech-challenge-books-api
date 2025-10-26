from pathlib  import Path
import pandas as     pd 


# Caminho do arquivo para a criação do dataframe
pasta_dados  = Path(__file__).parent.parent
caminho_dados= pasta_dados/'data'/'raw'/'books.csv'

#criação do dataframe
df =pd.read_csv(caminho_dados)
df_limpo = df.copy()
#verificação de valores repetidos pelo título e remoção dos mesmos
mascara = df_limpo.duplicated(subset=['title'],keep=False)
df_valor_replicado = df_limpo[mascara]
print(df_valor_replicado)
#Novo df
df = df.drop_duplicates(subset=['title'],keep='first')

#Verificação de valores nulls
mascara_nula = df_limpo.isnull().any(axis =1)
df_valor_nulo = df_limpo[mascara_nula]
print(df_valor_nulo['description'])
#Substituição dos null por um valor vazio
df_limpo = df_limpo.fillna(' ')
df_verificacao_null = df_limpo[mascara_nula]
#visualização só por garantia ,deve retornar apenas os índices e dados vazios 
print(df_verificacao_null['description'])

#salvando os dados limpos em data/processed
pasta_dados_limpos = Path(__file__).parent.parent
caminho_df_limpo   = pasta_dados_limpos/'data'/'processed'
df_limpo.to_csv(caminho_df_limpo/'books.csv')
