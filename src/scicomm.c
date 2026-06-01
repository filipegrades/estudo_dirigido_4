/*
 * scicomm.c
 *
 *  Created on: 13 de jun de 2025
 *      Author: Guilherme Márcio Soares
 */
#include "board.h"
#include "device.h"
#include "scicomm.h"


int protocolReceiveInt(unsigned int sci_base)
{
    uint16_t buffer[INT_SIZE];
    SCI_readCharArray(sci_base, buffer, INT_SIZE);
    return (buffer[0] | (buffer[1] << 8U));
}

void protocolSendInt(unsigned int sci_base,int data)
{
    uint16_t txBuf[INT_SIZE];
    txBuf[0] = (uint16_t)(data & 0x00FF);
    txBuf[1] = (uint16_t)((data >> 8U) & 0x00FF);

    SCI_writeCharArray(sci_base, txBuf, INT_SIZE);
}
