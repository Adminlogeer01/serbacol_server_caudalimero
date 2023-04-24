import socket

# definimos el host y el puerto
HOST = '127.0.0.1'
# HOST = '166.210.132.95'
PORT = 20106
datos = "none"
# creamos el socket y nos conectamos al servidor

def client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print('Creando socket')
        try:
            s.connect((HOST, PORT))
            print('Conectado al servidor')

            # enviamos un mensaje al servidor
            mensaje = 'CONSULTAR'
            s.sendall(mensaje.encode())

            # recibimos la respuesta del servidor
            datos = s.recv(1024)
            print('Respuesta del servidor:', datos.decode())

        except Exception as error:
            print(error)

if __name__ == '__main__':
    client()