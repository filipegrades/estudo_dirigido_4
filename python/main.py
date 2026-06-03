import serial
import numpy as np
import matplotlib.pyplot as plt
import time
import struct

# Configuração da porta serial
SERIAL_PORT = 'COM4'
BAUD_RATE = 115200

# Valores utilizado nas frequências e vetores
fs_dac = 20000
fs_adc = 10000
TB = 200    # Tamanhos vetores
dac_signal = [None]*TB    
adc_signal = [None]*TB

# Configurações dos sinais a serem sintetizados
fs = fs_dac
t_base = np.arange(TB)/fs
offset = 2048
f1 = 500
f1_2 = 1000
amplitude1 = 1000
f2 = 2000
amplitude2 = 750
f3 = 5000
amplitude3 = 500
f4 = 7000
amplitude4 = 250

#Função de envio de um int em bytes pela serial
def send_int_to_uart(serialobj: serial.Serial, value: int, byteorder: str) -> None:
    # Converter o valor float em bytes
    endian_format = '<' if byteorder == 'little' else '>'
    bytes_to_send = struct.pack(f'{endian_format}h', value)
    # Enviar os bytes pela porta serial
    serialobj.write(bytes_to_send)

# Função de recepção do bloco completo de interios
def receive_int_vector_from_uart(serialobj: serial.Serial, tb: int):
    # Limpa qualquer "lixo" que tenha ficado na linha antes de pedir os dados
    serialobj.flushInput()
    # Envia o pedido de envio do buffer
    send_int_to_uart(serialobj, 32000, 'little')
    
    # Realiza a leitura de todo o bloco de dados
    raw_data = serialobj.read(tb * 2)
    
    if len(raw_data) == tb * 2:
        # Converte o bloco de bytes para o vetor int e JÁ RETORNA ELE PRONTO
        return np.frombuffer(raw_data, dtype=np.int16)
    else:
        print(f"\n[AVISO] Timeout na Serial! Recebidos {len(raw_data)} bytes.")
        return None

# Função para plotagem dos graficos
def plotting(sinal_dac:int, fs_dac:int, sinal_adc:int, fs_adc:int):
    """
    Gera os gráficos de tempo e frequência recebendo os vetores e taxas de amostragem.
    """
    tb_dac = len(sinal_dac)
    tb_adc = len(sinal_adc)

    t_dac = np.arange(tb_dac) / fs_dac
    t_adc = np.arange(tb_adc) / fs_adc
    
    # ==========================================
    # FFT E CORREÇÃO DO OFFSET (DC)
    # ==========================================
    xf_dac = np.fft.rfftfreq(tb_dac, 1/fs_dac)
    fft_dac = (2.0 / tb_dac) * np.abs(np.fft.rfft(sinal_dac))
    fft_dac[0] = fft_dac[0] / 2.0  # Corrige o valor dobrado em 0 Hz

    xf_adc = np.fft.rfftfreq(tb_adc, 1/fs_adc)
    fft_adc = (2.0 / tb_adc) * np.abs(np.fft.rfft(sinal_adc))
    fft_adc[0] = fft_adc[0] / 2.0  # Corrige o valor dobrado em 0 Hz
    # ==========================================

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # --- Subplot 1: Tempo ---
    ax1.plot(t_dac * 1000, sinal_dac, label=f"Sinal Enviado", color='purple', linewidth=2)
    ax1.plot(t_adc * 1000, sinal_adc, label=f"Sinal Amostrado", color='darkorange', linewidth=2)
    
    ax1.set_title("Sinais no Domínio do Tempo")
    ax1.set_xlabel("Tempo (ms)")
    ax1.set_ylabel("Amplitude")
    
    limite_x_tempo = min(t_dac[-1] * 1000, t_adc[-1] * 1000)
    4
    ax1.set_xlim(0, limite_x_tempo)
    
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.7)

    # --- Subplot 2: Frequência (Linhas Limpas) ---
    ax2.plot(xf_dac, fft_dac, label="FFT do Sinal Enviado", color='purple')
    ax2.plot(xf_adc, fft_adc, label="FFT do Sinal Amostrado", color='darkorange')
    
    ax2.set_title("Espectro de Frequências - FFT")
    ax2.set_xlabel("Frequência (Hz)")
    ax2.set_ylabel("Magnitude")
    
    # ==========================================
    # LÓGICA DO EIXO X DINÂMICO (Grid de 500 Hz)
    # ==========================================
    limiar_ruido = 50 
    freqs_com_sinal = xf_dac[fft_dac > limiar_ruido]
    
    max_freq_real = np.max(freqs_com_sinal) if len(freqs_com_sinal) > 0 else 0
    limite_freq = min(fs_dac / 2, max_freq_real + 500)
    
    # Arredonda para o próximo múltiplo de 500 para manter o grid simétrico no final
    limite_freq = np.ceil(limite_freq / 500) * 500
    limite_freq = max(fs_adc / 2, limite_freq)

    # Aplica o limite dinâmico e o grid customizado de 500 em 500
    ax2.set_xlim(0, limite_freq) 
    ax2.set_xticks(np.arange(0, limite_freq + 1, 500))
    # ==========================================
    
    # Linhas indicativas de Nyquist
    ax2.axvline(x=fs_dac/2, color='purple', linestyle=':')
    ax2.axvline(x=fs_adc/2, color='darkorange', linestyle='--')
    
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.7)

    # Rotaciona levemente os números do eixo X para não ficarem amontoados
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    plt.show()

# Função principal
def main():
    try:
        # Abre a porta serial usando um bloco 'with' para garantir que ela seja fechada
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
            print(f"Porta serial {SERIAL_PORT} aberta com sucesso a {BAUD_RATE} bps.")
            time.sleep(1) # Um pequeno tempo para a serial estabilizar
            ser.flushInput() #limpa bytes remanescentes do buffer de entrada

            while True:
                print("Escolha o sinal a ser enviado:")
                print("1 - Sinal contendo apenas a frequencia fundamental de 500 Hz")
                print("2 - Sinal com a frequencia igual ao dobro da fundamental -> 1000 Hz")
                print("3- Sinal com a fundamental (500Hz) mais harmônicos,\n um abaixo da frequencia de Nyquist (2000 Hz),\n" \
                " um na frequeência de Nyquist (5000 Hz) e\n um acima da frequência de Nyquist (7000 Hz)")
                print("4 - Sair")
                se = input("Opção: ")

                #Pela opção escolhida realiza-se o preenchimento do buffer a ser enviado
                if se == '1':
                    dac_signal = (
                        offset + 
                        amplitude1 * np.sin(2 * np.pi * f1 * t_base) 
                    ).astype(int)
                elif se == '2':
                    dac_signal = (
                        offset + 
                        amplitude1 * np.sin(2 * np.pi * f1_2 * t_base) 
                    ).astype(int)
                elif se == '3':
                    dac_signal = (
                        offset + 
                        amplitude1 * np.sin(2 * np.pi * f1 * t_base) + 
                        amplitude2 * np.sin(2 * np.pi * f2 * t_base) + 
                        amplitude3 * np.sin(2 * np.pi * f3 * t_base) + 
                        amplitude4 * np.sin(2 * np.pi * f4 * t_base)
                    ).astype(int)
                elif se == '4':
                    break
                else:
                    dac_signal = (
                        offset + 
                        amplitude1 * np.sin(2 * np.pi * f1 * t_base) 
                    ).astype(int)   

                ser.flushInput()
                for key in range(TB):
                    send_int_to_uart(ser,dac_signal[key],'little')

                adc_signal = receive_int_vector_from_uart(ser,TB)

                plotting(dac_signal,fs_dac,adc_signal,fs_adc)



    except serial.SerialException as e:
        print(f"\nERRO: Nao foi possivel abrir a porta serial '{SERIAL_PORT}'.")
        print(f"Detalhe: {e}")
        print("Verifique se a porta esta correta e se nenhum outro programa a esta usando.")


if __name__ == '__main__':
    main()