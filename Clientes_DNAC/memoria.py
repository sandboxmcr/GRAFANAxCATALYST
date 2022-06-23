
# CODIGO DE RECUPERACIÓN DE USO DE MEMORIA PARA CLIENTES CON DNAC
"""
Este código se basa en llamadas de APIs para obtener el uso
de memoria de todos los equipos que se encuentran integrados 
con el DNAC.
    
    Se usaron las siguientes APIS:
    1. API para obtener TOKEN            ( https://{}/dna/system/api/v1/auth/token )
    2. API para obtener lista de equipos ( https://{}/api/v1/network-device )
    3. API para enviar comandos por terminal ( https://{}/api/v1/network-device-poller/cli/read-request )
    4. API para obtener información del comando emitido ( https://{}/api/v1/task/{} )
    5. API para obtener la salida del comando ( https://{}/api/v1/file/{} )

    Se usaron las siguientes funciones: 
    1.get_auth_token          5.get_task_info              9.getTime
    2.get_device_list         6.get_auth_token_first       10.almacenar_db
    3.cmd_runner_only         7.time_now                   11. get_cmd_output
    4.initiate_cmd_runner     8.delta_min
"""
######### Sección de importaciones######################
import time 
import json
from requests.auth import HTTPBasicAuth
from datetime import timedelta
import requests
import datetime
import sqlite3
import re
#########################################################

###### Credenciales de DNAC #############################
DNAC_URL = "10.96.246.70"
DNAC_USER = "admin"
DNAC_PASS = "Cisco12345"
#########################################################


lista = ["2a7567f6-e8d4-40d3-82b1-9a91479a4a4d",
        "9e6dcf5e-30cf-41c6-85f4-bd6457963a6c",
        "b8a9756f-1aa9-4cb9-be44-1aee13e1df89",
        "3ccf34ab-37f2-4d92-b4ba-91361c5868db",
        "c919d2ed-31a0-4570-a315-21f0ae9ec83e",
        "04ae491a-8032-4bd6-918b-ccf79e7db417",
        "75763d63-010f-4500-a32f-427ca4d81a68",
        "f8831289-b170-4815-9a94-5ef3b4b52bb8",
        "2cf0eee2-0cc2-4ed7-8b0e-dc1a5fc6f08d",
        "26c68e55-3427-4e4f-a299-c2a6ded81214",
        "69ddf9d6-349d-4188-a883-9f8dc19155d4",
        "53b2062f-a20a-4930-a888-2a43a2e1596d",
        "2abf194b-1371-4e41-9bc1-4a5c9d38e39c",
        "4a53852e-3730-4023-a80b-a580670afc42",
        "1989d66f-df32-4c9c-936b-609a9abdde7c"
         ]

#############Funcion time_now() se usa pra obtener la hora actual############
def time_now ():
    timenow = datetime.datetime.now()
    return timenow
##############################################################################
############## Funcion delta_min() se usa para variar en cierta cantidad de minutos un formato actual########
def delta_min(time):
    variacion = timedelta(minutes=60)
    time = time + variacion 
    return time  ## retorna la hora modificada 60 min 
#############################################################################################################
####### Funcion get_auth_token() se usa para obtener el token del DNAC ######################################
def get_auth_token():   
    hora_actual = time_now()
    flag = False
    hora_30 = delta_min(hora_actual) 
    url = 'https://{}/dna/system/api/v1/auth/token'.format(DNAC_URL)                 
    hdr = {'content-type' : 'application/json'}                                       
    while flag == False: ## mientras es false entrara a realizar el request 
        resp = requests.post(url, auth=HTTPBasicAuth(DNAC_USER, DNAC_PASS), headers=hdr, verify= False)
        hora_actual = time_now()  
        flag = True
        if hora_actual > hora_30:  ## si ya pasaron 30 min entonces se realiza el cambio de TOKEN 
            resp = requests.post(url, auth=HTTPBasicAuth(DNAC_USER, DNAC_PASS), headers=hdr, verify= False)
            hora_30 = delta_min(hora_actual)
            flag = False
        token = resp.json()['Token']                                                     
    return token  ## se retorna siempre el token actual o actualizado
##############################################################################################################
############# Funciones get_device_list() se usa para obtener la lista del dispositivos del DNAC #############
def get_device_list():
    token = get_auth_token()  ## Primero se obtiene el token del DNAC
    dic = {}
    url = "https://{}/api/v1/network-device".format(DNAC_URL) 
    hdr = {'x-auth-token': token, 'content-type' : 'application/json'}
    resp = requests.get(url, headers=hdr, verify= False)  # Make the Get Request
    device_list = resp.json()
    for device in device_list['response']: ## se busca obtener en un diccionario 
        dic[device['id']] = device['hostname']    
    initiate_cmd_runner(token,dic) ## se llama la funcion de iniciación de comandos 
######################################################################################################################
############## Funciones cmd_runner_only() se usa para inicial el comand runner cuando aparece un task id erroneo#####
def cmd_runner_only(token,id,cuenta):
    global task
    if cuenta <= 3:   #### se realizan un maximo intento de 3 veces, si continua con el error se salta al siguiente equipo ###### 
        task = ""
        ios_cmd = "show processes cpu | include one minute"
        param = {
            "name": "Show Command",
            "commands": [ios_cmd],
            "deviceUuids": [id]
                }
        url = "https://{}/api/v1/network-device-poller/cli/read-request".format(DNAC_URL)
        header = {'content-type': 'application/json', 'x-auth-token': token}
        time.sleep(10)
        response = requests.post(url, data=json.dumps(param), headers=header, verify= False)
        if "errorCode" in response.json()["response"].keys() :  #### se verifica que hay un error en el task_id
            cuenta = cuenta + 1   
            cmd_runner_only(token,id,cuenta)
        else:
            task = response.json()['response']['taskId'] ##### se obtiene el task_id del equipo
            print("error solucionado") 
    return task  ##########3 siempre se retonar el task vacio o con algun valor
#####################################################################################################################
######################### Función initiate_cmd_runnner() realiza el barrido de todos los equipos ejecutando todos los comandos ########
def initiate_cmd_runner(token,dic):
    global task_id 
    task_id = ""
    task_list = []
    global cuenta 
    cuenta = 0
    ios_cmd = "show processes cpu | include one minute"  
    for i in lista:  ########## cada elemento de la lista es el id de los equipos 
        print("Se esta ejecutando el cmd_runner para el id {} ".format(dic[i]))
        device_id = i
        param = {
        "name": "Show Command",
        "commands": [ios_cmd],
        "deviceUuids": [device_id]
                }  
        url = "https://{}/api/v1/network-device-poller/cli/read-request".format(DNAC_URL)
        header = {'content-type': 'application/json', 'x-auth-token': token}
        response = requests.post(url, data=json.dumps(param), headers=header, verify= False)
        print(response.json()["response"].keys())
        if "errorCode" in response.json()["response"].keys() : ##### verifica si hay un error en la salida
            print("error salioooo")
            task_id = cmd_runner_only(token,i,cuenta)  ############ si hay error entonces se va a la función cmd_runner_only
            if task_id == "" :
                continue
            continue
        task_id = response.json()['response']['taskId']
        task_list.append(task_id)  ## se crea una lista y se guardan todos los task_ids de los equipos
    lista_file_id = get_task_info(task_list,token)  ##### se obtiene una lista usando la lista task_list y se obtiene una lista de los file_id
    get_cmd_output(token, lista_file_id) ### se llama a la funcion get_cmd_ouptpu para obtener las salidas de los file_id
###############################################################################################################
######################## Funcion get_task_info() se usa esta función para obtener una lista con todos los file_id  de los task_id ################
def get_task_info(task_id, token):
    file_id_list = []
    for each in task_id:  
        url = "https://{}/api/v1/task/{}".format(DNAC_URL, each)
        hdr = {'x-auth-token': token, 'content-type' : 'application/json'}
        task_result = requests.get(url, headers=hdr, verify= False)
        file_id = task_result.json()['response']['progress']
        print(task_result.json())
        if "fileId" in file_id: ##### se realiza una verificaion para saber si existe un fileID
            unwanted_chars = '{"}'
            for char in unwanted_chars:  ### se realiza un bucle para obtener en la cadena de salida la sección de file_id
                file_id = file_id.replace(char, '')
            file_id = file_id.split(':')
            file_id = file_id[1]
            file_id_list.append(file_id)  ### se agrega cada file_id a la lista
        else: 
            get_task_info(task_id, token) ######## funcion recursiva, siempre se obtiene una salida del file_id, se espera hasta que se obtenga.
        print(file_id_list)
    return file_id_list ## se retorna la lista de los file_id
#######################################################################################################################################  
########### Funcion get_cmd_output() se usa para obtener la salida de la ejecucion de los comandos ##################################################################################################
def get_cmd_output(token,file_id_lista): 
    for element in file_id_lista:   ##### se usa cada file_id para buscar la salida de cada equipo 
        url = "https://{}/api/v1/file/{}".format(DNAC_URL, element)
        hdr = {'x-auth-token': token, 'content-type': 'application/json'}
        cmd_result = requests.get(url, headers=hdr, verify= False)
        print(cmd_result.json()) 
        if type(cmd_result.json()) != list:  ### si el valor es diferente a una lista etnonces hubo un error y solo sigue con el siguiente file_id
            print("hubo un error")
            continue
        result= json.dumps(cmd_result.json(), indent=4, sort_keys=True)
        device_uuid = json.loads(result)[0]['deviceUuid'] ## se parsea el device_uuid para llenar las tablas 
        if json.loads(result)[0]['commandResponses']["SUCCESS"]: ## y se obtiene la salida del comando para guardar
            sentence = json.loads(result)[0]['commandResponses']["SUCCESS"]['show processes cpu | include one minute']
            s = [ float(str(s).replace('%','')) for s in re.findall('[0-9]+[%]', sentence)] ##  se contruye una lista S con los datos
            fecha= getTime()  #### se llama a la función getTime para obtener la hora actual
            s.append(fecha) ## se agrega a la lista S la hora actual
            almacenar_db(device_uuid,s)   ## y se envia a la función almacenar_db() para realizar el guardado en la base de datos
###################################################################################################################################3
############funcion para obtener el tiempo actual en formato establecido########################################
def getTime(): 
    timenow = datetime.datetime.now().isoformat(timespec='seconds')
    return timenow
#################################################################################################################
############# Funcion almacenar_db() funcion para almacenar la lista S con los valores obtenidas  ################################################ 
def almacenar_db(device_uuid,s):
    lista = [tuple(s)]  ### se convierte en una tupla la lista S porque es el formato que usa Mysql
    conexion = sqlite3.connect("/home/ubuntulab/Desktop/chris/cpu_database_4.db") ### se conecta a la DB, colocar la ruta donde se creara 
    cursor = conexion.cursor() ### se crea el cursor para iniciar la escritura
    conexion.commit()  #### se carga la data
    try:  ##### en caso salga un error de que ya se creo la DB salta la excepción  
        cursor.execute("CREATE TABLE '{}' (FiveSeconds REAL, Interrup FLOAT, OneMinute FLOAT, FiveMinutes REAL, SDate TIMESTAMP)".format(device_uuid))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?)".format(device_uuid),lista)
        conexion.commit()
    except:
        print("La tabla {} ya existe".format(device_uuid),type(s[0])) ### se imprime que ya se creo previamente
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?)".format(device_uuid),lista)
        conexion.commit() #### y se guarda mas elementos
#######################################################################################################################
############### Funcion get_auth_token_first()  se usa para obtener el token por primera vez ########################################################################
def get_auth_token_first():
    global token
    url = 'https://{}/dna/system/api/v1/auth/token'.format(DNAC_URL)                 
    hdr = {'content-type' : 'application/json'} 
    resp = requests.post(url, auth=HTTPBasicAuth(DNAC_USER, DNAC_PASS), headers=hdr, verify= False)
    token = resp.json()['Token']                                                  
    return token 
#########################################################################################################
########################### MAIN ########################################################################
if __name__ == "__main__":
    global hora_actual
    global hora_60
    global token   
    token = get_auth_token_first()
    hora_actual = time_now()
    hora_60 = delta_min(hora_actual)     
    while True :
        get_device_list()
        time.sleep(30) ### se suspende por 30 segundos entre cada ciclo de busqueda por la cantidad de requests permitido en el DNAC
#################################################################################################################
