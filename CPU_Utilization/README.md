<h3> INTRODUCCIÒN </h3>
Este còdigo permite recuperar la informaciòn utilización de CPU de los diferentes equipos a través de la librería OpenSource NETMIKO, almacenarlo en una base de datos de tipo sqlite3 y mostrarlo en dashboards creados en la plataforma Grafana. 
<h4> DASHBOARD </h4>
En este dashboard mostramos la utilización de CPU para cada uno de los dispositivos que se han consultado mediante NETMIKO.
![image](https://user-images.githubusercontent.com/107586333/175187299-ca74dea8-5a43-4e48-bdbc-ab7bc62b1500.png)

<h4> QUERYS EN GRAFANA </h4> 
Para cada uno de los dashboard usaremos el siguiente query de SQLITE3 en Grafana, que permiten recupear la fecha-hora de muestreo y la utilización almacenada en la variable OneMinute. El tipo de dashlet usado es **Time Series**.
    
  ```sqlite3
  SELECT SDate, OneMinute FROM 'nombre_del_dispositivo'
  ```
  ![image](https://user-images.githubusercontent.com/107586333/175188615-308c9129-0cb4-4fa9-ab91-1c275a08a38a.png)

Importante, para poder usar los filtros de tiempo es importante declarar el formato de la variable que hemos llamdo **"SDate"**, eso lo haremos con la secciòn "Transform". El tipo de dashlet usado es **"Time Series"**. 
![image](https://user-images.githubusercontent.com/107586333/175169626-8acbda7f-5fdd-4b33-b8d7-19a27d354889.png) 
<h4> DATABASE </h4> 
Para este proyecto se utilizò una base de datos sqlite3, la llamamos CPU_NDNAC.db que contiene diversas tablas, todas con los nombres de cada dispositivo en especìfico. En cada tabla tenemos los siguientes parámetros, se puede escoger cual se desea mostrar en el dashboard.
<ol>
  <li>FiveSeconds</li>
  <li>Interrup</li>
  <li>OneMinute</li>
  <li>FiveMinutes</li>
  <li>SDate</li>
</ol>

![image](https://user-images.githubusercontent.com/107586333/175191898-1535d3de-7ea7-4956-98aa-85339e496fd1.png)

<h4> CREDENCIALES DE LOS EQUIPOS </h4>
Las cerenciales de los equipos se almacenan en un documento .csv en el siguiente formato. Contiene la dirección IP, el nombre del hostname, Username y Password para la conexión SSH con el dispositivo.
![image](https://user-images.githubusercontent.com/107586333/175192493-4e44373d-4f19-4859-b8ff-216e6bc680e5.png)
