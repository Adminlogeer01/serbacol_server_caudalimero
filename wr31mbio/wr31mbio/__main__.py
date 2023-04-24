############################################################################
#                                                                          #
# Copyright (c)2016, Digi International (Digi). All Rights Reserved.       #
#                                                                          #
# Permission to use, copy, modify, and distribute this software and its    #
# documentation, without fee and without a signed licensing agreement, is  #
# hereby granted, provided that the software is used on Digi products only #
# and that the software contain this copyright notice,  and the following  #
# two paragraphs appear in all copies, modifications, and distributions as #
# well. Contact Product Management, Digi International, Inc., 11001 Bren   #
# Road East, Minnetonka, MN, +1 952-912-3444, for commercial licensing     #
# opportunities for non-Digi products.                                     #
#                                                                          #
# DIGI SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED   #
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A          #
# PARTICULAR PURPOSE. THE SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, #
# PROVIDED HEREUNDER IS PROVIDED "AS IS" AND WITHOUT WARRANTY OF ANY KIND. #
# DIGI HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,         #
# ENHANCEMENTS, OR MODIFICATIONS.                                          #
#                                                                          #
# IN NO EVENT SHALL DIGI BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT,      #
# SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS,   #
# ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF   #
# DIGI HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.                #
#                                                                          #
############################################################################


import traceback
import sys
import re
import ConfigParser
import digilogger
import time
import modbus_tk
import modbus_tk.modbus_tcp as modbus_tcp
import modbus_tk.modbus_rtu as modbus_rtu
from modbus_tk import hooks
import serial
import digihw
import digisarcli
import struct
import socket
import sarcli

from functools import reduce 

VERSION = 1.0

LOGGER = digilogger.getLogger()

def get_config(filename):
    required_section = 'WR31ModBusIO'
    default_config = {'server_type': "TCP"}
    config = ConfigParser.ConfigParser(default_config)
    config.read(filename)
    if not config.has_section(required_section):
        LOGGER.warn('Config file does not have expected section: "{0}"'.format(required_section))
        config.add_section(required_section)
    return config

class WR31modmusio(object):
    def __init__(self, server_type):
        self.server_type = server_type
        if self.server_type == None:
            self.server_type = "TCP"
        else:
            self.server_type = server_type

    def start(self):
        self.cli = digisarcli.digisarcli(LOGGER)
        if self.server_type == 'TCP':
            self.setup_modbus_tcp()
        elif self.server_type == 'RTU':
            self.setup_modbus_rtu()
        hooks.install_hook("modbus.Slave.handle_read_holding_registers_request", self.hook_read_holding_registers)
        hooks.install_hook("modbus.Slave.handle_write_single_coil_request", self.hook_write_single_coil_request)
        hooks.install_hook("modbus.Slave.handle_read_coils_request", self.hook_read_coils_request)

    def setup_modbus_tcp(self):
        print ("Starting TCP Server..")
        self.server = modbus_tk.modbus_tcp.TcpServer(timeout_in_sec=3)
        self.server.start()
        self.setup_slave()

    def setup_modbus_rtu(self):
        print ("Starting RTU Server..")
        self.server = modbus_tk.modbus_rtu.RtuServer(serial.Serial(0))
        self.server.start()
        self.setup_slave()

    def setup_slave(self):
        self.slave1 = self.server.add_slave(1)
        self.slave1.add_block("hr0", modbus_tk.defines.HOLDING_REGISTERS, 0, 20) # 4 cambiado a 6 y de 6 a 10
        self.slave1.add_block("c0-1", modbus_tk.defines.COILS, 100, 2)

    def hook_read_holding_registers(self, request_pdu):
        """this is called just before handling the request"""
        """This will Read Analog Input AIN0 """
        """Register 0 will current and Register 1 will read voltage"""
        if (request_pdu[1][2] == '\x00') or (request_pdu[1][2] == '\x01'):
            ain = 0
            mode = 'current'
            """digihw.wr31_ain_get_value() returns integer so this portion is disabled untill firware fix"""
            # LOGGER.debug("Reading Digital IO {0}".format(dio) )
            #value = digihw.wr31_ain_get_value()
            #LOGGER.debug("Requsted Analog Input {0}. Reading value {1}".format(mode, value))
            """Read Analog Input from CLI"""
            ain_value = self.read_ain(mode)
            LOGGER.debug("Got from AIN: ( % s )" % ain_value)
            ain_value_high, ain_value_low = struct.unpack('>HH', struct.pack('f', ain_value))
        # elif (request_pdu[1][2] == '\x02') or (request_pdu[1][2] == '\x03'):
        #     ain = 2
        #     mode = 'voltage'
        #     """digihw.wr31_ain_get_value() returns integer so this portion is disabled untill firware fix"""
        #     # LOGGER.debug("Reading Digital IO {0}".format(dio) )
        #     #value = digihw.wr31_ain_get_value()
        #     #LOGGER.debug("Requsted Analog Input {0}. Reading value {1}".format(mode, value))
        #     """Read Analog Input from CLI"""
        #     ain_value = self.read_ain(mode)
        #     LOGGER.debug("Got from AIN: ( % s )" % ain_value)
        #     ain_value_high, ain_value_low = struct.unpack('>HH', struct.pack('f', ain_value))
        elif (request_pdu[1][2] == '\x02') or (request_pdu[1][2] == '\x03'):
            ain = 2
            Presion2 = self.Presion2()
            LOGGER.debug("Valor de Presion2: ( % s )" % Presion2)
            ain_value_high, ain_value_low = struct.unpack('>HH', struct.pack('f', Presion2))
            
        elif (request_pdu[1][2] == '\x04') or (request_pdu[1][2] == '\x05'):
            ain = 4
            Flujo = self.FlujoDeMasa()
            LOGGER.debug("Valor del flujo: ( % s )" % Flujo)
            ain_value_high, ain_value_low = struct.unpack('>HH', struct.pack('f', Flujo))
        elif (request_pdu[1][2] == '\x06') or (request_pdu[1][2] == '\x07'):
            ain = 6
            Total = self.Totalizador()
            LOGGER.debug("Valor del total: ( % s )" % Total)
            ain_value_high, ain_value_low = struct.unpack('>HH', struct.pack("f", Total))

        elif (request_pdu[1][2] == '\x08') or (request_pdu[1][2] == '\x09'):
            ain = 8
            Presion = self.Presion()
            LOGGER.debug("Valor de Presion: ( % s )" % Presion)
            ain_value_high, ain_value_low = struct.unpack('>HH', struct.pack('f', Presion))
       
        else:
            LOGGER.error("Invalid AIO number requested {0}".format(request_pdu[1][2]))
            return
       
       
        """Set the appropriate modbus Holding Registers to the Analog input value we just red - it will go to the modbus response"""
        LOGGER.info("Estableciendo Holding Register {0} to {1}".format(ain, ain_value_high))
        self.slave1.set_values("hr0", ain, ain_value_high)
        LOGGER.info("Estableciendo Holding Register {0} to {1}".format(ain + 1, ain_value_low))
        self.slave1.set_values("hr0", ain + 1, ain_value_low)
        
    def hook_write_single_coil_request(self, request_pdu):
        """this is called just before handling the request"""
        """This will Write Digtal I/O DIO0 (register 100) and DIO1 (register 101)"""
        if ord(request_pdu[1][2]) == 100:
           dio = 0
        elif ord(request_pdu[1][2]) == 101:
           dio = 1
        else:
           LOGGER.error("Invalid DIO number requested")
           return
        if request_pdu[1][3] == '\x00':
           value = 0
        elif request_pdu[1][3] == '\xff':
           value = 1
        else:
           LOGGER.error("Invalid DIO value requested")
           return
        LOGGER.debug("Requsted to set Digital IO {0} with  value {1}".format(dio, value))
        digihw.wr31_dio_set_value(dio, value)

    def hook_read_coils_request(self, request_pdu):
        """this is called just before handling the request"""
        """This will Read Digtal I/O DIO0 (Coil 0) and DIO1 (Coil 1)"""
        if ord(request_pdu[1][2]) == 100:
            dio = 0
        elif ord(request_pdu[1][2]) == 101:
            dio = 1
        else:
            LOGGER.error("Invalid DIO number requested {0}".format(request_pdu[1][2]))
            return
        value = digihw.wr31_dio_get_value(dio)
        LOGGER.debug("Requsted Digital IO {0}. Reading value {1}".format(dio, value))
        """Let's set the appropriate modbus coil to the gpio value we just red - it will go to the modbus response"""
        LOGGER.info("Setting Coil {0} to {1}".format(100+ dio, value))
        self.slave1.set_values("c0-1", 100 + dio , value)

    def read_ain(self, mode):
        read_ain_cmd = 'gpio ain ' + mode
        return_code = self.cli.send_command_get_response(read_ain_cmd)
        if return_code[1][2] != 'OK\r':
            LOGGER.warn("command  failed: ( % s)" % return_code[1][2].replace('\r', ' '))
        ain_value = float(re.findall("\d+\.\d+", return_code[1][1])[0])
        return ain_value

    def tearDown(self):
        self.server.stop()

    def Presion (self):
        print("Consulta a Ptap")
        Presion= self.ConsultarRegistro(4, 3, 14, 1)
        print ("la presion es=", Presion)
        if Presion:
            try:
                Presion=int(Presion, 16)
                if Presion < 100:
                    print("presion despues es=", Presion)
                    print("\n     Presion: %s PSI"%(Presion))
                else:
                    Presion = 60
                return Presion
            except Exception as error:
                print(error)

    def Presion2 (self):
        print("Consulta a Ptap")
        Presion= self.ConsultarRegistro(4, 3, 15, 1)
        print ("la presion es=", Presion)
        if Presion:
            try:
                Presion=int(Presion, 16)
                if Presion < 100:
                    print("presion despues es=", Presion)
                    print("\n     Presion: %s PSI"%(Presion))
                else:
                    Presion = 60
                return Presion
            except Exception as error:
                print(error)


    def FlujoDeMasa(self):
        FlujoMasaAbsoluta = self.ConsultarRegistro(1, 3, 3002, 2)
        if FlujoMasaAbsoluta:
            try:
                FlujoMasaAbsoluta = struct.unpack('!f', FlujoMasaAbsoluta.decode('hex'))[0]*1000
                FlujoMasaAbsoluta = float("{0:.4f}".format(FlujoMasaAbsoluta))
                print("\n     FlujoMasaAbsoluta: %s L/s"%(FlujoMasaAbsoluta))
                return FlujoMasaAbsoluta
            except Exception as error:
                print(error)
    
    def Totalizador(self):
        Totalizador1 = self.ConsultarRegistro(1, 3, 3014, 4)
        if Totalizador1:
            try:
                Totalizador1 = struct.unpack("<d", struct.pack("Q",int("0x"+Totalizador1, 16)))[0]
                #Totalizador1 = float("{0:.4f}".format(Totalizador1))
                print("\n     Totalizador1: %s m%s"%(Totalizador1, 3))
                return Totalizador1
            except Exception as error:
                print(error)

    # Consulta  de registros
    def ConsultarRegistro(self, id, funcion, registro, Nregistros):
        #print("\nConsultando-->\nEquipo: %s\nFuncion: %s\nRegistro: %s\nNo. de registros: %s\n" %(id, funcion, registro, Nregistros))
        lenRegister=len(str(registro))
        ID_t = 1
        ID_p = 0
        ID_tHex = str(self.DecHexa2B(ID_t))
        ID_pHex = str(self.DecHexa2B(ID_p))
        ID_uHex = str(self.DecHexa1B(id))
        Cod_fHex = self.DecHexa1B(funcion)
        if lenRegister==2: #en caso de registros bajos < 99
                RegistroH="00"
                RegistroL=self.DecHexa1B(registro)
        else:
                RegistroH = self.DecHexa2B(registro)[:2]
                RegistroL = self.DecHexa2B(registro)[2:]

        #RegistroH = self.DecHexa2B(registro)[:2]
        #RegistroL = self.DecHexa2B(registro)[2:]
        Dir_iHex = RegistroH+RegistroL
        NRegistrosH = self.DecHexa2B(Nregistros)[:2]
        NRegistrosL = self.DecHexa2B(Nregistros)[3:]
        Cant_rHex = NRegistrosH+NRegistrosL
        LonHex = self.DecHexa2B(int(len((ID_uHex+Cod_fHex+Dir_iHex+Cant_rHex).replace(" ",""))/2))
        #Para consultar registros pequeños modificar las comillas de -> RegistroH+" "+ 
        Comando = ID_uHex+" "+Cod_fHex+" "+RegistroH+" "+RegistroL+" "+NRegistrosH+" "+NRegistrosL
        Comando = Comando+" "+self.crc16(Comando)
        Respuesta = self.TCP2(Comando)
        Bytes =  "81 04"
        ValorFlotante = 0.00
        if Respuesta != None:
            #print("Mensaje recibido: "+Respuesta)
            if Respuesta == "81 04 ":
                print("Error ModBus")
            else:
                NBytes = int(self.ExtraerBytes(Respuesta, 3, 1), 16)
                #print("NBytes: %s"%NBytes)
                Bytes = self.ExtraerBytes(Respuesta, 4, NBytes)
                #print("Bytes: "+Bytes)
        return Bytes
    
    # Convertir a hex de 1 byte
    def DecHexa1B(self, x):
        x = hex(x).replace("0x","")
        if len(x)==1:
            x = "0"+x
        return x

    # Convertir a hex de 2 byte
    def DecHexa2B(self, y):
        y = hex(y).replace("0x","")
        if len(y)==1:
            y = "00 0"+y
        if len(y)==2:
            y = "00 "+y
        if len(y)==3:
            y = "0"+y
        return y

    # Calculo del CRC
    def crc16(self, data, bits=8):
        crc = 0xFFFF
        for op, code in zip(data.replace(" ","")[0::2], data.replace(" ","")[1::2]):
            crc = crc ^ int(op+code, 16)
            for bit in range(0, bits):
                if (crc&0x0001)  == 0x0001:
                    crc = ((crc >> 1) ^ 0xA001)
                else:
                    crc = crc >> 1
        CRC = self.typecasting(crc)
        #print("CRC: "+CRC)
        CRC16L = CRC[:2]
        CRC16H = CRC[2:]
        return CRC16L+" "+CRC16H

    # Organizar CRC L, H
    def typecasting(self, crc):
        msb = hex(crc >> 8).replace("0x","")
        lsb = hex(crc & 0x00FF).replace("0x","")
        if len(msb) == 1:
            msb = "0"+msb
        if len(lsb) == 1:
            lsb = "0"+lsb
        return lsb + msb

    # Funcion para enviar mensajes por TCP
    def TCP2(self, mensaje):
        try:
            #print ("Enviando mensaje: "+ mensaje)
            #Resultado = self.Get_Cli("gpstat")
            PuertoLogico = 4000 #int(self.Get_line("0    ASY  0    Listening    TCP   Norm", Resultado).split(" ")[31])
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente.connect(("127.0.0.1", PuertoLogico))
            mensaje = self.StringToBin(mensaje)
            cliente.send(mensaje)
            respuesta = cliente.recv(1024)
            respuesta = self.BintoHexString(respuesta)
            #cliente.close()
            return respuesta
        finally:#except Exception as error:
            cliente.close()
            #print (error)

    # Convierte una cadena hex a hex
    def StringToBin(self, D):
        bytes = D.split(" ")
        tamano = len(bytes)
        DatosH = ''
        for x in range(0, tamano):
            DatosH += chr(int(bytes[x],16))
        return DatosH

    # Convertir string to hex
    def BintoHexString(self, b):
        lst = []
        for ch in b:
            hv = hex(ord(ch)).replace('0x', '')
            if len(hv) == 1:
                hv = '0'+hv
            hv = hv + " "
            lst.append(hv)
        return reduce(lambda x,y:x+y, lst)

    # Exraccion de bytes de un string
    def ExtraerBytes(self, CadenaHex, Inicio, Nregistros):
        CadenaHex = CadenaHex.split(" ")
        CadenaBytes = ""
        for x in range(Inicio-1, Inicio+Nregistros-1):
            CadenaBytes += CadenaHex[x]
        #print("CadenaBytes: "+CadenaBytes)
        return CadenaBytes

    #Funcion para los comandos
    def Get_Cli(self, comando):
        clidata = ""
        cli = sarcli.open()
        cli.write(comando)
        while True:
            tmpdata = cli.read(-1)
            if not tmpdata:
                break
            clidata += tmpdata
        cli.close()
        return clidata

    #Funcion para extraer un linea especifica
    def Get_line(self, palabra, datos):
        respuesta = ""
        for line in datos.splitlines():
            if palabra in line:
                respuesta += line
        return respuesta


# programa principal que me toca modificar. 
counter = 0 
while True:
    try:
        if __name__ == "__main__":
            print(sys.argv)
            if len(sys.argv) > 2:
                CONFIG_FILE = sys.argv[1]
            else:
                CONFIG_FILE = "./config.cfg" #como se comporta el digi es decir servidor tcp o rtu 
            CONFIG = get_config(CONFIG_FILE)
            for config_item in CONFIG.options('WR31ModBusIO'):
                LOGGER.debug(CONFIG.get('WR31ModBusIO', config_item))
            run = WR31modmusio(CONFIG.get('WR31ModBusIO', 'server_type'))
            run.start()
            print('Run started !!!')
            while True:
                pass
            print('Run finished !!!')
    except BaseException as e:
            traceback.print_exc()
            exceptionType = repr(e)
            error = str(e)
            Get_Cli('setevent "NJAT: Exception type = '+exceptionType+'"')
            Get_Cli('setevent "NJAT: Error = '+error+'"')
            counter += 1
            if counter > 3:
                Get_Cli('reboot')



 
 
# este es un servidor. 
# este python consulta registros modbus, presion1 presion2 , caudal y totalizador
# que se conecte por serial
# ip de extreme 166.210.130.189
# puerto 502


#caudal corre en el 21 
#solo migrar los del w31, 

# son el _main_.py
# y reinicio pero el reinicio del digi se hace con el mismo
#  conservar la forma en como se ejecuta y probar en su totalidad 

#para simular abro la version maestro para simular el w31 y luego slave y simulo todo el funcionanmiento#
#apn red privada dentro de la red publica (rango de ip privado que solo se ven ellos)
#acces name point 