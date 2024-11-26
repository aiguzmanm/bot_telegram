#!/usr/bin/env python
# coding: utf-8

# In[1]:


import configparser
import sqlalchemy
from sqlalchemy import text
import pandas as pd
import pymysql
import os
import json
import datetime
import requests


# In[ ]:


config = configparser.ConfigParser()
config.read('config.ini')
#path_id_record = ""#config.get("ids","main_path")+"/Id_Record"

path_homologaciones=""
if os.name == "nt":
    path_homologaciones = config.get("ids","main_path_windows")+"/01_nombre_origen"
else:
    path_homologaciones = config.get("ids","main_path_ubuntu")+"/01_nombre_origen"


# In[ ]:


def buscar_nuevos(df_datos,homologacion,columna_nombre_datos,columna_nombre_homologacion,columna_id_homologacion):
    df_datos=df_datos.rename(columns={columna_nombre_datos:columna_nombre_homologacion})
    df_homologacion=homologacion[[columna_nombre_homologacion,columna_id_homologacion]]
    # Lee Centrales de Configuración
    df_nuevos=df_datos[~df_datos[columna_nombre_homologacion].isin(list(df_homologacion[columna_nombre_homologacion].unique()))].drop_duplicates(subset=[columna_nombre_homologacion], keep='first').dropna()
    #df_nuevos[columna_nombre_datos]=df_nuevos[columna_nombre_datos].astype(str).str.replace('\d+', '')

    if df_nuevos.shape[0]==0:
        df_nuevos=pd.DataFrame.from_dict({columna_nombre_datos:[]})
    return df_nuevos


# In[ ]:


#def buscar_nuevos(df_datos,homologacion,columna_nombre_datos,columna_nombre_homologacion,columna_id_homologacion):
#    df_homologacion=homologacion[[columna_nombre_homologacion,columna_id_homologacion]]
#    # Lee Centrales de Configuración
#    df_nuevos=df_datos[~df_datos[columna_nombre_datos].isin(list(df_homologacion[columna_nombre_homologacion].unique()))][[columna_nombre_datos]].drop_duplicates().dropna()
#    #df_nuevos[columna_nombre_datos]=df_nuevos[columna_nombre_datos].astype(str).str.replace('\d+', '')#
#
#    if df_nuevos.shape[0]>0:
#        df_nuevos=df_nuevos.rename(columns={columna_nombre_datos:columna_nombre_homologacion})
#    else:
#        df_nuevos=pd.DataFrame.from_dict({columna_nombre_datos:[]})
#    return df_nuevos


# In[ ]:


def formato_datos(df_datos, carpeta):
    diccionario={}
    diccionario["sipub_cmg_onl"]={"Id Record":"int64",
                            "Id Fecha":"int32",
                            "Id YYYYMM":"int32",
                            "Hora":"int32",
                            "Cuarto de Hora":"int32",
                            "CMg [USD/MWh]":"int32",
                            "Id Barra Origen Sipub":"int32",
                                       }
    diccionario["sipub_cmg_pre"]={"Id Record":"int64",
                            "Id Fecha":"int32",
                            "Id YYYYMM":"int32",
                            "Hora":"int32",
                            "Cuarto de Hora":"int32",
                            "CMg [USD/MWh]":"int32",
                            "Id Barra Origen Sipub":"int32",
                                       }
    diccionario["sipub_cmg_def"]={"Id Record":"int64",
                            "Id Fecha":"int32",
                            "Id YYYYMM":"int32",
                            "Hora":"int32",
                            "Cuarto de Hora":"int32",
                            "CMg [USD/MWh]":"int32",
                            "Id Barra Origen Sipub":"int32",
                                       }
    diccionario["rio_sscc"]={"Id Record":"int64",
                            "Id Fecha":"int32",
                            "Id YYYYMM":"int32",
                            "Id Hora Minuto Inicio":"int32",
                            "Id Hora Minuto Fin":"int32",
                            "Id Central Origen Rio":"int32",
                            "Id Configuracion Origen Rio":"int32",
                            "Instruccion SSCC":"str",
                            "Id Config":"int32",
                            "Central Subestacion PRS":"str",
                            "Barra CT":"str",
                            "Disponibilidad [MW]":"str",
                            "SSCC Baja":"str",
                            "SSCC Sube":"str",
                            "SSCC Unidad":"str",
                            "Motivo":"str",
                            "Comentario":"str"
                                       }
    
    diccionario["rio_movcen"]={"Id Record":"int64",
                                        "Id Fecha":"int32",
                                        "Id YYYYMM":"int32",
                                        "Id Hora Minuto":"int32",
                                        "Id Central Origen Rio":"int32",
                                        "Condicion Embalse":"str",
                                        "Neomante":"str",
                                        "Id Configuracion Origen Rio":"int32",
                                        "Despacho Requerido [MW]":"str",
                                        'Estado Operacional':"str",
                                        'Estado Operacional Combustible':"str",
                                        'Consigna CMg':"str",
                                        'Consigna Limitacion':"str", 
                                        'Instruccion CMg':"str", 
                                        'Motivo':"str",
    
                                        "Id Central Origen CMg Crucero 220":"int32",
                                        "Id Central Origen CMg Diego de Almagro 220":"int32",
                                        "Id Central Origen CMg Cardones 220":"int32",
                                        "Id Central Origen CMg Pan de Azucar 220":"int32",
                                        "Id Central Origen CMg Quillota 220":"int32",
                                        "Id Central Origen CMg Alto Jahuel 220":"int32",
                                        "Id Central Origen CMg Charrua 220":"int32",
                                        "Id Central Origen CMg Puerto Montt 220":"int32",
                                        "Id Central Origen CMg Las Palmas 220":"int32",
                                        }
    
    diccionario["rio_calc_cmg_15min"]={"Id Record":"int64",
                                        "Id Fecha":"int32",
                                        "Hora":"int32",
                                        "CMg [USD/MWh]":"float32",
                                        "Id Barra Origen Nemotecnico":"float32",
                                        }
    
    diccionario["programa_gen"]={"Id Record":"int64",
                                 "Id YYYYMM":"int32",
                                 "Id Fecha":"int32",
                                 "Hora":"int32",
                                 "Generacion Bruta [MWh]":"float32",
                                 "CPF Subida [MW]":"float32",
                                 "CPF Bajada [MW]":"float32",
                                 "CSF Subida [MW]":"float32",
                                 "CSF Bajada [MW]":"float32",
                                 "CTF Subida [MW]":"float32",
                                 "CTF Bajada [MW]":"float32",
                                 "Id Central Origen Programa":"int32",
                                        }
    
    diccionario["programa_tco"]={"Id Record":"int64",
                                        "Id Fecha":"int32",
                                        "Bloque":"int32",
                                        "CMg [USD/MWh]":"float32",
                                        "Id Central Origen Programa":"int32",
                                        }
    
    diccionario["programa_fp"]={"Id Record":"int64",
                                        "Id Fecha":"int32",
                                        "Hora":"int32",
                                        "FP":"float32",
                                        "Id Barra Origen Programa":"int32",
                                        }
    
    diccionario["programa_gen_dia"]={"Id Record":"int64",
                                        "Id Fecha":"int32",
                                        "Aporte Porcentual Subida 5Min":"float32",
                                        "Aporte Porcentual 10seg":"float32",
                                        "Aporte Porcentual Bajada 5Min":"float32",
                                        "Aporte Porcentual Subida 10Seg":"float32",
                                        "Aporte Porcentual Bajada 10Seg":"float32",
                                        "CVNC [USD/MWh]":"float32",
                                        "Partida Frio Costo [USD]":"float32",
                                        "CVC [USD/MWh]":"float32",
                                        "Costo Combustible":"float32",
                                        "Costo Medio Minimo Tecnico [USD/MWh]":"float32",
                                        "Costo Parada [USD]":"float32",
                                        "Partida Caliente Tiempo Fuera Servicio Min [h]":"float32",
                                        "Partida Caliente Tiempo Fuera Servicio Max [h]":"float32",
                                        "Partida Tibia Tiempo Fuera Servicio Min [h]":"float32",
                                        "Partida Tibia Costo [USD]":"float32",
                                        "Partida Caliente Costo [USD]":"float32",
                                        "Tiempo Partida [h]":"float32",
                                        "Partida Caliente Costo [USD]":"float32",
                                        "Partida Tibia Tiempo Fuera Servicio Max [h]":"float32"
                                        }
    
    diccionario["programa_flujo"]={"Id Record":"int64",
                                        "Id Fecha":"int32",
                                        "Id YYYYMM":"int32",
                                        "Hora":"int32",
                                        "Flujo [MW]":"float32",
                                        "Id Linea Origen Programa":"int32",
                                        }
    
    diccionario["programa_cmg"]={"Id Record":"int64",
                                        "Id Fecha":"int32",
                                        "Id YYYYMM":"int32",
                                        "Hora":"int32",
                                        "CMg [USD/MWh]":"float32",
                                        "Id Barra Origen Programa":"int32",
                                        }
    
    diccionario["programa_cota"]={"Id Record":"int64",
                                        "Id Fecha":"int32",
                                        "Hora":"int32",
                                        "Cota [msnm]":"float32",
                                        "Id Embalse Origen Programa":"int32",
                                        }
    
    diccionario["opreal_gen"]={"Id Record":"int64",
                                        "Id YYYYMM":"int32",
                                        "Id Fecha":"int32",
                                        "Hora":"int32",
                                        "Generacion Bruta [MWh]":"float32",
                                        "Id Central Origen Opreal":"int32",
                                        }
    
    diccionario["opreal_cota"]={"Id Record":"int64",
                                        "Id YYYYMM":"int32",
                                        "Id Fecha":"int32",
                                        "Hora":"int32",
                                        "Cota [m]":"float32",
                                        "Id Embalse Origen Opreal":"int32",
                                        }
    
    diccionario["opreal_caudal"]={"Id Record":"int64",
                                        "Id YYYYMM":"int32",
                                        "Id Fecha":"int32",
                                        "Hora":"int32",
                                        "Caudal [m3/s]":"float32",
                                        "Id Agua Caida Origen Opreal":"int32",
                                        }
    
    diccionario["opreal_agua_caida"]={"Id Record":"int64",
                                        "Id YYYYMM":"int32",
                                        "Id Fecha":"int32",
                                        "Hora":"int32",
                                        "Agua Caida [mm]":"float32",
                                        "Id Caudal Origen Opreal":"int32"
                                     }
    
    diccionario["gendia_cmg_programa_1h"]={"Id Record":"int64",
                                        "Id YYYYMM":"int32",
                                        "Id Fecha":"int32",
                                        "Hora":"int32",
                                        "Id Barra Origen Programa":"int32",
                                        "Id Barra":"int32",
                                        "Tipo":"str",
                                        "CMg [USD/MWh]":"float32"}
    
    diccionario["gendia_cmg_web_coordinador_15min"]={"Id Record":"int64",
                                     "Id YYYYMM":"int32",
                                     "Id Fecha":"int32",
                                     "Hora":"int32",
                                     "Cuarto de Hora":"int32",
                                     "Id Barra Origen Sipub":"int32",
                                     "Id Barra Origen Nemotecnico":"int32",
                                     "Tipo":"str",
                                     "Id Barra":"int32",
                                     "CMg [USD/MWh]":"float32",
                                     "CMg [$/KWh]":"float32"}
    
    diccionario["gendia_gen_opreal_1h"]={"Id Record":"int64",
                                     "Id Fecha":"int32",
                                     "Id YYYYMM":"int32",
                                     "Hora":"int32",
                                     "Id Central Origen Opreal":"int32",
                                     "Id Central":"int32",
                                     "Energia Bruta [MWh]":"float32",
                                     "Energia Neta [MWh]":"float32",
                                     "CMg [USD/MWh]":"float32",
                                     "Inyeccion [MM USD]":"float32",
                                     "CVC [MM USD]":"float32",
                                     "CVNC [MM USD]":"float32",
                                     "Margen [MM USD]":"float32",
                                     "Id Filtro":"int32",
                                     "Costo del Agua [MM USD]":"float32",
                                     "Sobrecosto [MM USD]":"float32",
                                     "Costo de Oportunidad [MM USD]	":"float32"}
    
    diccionario["gendia_gen_programa_1h"]={"Id Record":"int64",
                                     "Id Fecha":"int32",
                                     "Id YYYYMM":"int32",
                                     "Hora":"int32",
                                     "Id Central Origen Programa":"int32",
                                     "Id Central":"int32",
                                     "Energia Bruta [MWh]":"float32",
                                     "Energia Neta [MWh]":"float32",
                                     "CMg [USD/MWh]":"float32",
                                     "CVC [USD/MWh]":"float32",
                                     "CVNC [USD/MWh]":"float32",
                                     "Inyeccion [MM USD]":"float32",
                                     "Costo [MM USD]":"float32",
                                     "Margen [MM USD]":"float32"}
    


    if (carpeta in diccionario.keys()):
        for columna in list(diccionario[carpeta].keys()):
            if (columna in df_datos):
                if diccionario[carpeta][columna] in ["int32","int64","float32","float64"]:
                    df_datos[columna]=pd.to_numeric(df_datos[columna])
                df_datos[columna]=df_datos[columna].astype(diccionario[carpeta][columna])
                
    return df_datos


# In[ ]:





# In[ ]:





# In[ ]:


def first_load_from_parquet(relative_filepath,path_carga, tabla, incluye_obsoleto, script,column_with_id):
    exito=True
    df_local=pd.DataFrame()
        
    if incluye_obsoleto:
        config2 = configparser.ConfigParser()
        config2.read(path_id_record+'/'+relative_filepath.split("/")[-1]+'.ini')
        id_record_local=int(config2.get("ids","record"))

    
        arr = os.listdir(path_carga+'/'+relative_filepath)
        db = sqlalchemy.create_engine(config.get("ids","sql_conn"))
        conn=db.connect()
        tran=conn.begin()
        try:
            df_gen=pd.DataFrame.from_dict({"relative_filepath":[relative_filepath],"email":[config.get("ids","my_email")],"script":[script],"last_record":[id_record_local]})
            for nombreArchivo in arr:
                print(nombreArchivo)
                df_local=pd.read_parquet(path_carga+'/'+relative_filepath+'/'+nombreArchivo)
                df_local.to_sql(con=conn,schema=config.get("ids","schema"), name=tabla, if_exists='append', index=False)
            df_gen.to_sql(con=conn,schema=config.get("ids","schema"), name="general", if_exists='append', index=False)
            tran.commit()
        except Exception as inst:
            exito=False
            print(str(inst))
            tran.rollback()
        conn.close()
        db.dispose()
    else:
        db = sqlalchemy.create_engine(config.get("ids","sql_conn"))
        conn=db.connect()
        tran=conn.begin()
        df_local=pd.read_parquet(path_carga+'/'+relative_filepath)  
        df_local.to_sql(con=conn,schema=config.get("ids","schema"), name=tabla, if_exists='append', index=False)
        df_gen=pd.DataFrame.from_dict({"relative_filepath":[relative_filepath],"email":[config.get("ids","my_email")],"script":[script],"last_record":df_local[column_with_id].max()})
        df_gen.to_sql(con=conn,schema=config.get("ids","schema"), name="general", if_exists='append', index=False)
        tran.commit()

        conn.close()
        db.dispose()    
        #df_local.to_parquet(path_homologaciones+'/'+path_carga.split("/")[-1])
    return exito


# In[ ]:





# In[ ]:


def clonar(df_origen, tabla, incluye_obsoleto, columna_id_origen,sql_conn_clone,schema_clone):
    exito=True
    df_n=pd.DataFrame()
    df_o=pd.DataFrame()
    id_destino=0
    id_origen=int(df_origen.loc[[True],"last_record"])
    print("schema_clone>"+schema_clone)
    
    
    config2 = configparser.ConfigParser()
    config2.read(path_id_record+'/'+tabla+'.ini')
    id_destino=int(float(config2.get("ids","record")))

    
    print("id_destino> "+id_destino)
    if id_origen!=id_destino:    
        db = sqlalchemy.create_engine(config.get("ids","sql_conn"))
        conn=db.connect()

        df_n=pd.io.sql.read_sql("select "+tabla+".* from "+config.get("ids","schema")+".`"+ tabla + "` where "+tabla +".`"+columna_id_origen+"` <= " + str(id_origen) + "  and "+tabla +".`"+columna_id_origen+"` > " + str(id_destino)+  ";",conn)    
        if incluye_obsoleto:
            print('getting deprecated')
            df_o=pd.io.sql.read_sql("select * from "+config.get("ids","schema")+".`"+ tabla + "_obsoleto` where `"+columna_id_origen+"` <= " + str(id_origen) + "  and `"+columna_id_origen+"` > " + str(id_destino)+";",conn)
        conn.close()
        db.dispose()
        
        
        
        db2 = sqlalchemy.create_engine(sql_conn_clone)
        conn2=db2.connect()
        tran2=conn2.begin()
        try:
            if incluye_obsoleto:
                print('saving dep'+str(df_o.shape))
                conn2.execute(text("Delete FROM "+schema_clone+"."+tabla+"_obsoleto where " + columna_id_origen + " > " +str(id_destino)))
                df_o.to_sql(con=conn2,schema=schema_clone, name=tabla + "_obsoleto", if_exists='append', index=False)

            print('saving table' +str(df_n.shape))
            conn2.execute(text("Delete FROM "+schema_clone+"."+tabla+" where " + columna_id_origen + " > " + str(id_destino)))
            df_n.to_sql(con=conn2,schema=schema_clone, name=tabla, if_exists='append', index=False)

            tran2.commit()

        except Exception as inst:
            exito=False
            print(str(inst))
            tran2.rollback()
        conn2.close()
        db2.dispose()
    return exito


# In[ ]:


def actualizar_archivo_local(list_cols,idelement,max_id_local,limit_id,tabla,incluir_tabla_obsoletos,yyyymm):
    url = config.get("ids","sync_url")
    schema=config.get("ids","schema")

    
    myobj = {"schema":schema,'yyyymm':yyyymm,'access_key': "operaciones_gendia_sync","list_cols":list_cols,"idelement":idelement,"max_id_local":max_id_local,"limit_id":limit_id,"tabla":tabla,"incluir_tabla_obsoletos":incluir_tabla_obsoletos}
    x = requests.post(url, json = myobj)
    #print(str(x.text))
    return json.loads(x.text)


# In[ ]:


def actualizar_archivo_local_3306(list_cols,idelement,max_id_local,limit_id,tabla,incluir_tabla_obsoletos):
    campos=''
    df=pd.DataFrame()
    df_o=pd.DataFrame.from_dict({"Id Record":[],"Id Record Obsoleto":[],"Id Fecha":[]})

    for columna in list(list_cols):
        df[columna]=1
        campos=campos +"`" + tabla+"`.`" + columna+"` ,"
    campos=campos[:-2]

    db = sqlalchemy.create_engine(config.get("ids","sql_conn"))
    conn=db.connect()



    query="select " + campos + " from "+config.get("ids","schema")+"."+ tabla + " where `"+idelement+"` > " + str(max_id_local) + " and `" + idelement+"` <= " + str(limit_id) + ";"
    if incluir_tabla_obsoletos:
        query="select " + campos + " from "+config.get("ids","schema")+"."+ tabla + " LEFT JOIN  "+config.get("ids","schema")+".`"+ tabla + "_obsoleto` on `" +  tabla+"`.`Id Record` = `" + tabla +"_obsoleto`.`Id Record Obsoleto` where "+config.get("ids","schema")+"."+tabla+".`"+idelement + "` > " + str(max_id_local)+ " and " +tabla+".`"+ idelement +"` <= " + str(limit_id) + " and "+config.get("ids","schema")+".`" +tabla+"_obsoleto`.`Id Record Obsoleto` is null;"
        df_o=pd.io.sql.read_sql("select `Id Record`, `Id Record Obsoleto`, `YYYYMM` from "+config.get("ids","schema")+".`"+ tabla + "_obsoleto` where `Id Record Obsoleto` <= " + str(limit_id) + "  and `Id Record` > " + str(max_id_local )+";",conn)
    df=pd.io.sql.read_sql(query,conn)






    #resultado=conn.execute(query)
    #for row in resultado:
    #    fila={}
    #    for columna in list(df.columns):
    #        fila[columna]=[row[columna]]
    #    df=pd.concat([df,pd.DataFrame.from_dict(fila)])
    conn.close()
    db.dispose()
    return {"new":df,"rm":df_o}


# In[ ]:





# In[ ]:


def Sincronizar_Homologacion(df):
    for file in os.listdir(path_homologaciones):
        print(file)
        df_origen=pd.read_parquet(path_homologaciones+'/'+file)
        id_record_base_origen=int(df.loc[df['relative_filepath']==file.split(".")[0],'last_record'])

        config2 = configparser.ConfigParser()
        config2.read(path_id_record+'/'+file.split(".")[0]+'.ini')

        next_id_origen=int(float(config2.get("ids","record")))+1
        main_id=""
        for column in df_origen.columns:
            if column.startswith("Id"):
                main_id=column
        if (next_id_origen != id_record_base_origen+1):
            print("updating: " + str(next_id_origen) +" to "+ str(id_record_base_origen))
            df_origen=pd.concat([df_origen,pd.read_json(actualizar_archivo_local(list(df_origen.columns),main_id,next_id_origen-1,id_record_base_origen,file.lower().split(".")[0],False)["new"])])
            df_origen.to_parquet(path_homologaciones+"/"+file,compression='gzip', index=False)
            config3 = configparser.ConfigParser()
            config3.read(path_id_record+'/'+file.split(".")[0]+'.ini')
            config3['ids']["record"]=str(df_origen[main_id].max())
            with open(path_id_record+'/'+file.split(".")[0]+'.ini', 'w') as configfile:
                config3.write(configfile) 


# In[ ]:





# In[ ]:


def Sincronizar(path_carga,id_record_carga,prefijo,tabla,columnas,yyyymm):
    print("sinc1")
    id_record_max_local=0

    df_local=pd.DataFrame.from_records([columnas])
    df_local.columns=df_local.iloc[0,:]
    df_local=df_local.head(0)
    
    if (os.path.exists(path_carga+"/"+prefijo+str(yyyymm)+".parquet")):
        df_local=pd.read_parquet(path_carga+"/"+prefijo+str(yyyymm)+".parquet")
        id_record_max_local=int((df_local[df_local["Id Record"]==0]["Id YYYYMM"].values)[0])
        
    while(id_record_max_local<id_record_carga):
        id_record_carga_iter=min(int(id_record_max_local)+10**5,id_record_carga)
        print(id_record_carga_iter)

        x_movcen=actualizar_archivo_local(columnas,"Id Record",id_record_max_local,id_record_carga_iter,tabla,True,yyyymm)
        x_movcen_new=pd.read_json(x_movcen["new"])
        x_movcen_rm=pd.read_json(x_movcen["rm"])

        if x_movcen_new.shape[0]>0:
            print("new: "+ str(x_movcen_new.shape));
            x_movcen_new=formato_datos(x_movcen_new, tabla)
            
            #for columna in list(columnas):
            #    x_movcen_new[columna]=x_movcen_new[columna].astype(df_local.dtypes[columna])
            #if 'Id Fecha' in list(x_movcen_new.columns):
            #    x_movcen_new['YYYYMM']=x_movcen_new['Id Fecha'].astype(str).str[:6].astype(int)
            #if 'Id YYYYMM' in list(x_movcen_new.columns):
            #    for anomes in list(x_movcen_new['YYYYMM'].unique()):
            #        df_local=x_movcen_new.head(0)
            #        if (os.path.exists(path_carga+"/"+prefijo+str(anomes)+".parquet")):
            #            df_local=pd.read_parquet(path_carga+"/"+prefijo+str(anomes)+".parquet")
            #        pd.concat([x_movcen_new[x_movcen_new['YYYYMM']==anomes],df_local])[columnas].to_parquet(path_carga+"/"+prefijo+str(anomes)+".parquet",compression='gzip', index=False)
            #else:
            #    df_local=x_movcen_new.head(0)
            #    if (os.path.exists(path_carga+"/"+prefijo+".parquet")):
            #        df_local=pd.read_parquet(path_carga+"/"+prefijo+".parquet")
            df_local=pd.concat([x_movcen_new,df_local])[columnas]#.to_parquet(path_carga+"/"+prefijo+".parquet",compression='gzip', index=False)                
        if x_movcen_rm.shape[0]>0:
            print("remove: "+ str(x_movcen_rm.shape));
            #if 'YYYYMM' in list(x_movcen_rm.columns):
            #    for anomes in list(x_movcen_rm['YYYYMM'].unique()):
            #        if (os.path.exists(path_carga+"/"+prefijo+str(anomes)+".parquet")):
            #            df_local=pd.read_parquet(path_carga+"/"+prefijo+str(anomes)+".parquet")
            #            print(str(df_local.shape));
            lista_val=list((x_movcen_rm[x_movcen_rm["Id YYYYMM"]==yyyymm])["Id Record Obsoleto"].astype(int).unique())
            df_local=df_local[df_local["Id Record"].astype(int).isin(lista_val)==False][columnas]
            #df_local.to_parquet(path_carga+"/"+prefijo+str(anomes)+".parquet",compression='gzip', index=False)
            #print(str(df_local.shape));
            #else:
            #    if (os.path.exists(path_carga+"/"+prefijo+".parquet")):
            #        df_local=pd.read_parquet(path_carga+"/"+prefijo+".parquet")
            #        df_local[(df_local["Id Record"].isin(list(x_movcen_rm["Id Record Obsoleto"].unique())))==False][columnas].to_parquet(path_carga+"/"+prefijo+".parquet",compression='gzip', index=False)
        #if (os.path.exists(path_carga+"/"+prefijo+str(yyyymm)+".parquet")):
        #    df_local=pd.read_parquet(path_carga+"/"+prefijo+str(yyyymm)+".parquet")
        df_local=df_local[df_local["Id Record"]>0]
        if (df_local.shape[0]>0):
            df_local_max=df_local.head(1).copy()
            for columna in list(df_local.columns):
                if columna != "Id YYYYMM": #and columna != "Condicion Embalse" and columna != "Neomante":  
                    df_local_max.loc[0,columna]=0
                    #elif columna =="Condicion Embalse":
                    #    df_local_max.loc[0,columna]="-"
                    #elif columna =="Neomante":
                    #    df_local_max.loc[0,columna]=""
                else:
                    df_local_max.loc[0,columna]=id_record_carga_iter
            formato_datos(df_local_max, tabla)
            print("concat")
            df_local=df_local[df_local["Id Record"]>0]
            df_local=pd.concat([df_local_max,df_local])

            df_local=formato_datos(df_local, tabla)
            df_local.to_parquet(path_carga+"/"+prefijo+str(yyyymm)+".parquet",compression='gzip', index=False)
            
        id_record_max_local=id_record_carga_iter
        print("id_record_max_local:" + str(id_record_max_local))


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:


def procesa_cambios_sin_fecha(df_graba,path_graba,prefijo_archivo,tabla_graba,relative_filepath,columna_id,mantener_sin_match):
    df_graba=df_graba.drop_duplicates()

    id_record_base_graba=int(config2.get("ids","record"))

    
    columnas_compara=list(df_graba.columns)
    df_local=df_graba.head(0)
    df_local_base=df_graba.head(0)

    if (os.path.exists(path_graba+"/"+prefijo_archivo+".parquet")):
        df_local=pd.read_parquet(path_graba+"/"+prefijo_archivo+".parquet")
        if mantener_sin_match:
            df_local_base=df_local[df_local[columna_id].isin(list(df_graba[columna_id].unique()))==False]
            df_local=df_local[df_local[columna_id].isin(list(df_graba[columna_id].unique()))]
        
    df_update=df_local.merge(df_graba,on=columnas_compara,indicator=True,how='outer')
    df_update["Id Eliminacion"]=0

    next_id_record=id_record_base_graba+1
    
    
    df_update.loc[df_update.duplicated(subset=(columnas_compara)),'_merge']='left_only'
    if len(df_update[df_update['_merge']=='left_only'])>0:
        df_update.loc[df_update['_merge']=='left_only','Id Eliminacion']=range(next_id_record, next_id_record+len(df_update[df_update['_merge']=='left_only']))
        next_id_record=next_id_record+len(df_update[df_update['_merge']=='left_only'])
    if len(df_update[df_update['_merge']=='right_only'])>0:
        print('se agregaron registros')
        df_update.loc[df_update['_merge']=='right_only','Id Record']=range(next_id_record, next_id_record+len(df_update[df_update['_merge']=='right_only']))
        next_id_record=next_id_record+len(df_update[df_update['_merge']=='right_only'])


    df_nuevos=df_update[df_update['Id Record']>id_record_base_graba]
    df_nuevos=df_nuevos[columnas_compara+['Id Record']]
    df_eliminados=df_update[df_update['Id Eliminacion']>id_record_base_graba]
    
    df_eliminados=df_eliminados[['Id Record','Id Eliminacion']]
    df_eliminados=df_eliminados.rename(columns={"Id Record":"Id Record Obsoleto"})
    df_eliminados=df_eliminados.rename(columns={"Id Eliminacion":"Id Record"})
    id_record_base_graba=next_id_record-1

    if (df_nuevos.shape[0]+df_eliminados.shape[0])>0:
        #df_subset_agua=df[df["relative_filepath"]==relative_filepath]
        #df_subset_agua["last_record"]=id_record_base_graba
        #df_subset_agua=df_subset_agua[["relative_filepath", "last_record"]]

        if actualizar_bd([df_nuevos,df_eliminados],[tabla_graba,tabla_graba+"_obsoleto"],['',''],id_record_base_graba,path_graba.split("/")[-1]):
            print("p71")

            #df_update=df_update[df_update["Id Eliminacion"]==0][columnas_compara+['Id Record']]
            #pd.concat([df_local_base,df_update]).to_parquet(path_graba+"/"+prefijo_archivo+".parquet",compression='gzip', index=False)


# In[ ]:





# In[ ]:





# In[ ]:


def procesa_cambios_con_fecha(df_graba,path_graba,prefijo_archivo,tabla_graba,relative_filepath,AnoMes,id_record_base_graba):
    df_graba=df_graba.drop_duplicates()
    df_graba= formato_datos(df_graba, tabla_graba)
    print(AnoMes)
    columnas_compara=list(df_graba.columns)

    df_local=df_graba.head(0)
    #df_local_base=df_graba.head(0)

    if (os.path.exists(path_graba+"/"+prefijo_archivo+str(AnoMes)+".parquet")):
        df_local=pd.read_parquet(path_graba+"/"+prefijo_archivo+str(AnoMes)+".parquet")
        if "Id Fecha" in list(df_graba.columns):
            df_local["Id Fecha"]=df_local["Id Fecha"].astype(int)
            df_local= formato_datos(df_local, tabla_graba)
            df_graba["Id Fecha"]=df_graba["Id Fecha"].astype(int)
            if ("Version" in list(df_graba.columns)):
                df_local["Id Fecha"]=df_local["Id Fecha"].astype(int)+df_local["Version"]*100000000
                df_graba["Id Fecha"]=df_graba["Id Fecha"].astype(int)+df_graba["Version"]*100000000
            #df_local_base=df_local[df_local["Id Fecha"].isin(list(df_graba["Id Fecha"].unique()))==False]
            df_local=df_local[df_local["Id Fecha"].isin(list(df_graba["Id Fecha"].unique()))]
            if ("Version" in list(df_graba.columns)):
                df_local["Id Fecha"]=df_local["Id Fecha"].astype(int)-df_local["Version"]*100000000
                df_graba["Id Fecha"]=df_graba["Id Fecha"].astype(int)-df_graba["Version"]*100000000
        
    df_update=df_local.merge(df_graba,on=columnas_compara,indicator=True,how='outer')
    df_update["Id Eliminacion"]=0
    next_id_record=id_record_base_graba+1
    
    df_update.loc[df_update.duplicated(subset=(columnas_compara)),'_merge']='left_only'
    if len(df_update[df_update['_merge']=='left_only'])>0:
        df_update.loc[df_update['_merge']=='left_only','Id Eliminacion']=range(next_id_record, next_id_record+len(df_update[df_update['_merge']=='left_only']))
        next_id_record=next_id_record+len(df_update[df_update['_merge']=='left_only'])
    if len(df_update[df_update['_merge']=='right_only'])>0:
        print('se agregaron registros')
        df_update.loc[df_update['_merge']=='right_only','Id Record']=range(next_id_record, next_id_record+len(df_update[df_update['_merge']=='right_only']))
        next_id_record=next_id_record+len(df_update[df_update['_merge']=='right_only'])

    df_nuevos=df_update[df_update['Id Record']>id_record_base_graba]
    df_nuevos=df_nuevos[columnas_compara+['Id Record']]
    df_eliminados=df_update[df_update['Id Eliminacion']>id_record_base_graba]
    ##if ("YYYYMM" in list(df_graba.columns)) == False:
    if df_eliminados.shape[0]>0:
        df_eliminados["Id YYYYMM"]=df_eliminados["Id Fecha"].astype(str).str[:6].astype(int)
        df_eliminados=df_eliminados[['Id Record','Id Eliminacion','Id YYYYMM']]
        df_eliminados=df_eliminados.rename(columns={"Id Record":"Id Record Obsoleto"})
        df_eliminados=df_eliminados.rename(columns={"Id Eliminacion":"Id Record"})
    id_record_base_graba=next_id_record-1

    print("p1")
    if (df_nuevos.shape[0]+df_eliminados.shape[0])>0:

        #print("p2")
        #df_subset_agua=df[df["relative_filepath"]==relative_filepath]
        #print("p3")
        #df_subset_agua["last_record"]=id_record_base_graba
        #df_subset_agua=df_subset_agua[["relative_filepath", "last_record"]]
        print("p4")
        if actualizar_bd([df_nuevos,df_eliminados],[tabla_graba,tabla_graba+"_obsoleto"],['',''],id_record_base_graba,path_graba.split("/")[-1]):
            #print("p5")
            #df_update=df_update[df_update["Id Eliminacion"]==0][columnas_compara+['Id Record']]
            #print("p6")
            #pd.concat([df_local_base,df_update]).to_parquet(path_graba+"/"+prefijo_archivo+str(AnoMes)+".parquet",compression='gzip', index=False)
            print("p7")


# In[ ]:





# In[ ]:


def actualizar_bd(list_df_nuevos,list_tabla,list_delete,id_record_new,path_graba):
    exito=True
    schema=config.get("ids","schema")
    
    print("=x1")
    db = sqlalchemy.create_engine(config.get("ids","sql_conn"))
    conn=db.connect()
    print("=x2")
    tran=conn.begin()
    try:
        for k in range(0,len(list_df_nuevos)):
            print(list_tabla[k])    
            if (list_tabla[k]!="general"):
                if (list_delete[k]!=''):
                    conn.execute(text("Delete FROM "+schema+"."+list_tabla[k]+" where " + list_delete[k]))
                if list_df_nuevos[k].shape[0]>0:
                    print(list_tabla[k]+": "+str(list_df_nuevos[k].shape[0]))
                    cuenta=0
                    while(list_df_nuevos[k][cuenta:(cuenta+10**5)].shape[0]>0):
                        list_df_nuevos[k][cuenta:(cuenta+10**5)].to_sql(con=conn,schema=schema, name=list_tabla[k], if_exists='append', index=False)
                        cuenta=cuenta+10**5
        tran.commit()
        #print("1"+path_id_record+'/'+path_graba+'.ini')
        #config2 = configparser.ConfigParser()
        #config2.read(path_id_record+'/'+path_graba+'.ini')
        #config2['ids']["record"]=str(id_record_new)
        #with open(path_id_record+'/'+path_graba+'.ini', 'w') as configfile:
        #    config2.write(configfile)
        #print("xxx")
    except Exception as inst:
        exito=False
        print(str(inst))
        tran.rollback()
    conn.close()
    db.dispose()
    return exito


# In[ ]:


def get_max_id_database(tabla,tiene_yyyymm,columna):
    schema=config.get("ids","schema")
        
    url = config.get("ids","sync_url")
    myobj = {'columna':columna,'sql_conn':config.get("ids","sql_conn"),'access_key': "operaciones_gendia_v3_get_last_id",   'schema':schema, 'tabla': tabla,'tiene_yyyymm':tiene_yyyymm}
    x = requests.post(url, json = myobj)
    
    df=pd.DataFrame.from_dict(json.loads(x.text)).reset_index()
    df=df[df["Id Record"].isna()==False]
    return df


# In[ ]:


def get_max_id_df(df,yyyymm):
    id = 0
    df_temp=df.copy()
    if  yyyymm!="":
        df_temp=df_temp[df_temp["Id YYYYMM"]==yyyymm]
    if df_temp.shape[0]>0:
        id=int(df_temp["Id Record"])
    return id


# 
# 
