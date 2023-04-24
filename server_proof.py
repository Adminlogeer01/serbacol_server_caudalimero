# from pymodbus.server import ModbusTcpServer
# from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
# from pymodbus.datastore import ModbusSequentialDataBlock
# from pymodbus.server import StartTcpServer
# from pymodbus.client import ModbusTcpClient
# from pymodbus.pdu import ModbusRequest
# from pymodbus.server.async_io import ModbusConnectedRequestHandler
# from pymodbus.logging import Log
# from pymodbus.client.mixin import ModbusClientMixin 


# from pymodbus.datastore.context import ModbusServerContext 



# import pymodbus.bit_read_message as pdu_bit_read
# import pymodbus.bit_write_message as pdu_bit_write
# import pymodbus.diag_message as pdu_diag
# import pymodbus.file_message as pdu_file_msg
# import pymodbus.mei_message as pdu_mei
# import pymodbus.other_message as pdu_other_msg
# import pymodbus.register_read_message as pdu_reg_read
# import pymodbus.register_write_message as pdu_req_write
# from pymodbus.pdu import ModbusRequest, ModbusResponse

# from modbus_tk import modbus_rtu

# from pymodbus.exceptions import ModbusException
# from pymodbus.payload import BinaryPayloadDecoder,Endian
# from pymodbus.client import ModbusTcpClient
# from pymodbus.server import StartSerialServer,StartTcpServer
# from pymodbus.server.async_io import ModbusBaseRequestHandler
# from pymodbus.datastore import ModbusSequentialDataBlock
# from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
# from serial import Serial

# LOCAL_IP = '127.0.0.1'
# LOCAL_PORT = 402   

# def read_waterTotalizer():
#     print("consulta a totalizador de agua")

#     with ModbusTcpClient(LOCAL_IP, port= LOCAL_PORT) as client:
#         try:             
#             client.connect()
#             response_hex = client.read_holding_registers(address=3014,count=4,unit=1)
            
#             assert not response_hex.isError(), f'Error al leer el registro'
            
#             decoder = BinaryPayloadDecoder.fromRegisters(response_hex, byteorder=Endian.Big, wordorder=Endian.Little)
#             response_float = decoder.decode_64bit_float()
            
            
#             print(f"\n     TotalizadorAgua: {response_float} L")
#             return float('{0:.2f}'.format(response_float))
                                    
#         except AssertionError as e:
#             print(f"AssertionError: {e}")
#             return None
#         except ModbusException as e:
#             print(f"ModbusException: {e}")
#             return None
#         except Exception as e:
#             print(f"Error: {e}")
#             return None


# class Myhandle(ModbusConnectedRequestHandler):
#     def connection_made( transport):
#         print(f"connection made in {transport}\n\n\n") 
#         """Call when a connection is made."""
#         super().connection_made(transport)

#         client_address = (  # pylint: disable=attribute-defined-outside-init
#             transport.get_extra_info("peername")
#         )
#         server.active_connections[client_address] = #         txt = f"TCP client connection established [{client_address[:0]}]"
#         Log.debug(txt)

    
#     def data_received( data):
#         """Call when some data is received.

#         data is a non-empty bytes object containing the incoming data.
#         """
        
#         print(f"read data:{data}")
#         receive_queue.put_nowait(data)


#     def _send_( data):
#         """Send tcp."""
        
#         # print(f"send data:{hex(data[7])}\n")
#         print(f"send data:{data}\n")
#         transport.write(data)




# def setup_server():
    
#     store=ModbusSlaveContext(
#                             di=ModbusSequentialDataBlock(0, [1]*100),
#                             co=ModbusSequentialDataBlock(0, [1]*100),
#                             hr=ModbusSequentialDataBlock(0, [4]*20),
#                             ir=ModbusSequentialDataBlock(0, [1]*100)
#                             )
                           
#     context = ModbusServerContext(slaves={1:store}, single=False)
#     return context

# def run_TCP_server(context: ModbusServerContext):
#     print("Starting TCP Server..")
        
#     server = StartTcpServer(
#                             context = context, 
#                             address=("127.0.0.1",402),
#                             allow_reuse_address=False,
#                             # custom_functions=[handleproof],
                         
#                             defer_start=False,
#                             handler=Myhandle
#                             )
#     return server
    
# if __name__ == "__main__":
#     context = setup_server()
#     server = run_TCP_server(context)


from modbus_tk.modbus_tcp import TcpServer
from modbus_tk.defines import HOLDING_REGISTERS, COILS
from modbus_tk import hooks

from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder, Endian
from pymodbus.exceptions import ModbusException
import struct

LOCAL_IP = '127.0.0.1'
LOCAL_PORT = 402


def setup_slave(server):
    slave1 = server.add_slave(1)
    slave1.add_block("hr0",HOLDING_REGISTERS, 0, 20) # 4 cambiado a 6 y de 6 a 10
    slave1.add_block("c0-1",COILS, 100, 0)

def create_TCP_server():
    tcp_server = TcpServer(timeout_in_sec=3)
    tcp_server.start()
    setup_slave(tcp_server)

def star_server():
    create_TCP_server()
    print('creando el hook')
    hooks.install_hook("modbus.Slave.handle_read_holding_registers_request", hook_read_holding_registers)
    print("Server started")


def read_Pressure( address_id: int) -> int:
    print("consulta a Ptap")
    
    with ModbusTcpClient(LOCAL_IP,port= LOCAL_PORT) as client:
        try:             
            client.connect()
            response_hex = client.read_holding_registers(address=address_id,count=1,unit=4)

            assert not response_hex.isError(), f'Error al leer el registro' 
            
            # response_int = int(response_hex.registers,16)
            decoder = BinaryPayloadDecoder.fromRegisters(response_hex.registers, byteorder=Endian.Big)
            response_int = decoder.decode_16bit_uint()
            
            response_high = decoder.decode_16bit_uint()
            response_low = decoder.decode_16bit_uint()

            if response_int < 100:
                print(f'presion despues es igual a {response_int}')
                print(f'presion {response_int} PSI')
            else:
                response_int = 60
            return (response_int, response_high, response_low)
                        
        except AssertionError as e:
            print(f"AssertionError: {e}")
            return None
        except ModbusException as e:
            print(f"ModbusException: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
        

def read_MassFlow():
    print("consulta a flujo de masa")

    with ModbusTcpClient(LOCAL_IP, port= LOCAL_PORT) as client:
        try:             
            client.connect()
            response_hex = client.read_holding_registers(address=3002,count=3,unit=1)
            
            assert not response_hex.isError(), f'Error al leer el registro'
            
            decoder = BinaryPayloadDecoder.fromRegisters(response_hex.registers, byteorder=Endian.Big)
            response_float = decoder.decode_32bit_float() * 1000 
            print(f"\n     FlujoMasaAbsoluta: {response_float} L/s")
            return float('{0:.2f}'.format(response_float))
                                    
        except AssertionError as e:
            print(f"AssertionError: {e}")
            return None
        except ModbusException as e:
            print(f"ModbusException: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
        
def read_waterTotalizer():
    print("consulta a totalizador de agua")

    with ModbusTcpClient(LOCAL_IP, port= LOCAL_PORT) as client:
        try:             
            client.connect()
            response_hex = client.read_holding_registers(address=3014,count=4,unit=1)
            
            assert not response_hex.isError(), f'Error al leer el registro'
            
            decoder = BinaryPayloadDecoder.fromRegisters(response_hex, byteorder=Endian.Big, wordorder=Endian.Little)
            response_float = decoder.decode_64bit_float()
            
            
            print(f"\n     TotalizadorAgua: {response_float} L")
            return float('{0:.2f}'.format(response_float))
                                    
        except AssertionError as e:
            print(f"AssertionError: {e}")
            return None
        except ModbusException as e:
            print(f"ModbusException: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None


def hook_read_holding_registers(request_pdu):
    
    print(request_pdu[1])
    print(request_pdu[1][0])


    if (request_pdu[1][0] == '\x00') or (request_pdu[1][0] == '\x01'):
        pass
    elif (request_pdu[1][0] == '\x02') or (request_pdu[1][0] == '\x03'):
        #para leer presion 
    
        print('funcion llamada de alguna forma')
        ain = 0
        Presion2,ain_value_high,ain_value_low = read_Pressure(address_id=14)
        # LOGGER.debug("Valor de Presion2: ( % s )" % Presion2)
        ain_value_high, ain_value_low = struct.unpack('>HH', struct.pack('f', Presion2))
        print(Presion2)
        
    elif (request_pdu[1][0] == '\x04') or (request_pdu[1][0] == '\x05'):
        pass
    elif (request_pdu[1][0] == '\x06') or (request_pdu[1][0] == '\x07'):
        pass
    elif (request_pdu[1][0] == '\x08') or (request_pdu[1][0] == '\x09'):
        pass
    else:
        pass



if __name__ == "__main__":
    star_server() 