# librerias 

#nota: probablemente se accede al digi serial  asi serial.Serial("/dev/serial/port1", 115200) 


from pymodbus.payload import BinaryPayloadDecoder,Endian
from pymodbus.exceptions import ModbusException

from modbus_tk.defines import (READ_HOLDING_REGISTERS,
                                HOLDING_REGISTERS,
                                COILS
                                )
from modbus_tk.modbus_tcp import TcpServer
from modbus_tk.modbus_rtu import RtuServer
from modbus_tk import modbus_tcp
from modbus_tk import hooks

#
import struct
import serial
from time import sleep

#importar el cli para realizar el reboot del dispositivo y reiniciar 
# from digidevice import cli 




LOCAL_IP = '127.0.0.1'
LOCAL_PORT = 4000


class MiError(Exception):
    def __init__(self, mensaje):
        self.mensaje = mensaje

class IX10ModbusIO(object):


    def __init__(self,server_type):
        """Constructor for the IX10ModbusIO class.
        Parameters:
            self: The object pointer.
            server_type: The type of server to use. Can be 'TCP' or 'RTU'.
        Returns:
            None
        """
      
        self.server_type = server_type
        if self.server_type == None or self.server_type == 'TCP':
            self.server_type = 'TCP'

        elif self.server_type == 'RTU':
            self.server_type = 'RTU'
        else:
            raise MiError("Invalid server type. Must be 'TCP' or 'RTU'.")
  

    
    def start_serverIX10ModbusIO(self):
        """Start the server
            
        Parameters:
            self: The object pointer.
        Returns:
            None
            
        """
        #aca debe ir un manejo del logger usando digisarcli 
       
        if self.server_type == 'TCP':
            self.setup_modbus_tcpServer()
        elif self.server_type == 'RTU':
            self.setup_modbus_rtuServer()
        else: 
            raise MiError("Invalid server type. Must be 'TCP' or 'RTU'.")
        
        hooks.install_hook("modbus.Slave.handle_read_holding_registers_request", self.hook_read_holding_registers)
        print("Server started")
            


    def setup_modbus_rtuServer(self):
        """
        configura el servidor Modbus RTU.
        Este método configura el servidor Modbus RTU. Crea un objeto de servidor RTU y lo inicia. Luego llama al método
        'setup_slave' para configurar los esclavos. No devuelve nada.

        NOTA: el puerto serial para el digi IX10 es /dev/serial/port1 segun su documentacion 
        
        Args:
            self: El objeto puntero.
        Returns:
            None
        """
        
        self.server = RtuServer(serial.Serial(port='/dev/serial/port1',
                                            baudrate=115200,
                                            bytesize=8,
                                            parity='N',
                                            stopbits=1,
                                            xonxoff=0))
        self.server.start()
        self.setup_slave()
  


    def setup_modbus_tcpServer(self):
        """
        Configura el servidor Modbus TCP.
        Este método configura el servidor Modbus TCP. Crea un objeto de servidor TCP y lo inicia. Luego llama al método
        'setup_slave' para configurar los esclavos. No devuelve nada.
        Args:
            self: El objeto puntero.
        Returns:
            None

        """
        self.server = TcpServer(timeout_in_sec=3)
        self.server.start()
        self.setup_slave()
        
      
    def setup_slave(self):
        """
        Configura los bloques de datos del esclavo.
        Este método configura los bloques de datos del esclavo. Crea un esclavo y agrega dos bloques de datos: uno de tipo
        'HOLDING_REGISTERS' y otro de tipo 'COILS'. El bloque 'HOLDING_REGISTERS' comienza en la dirección 0 y tiene una
        longitud de 20 registros, mientras que el bloque 'COILS' comienza en la dirección 100 y tiene una longitud de 2
        bobinas. No devuelve nada
      
          Args:
            self: El objeto puntero.

        Returns:
            None

        """
        self.slave1 = self.server.add_slave(1)
        self.slave1.add_block("hr0",HOLDING_REGISTERS, 0, 20) # 4 cambiado a 6 y de 6 a 10
        self.slave1.add_block("c0-1",COILS, 100, 2)
  

    def Pressure(self, address_id: int) -> int:
        """
        Este método lee el valor de la presión desde una dirección específica utilizando Modbus . Primero crea un objeto
        de cliente TCP y abre una conexión al host y puerto especificados. Luego envía una solicitud de Modbus "leer
        registros de retención" para leer el valor de la presión desde la dirección especificada, y devuelve el resultado como
        un entero que representa el valor de presión en PSI. Si el valor leído es menor que 100 PSI, se devuelve tal cual.
        De lo contrario, se devuelve un valor predeterminado de 60 PSI. El método también devuelve el valor sin procesar que
        se leyó de la dirección especificada, así como un código de estado (que siempre es 0 en esta implementación).

        Args:
            address_id (int): La dirección de inicio del valor de presión que se va a leer.

        Returns:
            Una tupla con los siguientes elementos:
            - Un entero que representa el valor de presión (en PSI) que se leyó de la dirección especificada.
            - Un entero que representa el valor sin procesar que se leyó de la dirección especificada.
            - Un entero que representa el código de estado (siempre 0 en esta implementación ya que solo se lee un registro).


        """
        try:

            client =  modbus_tcp.TcpMaster(host=LOCAL_IP, port=LOCAL_PORT)
            client.open()
            print("leyendo la presion")
            response= client.execute(slave=4, 
                                        function_code = READ_HOLDING_REGISTERS, 
                                        starting_address=address_id, 
                                        quantity_of_x=1)
            client.set_timeout(5.0)
            print(f'presion antes es igual a {response[0]}')
            response_int  = response[0]
            if response_int < 100:
                print(f'presion despues es igual a {response_int}')
                print(f'presion {response_int} PSI')
            else:
                response_int = 60

            return (response_int, response[0],0)
                    
        except AssertionError as e:
            print(f"AssertionError: {e}")
            return None
        except ModbusException as e:
            print(f"ModbusException: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            client.close()

    def read_MassFlow(self):
        """
        Este método lee el valor de la masa de flujo desde una dirección específica utilizando Modbus . Primero crea un objeto
        de cliente TCP y abre una conexión al host y puerto especificados. Luego envía una solicitud de Modbus "leer
        registros de retención" para leer el valor de la masa de flujo desde la dirección especificada, y devuelve el resultado como

        Args:
            self : El objeto puntero.

        Returns:
            Una tupla con los siguientes elementos: 
            - Un entero que representa el valor de masa de flujo (en kg/h) que se leyó de la dirección especificada.
            - Un entero que representa el valor sin procesar que se leyó de la dirección especificada.
            - Un entero que representa el código de estado (siempre 0 en esta implementación ya que solo se lee un registro).

        """
    

        try:             
            client =  modbus_tcp.TcpMaster(host=LOCAL_IP, port=LOCAL_PORT)
            client.open()
            response= client.execute(slave=1, 
                                    function_code = READ_HOLDING_REGISTERS, 
                                    starting_address=3002, 
                                    quantity_of_x=2
                                    )
            client.set_timeout(5.0)
        
            decoder = BinaryPayloadDecoder.fromRegisters(
                                                    list(response),
                                                    byteorder=Endian.Little, wordorder=Endian.Little
                                                    )
            return (float('{0:.2f}'.format(decoder.decode_32bit_float())),
                    response[0],
                    response[1])

                                    
        except AssertionError as e:
            print(f"AssertionError: {e}")
            return None
        except ModbusException as e:
            print(f"ModbusException: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            client.close()
           


    def read_waterTotalizer(self):
        """
        Este método lee el valor del totalizador de agua desde una dirección específica utilizando Modbus . Primero crea un objeto
        de cliente TCP y abre una conexión al host y puerto especificados. Luego envía una solicitud de Modbus "leer registros de retención"
        cabe aclarar que lee 4 registros en formatos little endian para luego convertirlos a float
        
        Args:
            self: El objeto puntero.

        Returns:
            Una tupla con los siguientes elementos:
            - Un entero que representa el valor de presión (en PSI) que se leyó de la dirección especificada.
            - Un entero que representa el valor sin procesar que se leyó de la dirección especificada.
            NOTA TERMINAR LA DOCUMENTACION CUANDO SE REALICE EL RETURN DE DOS REGISTROS EN LUGAR DE 4 
        """

    
        try:             
            client =  modbus_tcp.TcpMaster(host=LOCAL_IP, port=LOCAL_PORT)
            client.open()
            response_hex = client.execute(slave=1, 
                                    function_code = READ_HOLDING_REGISTERS, 
                                    starting_address=3014, 
                                    quantity_of_x=4
                                    )
            client.set_timeout(5.0)

            decoder = BinaryPayloadDecoder.fromRegisters(list(response_hex), byteorder=Endian.Little, wordorder=Endian.Little)
            response_float = decoder.decode_64bit_float()
            response1, response2 = struct.unpack('>HH', struct.pack("f", response_float))

            return (float('{0:.2f}'.format(response_float)),response1, response2)
                                    
        except AssertionError as e:
            print(f"AssertionError: {e}")
            return None
        except ModbusException as e:
            print(f"ModbusException: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            client.close()
    
    
    
    def hook_read_holding_registers(self, request_pdu):
        """
        Este método se llama cuando se recibe una solicitud de Modbus "leer registros de retención" y devuelve una respuesta
        con el valor de los registros solicitados. Primero verifica que la solicitud sea válida y luego devuelve una respuesta
        con los valores de los registros solicitados.

        cabe aclarar que este metodo escribe los registros de retencion al final del metodo
        a demas este metodo se llama como hook por lo cual en cada solicitud de lectura de registros de retencion
        esta funcion sera llamada

        Args:
            self: El objeto puntero.
            request_pdu (tupla): una tupla con la siguiente informacion: 

                1. El objeto Slave de Modbus que maneja la comunicación con el dispositivo esclavo.
                2. Un objeto bytearray que representa la unidad de datos de protocolo de solicitud (PDU) de la función de lectura de registros de retención.
                EJEMPLO DE request_pdu:
                        (<modbus_tk.modbus.Slave object at 0x0000027E292AA010>, bytearray(b'\x03\x00\x08\x00\x01'))
                        en el cual la posicion [1,2] es el registro que se esta leyendo
        Returns:
            None 
        """
        #NOTA: ADDITIONAL INFORMATION PROVIDED BY THE ORIGINAL CODER
        """this is called just before handling the request"""
        """This will Read Analog Input AIN0 """
        """Register 0 will current and Register 1 will read voltage"""
       
       #NOTA: verificar si el mensaje llega como un extero o como un sting 
       # es decir 2 o '0x02' 

        # print(request_pdu[1]) #este es el registro que se esta leyendo
        # print(type(request_pdu[1][2])) #este es el tipo de dato que llega en el mensaje pdu
        

        if (request_pdu[1][2] == 0 or request_pdu[1][2] == '0x00') or (request_pdu[1][2] == 1 or request_pdu[1][2] == '0x01'):
            #ELABORAR EL RESTO DE CODIGO CORRESPONDIENTE, SIN EMBARGO PARECE TRABAJAR CON 
            #COMANDOS DEL SISTEMA PARA LEER PUERTOS FISICOS I/O
            ain = 0
            return 
            
        elif (request_pdu[1][2] == 2 or request_pdu[1][2] == '0x02') or (request_pdu[1][2] == 3 or request_pdu[1][2] == '0x03'):
            #para leer presion 
            ain = 2
            pressure2,ain_value_high,ain_value_low = self.Pressure(address_id=14)
            print(f"presion: {pressure2} \n valor alto : {ain_value_high} \n valor bajo:{ain_value_low}")
            
            
        elif (request_pdu[1][2] == 4 or request_pdu[1][2] == '0x04') or (request_pdu[1][2] == 5 or request_pdu[1][2] == '0x05'):
            ain = 4
            flowMass,ain_value_high,ain_value_low = self.read_MassFlow()
            print(f'flujo de masa de agua : {flowMass} \n valor alto : {ain_value_high} \n valor bajo:{ain_value_low}')
        
        elif (request_pdu[1][2] == 6 or request_pdu[1][2] == '0x06') or (request_pdu[1][2] == 7 or request_pdu[1][2] == '0x07'):
            ain = 6
            totalizer,ain_value_high,ain_value_low = self.read_waterTotalizer()
            print(f"totalizador de agua: {totalizer}")

        elif (request_pdu[1][2] == 8 or request_pdu[1][2] == '0x08') or (request_pdu[1][2] == 9 or request_pdu[1][2] == '0x09'):
            ain = 8
            pressure,ain_value_high,ain_value_low= self.Pressure(address_id=15)
            print(f"presion: {pressure} \n valor alto : {ain_value_high} \n valor bajo:{ain_value_low}")
            
        else:       
            print("Invalid register address to read from")
            return 

        #NOTA: Escribimos los valores en los registros de retencion
        self.slave1.set_values("hr0", ain, ain_value_high)
        self.slave1.set_values("hr0", ain + 1,ain_value_low)


if __name__ == "__main__":

        counter_error = 0

        
        while 1: 
            try:
                                
                #error case 
                # miclass = IX10ModbusIO('TsCP').start_serverIX10ModbusIO()
                #tcp server case
                # miclass = IX10ModbusIO('TCP').start_serverIX10ModbusIO()
                #serial RTU  server case 
                miclass = IX10ModbusIO('RTU').start_serverIX10ModbusIO()

                while 1: sleep(10)
                print("server ended")
                sleep(1)
               
            except Exception as e : 
                print(f"error al iniciar el servidor:\n\t{e} ")
                counter_error += 1
                if counter_error > 3:
                    print("el servidor no se pudo iniciar")
                    # cli.execute("reboot") 
                    break
               #NOTA: realizar el reboot del dispositivo en esta seccion si falla tres veces el programa
                
