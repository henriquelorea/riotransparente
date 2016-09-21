# -*- coding: utf-8 -*-

# importing modules
import requests
import csv
from bs4 import BeautifulSoup
import unicodedata
from re import sub
from decimal import Decimal
import os
from urlparse import urlparse, urljoin
import pandas as pd

# functions
def mkDirsFromUrl(urlArg, dirArg):
    url = urlparse(urlArg)
    pathList = url.path.split('/')
    if os.path.isdir(dirArg) == True:
        dirStruct = dirArg
        for pathPart in pathList[:-1]: #### talvez transformar em funcao para recuperar em outros pontos do codigo
            dirStruct = os.path.join(dirStruct, pathPart)
            if os.path.isdir(dirStruct) == False:
                # print 'Diretorio', dirStruct, 'criado'
                os.makedirs(dirStruct)
    return dirStruct

def realToFloat(x):
    '''transforms R$ currency strings into floats'''
    real = x
    real = real[3:]
    real = sub('[\.]','', real)
    real = sub('[,]', '.', real)
    return float(real)

def agoravai(baseUrlArg, dirArg):
    # variables
    linkList = []
    linkList.append(baseUrlArg)

    header = {}
    header[1] = ['ano', 'tipo_orgao', 'periodo', 'ID_SE', 'ID_SE_descricao', 'n1_valor_previsto', 'n1_valor_arrecadado']
    header[2] = ['ID_SE_pai', 'id_fr', 'id_fr_descricao', 'n2_valor_previsto', 'n2_valor_arrecadado']
    header[3] = ['id_fr_pai', 'id_sr', 'id_sr_descricao', 'n3_valor_previsto', 'n3_valor_arrecadado']
    header[4] = ['id_sr_pai', 'id_RUB', 'id_RUB_descricao', 'n4_valor_previsto', 'n4_valor_arrecadado']
    header[5] = ['id_RUB_pai', 'ID_srub', 'ID_srub_descricao', 'n5_valor_previsto', 'n5_valor_arrecadado']
    header[6] = ['ID_srub_pai', 'n6_codigo', 'n6_descricao', 'n6_valor_previsto', 'n6_valor_arrecadado']

    output = {}
    for i in range(7):
        output[i] = []

    for urlArg in linkList:
        # Remote or local response
        wd = mkDirsFromUrl(urlArg, dirArg)
        wf = os.path.join(wd, urlArg.split('/')[-1])
        if os.path.isfile(wf) == False:
            response = requests.get(urlArg)
            with open(wf, 'w') as fw:
                fw.write(response.content)
        with open(wf, 'r') as fr:
            soup = BeautifulSoup(fr, 'html.parser', from_encoding="iso-8859-1")
        # Extracting attributes from URL
        urlAttr = urlArg[urlArg.find('?')+1:].split('&')
        urlAttr = [i.split('=') for i in urlAttr]
        urlAttr = {i[0] : i[1] for i in urlAttr}
        prenivel = urlArg[urlArg.find('resposta')+len('resposta'):urlArg.find('resposta')+len('resposta')+1]
        if prenivel in [str(i) for i in range(2,7)]:
            urlAttr['nivel'] = int(prenivel)
        else:
            urlAttr['nivel'] = 1
        # Extracting attributes from response
        responseAttrList = []
        for row in soup.find_all('tr', class_='tabela'):
            responseAttr = {}
            rowList = []
            for i in row.stripped_strings:
                rowList.append(i)
            responseAttr['cod'] = rowList[0][:rowList[0].find('-')]
            responseAttr['desc'] = rowList[0][rowList[0].find('-')+2:]
            responseAttr['valorPrev'] = realToFloat(rowList[1])
            responseAttr['valorArrec'] = realToFloat(rowList[2])
            # Parsing a href and returning a url link
            prelink = row.find('a')
            if prelink is not None:
                bruto = row.find('a')['onclick']
                bruto = bruto[bruto.find('(')+1:bruto.find(')')]
                bruto = sub("[\']",'', bruto)
                bruto = sub("[ ]",'', bruto)
                bruto = sub('^[&]','?', bruto)
                bruto = bruto.split(',')
                responseAttr['link'] = '/'.join(urlArg.split('/')[:-3]+[bruto[8] + bruto[0]])
                linkList.append(responseAttr['link'])
            responseAttrList.append(responseAttr)

        # Preparing output
        for resp in responseAttrList:
            if urlAttr['nivel'] == 1:
                output[urlAttr['nivel']].append([urlAttr['EXERCICIO'], urlAttr['tipoOrgao'], urlAttr['periodo'], resp['cod'], resp['desc'], resp['valorPrev'], resp['valorArrec']])
            elif urlAttr['nivel'] == 2:
                output[urlAttr['nivel']].append([urlAttr['ID_SE'], resp['cod'], resp['desc'], resp['valorPrev'], resp['valorArrec']])
            elif urlAttr['nivel'] == 3:
                output[urlAttr['nivel']].append([urlAttr['id_fr'], resp['cod'], resp['desc'], resp['valorPrev'], resp['valorArrec']])
            elif urlAttr['nivel'] == 4:
                output[urlAttr['nivel']].append([urlAttr['id_sr'], resp['cod'], resp['desc'], resp['valorPrev'], resp['valorArrec']])
            elif urlAttr['nivel'] == 5:
                output[urlAttr['nivel']].append([urlAttr['id_RUB'], resp['cod'], resp['desc'], resp['valorPrev'], resp['valorArrec']])
            elif urlAttr['nivel'] == 6:
                output[urlAttr['nivel']].append([urlAttr['ID_srub'], resp['cod'], resp['desc'], resp['valorPrev'], resp['valorArrec']])

        df1 = pd.DataFrame(output[1], columns=header[1])
        df2 = pd.DataFrame(output[2], columns=header[2])
        df3 = pd.DataFrame(output[3], columns=header[3])
        df4 = pd.DataFrame(output[4], columns=header[4])
        df5 = pd.DataFrame(output[5], columns=header[5])
        df6 = pd.DataFrame(output[6], columns=header[6])

        df = pd.merge(left=df1,right=df2, left_on='ID_SE', right_on='ID_SE_pai')
        df = pd.merge(left=df,right=df3, left_on='id_fr', right_on='id_fr_pai')
        df = pd.merge(left=df,right=df4, left_on='id_sr', right_on='id_sr_pai')
        df = pd.merge(left=df,right=df5, left_on='id_RUB', right_on='id_RUB_pai')
        df = pd.merge(left=df,right=df6, left_on='ID_srub', right_on='ID_srub_pai')

        #df.to_csv('2016.csv', index=False)
    df_clean = df[['ano', 'ID_SE_descricao', 'id_fr_descricao', 'id_sr_descricao', 'id_RUB_descricao', 'ID_srub_descricao', 'n6_descricao', 'n6_valor_previsto', 'n6_valor_arrecadado']]
    clean_columns = ['ano', 'nivel1', 'nivel2', 'nivel3', 'nivel4', 'nivel5', 'nivel6', 'valor_previsto', 'valor_arrecadado']
    df_clean.columns = clean_columns

    return df_clean


    # for key in output.iterkeys():
    #     with open(os.path.join(dirArg, 'receita_' + output[1][1][2] + '_' + output[1][1][0] + '_nivel_' + str(key) + '.csv'), 'w') as f:
    #         csvf = csv.writer(f, delimiter='\t')
    #         csvf.writerow(header[key])
    #         for row in output[key]:
    #             csvf.writerow(row)
    #
    # outputAll = []



    # print sum([i[-2] for i in output[1]])
    # print sum([i[-2] for i in output[2]])
    # print sum([i[-2] for i in output[3]])
    # print sum([i[-2] for i in output[4]])
    # print sum([i[-2] for i in output[5]])
    # print sum([i[-2] for i in output[6]])
    return True

baseUrl = 'http://riotransparente.rio.rj.gov.br/receitas/orgao/receitasPorOrgaoApresentacaoDados.asp?EXERCICIO={0}&tipoOrgao=Todos&periodo=Anual'
baseDir = '/home/henrique/Documents/dapp/riotransparente'

dfList = []
for ano in range(1995, 2017):
    print ano
    dfList.append(agoravai(baseUrl.format(ano), baseDir))
df_all = pd.concat(dfList)
df_all.to_csv('receitas_por_orgao_1995_2016.csv', index=False)
