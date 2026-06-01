import serial
import numpy as np
import matplotlib.pyplot as plt
import time
import struct

# Configuração da porta serial
SERIAL_PORT = 'COM4'
BAUD_RATE = 115200

# Sinal a ser enviado
fs = 20000      #Frequência de amostragem do sinal
amplitude = 2000   #Amplitude do sinal desejado
offset = 2048    #Offset do sinal desejado
fsig = 60      #Frequência do sinal
#TB = 2*(int)(fs/fsig)    #Tamano do buffer
TB = 666
sinal = [None]*TB     #Vetor vazio
#Loop para criar o vetor do sinal
fsig_es = input("Escolha uma frequência: (1-60Hz; 2-120Hz; 3-240Hz)")
if fsig_es == '1':
    fsig = 60
elif fsig_es == '2':
    fsig = 120
elif fsig_es == '3':
    fsig = 240
else:
    fsig = 60
    
for key in range(TB):
    sinal[key] = (int)(amplitude*np.sin(2*np.pi*fsig*key/fs) + offset)

#Função de envio de um int em bytes pela serial
def send_int_to_uart(serialobj: serial.Serial, value: int, byteorder: str) -> None:
    # Converter o valor float em bytes
    endian_format = '<' if byteorder == 'little' else '>'
    bytes_to_send = struct.pack(f'{endian_format}h', value)
    # Enviar os bytes pela porta serial
    serialobj.write(bytes_to_send)

#Função principal
def main():
    try:
        # Abre a porta serial usando um bloco 'with' para garantir que ela seja fechada
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
            print(f"Porta serial {SERIAL_PORT} aberta com sucesso a {BAUD_RATE} bps.")
            time.sleep(1) # Um pequeno tempo para a serial estabilizar
            ser.flushInput() #limpa bytes remanescentes do buffer de entrada

            for key in range(TB):
                send_int_to_uart(ser,sinal[key],'little')

            plt.figure()
            plt.plot(sinal)
            plt.show()


            # while True:
            #     pass

    except serial.SerialException as e:
        print(f"\nERRO: Nao foi possivel abrir a porta serial '{SERIAL_PORT}'.")
        print(f"Detalhe: {e}")
        print("Verifique se a porta esta correta e se nenhum outro programa a esta usando.")
    

if __name__ == '__main__':
    main()