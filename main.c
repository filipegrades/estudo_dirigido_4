//
// Included Files
//
#include "driverlib.h"
#include "device.h"
#include "board.h"
#include "scicomm.h"

#define TB 666

int g_signal_buffer[TB];
int g_cont = 0;


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
        
    }
}

__interrupt void INT_SCI0_RX_ISR(void)
{
    g_signal_buffer[g_cont] = protocolReceiveInt(SCI0_BASE);
    g_cont = (g_cont+1)%TB;
    
    SCI_clearInterruptStatus(SCI0_BASE, SCI_INT_RXFF);
    Interrupt_clearACKGroup(INT_SCI0_RX_INTERRUPT_ACK_GROUP);
}

__interrupt void INT_myCPUTIMER1_ISR(void)
{
    static uint16_t cnt_dac = 0;
    DAC_setShadowValue(DAC0_BASE, (uint16_t) (g_signal_buffer[cnt_dac]));
    cnt_dac = (cnt_dac+1)%TB;
}