# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 22:35:51 2021

@author: Carlos Archaga 
"""

import tkinter
import os
from tkinter import *
from tkinter import messagebox as ms 
from tkinter import filedialog
import os.path
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.backends.backend_tkagg import  FigureCanvasTkAgg
import snappy
from snappy import Product
from snappy import ProductIO
from snappy import ProductUtils
from snappy import WKTReader
from snappy import HashMap
from snappy import GPF
# Para leer shapefiles
import shapefile
import pygeoif

ventana = Tk()
ventana.geometry("900x900")
ventana.title("Programa calculo de zonas inundadas snap")
ventana.config(bg="Blue")
ventana.resizable(0,0)
#funcione leer archivo zip
def open_file():
    Entrada.delete(1,END)
    filename = filedialog.askopenfilename(title="Selecciona una imagen zip",filetypes=(('Arhivos comprimido','.zip'),))
    Entrada.insert(END,filename)
    return filename
#etiqueta
Label1 = Label(ventana,text="programa calculo de zonas inundadas a partir de sentinel1")
Label1.pack()
Label1.config(bg="black",fg="white",cursor="star",font=("verdana",8))
#etiqueta2
Label2 = Label(ventana,text="Seleccione la imagen a utilizar en formato .zip")
Label2.pack()
Label2.config(bg="black",fg="white",cursor="star",font=("verdana",8))
#primer boton
boton1 = Button(ventana,text="Selecciona tu imagen: ",command=open_file)
boton1.pack()
#Entrada de la imagen
Entrada = Entry(ventana)
Entrada.pack()
Entrada.config(font=("verdana",9))   
#funcion para leer archivo shapefile
def open_file2():
    Entrada2.delete(1,END)
    filename = filedialog.askopenfilename(initialdir="/", title="Selecciona un archivo shp", filetypes=(("shp files", "*.shp"),("all files", "*.*")))
    Entrada2.insert(END,filename)
    return filename
#etiqueta 3
Label3 = Label(ventana,text="Selecciona un archivo shapefile para delimitar: ")
Label3.pack()
Label3.config(bg="black",fg="white",cursor="star",font=("verdana",8))

#Boton que busque el shapefile
boton2 = Button(ventana,text="Selecciona tu archivo shp: ",command=open_file2)
boton2.pack()
#entrada de la direccion 
Entrada2 = Entry(ventana)
Entrada2.pack()
Entrada2.config(font=("verdana",8))

####3 correccion de  la imagen ######
####LEER LOS DATOS DE LA IMAGEN
#Cargar imagenes
open_data = open_file() #funcion para almacenar la ruta
data = open_data 
product = ProductIO.readProduct(data)  #funcion para crear la imagen cruda
##Aplicar correccion orbital
def correcion_orbital():
    global product
    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    parameters.put('orbitType', 'Sentinel Precise (Auto Download)')
    parameters.put('polyDegree', '3')
    parameters.put('continueOnFail', 'false')
    apply_orbit_file = GPF.createProduct('Apply-Orbit-File', parameters, product)
    return apply_orbit_file
orbital = correcion_orbital() #variable para almacenar la imagen corregida de manera orbital 
### hacer el corte de la imagen 
path_shapefile = open_file2() 
shp = shapefile.Reader(path_shapefile)
g=[] #lista que almacenara las coordenadas obtenidad de los bounds del shapefile
for s in shp.shapes():
    g.append(pygeoif.geometry.as_shape(s))
m = pygeoif.MultiPoint(g)
wkt = str(m.wkt).replace("MULTIPOINT", "POLYGON(") + ")"
#Usar el shapefile para cortar la imagen
SubsetOp = snappy.jpy.get_type('org.esa.snap.core.gpf.common.SubsetOp')
bounding_wkt = wkt
geometry = WKTReader().read(bounding_wkt)
HashMap = snappy.jpy.get_type('java.util.HashMap')
GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
parameters = HashMap()
parameters.put('copyMetadata', True)
parameters.put('geoRegion', geometry)
product_subset = snappy.GPF.createProduct('Subset', parameters, orbital)
##Aplicar la calibracion de la imagen
def calibracion():
    global product_subset
    parameters = HashMap()
    parameters.put('outputSigmaBand', True)
    parameters.put('sourceBands', 'Intensity_VV')
    parameters.put('selectedPolarisations', "VV")
    parameters.put('outputImageScaleInDb', False)
    product_calibrated = GPF.createProduct("Calibration", parameters, product_subset)
    return product_calibrated
#imagen_calibrada = calibracion()
##Aplicar el filtro Speckle
def Speckle():
    imagen_calibrada = calibracion()
    filterSizeY = '3'
    filterSizeX = '3'
    parameters = HashMap()
    parameters.put('sourceBands', 'Sigma0_VV')
    parameters.put('filter', 'Lee')
    parameters.put('filterSizeX', filterSizeX)
    parameters.put('filterSizeY', filterSizeY)
    parameters.put('dampingFactor', '2')
    parameters.put('estimateENL', 'true')
    parameters.put('enl', '1.0')
    parameters.put('numLooksStr', '1')
    parameters.put('targetWindowSizeStr', '3x3')
    parameters.put('sigmaStr', '0.9')
    parameters.put('anSize', '50')
    speckle_filter = snappy.GPF.createProduct('Speckle-Filter', parameters, imagen_calibrada)
    return speckle_filter
#funcion para indicar al usuario que esta procesando lax imagen
def mensaje():
    messenger = ms.showinfo("Informacion","La imagen este procesando espera que se aplique los procesos")
    return messenger
##Aplicar la correccion del terremo
def terreno():
    filtro_speckle = Speckle()
    parameters = HashMap()
    parameters.put('demName', 'SRTM 3Sec')
    parameters.put('pixelSpacingInMeter', 10.0)
    parameters.put('sourceBands', 'Sigma0_VV')
    speckle_filter_tc = GPF.createProduct("Terrain-Correction", parameters, filtro_speckle)
    return speckle_filter_tc
#etiqueta 4
#etiqueta4
Label4 = Label(ventana,text="presione aqui para procesar la imagen: ")
Label4.pack()
Label4.config(bg="black",fg="white",cursor="star",font=("verdana",8))
#boton para realizar operacion
boton3 = Button(ventana,text="Procesar imagen sentinel 1",command=mensaje)
boton3.pack()
boton3 = Button(ventana,text="Procesar imagen sentinel 1",command=terreno)
boton3.pack() 
print("Vamos bien")
#funcion que almacena el parametro
#funcion de ploteo de imagenes 
def plotBand(product, band, vmin, vmax):
    band = product.getBand(band)
    w = band.getRasterWidth()
    h = band.getRasterHeight()
    print(w, h)
    band_data = np.zeros(w * h, np.float32)
    band.readPixels(0, 0, w, h, band_data)
    band_data.shape = h, w
    width = 12
    height = 12
    plt.figure(figsize=(width, height))
    imgplot = plt.imshow(band_data, cmap=plt.cm.binary, vmin=vmin, vmax=vmax)
    return imgplot
#ploteo_terreno = plotBand(correcion_terreno,'Sigma0_VV', 0, 0.1)
#print(type(ploteo_terreno))

    global ploteo_terreno
    return ploteo_terreno
#etiqueta 5
Label5 = Label(ventana,text="Definir el umbral para la mascara de agua: ")
Label5.pack()
Label5.config(bg="black",fg="white",cursor="star",font=("verdana",8))
#aplicar mascara binaria 
filtro_poner = 1.77E-2
#entrada para definir el umbral
Entrada3 = Entry(ventana)
Entrada3.pack()
Entrada3.config(font=("verdana",15),justify='center') 
#print(type(entrada3))
#filtro_binario = float(Entrada3.get()) 
def binaria():
    correcion_terreno = terreno()
    entrada3 = Entrada3.get()
    parameters = HashMap()
    BandDescriptor = snappy.jpy.get_type('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor')
    targetBand = BandDescriptor()
    targetBand.name = 'Sigma0_VV_Flooded'
    targetBand.type = 'uint8'
    targetBand.expression = f'(Sigma0_VV < {entrada3}) ? 1 : 0'
    targetBands = snappy.jpy.array('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor', 1)
    targetBands[0] = targetBand
    parameters.put('targetBands', targetBands)
    flood_mask = GPF.createProduct('BandMaths', parameters, correcion_terreno)
    return flood_mask
#boton para realizar operacion
boton4 = Button(ventana,text="presiona aqui para generar umbral de agua",command=binaria)
boton4.pack()
#Crear imagen geotif a partir de loa imagen 
direccion = data.split('S1A')[0]
def crear_imagen():
    binario_filtro = binaria()
    global direccion
    imagen_final = ProductIO.writeProduct(binario_filtro, '{}/Raster_agua'.format(direccion), 'GeoTIFF')
    return imagen_final     
Label6 = Label(ventana,text=" Crear imagen Geptiff de la mascara")
Label6.pack()
Label6.config(bg="black",fg="white",cursor="star",font=("verdana",8))
#boton para crear la imagen 
boton5 = Button(ventana,text="presiona aqui para generar la imagen",command=crear_imagen)
boton5.pack()
def mensaje_final():
    mensaje_f = ms.showinfo("Atencion","Ya se proceso revisa tu carpeta la imagen esta guardada")
    return mensaje_f
boton6 = Button(ventana,text="Presion aqui informacion imagen",command = mensaje_final)
boton6.pack()
ventana.mainloop()

