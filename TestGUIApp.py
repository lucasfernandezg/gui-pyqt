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
from mystylesheet import stylesheet

class MainWindow(QMainWindow, Ui_Form, QWidget):
    rightClicked = pyqtSignal()
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.CalculateButton.installEventFilter(self)

        self.textEdit.setText("Al iniciar esta aplicación por primera vez se crea un archivo llamado 'Materiales.xlsx' donde se guardan los datos de cada material. Si se desea agrandar la lista, solo agregue los nuevos materiales en el excel y reinicie la app.\n-NO cambie el nombre del excel.\n-NO cambie el nombre de las columnas ni la ubicacion de la tabla (que arranque en A1,1).'")

        self.counter = 0

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
        #ComboBox con Materiales
        self.comboBox.addItems(list(self.comboitems.values())[0])
        self.comboBox.addItems(["Usuario"])
        #Funcion que se ejecuta cuando elijo material
        self.comboBox.currentIndexChanged.connect(self.what)

        self.pushButton_3.setEnabled(False)

        self.lineEditFactorP.setReadOnly(True)
        self.lineEditModuloP.setReadOnly(True)
        self.lineEditModuloY.setReadOnly(True)
        self.lineEditDensidad.setReadOnly(True)

        #Cuando cambio Parametros material a mano
        self.pushButton_3.clicked.connect(self.AsignarMP)
        self.pushButton_3.clicked.connect(self.AsignarMY)
        self.pushButton_3.clicked.connect(self.AsignarFP)
        self.pushButton_3.clicked.connect(self.AsignarD)


        #Boton de calculo y graficado
        self.CalculateButton.clicked.connect(self.Calculo)
         #PRUEBA
        self.ExportButton.clicked.connect(self.Exportar)

        ftercio = [20,25,31.5,40,50,63,80,100,125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000,10000,12500,16000,20000]
        self.foct = [31.5,63,125,250,500,1000,2000,4000,8000,16000]

        self.Resultados = {
        "Frecuencia":[20,25,31.5,40,50,63,80,100,125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000,10000,12500,16000,20000],
        "Pared Simple":[],
        "Sharp":[],
        "Davy":[],
        "ISO 12354-1":[]
        }

        #self.pushButton_2.clicked.connect(self.getfiles)


    ###### Funciones ######
    def onClicked(self):
        super(MainWindow, self).onClicked(event)


    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            print("click derecho")
        super(MainWindow, self).mousePressEvent(event)

    def what(self):
        if self.comboBox.currentText() == "Usuario":
            self.pushButton_3.setEnabled(True)
            self.lineEditFactorP.setReadOnly(False)
            self.lineEditModuloP.setReadOnly(False)
            self.lineEditModuloY.setReadOnly(False)
            self.lineEditDensidad.setReadOnly(False)
            self.lineEditFactorP.clear()
            self.lineEditModuloP.clear()
            self.lineEditModuloY.clear()
            self.lineEditDensidad.clear()
            self.textEdit.setText("Para asignar los valores ingresados clickear 'Asignar' antes de 'Calcular'.")
        else:
            self.pushButton_3.setEnabled(False)
            self.lineEditFactorP.setReadOnly(True)
            self.lineEditModuloP.setReadOnly(True)
            self.lineEditModuloY.setReadOnly(True)
            self.lineEditDensidad.setReadOnly(True)
            self.Act()


    def getfiles(self):
        fileName, _ = QFileDialog.getSaveFileName(self, 'Single File', QDir.rootPath() , '*.xlsm')


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



    #########PRINCIPAL###########
    def Calculo(self):
        #Fijarnos que valores sean numeros y positivos.
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

                #Limpia el grafico
                #self.MplWidget.canvas.axes.clear()

                #Reseteo de resultados
                self.Resultados["Pared Simple"]=[]
                self.Resultados["Sharp"]=[]
                self.Resultados["Devy"]=[]
                self.Resultados["ISO 12354-1"]=[]

                #Calculos Compartidos. fd=freq densidad, fc=freq critica, fr=freq resonancia(1,1)
                self.B = (self.ModuloY*(self.Espesor**3))/(12*(1-self.ModuloP**2))
                self.fc = ((c0**2)/(2*np.pi))*np.sqrt(masa/self.B)
                self.fd = (self.ModuloY/(np.pi*2*self.Densidad))*np.sqrt(masa/self.B)
                self.fr = ((c0**2)/(4*self.fc))*((1/self.Ancho**2)+(1/self.Alto**2))
                self.PerdidaxFreq = list(self.FactorP + masa/(485*np.sqrt(np.array(self.Resultados["Frecuencia"]))))

                ## Muestra data en la cajita de texto
                self.textEdit.setText("Frecuencia Critica: "+str(round(self.fc,0))+
                " Hz\nFrecuencia de Densidad: "+str(round(self.fd,0))+
                " Hz\nFrecuencia de Resonancia (Primer modo): "+str(round(self.fr,0))+" Hz")

                #Resetea el grafico
                if self.counter>0:
                    self.GraphWidget.canvas.axes.clear()

                ### Arrancamos con cada modelo ###
                freq = np.array(self.Resultados["Frecuencia"])
                #PANEL SIMPLE:
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
                    self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], self.Resultados["Panel Simple"])

                else:
                    self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], np.zeros(len(self.Resultados["Frecuencia"])),linestyle="None")

                #SHARP:
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
                        y = freqE[0] - freqD[-1]
                        x = RE[0] - RD[-1]
                        px = [freqD[-1],freqE[0]]
                        py = [RD[-1],RE[0]]
                        p = np.polyfit(px,py,1)
                        RF = p[0]*freqF+p[1]
                        #print(p[0])

                        arr2 = (RD,RF,RE)
                        arr2 = np.around(np.concatenate(arr2),decimals=1)
                    else:
                        # freqE = freq[freq > self.fc/2]
                        # cutE = np.where(freq == freqE[0])
                        # ntE = np.array(self.PerdidaxFreq[cutE[0][0]:cutE[0][0]+len(freqE)])
                        RE1 = 10*np.log10(1+((np.pi*masa*freq)/(p0*c0))**2) + 10*np.log10(2*self.PerdidaxFreq*freq/(np.pi*self.fc))
                        RE2 = 10*np.log10(1+((np.pi*masa*freq)/(p0*c0))**2)-5.5
                        RE = np.minimum(RE1,RE2)
                        arr2=RE

                    self.Resultados["Sharp"] = list(arr2)
                    self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], self.Resultados["Sharp"])

                else:
                    self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], np.zeros(len(self.Resultados["Frecuencia"])),linestyle="None")

                #DAVY:
                if self.checkBoxDavy.isChecked() == True:
                    ### Calculos Davy
                    pass
                else:
                    self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], np.zeros(len(self.Resultados["Frecuencia"])),linestyle="None")

                #ISO
                if self.checkBoxIso.isChecked() == True:
                    ### Calculos Iso
                    pass
                else:
                    self.GraphWidget.canvas.axes.plot(self.Resultados["Frecuencia"], np.zeros(len(self.Resultados["Frecuencia"])),linestyle="None")

                #### ......  ####



                #Detalles Grafico:

                self.GraphWidget.canvas.axes.legend(("Panel",'Sharp',"Davy","Iso"),loc='lower right')
                self.GraphWidget.canvas.axes.axvline(self.fc,color="r",linestyle="--")
                self.GraphWidget.canvas.axes.axvline(self.fd,color="r",linestyle="--")
                if self.fr>10:
                    self.GraphWidget.canvas.axes.axvline(self.fr,color="r",linestyle="--")
                self.GraphWidget.canvas.axes.set_title('Indice de Reduccion Sonora')
                self.GraphWidget.canvas.axes.set_xscale('log')
                # self.GraphWidget.canvas.axes.set_xticks(self.Resultados["Frecuencia"])
                # self.GraphWidget.canvas.axes.set_xticklabels(["","","31.5","","","63","","","125","","","250","","","500","","","1000","","","2000","","","4000","","","8000","","","16000"])
                self.GraphWidget.canvas.draw()
                self.counter = self.counter + 1

        except AttributeError:
            self.Error(2)

        except IndexError:
            self.Error(3)
    #################################################### END CALCULO
    ####END CALCULO

    #Asociar parametros del material a variables
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
    ###########

    #Asociar parametros que meto a mano a variables
    def AsignarMP(self):
        self.ModuloP = float(self.lineEditModuloP.text())
    def AsignarMY(self):
        self.ModuloY = float(self.lineEditModuloY.text())
    def AsignarFP(self):
        self.FactorP = float(self.lineEditFactorP.text())
    def AsignarD(self):
        self.Densidad = float(self.lineEditDensidad.text())
    ###########



    #Exportar el excel con la tabla y datos calculados
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

    def Exportar(self):
        name,_ = QFileDialog.getSaveFileName(self, 'Save File', QDir.rootPath() , '*.xlsx')
        workbook = xlsxwriter.Workbook(name)
        worksheet = workbook.add_worksheet()
        #worksheet.write
        row_num = 0
        for key, value in self.Resultados.items():
            worksheet.write(row_num, 1, key)
            worksheet.write_row(row_num, 2, value)
            row_num += 1
        workbook.close()




    ##########



# Loop de la aplicacion.
if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)
    #Style de la app (importada)
    app.setStyleSheet(stylesheet)
    # Create and show the application's main window
    win = MainWindow()
    win.show()
    # Run the application's main loop
    sys.exit(app.exec())
