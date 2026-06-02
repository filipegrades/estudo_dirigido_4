import serial
import numpy as np
import matplotlib.pyplot as plt
import time
import struct

# Configuração da porta serial
SERIAL_PORT = 'COM4'
BAUD_RATE = 115200
DATA_BITS = 2

# Sinal a ser enviado
fs = 20000      #Frequência de amostragem do sinal
amplitude = 1500   #Amplitude do sinal desejado
offset = 2048    #Offset do sinal desejado
fsig = 120      #Frequência do sinal
#TB = 2*(int)(fs/fsig)    #Tamano do buffer
TB = 334
sinal = [None]*TB     #Vetor vazio
adc_signal = [None]*TB
fs_dac = 20000    # Frequência que o Python usa para gerar o vetor (Timer do DAC)
fs_adc = 10000    # Nova frequência de amostragem do hardware

#Loop para criar o vetor do sinal
print("Escolha o cenário de harmônicos para injetar no sinal:")
print("1 - Harmônico ABAIXO de Nyquist (f = 3.000 Hz) -> Captura perfeita")
print("2 - Harmônico NA Frequência de Nyquist (f = 10.000 Hz) -> Limite teórico")
print("3 - Harmônico ACIMA de Nyquist (f = 17.000 Hz) -> Efeito de Aliasing (Rebatimento)")
opc = input("Opção: ")

# Define a frequência e amplitude do harmônico com base na escolha
if opc == '1':
    f_harmonico = 3000
    amp_harmonico = 500  
    print(f"\nGerando Fundamental (1200Hz) + Harmônico de {f_harmonico} Hz...")
elif opc == '2':
    f_harmonico = 5000
    amp_harmonico = 500  
    print(f"\nGerando Fundamental (1200Hz) + Harmônico de {f_harmonico} Hz (Nyquist)...")
elif opc == '3':
    f_harmonico = 8000
    amp_harmonico = 500  
    print(f"\nGerando Fundamental (1200Hz) + Harmônico de {f_harmonico} Hz (Aliasing)...")
elif opc == '4':
    f_harmonico = 0
    amp_harmonico = 0  
    print(f"\nGerando Fundamental (120Hz) + Harmônico de {f_harmonico} Hz (Aliasing)...")
else:
    f_harmonico = 0
    amp_harmonico = 0
    print("\nApenas a componente fundamental de 120Hz será enviada.")

# 1. Cria o vetor de tempo absoluto para o DAC (em segundos)
t_dac = np.arange(TB) / fs_dac

# Gera o sinal usando o vetor de tempo do DAC diretamente
for key in range(TB):
    fundamental = amplitude * np.sin(2 * np.pi * fsig * t_dac[key])
    harmonico = amp_harmonico * np.sin(2 * np.pi * f_harmonico * t_dac[key])
    sinal[key] = int(fundamental + harmonico + offset)

# for key in range(TB):
#     sinal[key] = (int)(amplitude*np.sin(2*np.pi*fsig*key/fs) + offset)

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
# Limpa qualquer "lixo" que tenha ficado na linha antes de pedir os dados
            ser.flushInput() 
            
            # Envia o gatilho
            send_int_to_uart(ser, 32000, 'little')

            # Lê todos os 666 bytes (333 int16) de uma só vez
            # Isso evita que o SO atrase a leitura entre um byte e outro
            raw_data = ser.read(TB * 2)

            if len(raw_data) == TB * 2:
                # Converte o bloco de bytes direto para o vetor Numpy
                adc_signal = np.frombuffer(raw_data, dtype=np.int16)
                
                # 2. Cria o vetor de tempo absoluto para o ADC lido (em segundos)
                # Como o ADC roda na metade da velocidade, ele demorou o dobro do tempo
                # para preencher os mesmos 333 pontos.
                t_adc = np.arange(len(adc_signal)) / fs_adc
                
                # FFT DO SINAL ENVIADO
                xf_sinal = np.fft.rfftfreq(TB, 1/fs_dac)
                fft_sinal = (2.0 / TB) * np.abs(np.fft.rfft(sinal))

                # FFT DO SINAL LIDO
                xf_adc = np.fft.rfftfreq(len(adc_signal), 1/fs_adc)
                fft_adc = (2.0 / len(adc_signal)) * np.abs(np.fft.rfft(adc_signal))

                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

                # Plot no Tempo (Multiplicando por 1000 para exibir em milissegundos)
                ax1.plot(t_dac * 1000, sinal, label="Sinal Enviado (DAC a 20kHz)", linewidth=2)
                ax1.plot(t_adc * 1000, adc_signal, label="Sinal Lido (ADC a 10kHz)", linewidth=2)
                
                ax1.set_title("Sinais no Domínio do Tempo")
                ax1.set_xlabel("Tempo (ms)")
                ax1.set_ylabel("Amplitude")

                # Descobre o tempo máximo de cada vetor (multiplicado por 1000 para ficar em ms)
                max_tempo_dac = t_dac[-1] * 1000
                max_tempo_adc = t_adc[-1] * 1000
                
                # Encontra o menor valor temporal para cortar o gráfico no ponto exato
                limite_x_tempo = min(max_tempo_dac, max_tempo_adc)
                ax1.set_xlim(0, limite_x_tempo)
                
                ax1.legend()
                ax1.grid(True, linestyle='--', alpha=0.7)

                # Plot na Frequência
                ax2.plot(xf_sinal, fft_sinal, label="FFT Enviada (Pico em 8kHz)", color='blue', marker='o', markersize=4)
                ax2.plot(xf_adc, fft_adc, label="FFT Lida (Aliasing em 2kHz)", color='orange', marker='x', markersize=6)
                
                ax2.set_title("Espectro de Frequências - Aliasing Físico no C2000")
                ax2.set_xlabel("Frequência (Hz)")
                ax2.set_ylabel("Magnitude")
                
                # ax2.set_xlim(0, 10000) 
                # ax2.set_ylim(0, amplitude + 200)

                # Linhas de Nyquist
                ax2.axvline(x=10000, color='blue', linestyle=':', label='Nyquist do DAC (10kHz)')
                ax2.axvline(x=5000, color='orange', linestyle='--', label='Nyquist do ADC (5kHz)')
                
                ax2.legend()
                ax2.grid(True, linestyle='--', alpha=0.7)

                plt.tight_layout()
                plt.show()
            else:
                print(f"Erro de timeout: Foram recebidos {len(raw_data)} bytes de {TB * 2} esperados.")

            # plt.figure()
            # plt.plot(sinal)
            # plt.plot(adc_signal)
            # plt.show()


            # while True:
            #     pass

    except serial.SerialException as e:
        print(f"\nERRO: Nao foi possivel abrir a porta serial '{SERIAL_PORT}'.")
        print(f"Detalhe: {e}")
        print("Verifique se a porta esta correta e se nenhum outro programa a esta usando.")
    

if __name__ == '__main__':
    main()