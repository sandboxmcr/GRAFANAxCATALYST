# CODIGO DE RECUPERACIÓN DE DATOS DE UTILIZACIÓN POE PARA DISPOTIVOS, 
# MEDIANTE NETMIKO
"""
Este código se basa en una herramienta de automatizaciòn llamada NETMIKO 
para obtener el uso cpu de todos los equipos que se desean. NO es requerido 
tener la soluciòn DNAC pues no usaremos APIs.
    Se usaron las siguientes funciones: 
    1.almacenar_db                    
    2.getTime                     
    3.connect_netmiko                         
    4.excel_credential       
"""
################# Sección de importaciones #####################
import csv
from netmiko import ConnectHandler
import re
import datetime
import time 
import sqlite3

#Función para obtener las credenciales y dispositivos del archivo de excel
def excel_credential():
    lista_general = []
    #abrir la el archivo de excel
    with open("/home/ubuntulab/Desktop/chris/NDNAC/memoria/credenciales.csv",newline="\n") as csvfile:
        spamreader = csv.reader(csvfile,delimiter=",") 
        for row in spamreader: #leer cada columna del archivo de excel y almacenarlo en una lista general
            if row == ["","","",""] or row == ['IP Address', 'Hostname', 'Username', 'Password']: #si es una columna que NO contiene credenciales de equipos
                continue
            else: #si es una columna que si contiene credenciales de equipos, entonces almacenarlo en una lista general
                lista_general.append(row)
    return lista_general  #retornar la lista general

#Función de NETMIKO inicializada, le damos como parametro la lista general anterior
def connect_netmiko(lista):
        #i = ['ip','name','username','password']
        for i in lista: #recorrer cada elemento de la lista general
            net_connect = ConnectHandler(
                device_type = "cisco_xe",
                ip = i[0],
                username = i[2],
                password = i[3]
                                        )
            if net_connect.check_enable_mode(): #revisamos la conexión 
                    print("Success: in enable mode")
            else:  #en caso no se establezca la conexión
                print("Fail... con el equipo {}".format(i[1]))
                continue #continuar con el siguiente dispositivo en caso no establecer conexión
            net_connect.find_prompt() #acceder al prompt del dispositivo
            net_connect.enable() #entrar al modo usuario privilegiado
            print("se logro en el equipo {}".format(i[1]))
            #le pasamos el comando para obtener los parámetros de uso del cpu, lo filtramos pues solo queremos la primera línea
            output_CPU = net_connect.send_command("show processes cpu | include one minute")
            net_connect.disconnect() #desconectamos la sesión
            print("Cierre sesion del equipo {}".format(i[1]))
            #filtramos la respuesta obtenida de ejecutar el comando, con el fin de buscar solo lo datos numericos
            s = [ float(str(s).replace('%','')) for s in re.findall('[0-9]+[%]', output_CPU)]
            fecha= getTime() #obtener la hora de muestreo 
            s.append(fecha)  #anexar la hora en la lista a almacenar en el DB
            almacenar_db(i[1],s) #llamar a la función almacenar en DB, le pasamos el nombre del dispositivo y la lista de parámetros
            time.sleep(10)
            
#Función para almacenar la información en la base de datos
def almacenar_db(device_uuid,s):
    lista = [tuple(s)] #convertir los datos a formato tupla para almacenar
    conexion = sqlite3.connect("/home/ubuntulab/Desktop/chris/NDNAC/memoria/CPU_NDNAC.db")
    cursor = conexion.cursor()
    conexion.commit()
    try:
        cursor.execute("CREATE TABLE '{}' (FiveSeconds REAL, Interrup FLOAT, OneMinute FLOAT, FiveMinutes REAL, SDate TIMESTAMP)".format(device_uuid))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?)".format(device_uuid),lista)
        conexion.commit()
    except:
        print("La tabla {} ya existe".format(device_uuid),type(s[0]))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?)".format(device_uuid),lista)
        conexion.commit()
#Función para obtener la hora
def getTime():
    timenow = datetime.datetime.now().isoformat(timespec='seconds')
    return timenow   

if __name__ == "__main__":
    while True:
        lista = excel_credential() #llamar a la función de obtención de credenciales
        connect_netmiko(lista)     #llamar a la lista de conexión con netmiko
        time.sleep(40)    
