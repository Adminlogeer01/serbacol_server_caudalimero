import datetime, time
import sarcli
from BaseWizard import write_cli

#datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#tiempos  = ["00:00:00","04:00:00","08:00:00","12>00:00","16:00:00"<"20:00:00"]
#tiempos  = ["14:40:00","14:50:00","15:00:00","15:10:80","15:20:00","15:30:00"]
tiempos  = ["15:00","45:00"]

#Funcion para los comandos
def Get_Cli(comando):
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

#Funcion para extrqer un linea uspecmfica
def Getline(palabra, datos):
    respuesta = ""
    for line in datos.splitlines():
        if palabra in line:
            respuesta += line
    return respuesta

hora = datetime.datetime.now().strftime('%M:%S')
print("\nHora actual:\n%s"%(hora))
print("\nHorqs de reinicio:\n%s"%(tiempos))

eventlog = write_cli('setevent "Reinicios %s"'%tiempos)

while 1:
    hora = datetime.datetime.now().strftime('%M:%S')
    print("Hora: %s"%hora)
    if(hora in tiempos):
        print("Reiniciando python")
        eventlog = write_cli('setevent "Reinicio de las %s"'%hora)
        Get_Cli("reboot")
    time.sleep(1) 




# reinicio.py ejecuta un reinicio del sitema a las () horas, sin embargo se 
# eliminara esta archivo y se ejecutara el reinicio desde el sistema del digi