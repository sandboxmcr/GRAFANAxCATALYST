
# CODIGO DE RECUPERACIÓN DE UTILIZACIÓN DE ENERGÍA EN PUERTOS POE
"""
Este código se basa en llamadas de APIs para obtener la
utilización de los puertos POE de los equipos accedidos por Netmiko.
    
    Netmiko es una libreria de redes multivendedores que es una libreria 
    estandar para las conexiones ssh Python. Con Netmiko como base, se pueden 
    realizar programas y scripts que faciliten y mejoren la administracion de 
    los equipos de redes.
    
    Se usaron las siguientes funciones: 
      1.getTime
      2.almacenar_db
      3.almacenar_db_perdevice
      4.connect_netmiko   
      5.excel_credential
      
"""
######### Sección de importaciones######################
import csv
from netmiko import ConnectHandler
import datetime
import time 
import sqlite3
###########################################################
############# Funcion almacenar_db() funcion para almacenar la lista S con los valores obtenidas  ################################################ 
def almacenar_db(device_uuid,s):
    lista = [tuple(s)] ### se convierte en una tupla la lista S porque es el formato que usa Mysql
    conexion = sqlite3.connect("/home/ubuntulab/Desktop/chris/NDNAC/PoE/PoE_NDNAC_general.db") ### se conecta a la DB, colocar la ruta donde se creara 
    cursor = conexion.cursor() ### se crea el cursor para iniciar la escritura
    conexion.commit() #### se carga la data
    try:##### en caso salga un error de que ya se creo la DB salta la excepción  
        cursor.execute("CREATE TABLE '{}' (DeviceName TEXT,powerAllocated REAL, powerConsumed REAL, powerRemaining REAL, powerUsed'%' REAL ,SDate TIMESTAMP)".format(device_uuid))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?,?)".format(device_uuid),lista)
        conexion.commit() 
    except:### se imprime que ya se creo previamente
        print("La tabla {} ya existe".format(device_uuid),type(s[4]))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?,?)".format(device_uuid),lista) ##### cuentan con 6 variables
        conexion.commit()
#######################################################################################################################
################## Funcion almacenar_db_perdevice que crea otra base de datos para una tabla por diposictivo ##############
def almacenar_db_perdevice(name, s):
    lista = [tuple(s)]
    conexion = sqlite3.connect("/home/ubuntulab/Desktop/chris/NDNAC/PoE/PoE_NDNAC.db")
    cursor = conexion.cursor()
    conexion.commit()
    print(lista)
    try:                ### las variables
        cursor.execute("CREATE TABLE '{}' (powerAllocated REAL, powerConsumed REAL, powerRemaining REAL, powerUsed'%' REAL ,SDate TIMESTAMP)".format(name))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?)".format(name),lista)
        conexion.commit()
    except:
        print("La tabla {} ya existe".format(name),type(s[4]))
        cursor.executemany("INSERT INTO '{}' VALUES(?,?,?,?,?)".format(name),lista) ### cuentan con 5 variables
        conexion.commit()
################################################################################################################
##################getTime() funcion para obtener el tiempo actual en formato establecido########################
def getTime():
    timenow = datetime.datetime.now().isoformat(timespec='seconds')
    return timenow  
################################################################################################################
###################### Funcion excel_credential busca el archivo excel donde se tienen las credenciales de los equipos ##########
def excel_credential():
    lista_general = []
    with open("/home/ubuntulab/Desktop/chris/NDNAC/memoria/credenciales.csv",newline="\n") as csvfile: #### se abre el archivo como scvfiles
        spamreader = csv.reader(csvfile,delimiter=",") 
        for row in spamreader: #### obteniendo los datos en cada fila 
            if row == ["","","",""] or row == ['IP Address', 'Hostname', 'Username', 'Password']: ### se obvia el titulo
                continue
            else:
                lista_general.append(row)
    return lista_general ##### se retorna la lista completo de los valores
#################################################################################################################
################### funcion connect_netmiko realiza la conexion por ssh hacia los equipos ######################
def connect_netmiko(lista):
        for i in lista:  ############ cada elemento de la lista se conectara por netmiko########################
            net_connect = ConnectHandler( ############ se usa la funcion connectHandler con los parametro
                device_type = "cisco_xe",  #### tipo de dispositivo
                ip = i[0],  ## direccion IP
                username = i[2],  ##### username
                password = i[3]  ######  password
                                        )
            if net_connect.check_enable_mode():
                    print("Success: in enable mode")  #### si la conexion se realiza correctamente
            else:
                print("Fail... con el equipo {}".format(i[1])) #### si falla se imprime ese mensaje
                continue
            net_connect.find_prompt()  
            net_connect.enable() ##### habilitar la conexión 
            print("se logro conectar con el equipo {}".format(i[1]))
            output_CPU = net_connect.send_command("show power inline police") #### se usa el send_command(con el comando como argumento)
            spl = output_CPU.split()
            if spl[0] != "Module": ####### si no aparece en la salida module no es un equipo POE
                print("El dispositivo {} no es un equipo PoE ".format(i[1]))
            else:  #### se obtienen todos los valores necesitados para crear las tablas 
                pwr_allocated = float(spl[12])    ## power allocated
                pwr_consumed = float(spl[13])     ## power consumed
                pwr_Remainig = float(spl [14])    ## power remaining
                pwr_consumed_perc = float(round(pwr_consumed*100/pwr_allocated,2)) ## power consumed en porcentaje
                fecha= getTime()  #### se usa la funcion para obteneer el tiempo actual 
                lista_para = [i[1], pwr_allocated,pwr_consumed,pwr_Remainig,pwr_consumed_perc,fecha] ##### se crea la lista para el general 
                lista_espe = [pwr_allocated,pwr_consumed,pwr_Remainig,pwr_consumed_perc,fecha] ###### se crea la lista para el especifico
                almacenar_db('General',lista_para)  ####### se usan las funciones de almacenar
                almacenar_db_perdevice(i[1],lista_espe)
################################################################################################################################
########################### MAIN ########################################################################
if __name__ == "__main__":
    while True:
        lista = excel_credential()
        connect_netmiko(lista)  
        time.sleep(400)  #### se espera un tiempo de 400 segundos porque las metricas se actualizan cada cierto tiempo 
#########################################################################################################            