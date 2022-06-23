# CODIGO DE RECUPERACIÓN DE DATOS DE UTILIZACIÓN DE PUERTOS PARA DISPOTIVOS, 
# MEDIANTE NETMIKO
"""
Este código se basa en una herramienta de automatizaciòn llamada NETMIKO 
para obtener el uso cpu de todos los equipos que se desean. NO es requerido 
tener la soluciòn DNAC pues no usaremos APIs.
    Se usaron las siguientes funciones: 
    1.get_devices               6.getTime                   11.get_output_info
    2.get_interfaces            7.connect_netmiko           12.pre_storage
    3.read_interfaces           8.connect_netmiko_uti       13.excel_credential     
    4.almacenar_db              9.limpiar_equipos  
    5.clear_counters            10.get_input_info
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
    #abrir el archivo de excel
    with open("/home/ubuntulab/Desktop/chris/NDNAC/memoria/credenciales.csv",newline="\n") as csvfile:
        spamreader = csv.reader(csvfile,delimiter=",") 
        for row in spamreader: #leer cada columna del archivo de excel y almacenarlo en una lista general
            if row == ["","","",""] or row == ['IP Address', 'Hostname', 'Username', 'Password']:
                continue
            else: #si es una columna que si contiene credenciales de equipos, entonces almacenarlo en una lista general
                lista_general.append(row)
        get_devices(lista_general)
    return lista_general    #retornar la lista general

#Función para almacenar los dispositivos en una lista global de dispositivos y credenciales
def get_devices(lista): 
    global dispositivos  
    dispositivos = []
    for i in lista:
        dispositivos.append(i[1])
        
#Función de NETMIKO inicializada, le damos como parametro la lista general anterior        
def connect_netmiko(lista):
        global net_connect
        for i in lista: #recorrer cada elemento de la lista general
            #i = ['ip','name','username','password']
            net_connect = ConnectHandler(
                device_type = "cisco_xe",
                ip = i[0],
                username = i[2],
                password = i[3])
            if net_connect.check_enable_mode():  #revisamos la conexión 
                    print("Success: in enable mode")
            else:  #en caso no se establezca la conexión
                print('')   #continuar con el siguiente dispositivo en caso no establecer conexión
                continue
            net_connect.enable()  #entrar al modo usuario privilegiado
            print("se logro en el equipo {}".format(i[1]))
            get_interfaces(i[1]) #pasamos a la función para obtener información de las interfaces de cada uno de los equipos

#Función para obtener las interfaces de los equipos
def get_interfaces(device):
    lista_interfaces =  []  #variable para almacenar las interfaces en una lista
    inter = net_connect.send_command("show ip interface brief") #pasamos el comando al equipo para obtener todas las interfaces del equipo
    for i in list(inter.split('\n')): #parsear la respuesta del comando, para obtener cada interfaces y almacenarlo en una lista
        inter = list(i.split())
        print(inter)
        lista_interfaces.append(inter) #almacenar en una lista las interfaces
    #Guardamos las interfaces de cada equipo en un archivo .csv para cada uno de ellos.
    with open("/home/ubuntulab/Desktop/chris/NDNAC/puertos/archivos/{}.csv".format(device),"w")as file:
        writer = csv.writer(file)
        writer.writerows(lista_interfaces)
    close()

#Función para leer las interfaces de los archivos txt almacenados
def read_interfaces():
    global diccionario
    #formato del diccionario -> {'cat832' : '['giga0/0','loopback0']'}
    diccionario = {}
    # formato de list(row) = GigabitEthernet1,10.96.246.37,YES,NVRAM,up,up
    for i in dispositivos:  #leer la lista de interfaces de cada dispositivos
        interfaces_per_device = []
        with open("/home/ubuntulab/Desktop/chris/NDNAC/puertos/archivos/{}.csv".format(i),newline="\n") as csvfile:
            spamreader = csv.reader(csvfile,delimiter=",") 
            for row in spamreader:
                inter = list(row)[0]
                if list(row)[4] == 'up' and ('LISP' not in list(row)[0]):  #filtrar las interfaces que estén en down y las interfaces LISP
                    interfaces_per_device.append(inter) 
            diccionario[i] = interfaces_per_device    
    #almacenar en un txt el diccionario donde se almacena el diccionario antes llenado
    with open("/home/ubuntulab/Desktop/chris/NDNAC/puertos/archivos/INTERFACES.txt","w")as file:
        file.write(str(diccionario))

#Función para obtener los parámetros de utilización de cada uno de los puertos
def connect_netmiko_uti(lista):
        global net_connect
        global lista_utilizacion
        #i = ['ip','name','username','password']
        limpiar_equipos(lista) #primero limpiaremos los contadores de las interfaces de todos los equipos
        time.sleep(240)
        for i in lista: #Para cada uno de los equipos procedemos a iterar
            print("\nINICIAMOS EL PROCESO PARA EL EQUIPO {}\n".format(i[1]))
            lista_utilizacion = []
            net_connect = ConnectHandler(
                device_type = "cisco_xe",
                ip = i[0], 
                username = i[2],
                password = i[3])
            if net_connect.check_enable_mode():
                    print(" 1. Success: in enable mode")
            else:
                print('')
                #print("Fail... con el equipo {}".format(i[1]))
                #continue
            net_connect.enable()
            print(" 2.CONEXIÓN ESTABLECIDA CON EL DISPOSITIVO {}".format(i[1])) 
            lista_interfaces = diccionario[i[1]]
            for inte in lista_interfaces: #comenzaron la recopilación de los contadores para cada una de las interfaces
                lista_utilizacion = []
                lista_utilizacion.append(inte)
                get_input_info(inte, lista_utilizacion) #función para obtener parametros de input
                get_output_info(inte,lista_utilizacion) #función para obtener parametros de output
                pre_storage(lista_utilizacion)
                almacenar_db(i[1],lista_utilizacion)
                print(" 5.DATOS ALMACENADOS PARA EL {} ,INTERFACE {}".format(i[1],inte),)
            close()

#Función para limpiar los contadores de las interfaces de los equipos
def limpiar_equipos(lista):
    global net_connect
    global lista_utilizacion
    for i in lista:
            print("\nINICIAMOS EL PROCESO PARA EL EQUIPO {}\n".format(i[1]))
            lista_utilizacion = []
            net_connect = ConnectHandler(
                device_type = "cisco_xe",
                ip = i[0], 
                username = i[2],
                password = i[3])
            if net_connect.check_enable_mode():
                    print(" 1. Success: in enable mode")
            else:
                print('')
            net_connect.enable()
            print(" 2.CONEXIÓN ESTABLECIDA CON EL DISPOSITIVO {}".format(i[1])) 
            clear_counters(i[1])  #llamar a la función para limpiar los contadores 
            close() 
def clear_counters(dispo = ''):
    lista = []
    net_connect.send_command("clear counters", expect_string="\[confirm\]") #enviamos el comando clear counters que de forma global limpia los contadores en el dispositivo
    net_connect.send_command("\n", expect_string="#") #enviamos la confirmación para reiniciar los contadores
    print(" 3.LOS CONTADORES SE HAN REINICIADO -> ".format(dispo))
  
#Función para obtener los parámetros de utilización de input de los puertos
def get_input_info(interface,lista):
    #enviar el comando 'show interface' filtrando solo la línea de input packets
    input_info = net_connect.send_command("show interface {} | include packets input".format(interface))
    input = [float(str(s)) for s in re.findall('[0-9]+', input_info)] #filtrar los parámetros numéricos
    inpackets= input[0]
    inbytes =input[1]
    lista.append(inpackets)
    lista.append(inbytes)
    #enviar el comando 'show interface' filtrando solo la línea de input rate
    input_info2 = net_connect.send_command("show interface {} | include  input rate".format(interface))
    input2 = [float(str(s)) for s in re.findall('[0-9]+', input_info2)] #filtrar los parámetros numéricos
    print(input2)
    inrate =input2[1]
    lista.append(inrate)
    
def get_output_info(interface,lista):
    #enviar el comando 'show interface' filtrando solo la línea de output packets
    output_info = net_connect.send_command("show interface {} | include packets output".format(interface))
    output = [float(str(s)) for s in re.findall('[0-9]+', output_info)]
    #print(re.findall('[0-9]+', output_info))
    inpackets= output[0]
    inbytes = output[1]
    lista.append(inpackets)
    lista.append(inbytes)
    #enviar el comando 'show interface' filtrando solo la línea de output rate
    output_info2 = net_connect.send_command("show interface {} | include output rate".format(interface))
    output2 = [float(str(s)) for s in re.findall('[0-9]+', output_info2)]
    #print(output2)
    outrate =output2[1]
    lista.append(outrate)
    print(" 4.ESTADISTICAS DE SALIDA Y ENTRADA RECOPILADAS PARA LA INTERFACE {}".format(interface))

#Función para obtener el tiempo de muestreo    
def pre_storage(lista):
    time = getTime()
    lista.append(time)
    print(lista)   
       
def close():
    net_connect.disconnect()
    
def almacenar_db(device_uuid,s):
    lista = [tuple(s)]
    conexion = sqlite3.connect("/home/ubuntulab/Desktop/chris/NDNAC/puertos/INTER_UTI.db")
    cursor = conexion.cursor()
    conexion.commit()
    try:
        cursor.execute("CREATE TABLE '{}' (Interface TEXT , InPackets FLOAT, InBytes FLOAT,InRate FLOAT, OutPackets REAL, OutBytes REAL, OutRate FLOAT, SDate TIMESTAMP)".format(device_uuid))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?,?,?,?)".format(device_uuid),lista)
        conexion.commit()
    except:
        print("La tabla {} ya existe".format(device_uuid),type(s[0]))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?,?,?,?)".format(device_uuid),lista)
        conexion.commit()
      
def getTime():
    timenow = datetime.datetime.now().isoformat(timespec='seconds')
    return timenow    

if __name__ == "__main__":
    conexion = sqlite3.connect("/home/ubuntulab/Desktop/chris/NDNAC/puertos/INTER_UTI.db")
    cursor = conexion.cursor()
    conexion.commit() 
    lista = excel_credential()  #leer las credenciales de los dispositivos
    connect_netmiko(lista)      #conectar con cada uno de los dispositivos a través de NETMIKO
    read_interfaces()           #recopilar la lista de interfaces de cada dispositivo
    while True:
        connect_netmiko_uti(lista)  #iniciar el proceso de lectura de parametros de las interfaces
        time.sleep(40)    
