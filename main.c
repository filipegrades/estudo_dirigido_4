//
// Included Files
//
#include "driverlib.h"
#include "device.h"
#include "board.h"
#include "scicomm.h"

#define TB 200

int g_signal_buffer[TB];
int g_cont = 0;
int g_adc_signal_buffer[TB];
int g_adc_cont = 0;
bool g_flagEnviaBuffer = false;
int g_envia_cont = 0;
int i=0;

//
// Fun��o Principal
//
void main(void)
{
    // Inicializa��o do dispositivo
    Device_init();
    Interrupt_initModule();
    Interrupt_initVectorTable();
    Board_init();

    // Habilita interrup��es globais e de tempo real
    EINT;
    ERTM;

    while (1)
    {
        if(g_flagEnviaBuffer)
        {
            for(i=0; i<TB; i++)
            {
                protocolSendInt(SCI0_BASE, g_adc_signal_buffer[g_envia_cont]);
                g_envia_cont = (g_envia_cont+1)%TB;
            }

            g_flagEnviaBuffer = false;
        }
        
    }
}

__interrupt void INT_SCI0_RX_ISR(void)
{
    int dado;
    dado = protocolReceiveInt(SCI0_BASE);
    if(dado == 32000)
    {
        g_flagEnviaBuffer = true;
    }
    else 
    {
        g_signal_buffer[g_cont] = dado;
        g_cont = (g_cont+1)%TB;
    }
    
    SCI_clearInterruptStatus(SCI0_BASE, SCI_INT_RXFF);
    Interrupt_clearACKGroup(INT_SCI0_RX_INTERRUPT_ACK_GROUP);
}

__interrupt void INT_myCPUTIMER1_ISR(void)
{
    static uint16_t cnt_dac = 0;
    DAC_setShadowValue(DAC0_BASE, (uint16_t) (g_signal_buffer[cnt_dac]));
    cnt_dac = (cnt_dac+1)%TB;
}

__interrupt void INT_ADC0_1_ISR(void)
{
    g_adc_signal_buffer[g_adc_cont] = ADC_readResult(ADC0_RESULT_BASE, ADC0_SOC0);
    g_adc_cont = (g_adc_cont+1)%TB;
    ADC_clearInterruptStatus(ADC0_BASE, ADC_INT_NUMBER1);
    Interrupt_clearACKGroup(INT_ADC0_1_INTERRUPT_ACK_GROUP);
}