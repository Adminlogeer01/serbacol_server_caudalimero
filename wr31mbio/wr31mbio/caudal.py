import socket, threading, time, struct, sys
from functools import reduce

try:
    Puerto = int(sys.argv[2])
except Exception as error:
    print(error)
    Puerto = 20156

try:
    IP = str(sys.argv[1])
except Exception as error:
    print(error)
    IP = "166.210.132.95"
    
print("Puerto local %d e IP de destino %s"%(Puerto, IP))

class HiloDeServidores(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

    def listen(self):
        self.sock.listen(0)
        while True:
            print('iniciando espera de conexion')
            client, address = self.sock.accept()
            client.settimeout(599)
            # print('conexion establecida')
            threading.Thread(target = self.listenToClient,args = (client, address)).start()
            print(f'Server listening on port {Puerto}...')

    # Consulta de registros
    #verificar si se puede eliminar esta funcion ya que se puede usar la libreria de modbus
    def Consultar(self, registro):
        ConsultaMbusTCP = struct.pack('12B', 0x00, 0x01, 0x00, 0x00, 0x00, 0x06, 0x01, 0x03, 0x00, int(registro), 0x00, 0x02)
        Respuesta = self.TCP(ConsultaMbusTCP)
        print("RespuestaMbus: %s"%Respuesta)
        Bytes =  "81 04"
        if Respuesta != None:
            print("Mensaje recibido: "+Respuesta)
            if Respuesta == "81 04 ":
                print("Error ModBus")
            else:
                Bytes = self.ExtraerBytes(Respuesta, 10, 4)
                print("Bytes: "+Bytes)
                try:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
                    valor = struct.unpack('!f', Bytes.decode('hex'))[0]
                    #valor_e = format(valor,'.3E')
                    print("      valor: %s L/s"%(valor))
                    return valor
                except Exception as error:
                    print(error)
    
    # Conexion TCP local
    def TCP(self, mensaje):
        try:
            print ("Enviando mensajeTCP: "+ mensaje)
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente.settimeout(59)
            cliente.connect((IP, 502)) # 127.0.0.1 166.210.133.79
            #mensaje = self.StringToBin(mensaje)
            cliente.send(mensaje)
            respuesta = cliente.recv(1024)
            #envio y esto me responde el wr31
            print(respuesta, "HERE")
            respuesta = self.BintoHexString(respuesta) #paso binario a Hexa
            cliente.close()
            return respuesta
            #finally:
        except Exception as error:
            print (error)
            cliente.close()           
    
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
    	# print
        CadenaHex = CadenaHex.split(" ")
        CadenaBytes = ""
        for x in range(Inicio-1, Inicio+Nregistros-1):
            CadenaBytes += CadenaHex[x] + " "
        CadenaBytes = CadenaBytes[:11].split(" ")
        CadenaBytes = CadenaBytes[3] +  CadenaBytes[2] +  CadenaBytes[1] +  CadenaBytes[0]
        print("CadenaBytes: "+CadenaBytes)
        return CadenaBytes

    def listenToClient(self, client, address):
        size = 1024
        print("%s se ha conectado"%str(address))
        while True:
            try:
                dato = client.recv(size)
                if dato == "CONSULTAR":
                    print("Recibido: %s"%(dato))
                    Caudal = self.Consultar(4)#4
                    Total = self.Consultar(6) #6
                    #Presionp=self.Consultar(14)
                    Presion01 = self.Consultar(8)#Prueba
                    Presion02 = self.Consultar(2)
                    print("herre")
                    Json = "{\"Caudales\": %s,\"Totalizador\": %s, \"Presion01\": %s,\"Presion02\": %s}"%(Caudal, Total,Presion01,Presion02)
                    client.send(Json)
                    print("Enviiado: %s"%(Json))
                else:
                    raise error('Client disconnected')
            except Exception as error:
                print("%s se ha desconectado"%str(address))
                client.close()
                return False

if __name__ == "__main__":
    print("iniciando... ")
    server = HiloDeServidores('',Puerto)
    server.listen()