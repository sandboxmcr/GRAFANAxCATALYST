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
    3.time_now                7. get_cmd_output            11.get_command
    4.delta_min               8. port_list                 12.get_command_only
    
"""
######### Sección de importaciones######################
import requests
import json
from requests.auth import HTTPBasicAuth
from datetime import timedelta
import datetime
import time 
import sqlite3
########################################################
###### Credenciales de DNAC #############################
DNAC_URL = "10.96.246.70"
DNAC_USER = "admin"
DNAC_PASS = "Cisco12345"
#########################################################
#############Funcion time_now() se usa pra obtener la hora actual############
def time_now ():
    timenow = datetime.datetime.now()
    return timenow
##############################################################################
############## Funcion delta_min() se usa para variar en cierta cantidad de minutos un formato actual########
def delta_min(time):
    variacion = timedelta(minutes=60)
    time = time + variacion
    return time ## retorna la hora modificada 60 min 
#############################################################################################################
############funcion para obtener el tiempo actual en formato establecido########################################
def getTime():
    timenow = datetime.datetime.now().isoformat(timespec='seconds')
    return timenow
#################################################################################################################
####### Funcion get_auth_token() se usa para obtener el token del DNAC ######################################
def get_auth_token():   
    hora_actual = time_now()
    flag = False
    hora_30 = delta_min(hora_actual)
    url = 'https://{}/dna/system/api/v1/auth/token'.format(DNAC_URL)                 
    hdr = {'content-type' : 'application/json'}                                       
    while flag == False:## mientras es false entrara a realizar el request
        resp = requests.post(url, auth=HTTPBasicAuth(DNAC_USER, DNAC_PASS), headers=hdr, verify= False)
        hora_actual = time_now()  
        flag = True
        if hora_actual > hora_30: ## si ya pasaron 30 min entonces se realiza el cambio de TOKEN 
            resp = requests.post(url, auth=HTTPBasicAuth(DNAC_USER, DNAC_PASS), headers=hdr, verify= False)
            hora_30 = delta_min(hora_actual)
            flag = False
        token = resp.json()['Token']                                                     
    return token   ## se retorna siempre el token actual o actualizado
#############################################################################################################
############### Funcion get_auth_token_first()  se usa para obtener el token por primera vez ########################################################################
def get_auth_token_first():
    global token
    url = 'https://{}/dna/system/api/v1/auth/token'.format(DNAC_URL)                 
    hdr = {'content-type' : 'application/json'} 
    resp = requests.post(url, auth=HTTPBasicAuth(DNAC_USER, DNAC_PASS), headers=hdr, verify= False)
    token = resp.json()['Token']                                                  
    return token 
#########################################################################################################
############# Funciones get_device_list() se usa para obtener la lista del dispositivos del DNAC #############
def get_device_list():
    token = get_auth_token_first()## Primero se obtiene el token del DNAC
    url = "https://{}/api/v1/network-device".format(DNAC_URL)
    hdr = {'x-auth-token': token, 'content-type' : 'application/json'}
    resp = requests.get(url, headers=hdr, verify= False)  # Make the Get Request
    device_list = resp.json()
    dict ={}
    for device in device_list['response']: ## se busca obtener en un diccionario 
        dict[device["id"]] = device["hostname"]
    port_list()  ## se llama a la fucion de port_list para obener la lista de dispositivos 
###################################################################################################################
############### Funcion port_list obtiene los puertos de todos los equipos ###################################
def port_list():
    token = get_auth_token()
    list_ports = []
    url = "https://{}/dna/intent/api/v1/interface".format(DNAC_URL)
    header = {'content-type': 'application/json', 'x-auth-token': token}
    response = requests.get(url, headers=header, verify= False) ##### hace el request 
    json_response = response.json() 
    result= json.dumps(json_response, indent=4, sort_keys=True)
    longitud = len(json.loads(result)["response"])  ##### se obtiene la longitud de la respuesta en string
    for i in range (0,longitud):  ### y se realiza la busqueda de los parametros que se necesitan
        port = (json.loads(result)["response"][i]["portName"])
        uuid = (json.loads(result)["response"][i]["deviceId"])
        dupla = (uuid,port)  ### se llena lista_ports con tuplas formadas por el uuid y el puerto
        list_ports.append(dupla) ###
    print(list_ports)
    get_command(token,list_ports)  ##### se llama a la funcion get_command
##################################################################################################################
############################get_command() se ejecuta el comando show interface "(la interfaz que se busca)" 
def get_command(token,puertos):
    global task_id
    task_id = ""
    global cuenta 
    cuenta = 0
    task_list = [] 
    for i in puertos:   ### se realiza el comando con cada puerto 
        ios_cmd = "show interface {} ".format(i[1])
        device_id = i[0]
        param = {
            "name": "Show Command",
            "commands": [ios_cmd],
            "deviceUuids": [device_id]
            }
        url = "https://{}/api/v1/network-device-poller/cli/read-request".format(DNAC_URL)
        header = {'content-type': 'application/json', 'x-auth-token': token} 
        response = requests.post(url, data=json.dumps(param), headers=header, verify= False)
        if "errorCode" in response.json()["response"].keys():  #### verifica si existe un error en la salida del request
            print("error salio")
            task_id = get_command_only(token,i[0],cuenta) ### se va a la funcion de get_comand_only para trabajar esa unica interfaz
            print("obtuve task id con el error") 
            if task_id == "": ### Si no se obtiene el task_id sigue con la siguiente interfaz
                print("no pude obtener el taskid :( ")
                continue
            continue
        task_id = response.json()['response']['taskId']
        tupla_1 = (task_id,i)  ## se crean tuplas de los task_id y del elmento
        task_list.append(tupla_1)
    get_task_info(task_list,token)  ### se busca la funcion get_task_info
########################################################################################################
#####################get_command_only se usa para una sola interfaz se usa cuando aparece un error en una interfaz en la funcion get_command ######  
def get_command_only(token,id,cuenta):
    global task
    if cuenta <= 3:   
        task = ""
        ios_cmd =  "show interface {} ".format(id)
        param = {
            "name": "Show Command",
            "commands": [ios_cmd],
            "deviceUuids": [id]
                }
        url = "https://{}/api/v1/network-device-poller/cli/read-request".format(DNAC_URL)
        header = {'content-type': 'application/json', 'x-auth-token': token}
        response = requests.post(url, data=json.dumps(param), headers=header, verify= False)
        if "errorCode" in response.json()["response"].keys() :
            cuenta = cuenta + 1  #### se busca hacer la tarea en 3 intentos 
            get_command_only(token,id,cuenta)   
        else:  ### si no se encuentra salida no se entrega nada 
            task = response.json()['response']['taskId']
            print("termine aquí con el {}".format(id)) 
    return task #### siempre se retorna el task_id
#################################################################################################################
######################## Funcion get_task_info() se usa esta función para obtener una lista con todos los file_id  de los task_id ################
def get_task_info(task_id, token):
    file_id_list = []
    for element in task_id:
        url = "https://{}/api/v1/task/{}".format(DNAC_URL, element[0])
        hdr = {'x-auth-token': token, 'content-type' : 'application/json'}
        task_result = requests.get(url, headers=hdr, verify= False)
        file_id = task_result.json()['response']['progress']
        print(task_result.json())
        if "fileId" in file_id:##### se realiza una verificaion para saber si existe un fileID
            unwanted_chars = '{"}'
            for char in unwanted_chars: ### se realiza un bucle para obtener en la cadena de salida la sección de file_id
                file_id = file_id.replace(char, '')
            file_id = file_id.split(':')
            file_id = file_id[1]
            tupla = (file_id,element[1]) ### se agrega cada file_id a la lista
        else:  
            print("entre porque aun no esta listo")
            time.sleep(10)
            file_id = get_task_info_only(element, token) ######## funcion recursiva, siempre se obtiene una salida del file_id, se espera hasta que se obtenga.
            tupla = (file_id,element[1])
        file_id_list.append(tupla)
    print(file_id_list)    
    get_cmd_output(token,file_id_list)
#######################################################################################################################################  
############## get_task_info_only se realiza la funcion cuando se obtiene un error en la fucnion get_task_info
def get_task_info_only(task_id, token):
    url = "https://{}/api/v1/task/{}".format(DNAC_URL, task_id)
    hdr = {'x-auth-token': token, 'content-type' : 'application/json'}
    task_result = requests.get(url, headers=hdr, verify= False)
    file_id = task_result.json()['response']['progress']
    print(task_result.json())
    if "fileId" in file_id:
        unwanted_chars = '{"}'
        for char in unwanted_chars:
            file_id = file_id.replace(char, '')
        file_id = file_id.split(':')
        file_id = file_id[1]
        print("obtuve el file_id por la funcion sola")  ###### avisa que se obtuvo el file_id por la  funcion de error
    else:  
        get_task_info_only(task_id, token)    
    return file_id
#############################################################################################################3
########################### get_cmd_output####################################################################
def get_cmd_output(token,file_id):
    lista = []
    for each in file_id:  ### se realiza la busqueda en cada elemento del file_id
        url = "https://{}/api/v1/file/{}".format(DNAC_URL, each[0]) 
        hdr = {'x-auth-token': token, 'content-type': 'application/json'}
        cmd_result = requests.get(url, headers=hdr, verify= False)
        result= json.dumps(cmd_result.json(), indent=4, sort_keys=True)
        if type(cmd_result.json()) != list:  ### en caso la salida no sea una lista entonces es un error y sigue con el sigueinte elemento ########
            print("entro al error ")
            time.sleep(10) ########## espera 10s para seguir buscando
            continue
        print("sali de aqui") ########## avisa que salio del error
        if json.loads(result)[0]['commandResponses']["SUCCESS"]: ####### se parsea  para obtener los valores en las tablas
            valor = json.loads(result)[0]['commandResponses']["SUCCESS"]["show interface {} ".format(each[1][1])]
            string_valor = str(valor)
            busque = string_valor.split()
            bits_sec = []  ### listas para guardar los valores 
            bytes = []
            lon = len(busque)
            for j in range (0,lon) : ### se busca hacer un bucle para obtener los valores de la salida del request
                if busque[j] == "bits/sec,":   ### bits/sec 
                    bits_sec.append(float(busque[j-1]))
                if (busque[j] == "packets" and busque[j-1] != "input"): #### packets input y output 
                    bytes.append(float(busque[j+2]))
            if bytes != [] and bits_sec != []:   
                lista = bits_sec + bytes  ### se agregan ambas listas 
                fecha = getTime()  ### se obtiene la hora
                lista.append(fecha)
                lista.insert(0,each[1][1])
                almacenar_db(lista,each[1])     ### se manda la lista a almacenar 
###############################################################################################################
############### Funcion almacenar_db ##########################################################################                   
def almacenar_db(lista,datos): 
    s = [tuple(lista)] ### se convierte en una tupla la lista S porque es el formato que usa Mysql
    conexion = sqlite3.connect("/home/ubuntulab/Desktop/chris/utIlization/utili_real.db") ### se conecta a la DB, colocar la ruta donde se creara 
    cursor = conexion.cursor() ### se crea el cursor para iniciar la escritura
    conexion.commit()  #### se carga la data
    try: #### en caso salga un error de que ya se creo la DB salta la excepción  
        cursor.execute("CREATE TABLE '{}' (Port CHAR,Input_Rate FLOAT, Output_Rate FLOAT, Input_bytes FLOAT,Output_bytes FLOAT, SDate TIMESTAMP)".format(datos[0]))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?,?)".format(),s)
        conexion.commit()
    except:
        print("La tabla {} ya existe".format(datos[0]))  ### se imprime que ya se creo previamente
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?,?)".format(datos[0]),s)
        conexion.commit() #### y se guarda mas elementos 
    conexion.close() ### se cierra la conexion con la DB
#######################################################################################################################
####################### MAIN ####################################################################################
if __name__ == "__main__":
    global hora_actual
    global hora_60
    global token   
    token = get_auth_token_first()
    hora_actual = time_now()
    hora_60 = delta_min(hora_actual)     
    while True :
        get_device_list()
        time.sleep(120) ######## se realiza el ciclo cada 120 segundos 