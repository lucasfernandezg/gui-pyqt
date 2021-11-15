import sys
import os.path
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QMessageBox, QFileDialog)
from PyQt5.QtCore import *
from PyQt5.Qt import Qt
from PyQt5.QtGui import *
import xlsxwriter
import numpy as np
import pandas as pd
import xlrd
from TestGUI import Ui_Form
from mystylesheet import (stylesheet1, stylesheet2)
import matplotlib


####### Clase MAIN ######
class MainWindow(QMainWindow, Ui_Form, QWidget):
    rightClicked = pyqtSignal()
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowTitle("Medicion y Calculo de Indice de Reduccion Sonora")



        self.CalculateButton.installEventFilter(self)
        # Explicacion
        self.Consola.setText("Al iniciar esta aplicación por primera vez se crea un archivo llamado 'Materiales.xlsx' donde se guardan los datos de cada material. Si se desea agrandar la lista, solo agregue los nuevos materiales en el excel y reinicie la app.\n-NO cambie el nombre del excel.\n-NO cambie el nombre de las columnas ni la ubicacion de la tabla (que arranque en A1,1).'")
        # Contador para saber clean() el graph.
        self.counter = 0
        # Data Materiales de base
        self.excel = {
        "Material":["Densidad","Módulo de Young","Factor de pérdidas","Módulo Poisson",],
        "Acero":["7700","195000000000","0.0001","0.3"],
        "Aluminio":["2700","71000000000","0.001","0.15"],
        "Bronce":["8500","8500","0.01","0.35"],
        "Cobre":["8915","127000000000","0.01","0.34"],
        "Contrachapado":["600","8300000000","0.05","0.000000001"],
        "Hierro":["7700","195000000000","0.0001","0.15"],
        "Hormigón":["2400","30000000000","0.05","0.2"],
        "Hormigón Ladrillo":["900","4800000000","0.05","0.12"],
        "Ladrillo":["2100","25000000000","0.01","0.15"],
        "Madera":["650","12000000000","0.01","0.15"],
        "Neopreno":["1200","100000000","0.1","0.49"],
        "Plomo":["11300","17000000000","0.0005","0.15"],
        "Vidrio":["2500","68000000000","0.02","0.23"],
        "PYL":["800","2000000000","0.006","0.24"],
        }



        #### Importamos o creamos data Materiales del excel ####
        if os.path.isfile('Materiales.xlsx'):
            self.df = pd.read_excel("Materiales.xlsx")
        else:
            self.CrearExcel()
            self.df = pd.read_excel("Materiales.xlsx")
        self.df.to_csv('csvfile.csv', encoding='utf-8')
        self.df = pd.read_csv("csvfile.csv", encoding='utf-8')
        self.comboitems = {
        "Material":list(self.df["Material"].values),
        }
        #ComboBox con Materiales Importados o creados
        self.comboBox.addItems(list(self.comboitems.values())[0])
        #Agregamos modo Usuario
        self.comboBox.addItems(["Usuario"])
        #Funcion que se ejecuta cuando elijo material
        self.comboBox.currentIndexChanged.connect(self.what)
        #Boton Asignar
        self.AsignarButton.setEnabled(False)
        # Line Edits de los parametros de material
        self.lineEditFactorP.setReadOnly(True)
        self.lineEditModuloP.setReadOnly(True)
        self.lineEditModuloY.setReadOnly(True)
        self.lineEditDensidad.setReadOnly(True)

        #Cuando cambio Parametros material a mano (solo cuando modo usuario)
        self.AsignarButton.clicked.connect(self.AsignarMP)
        self.AsignarButton.clicked.connect(self.AsignarMY)
        self.AsignarButton.clicked.connect(self.AsignarFP)
        self.AsignarButton.clicked.connect(self.AsignarD)


        #Boton de calculo y graficado, y exportar
        self.CalculateButton.clicked.connect(self.Calculo)
        self.ExportButton.clicked.connect(self.Exportar)

        self.ftercio = [20,25,31.5,40,50,63,80,100,125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000,10000,12500,16000,20000]
        self.foct = [31.5,63,125,250,500,1000,2000,4000,8000,16000]

        #Dictionary a usar para data final
        self.Resultados = {
        "Frecuencia":[20,25,31.5,40,50,63,80,100,125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000,10000,12500,16000,20000],
        "Panel Simple":[],
        "Sharp":[],
        "Davy":[],
        "ISO 12354-1":[]
        }



    ###### TP1 #####
    #### Si modo usario, o no modo usuario ####
    def what(self):
        if self.comboBox.currentText() == "Usuario":
            self.AsignarButton.setEnabled(True)
            self.lineEditFactorP.setReadOnly(False)
            self.lineEditModuloP.setReadOnly(False)
            self.lineEditModuloY.setReadOnly(False)
            self.lineEditDensidad.setReadOnly(False)
            self.lineEditFactorP.clear()
            self.lineEditModuloP.clear()
            self.lineEditModuloY.clear()
            self.lineEditDensidad.clear()
            self.Consola.setText("Para asignar los valores ingresados clickear 'Asignar' antes de 'Calcular'.")
        else:
            self.AsignarButton.setEnabled(False)
            self.lineEditFactorP.setReadOnly(True)
            self.lineEditModuloP.setReadOnly(True)
            self.lineEditModuloY.setReadOnly(True)
            self.lineEditDensidad.setReadOnly(True)
            self.Act()
    ########

    ## Para guardar file
    # def getfiles(self):
    #     fileName, _ = QFileDialog.getSaveFileName(self, 'Single File', QDir.rootPath() , '*.xlsm')

    ##### Dialogo dependiendo el tipo de error (VER CheckError)
    def Error(self,tipo):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Detectamos un error!")
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QMessageBox.Ok)
        if tipo == 0:
            msg.setDetailedText("Rompiste la realidad. Algun parametro ingresado es menor a cero!")
        elif tipo == 1:
            msg.setDetailedText("Ya estamos grandes... los parametros tienen que ser números.")
        elif tipo == 2:
            msg.setDetailedText("Parametros vacíos Willis. Puede que te hayas olvidado de tocar 'asignar' si estas en modo 'Usuario'.\nJaque Mate!")
        elif tipo == 3:
            msg.setDetailedText("La Frecuencia Critica quedó arriba de 20kHz a partir de los parametros dados. En un caso real, eso no sucede amigo.\nFrecuencia Critica: "+str(self.fc))
        msg.exec_()


    #### Decide que tipo de error tengo y luego Error(tipo)
    def CheckError(self,val):
        try:
            a = float(val)
            if val:
                if a > 0:
                    return True
                else:
                    self.Error(0) #menor a 0
                    return False
            # else:
            #     self.Error(2)
            #     return False
        except (ValueError,TypeError):
            self.Error(1) #No es numero
            return False
    ##########


    ############## PRINCIPAL (Hace todos los calculos) ################
    def Calculo(self):
        #Fijarnos que valores sean numeros y positivos: CheckError().
        if self.radioButton3.isChecked():
            self.Resultados["Frecuencia"] = self.ftercio
        else:
            self.Resultados["Frecuencia"] = self.foct

        try:
            if self.CheckError(self.ModuloP) and self.CheckError(self.ModuloY) and self.CheckError(self.FactorP) and self.CheckError(self.Densidad) and self.CheckError(self.lineEditAncho.text()) and self.CheckError(self.lineEditAlto.text()) and self.CheckError(self.lineEditEspesor.text()):

                #Asignacion de variables base
                c0 = 343
                p0 = 1.18
                londa = list(c0/np.array(self.Resultados["Frecuencia"]))
                self.Ancho = float(self.lineEditAncho.text())
                self.Alto = float(self.lineEditAlto.text())
                self.Espesor = float(self.lineEditEspesor.text())
                masa = self.Densidad*self.Espesor

                #Reseteo de resultados
                self.Resultados["Panel Simple"]=[]
                self.Resultados["Sharp"]=[]
                self.Resultados["Davy"]=[]
                self.Resultados["ISO 12354-1"]=[]

                #Calculos Compartidos. fd=freq densidad, fc=freq critica, fr=freq resonancia(1,1)
                self.B = (self.ModuloY*(self.Espesor**3))/(12*(1-self.ModuloP**2))
                self.fc = ((c0**2)/(2*np.pi))*np.sqrt(masa/self.B)
                self.fd = (self.ModuloY/(np.pi*2*self.Densidad))*np.sqrt(masa/self.B)
                self.fr = ((c0**2)/(4*self.fc))*((1/self.Ancho**2)+(1/self.Alto**2))
                self.PerdidaxFreq = list(self.FactorP + masa/(485*np.sqrt(np.array(self.Resultados["Frecuencia"]))))

                ## Muestra data en la cajita de texto
                self.Consola.setText("Frecuencia Critica: "+str(round(self.fc,0))+
                " Hz\nFrecuencia de Densidad: "+str(round(self.fd,0))+
                " Hz\nFrecuencia de Resonancia (Primer modo): "+str(round(self.fr,0))+" Hz")

                ## Resetea el grafico si ya habia uno antes
                if self.counter>0:
                    self.GraphWidget.canvas.axes.clear()

                ### Arrancamos con cada modelo ###
                #Frecuencias:
                freq = np.array(self.Resultados["Frecuencia"])

                #### PANEL SIMPLE: ####
                if self.checkBoxPanel.isChecked() == True:

                    if self.fc<self.fd:
                        # Debajo fc
                        freqA = freq[freq<self.fc]
                        RA = 20*np.log10(masa*freqA)-47

                        #Entre fc y fd

                        freqz = freq[freq>self.fc]
                        freqB = freqz[freqz<self.fd]
                        if len(freqB>0):
                            cutB = np.where(freq == freqB[0])
                            ntB = np.array(self.PerdidaxFreq[cutB[0][0]:cutB[0][0]+len(freqB)])
                        else:
                            ntB = np.array(self.PerdidaxFreq[0:len(freqB)])
                        RB = 20*np.log10(masa*freqB) - 10*np.log10(np.pi/(4*ntB)) - 10*np.log10(self.fc/(freqB-self.fc)) - 47

                        #Arriba de fd
                        freqC = freq[freq>self.fd]
                        RC = 20*np.log10(masa*freqC)-47

                        #Armamos el array con RA,RB,RC para todas las freqs
                        arr = (RA,RB,RC)
                        self.Resultados["Panel Simple"] = list(np.around(np.concatenate(arr),decimals=1))
                    else:
                        arr = 20*np.log10(masa*freq)-47
                        self.Resultados["Panel Simple"] = list(np.around(arr))
                    #print(self.Resultados["Sharp"])

                    #Graficar:
                    self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], self.Resultados["Panel Simple"],marker="o",label="Panel")

                else:
                    #self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], np.zeros(len(self.Resultados["Frecuencia"])),linestyle="None",marker="o")
                    pass

                ################

                #### SHARP: ####
                if self.checkBoxSharp.isChecked() == True:
                    ### Calculos Sharp
                    if self.fc/2 > 20:
                    #Debajo de frecuencia Critica/2
                        freqD = freq[freq < (self.fc/2)]
                        RD = 10*np.log10(1+((np.pi*masa*freqD)/(p0*c0))**2) - 5.5

                        #arriba de frecuencia Critica
                        freqE = freq[freq > self.fc]
                        # print(freqE)
                        # print(self.fc)
                        cutE = np.where(freq == freqE[0])
                        ntE = np.array(self.PerdidaxFreq[cutE[0][0]:cutE[0][0]+len(freqE)])
                        RE1 = 10*np.log10(1+((np.pi*masa*freqE)/(p0*c0))**2) + 10*np.log10(2*ntE*freqE/(np.pi*self.fc))
                        RE2 = 10*np.log10(1+((np.pi*masa*freqE)/(p0*c0))**2)-5.5
                        RE = np.minimum(RE1,RE2)


                        freq1 = freq[freq > (self.fc/2)]
                        freqF = freq1[freq1 < self.fc]
                        # y = freqE[0] - freqD[-1]
                        # x = RE[0] - RD[-1]
                        px = [freqD[-1],freqE[0]]
                        py = [RD[-1],RE[0]]
                        p = np.polyfit(px,py,1)
                        RF = p[0]*freqF+p[1]
                        #print(p[0])

                        arr2 = (RD,RF,RE)
                        arr2 = list(np.around(np.concatenate(arr2),decimals=1))
                    else:
                        # freqE = freq[freq > self.fc/2]
                        # cutE = np.where(freq == freqE[0])
                        # ntE = np.array(self.PerdidaxFreq[cutE[0][0]:cutE[0][0]+len(freqE)])

                        RE1 = 10*np.log10(1+((np.pi*masa*freq)/(p0*c0))**2) + 10*np.log10(2*np.array(self.PerdidaxFreq)*freq/(np.pi*self.fc))
                        RE2 = 10*np.log10(1+((np.pi*masa*freq)/(p0*c0))**2)-5.5
                        RE = np.minimum(RE1,RE2)
                        arr2=list(np.around(RE,decimals=1))

                    self.Resultados["Sharp"] = list(arr2)
                    self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], self.Resultados["Sharp"],marker="o",label="Sharp")

                else:
                    #self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], np.zeros(len(self.Resultados["Frecuencia"])),linestyle="None",marker="o")
                    pass

                #################

                ##### DAVY: #####
                if self.checkBoxDavy.isChecked() == True:
                    ### Calculos Davy
                    ms = self.Densidad * self.Espesor                          #Masa superficial
                    B = (self.ModuloY*(self.Espesor**3))/(12*(1-(self.ModuloP**2)))  #B


                    normal = p0 * c0 / (np.pi * freq * ms)
                    normal2 = normal * normal
                    e = 2*self.Ancho*self.Alto/(self.Ancho+self.Alto)
                    cos2l = c0/(2*np.pi*freq*e)
                    cos21Max = 0.9
                    cos2l[cos2l>cos21Max] = cos21Max

                    tau1 = normal2*np.log((normal2 + 1) / (normal2 + cos2l))
                    ratio = freq/self.fc

                    r = 1-1/ratio
                    r[r<0] = 0

                    G = np.sqrt(r)
                    rad = self.sigma(G, freq, self.Ancho, self.Alto)
                    rad2 = rad * rad
                    netatotal = self.FactorP + rad * normal
                    z = 2 / netatotal
                    y = np.arctan(z)-np.arctan(z*(1-ratio))
                    tau2 = normal2 * rad2 * y / (netatotal * 2 * ratio)
                    tau2 = tau2 * self.shear(freq, self.Densidad, self.ModuloY, self.ModuloP, self.Espesor)

                    tau = np.zeros_like(freq)
                    tau[freq<self.fc] = tau1[freq<self.fc] + tau2[freq<self.fc]
                    tau[freq>=self.fc] = tau2[freq>=self.fc]

                    Rrr = -10 * np.log10(tau)

                    self.Resultados["Davy"] = list(np.around(Rrr,decimals=1))
                    self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], self.Resultados["Davy"],marker="o",label="Davy")

                else:
                    #self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], np.zeros(len(self.Resultados["Frecuencia"])),linestyle="None",marker="o")
                    pass

                #################

                ##### ISO: ######
                if self.checkBoxIso.isChecked() == True:
                    ### Calculos Iso

                    if self.Ancho>self.Alto:
                        l1 = self.Ancho
                        l2 = self.Alto
                    else:
                        l1 = self.Alto
                        l2 = self.Ancho

                    ms = self.Densidad * self.Espesor                      #Masa superficial
                    B = (self.ModuloY*(self.Espesor**3))/(12*(1-(self.ModuloP**2)))  #B

                    fc = ((c0**2)/(2*np.pi))*(np.sqrt(ms/B))        #Frecuencia critica
                    k0 = 2*np.pi*freq/c0                           #Numero de onda
                    vlambda = np.sqrt(freq/self.fc)                     #Lambda

                    delta1 = (((1-(vlambda**2))*np.log((1+vlambda)/(1-vlambda))+2*vlambda)/
                              (4*(np.pi**2)*((1-(vlambda**2))**1.5)))
                    delta2 = np.hstack(((8*(c0**2)*(1-2*(vlambda[freq<=self.fc/2]**2)))/
                             ((fc**2)*(np.pi**4)*l1*l2*vlambda[freq<=self.fc/2]*np.sqrt(1-vlambda[freq<=self.fc/2]**2)),
                             np.zeros_like(freq[freq>self.fc/2])))

                    # Cálculo del factor SIGMA de radiación para ondas libres
                    sigma1 = 1/np.sqrt(1-(self.fc/freq))
                    sigma2 = 4*l1*l2*((freq/c0)**2)
                    sigma3 = np.sqrt((2*np.pi*freq*(l1+l2))/(16*c0))
                    f11 = ((c0**2)/(4*self.fc))*(l1**-2+l2**-2)          #Frecuencia 1er modo axial

                    if f11<=fc/2:
                        # sigma_d = ((2*(l1+l2))/(l1*l2))*(c0/fc)*delta1[freqs<fc] + delta2[freqs<fc]
                        sigma_d = ((2*(l1+l2))/(l1*l2))*(c0/self.fc)*delta1[freq<self.fc]
                        sigma2 = sigma2[freq<self.fc]
                        freqs_under_fc = freq[freq<self.fc]
                        sigma_d[(freqs_under_fc<f11)&(sigma_d>sigma2)] = sigma2[(freqs_under_fc<f11)&(sigma_d>sigma2)]
                        sigma = np.hstack((sigma_d,sigma1[freq>=self.fc]))

                    elif f11>fc/2:
                        sigma = np.zeros_like(freq)
                        sigma[(freq<self.fc)&(sigma2<sigma3)] = sigma2[(freq<self.fc)&(sigma2<sigma3)]
                        sigma[(freq>=self.fc)&(sigma1<sigma3)] = sigma1[(freq>=self.fc)&(sigma1<sigma3)]
                        sigma[sigma==0] = sigma3[sigma==0]

                    # Se limita a sigma<=2 segun la norma.
                    sigma[sigma>=2] = 2

                    n_tot = self.FactorP + (ms/(485*np.sqrt(freq)))
                    pico = -0.964-(0.5+(l2/(l1*np.pi)))*np.log(l2/l1)+(5*l2)/(2*np.pi*l1)-1/(4*np.pi*l1*l2*(k0**2))
                    sigma_f = 0.5*(np.log(k0*np.sqrt(l1*l2)) - pico)
                    sigma_f[sigma_f>=2] = 2
                    sigma_f = np.abs(sigma_f)


                    # 1st condition f < fc
                    f1 = freq[freq<self.fc]
                    n1_tot = n_tot[freq<self.fc]
                    sigma1_f = sigma_f[freq<self.fc]
                    a = (2*p0*c0)/(2*np.pi*f1*ms)
                    b = 2*sigma1_f+(((l1+l2)**2)/(l1**2+l2**2))*np.sqrt(fc/f1)*((sigma[freq<self.fc]**2)/n1_tot)
                    # b[0] = b[0]*-1
                    tau1 = (a**2)*b

                    # 2nd condition f >= fc
                    f2 = freq[freq>=self.fc]
                    n2_tot = n_tot[freq>=self.fc]
                    a2 = (2*p0*c0)/(2*np.pi*f2*ms)
                    b2 = (np.pi*fc*(sigma[freq>=self.fc]**2))/(2*f2*n2_tot)
                    tau2 = (a2**2)*b2

                    tau = np.hstack((tau1,tau2))
                    Rar = -10*np.log10(tau)

                    self.Resultados["ISO 12354-1"] = list(np.around(Rar,decimals=1))
                    self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], self.Resultados["ISO 12354-1"],marker="o",label="ISO 12354-1")

                else:
                    #self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], np.zeros(len(self.Resultados["Frecuencia"])),linestyle="None",marker="o")
                    pass

                ###############

    ################ ......  #######################


                ### Detalles Grafico: ###

                self.GraphWidget.canvas.axes.legend(loc='lower right')
                self.GraphWidget.canvas.axes.axvline(self.fc,color="r",linestyle="--")
                self.GraphWidget.canvas.axes.axvline(self.fd,color="r",linestyle="--")
                if self.fr>10:
                    self.GraphWidget.canvas.axes.axvline(self.fr,color="r",linestyle="--")
                self.GraphWidget.canvas.axes.set_title('Indice de Reduccion Sonora')
                self.GraphWidget.canvas.axes.set_xscale('log')
                self.GraphWidget.canvas.axes.grid()
                # self.GraphWidget.canvas.axes.set_xticks(self.Resultados["Frecuencia"])
                # self.GraphWidget.canvas.axes.set_xticklabels(["","","31.5","","","63","","","125","","","250","","","500","","","1000","","","2000","","","4000","","","8000","","","16000"])
                self.GraphWidget.canvas.draw()
                self.counter = self.counter + 1

            ##Cierra if de CheckError

        ## Ciera Try con excepciones y errores:
        except AttributeError:
            self.Error(2)

        except IndexError:
            self.Error(3)

    ################### END CALCULO ########################
    #END CALCULO


    def shear(self,freqs, density, young, poisson, thickness):
        chi = ((1 + poisson) / (0.87 + 1.12*poisson))**2
        X = thickness**2 /12
        QP = young / (1-poisson**2)
        C = -((2*np.pi*freqs)**2)
        B = C*(1 + 2*chi/(1-poisson))*X
        A = X*QP / density
        kbcor2 = (np.sqrt(B**2 - 4*A*C) - B) / (2*A)
        kb2 = np.sqrt((-C) / A)
        G = young/(2*(1+poisson))
        kT2 = -C * density * chi / G
        kL2 = -C * density / QP
        kS2 = kT2 + kL2
        ASI = 1 + X*((kbcor2*kT2 / kL2) - kT2)
        ASI *= ASI
        BSI = 1 - X*kT2 + kbcor2 * kS2 / (kb2**2)
        CSI = np.sqrt(1- X*kT2 + (kS2**2)/(4*kb2*kb2))

        return ASI / (BSI*CSI)

    def sigma(self,G, freqs, lx, ly):
        # Definición de constantes:
        c0 = 343
        w = 1.3
        beta = 0.234
        n = 2

        S = lx*ly
        U = 2 * (lx + ly)
        twoa = 4 * S / U
        k = 2 * np.pi * freqs / c0
        f = w * np.sqrt(np.pi/(k*twoa))
        f[f>1] = 1

        h = 1 / (np.sqrt(k * twoa / np.pi) * 2 / 3 - beta)
        q = 2 * np.pi / (k * k * S)
        qn = q**n

        alpha = h / f - 1
        xn = np.zeros_like(freqs)

        xn[G<f] = (h[G<f] - alpha[G<f]*G[G<f])**n
        xn[G>=f] = G[G>=f]**n

        rad = (xn + qn)**(-1 / n)

        return rad



    ### Del excel a las variables y LineEdits ###
    def Act(self):
        d = self.df.loc[self.df['Material'] == self.comboBox.currentText()]["Densidad"].values[0]
        my = self.df.loc[self.df['Material'] == self.comboBox.currentText()]["Módulo de Young"].values[0]
        fp = self.df.loc[self.df['Material'] == self.comboBox.currentText()]["Factor de pérdidas"].values[0]
        mp = self.df.loc[self.df['Material'] == self.comboBox.currentText()]["Módulo Poisson"].values[0]
        if self.CheckError(d) and self.CheckError(my) and self.CheckError(fp) and self.CheckError(mp):
            self.Densidad = d
            self.ModuloY = my
            self.FactorP = fp
            self.ModuloP = mp
            self.lineEditModuloP.setText(str(self.ModuloP))
            self.lineEditModuloY.setText(str(self.ModuloY))
            self.lineEditFactorP.setText(str(self.FactorP))
            self.lineEditDensidad.setText(str(self.Densidad))
        else:
            pass
    ##############

    ###  Modo Usuario: Al tocar el botton "Asignar"  ###
    def AsignarMP(self):
        self.ModuloP = float(self.lineEditModuloP.text())
    def AsignarMY(self):
        self.ModuloY = float(self.lineEditModuloY.text())
    def AsignarFP(self):
        self.FactorP = float(self.lineEditFactorP.text())
    def AsignarD(self):
        self.Densidad = float(self.lineEditDensidad.text())
    ###########



    ### Si NO hay un "Materiales.xlsx", entonces crea este excel ###
    def CrearExcel(self):
        workbook = xlsxwriter.Workbook('Materiales.xlsx')
        worksheet = workbook.add_worksheet()
        #worksheet.write
        row_num = 0
        for key, value in self.excel.items():
            worksheet.write(row_num, 0, row_num)
            worksheet.write(row_num, 1, key)
            worksheet.write_row(row_num, 2, value)
            row_num += 1
        worksheet.write(0, 0, "Id.")
        workbook.close()

    #####################



    ########## EXCEL Al exportar #############
    def Exportar(self):
        name,_ = QFileDialog.getSaveFileName(self, 'Save File', QDir.rootPath() , '*.xlsx')
        workbook = xlsxwriter.Workbook(name)
        bold = workbook.add_format({'bold': True})
        worksheet = workbook.add_worksheet()
        worksheet.set_column('B:B', 12)
        border = workbook.add_format({'border': 1})
        #worksheet.write
        row_num = 0
        for key, value in self.Resultados.items():
            worksheet.set_row(row_num,18)
            worksheet.write(row_num, 1, key, bold)
            worksheet.write_row(row_num, 2, value,border)
            row_num += 1
        # Create a new chart object.
        chart = workbook.add_chart({'type': 'line'})

        # Add a series to the chart.
        chart.add_series({
        'values': '=Sheet1!$C$2:$AG$2',
        'categories': '=Sheet1!$C$1:$AG$1',
        'marker': {'type': 'diamond'},
        #'data_labels': {'value': True},
        'name':'Panel Simple',
        'line':{'color':'red'}
        })

        chart.add_series({
        'values': '=Sheet1!$C$3:$AG$3',
        'categories': '=Sheet1!$C$1:$AG$1',
        'marker': {'type': 'diamond'},
        #'data_labels': {'value': True},
        'name':'Sharp',
        'line':{'color':'blue'}
        })

        chart.add_series({
        'values': '=Sheet1!$C$4:$AG$4',
        'categories': '=Sheet1!$C$1:$AG$1',
        'marker': {'type': 'diamond'},
        #'data_labels': {'value': True},
        'name':'Davy',
        'line':{'color':'green'}
        })

        chart.add_series({
        'values': '=Sheet1!$C$5:$AG$5',
        'categories': '=Sheet1!$C$1:$AG$1',
        'marker': {'type': 'diamond'},
        #'data_labels': {'value': True},
        'name':'ISO',
        'line':{'color':'orange'}
        })
        chart.set_x_axis({'log_base': 10})
        chart.set_size({'width': 1600, 'height': 600})
        chart.set_title({'name': 'Indice de Reducción Sonora'})

        # Insert the chart into the worksheet.
        worksheet.insert_chart('B8', chart)
        workbook.close()





########################### END FUNCIONES ###############################




# Loop de la aplicacion.
if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)
    #Style de la app (importada)
    app.setStyleSheet(stylesheet1)
    # Create and show the application's main window
    win = MainWindow()
    win.show()
    # Run the application's main loop
    sys.exit(app.exec())
