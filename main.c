//
// Included Files
//
#include "driverlib.h"
#include "device.h"
#include "board.h"
#include "scicomm.h"

#define TB 666

static int buffer[TB];
static int cont = 0;


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
    buffer[cont] = protocolReceiveInt(SCI0_BASE);
    cont = (cont+1)%TB;
    
    SCI_clearInterruptStatus(SCI0_BASE, SCI_INT_RXFF);
    Interrupt_clearACKGroup(INT_SCI0_RX_INTERRUPT_ACK_GROUP);
}

