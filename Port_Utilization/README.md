<h3> INTRODUCCIÒN </h3>
Este còdigo permite recuperar la informaciòn de utilización de puertos de diferentes equipos, almacenarlo en una base de datos de tipo sqlite3 y mostrarlo en dashboards creados en la plataforma Grafana.

<h4> DASHBOARD </h4>
En este dashboard tenemos información en el tiempo de la utilización de las interfaces más usadas en sentido de salida (output) para cada uno de los dispositivos. Se muestra a continuaciòn:

![image](https://user-images.githubusercontent.com/107586333/175198518-aba544ff-76f1-498e-8851-119f4ba7f5d7.png)

En este dashboard tenemos información en el tiempo de la utilización de las interfaces más usadas en sentido de entrada (input) para cada uno de los dispositivos. Se muestra a continuaciòn:

![image](https://user-images.githubusercontent.com/107586333/175198614-8e92dc30-8b59-4666-a553-1db1b2bb6de4.png)

<h4> QUERYS EN GRAFANA </h4> 
Para cada uno de los dashboard usaremos el siguiente query de SQLITE3 en Grafana, que permiten recupear la fecha-hora de muestreo y la utilización almacenada en la variable InBytes(para recuperar info de entrada) y OutBytes(para recuperar info de salida). El tipo de dashlet usado en ambos es Time Series.
Realizaremos un query para cada una de las interfaces de las cuales queremos mostrar información. El query será el siguiente.

  ```sqlite3
  SELECT Interface, SDate, (InBytes*8/1000)/450 as 'GigabitEthernet1/0/3'
  FROM 'nombre_del_dispositivo'
  WHERE Interface = 'GigabitEthernet1/0/3'
  ```
Para pasar a Mbps, hacemos la operación que se muestra en el query, pues la información recuperada está en bytes y es es un período de muestreo de 450 segundos aproximandamente.

![image](https://user-images.githubusercontent.com/107586333/175198826-f02e8956-5658-4caa-9aab-da2e96264bda.png)

Importante, para poder usar los filtros de tiempo es importante declarar el formato de la variable que hemos llamdo **"SDate"**, eso lo haremos con la secciòn "Transform".
![image](https://user-images.githubusercontent.com/107586333/175198862-656accd2-b54d-44f5-8379-3066efb051db.png)

<h4> DATABASE </h4> 
Para este proyecto se utilizò una base de datos sqlite3, la llamamos PoE_uti.db que contiene diversas tablas, todas con los nombres de cada dispositivo en especìfico. En cada tabla tenemos los siguientes parámetros, **se puede escoger cual se desea mostrar en el dashboard.**
<ol>
  <li>Interface</li>
  <li>InPackets</li>
  <li>InBytes</li>
  <li>InRate</li>
  <li>OutPackets</li>
  <li>OutBytes</li>
  <li>OutRate</li>
  <li>SDate</li>
</ol>

![image](https://user-images.githubusercontent.com/107586333/175199393-0319fb4a-d7ba-4a20-bb64-967d723a3007.png)

