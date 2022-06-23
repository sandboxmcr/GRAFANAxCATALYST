<h3> INTRODUCCIÒN </h3>
Este còdigo permite recuperar la informaciòn PoE de los diferentes equipos que se tienen en la plataforma DNAC (DNA Center), almacenarlo en una base de datos de tipo sqlite3 y mostrarlo en dashboards creados en la plataforma Grafana.
<h4> DASHBOARD </h4>
En este dashboard tenemos un primer dashlet que muestra una lista de los dispositivos TOP que màs uso de PoE tienen en los ùltimos 10 minutos, desde luego se va actualizando. Se muestra a continuaciòn:

![image](https://user-images.githubusercontent.com/107586333/175133883-53fafbe2-2d6d-4540-93b7-a41182ab7924.png)
Por otro lado, el segundo dashlet muestra la utilizaciòn PoE por cada uno de los dispositivos a lo largo del tiempo, es posible usar los filtros de rango de tiempo que nos permite ver el historial de uso PoE en un rangos de minutos o cientos de dìas. 

![image](https://user-images.githubusercontent.com/107586333/175136035-b1a50af0-1f49-4fa0-ba4d-ca48a8936140.png)

<h4> QUERYS EN GRAFANA </h4> 
<ol>
  <li>TOP DEVICES UTILIZATION POE - LAST 10 MINUTES</li>
    
El promedio de utilizaciòn en nuestro ambiente es aproximadamente 2%, eso se ve reflejado en la condiciòn que usamos en el query, para obtener los dispositivos que sobrepasan ese porcentaje de uso. El tipo de dashlet usado es Bar Chart. 
    
  ```sqlite3
  SELECT SDate, DeviceName, powerUsed, datetime('now','localtime') as now, datetime('now','localtime','-9 minutes') as now9min
  FROM 'General2'
  WHERE powerUsed > 2 AND time(SDate) BETWEEN time(now) ANS DATE(SDate) = DATE(now)
  ```
  
  ![image](https://user-images.githubusercontent.com/107586333/175141878-ff9d8f78-1d06-409e-bd42-6c7841c06507.png)  
  <li>POE UTILIZATION PER DEVICE</l>
 Haremos un query por cada dispositivo, en el query debemos llamar a la tabla correspondiente al id o nombre de la tabla correspondiente al dispositivo, solo seleccionaremos la fecha y hora de muestreo y el porcentaje% de PoE usado.
  
   ```sqlite3
  SELECT SDate, powerUsed FROM '3850-2.lap.pe'
  ```
  ![image](https://user-images.githubusercontent.com/107586333/175142735-7db43e5a-bf2c-48ed-84d5-c740afd5c9c4.png)

Importante, para poder usar los filtros de tiempo es importante declarar el formato de la variable que hemos llamdo **"SDate"**, eso lo haremos con la secciòn "Transform". El tipo de dashlet usado es **"Time Series"**. 
![image](https://user-images.githubusercontent.com/107586333/175169626-8acbda7f-5fdd-4b33-b8d7-19a27d354889.png) 
</ol>
<h4> DATABASE </h4> 
Para este proyecto se utilizò una base de datos sqlite3, la llamamos PoE.db que contiene diversas tablas, la tabla General2 es la que almacena la informaciòn PoE de todos los dispositivos y que se usarà en los querys de Grafana para mostrar el TOP de dispositivos. Luego tenemos todas las demàs tablas con los nombres de cada dispositivo en especìfico.

![image](https://user-images.githubusercontent.com/107586333/175173601-7a438ca7-c8d7-4127-8158-83eb57bb3e85.png)
Contenido de la tabla General2:
![image](https://user-images.githubusercontent.com/107586333/175180284-0d5a6a24-cdbb-4262-a518-fa0a334ecc70.png)



