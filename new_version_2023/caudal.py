import socket,sys,threading

from pymodbus.client import ModbusTcpClient 


MODBUS_PORT = 502

try:
    IP = str(sys.argv[1])
except Exception as error:
    print(f'no ip input, using default: {error}')
    IP = "166.210.132.95"  #esto es el centro de control en cali 
    
try:
    Puerto = int(sys.argv[2])
except Exception as error:
    print(f'no port input, using default: {error}')
    Puerto = 4968



print("Puerto local %d e IP de destino %s"%(Puerto, IP))


class threadServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        print(f'Socket abierto en el puerto {self.port}')

      
    
    def Listen(self):
        self.sock.listen(1)
        # while True:
        #     client, address = self.sock.accept()
        #     client.settimeout(599)
        #     threading.Thread(target = self.ListenToClient,args = (client, address)).start()
        #     print(f'Server listening on port {Puerto}...')
        print(f'Server listening on port {Puerto}...')
        conn, addr = self.sock.accept()
        print(f"Se ha recibido una conexión desde {addr}")
        # Aquí se puede hacer lo que se desee con la conexión entrante
        # Por ejemplo, enviar un mensaje de bienvenida:
        conn.sendall(b"Bienvenido al servidor")
        # Y luego cerrar la conexión
        conn.close()

    def ModbusQuery(self,register):

        # se debe verificar la conexion del cliente y si no se puede conectar se debe retornar un error
        # es decir se debe manejar de una mejor forma el socket que abre el cliente tcp modbus
        modbusClient = ModbusTcpClient(IP,MODBUS_PORT)
        modbusClient.connect()
        result_register = modbusClient.read_holding_registers(int(register),2,unit=1)
        modbusClient.close()

        if result_register.isError():
            print("Error ModBus")
        else:
            # convertir los valos a un valor de punto flotante y retornarlos par su utilizacion 
            # por ahora se devolvera el valor sin convertir para probar el funcionamiento
            return result_register.registers 
            
    

    def ListenToClient(self, client:str, address:str):
        size = 1024
        print(f'client {address} connected')

        while True: 
            try:
                data = client.recv(size)
                if data == 'CONSULTAR':
                    print(f'recived {data} from {address}')
                    cuadal = self.ModbusQuery(1)
                    Total = self.ModbusQuery(2)
                    Presion01 = self.ModbusQuery(4)
                    Presion02 = self.ModbusQuery(6)
                    # se debe convertir en un json y enviar los valores a el cliente por ahora
                    # solo lo vamos a imprimir por pantall para probar el funcioamiento
                    print(f'cuadal: {cuadal}, Total: {Total}, Presion01: {Presion01}, Presion02: {Presion02}')
                else :
                    raise Exception('no valid data received') 
            except Exception as error:
                print(f'client {address} disconnected for {error}')
                client.close()
                return False

        

if __name__ == "__main__":
    threadServer('',Puerto).Listen()

  
    


 


# 
# se puede probar por hercules
# parte de campo este es el digi,(el que se danio) y debe apuntar a dos direcciones ip
# 
# este es el que no hay que modificar entonces...
# 
# 