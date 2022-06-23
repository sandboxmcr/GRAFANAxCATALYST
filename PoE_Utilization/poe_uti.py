# CODIGO DE RECUPERACIÓN DE DATOS DE UTILIZACIÓN POE PARA DISPOTIVOS, 
# MEDIANTE APIS DE DNAC
"""
Este código se basa en llamadas de APIs para obtener el uso
de PoE de todos los equipos que se encuentran integrados 
con el DNAC.
    
    Se usaron las siguientes APIS:
    1. API para obtener TOKEN            ( https://{}/dna/system/api/v1/auth/token )
    2. API para obtener lista de equipos ( https://{}/api/v1/network-device )
    3. API para retornar detalles de PoE de las interfaces ( https://{}/api/v1/network-device/{deviceUuid}/poe)

    Se usaron las siguientes funciones: 
    1.delta_min              5.poe_request              9.almacenar_db
    2.get_auth_token_first   6.getTime       
    3.get_auth_token         7.time_now                  
    4.get_device_list        8.almacenar_db
"""
################# Sección de importaciones #####################
from time import sleep
import requests
from requests.auth import HTTPBasicAuth
import os
import datetime
import sqlite3
from datetime import timedelta

################# Sección de credenciales de DNAC ################
DNAC_URL = ""
DNAC_USER = ""
DNAC_PASS = ""

#Función para obtener la hora a la que se deberá actualizar nuevamente el token
def delta_min(time):
    variacion = timedelta(minutes=60)
    time = time + variacion
    return time
#Función para obtener el token por primera vez 
def get_auth_token_first():
    global token
    url = 'https://{}/dna/system/api/v1/auth/token'.format(DNAC_URL)                 
    hdr = {'content-type' : 'application/json'} 
    resp = requests.post(url, auth=HTTPBasicAuth(DNAC_USER, DNAC_PASS), headers=hdr, verify= False)
    token = resp.json()['Token']
    print (token)                                                      
    return token #retornamos el token
#Función que comprueba la hora y genera un nuevo token si es necesario
def get_auth_token():
    global hora_30
    global token
    global hora_actual
    flag = False
    url = 'https://{}/dna/system/api/v1/auth/token'.format(DNAC_URL)                 
    hdr = {'content-type' : 'application/json'}                                       
    while flag == False:
        hora_actual = time_now()  
        flag = True
        if hora_actual > hora_30: #si la hora actual alcanza o es mayor a la hora calculada para la actualización se genera un nuevo token
            resp = requests.post(url, auth=HTTPBasicAuth(DNAC_USER, DNAC_PASS), headers=hdr, verify= False)
            hora_30 = delta_min(hora_actual) #actualizamos la siguiente hora de generación de token
            flag = False
            token = resp.json()['Token']
        print (token)                                                   
    return token #retornamos el token actual o el nuevo según la condición evaluada

#Función de inicio, obtiene la lista de dispositivos en la plataforma DNAC
def get_device_list():
    dic = {} #diccionario para guardar los dispositivos
    url = "https://{}/api/v1/network-device".format(DNAC_URL)
    #Declarar parámetros para el request
    hdr = {'x-auth-token': token, 'content-type' : 'application/json'}
    resp = requests.get(url, headers=hdr, verify= False)  # Realizar el get request mediante la API
    device_list = resp.json() #Almacenar la respuesta, lista de dispositivos
    print("{0:25}{1:25}".format("hostname", "id"))
    for device in device_list['response']:
        dic[device['hostname']] = device['id'] #almacenar los hostnames y id de dispositivos en un diccionario
    poe_request(token,dic) #llamamos a la función para obtener información de PoE

def poe_request(token,dic):
    #recorremos el diccionario, tanto el hostname como el ID de cada dispositivo
    #Para cada dispositivo solicitamos información de PoE sobre 
    for name,id in dic.items():
        print("**** PARA EL {} *****".format(id))
        #Declarar parámetros para el request
        uuid = id
        url = "https://{}/api/v1/network-device/{deviceUuid}/poe".format(DNAC_URL,deviceUuid = uuid)
        hdr = {'x-auth-token': token, 'content-type' : 'application/json'}
        respuesta = requests.get(url, headers=hdr, verify= False)  # Make the Get Request
        resp = respuesta.json()
        #Verificar que la respuesta no sea errada
        if 'errorCode' not in resp['response']:
            po_Allo = resp['response']['powerAllocated'] #Almacenar la capacidad PoE
            if po_Allo == None:  #Verificar si NO es dispositivo PoE
                print(name , " NO ES POE") 
            else:                #Si es PoE entonces almacenar en variables las características PoE
                pwr_allocated = float(resp['response']['powerAllocated'])  #almacenar capacidad PoE
                pwr_consumed = float(resp['response']['powerConsumed'])    #almacenar la potencia consumida
                pwr_Remainig = float(resp['response']['powerRemaining'])   #almacenar la potencia remanente
                pwr_consumed_perc = float(round(pwr_consumed*100/pwr_allocated,2)) #calcular el % de potencia usada
                time = getTime() #obtener la hora de muestreo
                lista_para = [name, pwr_allocated,pwr_consumed,pwr_Remainig,pwr_consumed_perc,time] #lista para tabla de la base de datos General, donde se tienen todos los dispositivos
                lista_espe = [pwr_allocated,pwr_consumed,pwr_Remainig,pwr_consumed_perc,time]       #lista para la tabla de la base de datos individual para cada dispositivo
                #Almacenar en las bases de datos ambas listas
                almacenar_db('General2',lista_para) #lista de todos los dispositivos
                almacenar_db_perdevice(name,lista_espe) #lista de cada dispositivo
                
#Funciones para obtener la hora y fecha de muestreo                
def getTime():
    timenow = datetime.datetime.now().isoformat(timespec='seconds') 
    print(timenow)
    return timenow
def time_now ():
    timenow = datetime.datetime.now()
    return timenow

#Funciones para almacenar datos en formato tupla en la base de datos
def almacenar_db(device_uuid,s):
    lista = [tuple(s)] #para almacenar en la base de datos, pasamos los datos a un formato tupla
    try:  #creamos la tabla en la base de datos
        cursor.execute("CREATE TABLE '{}' (DeviceName TEXT,powerAllocated REAL, powerConsumed REAL, powerRemaining REAL, powerUsed'%' REAL ,SDate TIMESTAMP)".format(device_uuid))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?,?)".format(device_uuid),lista)
        conexion.commit()
    except: #si ya existe la tabla solo almacenamos la información
        print("La tabla {} ya existe".format(device_uuid),type(s[4]))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?,?)".format(device_uuid),lista)
        conexion.commit()       
def almacenar_db_perdevice(name, s):
    lista = [tuple(s)]
    try:
        cursor.execute("CREATE TABLE '{}' (powerAllocated REAL, powerConsumed REAL, powerRemaining REAL, powerUsed'%' REAL ,SDate TIMESTAMP)".format(name))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?)".format(name),lista)
        conexion.commit()
    except:
        print("La tabla {} ya existe".format(name),type(s[4]))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?)".format(name),lista)
        conexion.commit()
        
if __name__ == "__main__":
    global hora_actual
    global hora_30
    global token
    #Obtener el token por primera vez
    token = get_auth_token_first()
    #Guardar la hora de primera ejecución
    hora_actual = time_now()
    #Calcular el primer período en el que se creará un nuevo token
    hora_30 = delta_min(hora_actual)
    #Inicio del bucle principal
    while True:
        #Establecer conexión a la base de datos y comenzar la lógica con la primera función.
        conexion = sqlite3.connect("/home/ubuntulab/Desktop/chris/DNAC/POE/POE.db")
        cursor = conexion.cursor()
        conexion.commit()
        get_device_list()
        conexion.close()
        sleep(400)


