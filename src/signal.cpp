#include "signal.h"

/***********************************************************************
 * Signal handlers
 **********************************************************************/

bool stop_signal_called = false;

void sig_int_handler(int)
{
    stop_signal_called = true;
}
