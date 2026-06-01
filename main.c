
#include "driverlib.h"
#include "device.h"
#include "board.h"
#include "scicomm.h"

#define TB 666

static int buffer[TB];
static int cont = 0;

//
// Main
//
void main(void)
{
    // Device Initialization
    Device_init();

    //
    // Initializes PIE and clears PIE registers. Disables CPU interrupts.
    //
    Interrupt_initModule();

    //
    // Initializes the PIE vector table with pointers to the shell Interrupt
    // Service Routines (ISR).
    //
    Interrupt_initVectorTable();

	Board_init();

    //
    // Enable Global Interrupt (INTM) and realtime interrupt (DBGM)
    //
    EINT;
    ERTM;

    while(1)
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


//
// End of File
//
