/*
_433D.h
2015-11-17
Public Domain
*/

#ifndef _433D_H
#define _433D_H

struct _433D_rx_s;

typedef struct _433D_rx_s _433D_rx_t;

struct _433D_tx_s;

typedef struct _433D_tx_s _433D_tx_t;

typedef struct
{
   uint64_t code;
   int bits;
   int gap;
   int t0;
   int t1;
} _433D_rx_data_t;

typedef void (*_433D_rx_CB_t)(_433D_rx_data_t);

/* RX

_433D_rx starts a receiver on Pi pi with GPIO gpio.  By default
only codes with bit length 8-32 are reported and any edges
shorter than 150 microseconds are ignored.

_433D_rx_set_bits may be used to exclude codes less than min_bits
bits and more than max_bits bits.  Such codes will be assumed to
be an error and will be ignored.

_433D_rx_set_glitch may be used to exclude any level changes shorter
than glitch microseconds long.  This is useful when the receiver is
prone to static interference.

If cb_func is not null it will be called whenever a valid code
is received.  The callback receives a _433D_rx_data_t object.

If cb_func is null then the _433D_rx_ready function should be
called to check for new data which may then be retrieved by
a call to _433D_rx_data.

At program end the rx receiver should be cancelled using
_433D_rx_cancel.  This releases system resources.

*/


_433D_rx_t *_433D_rx           (int pi, int gpio, _433D_rx_CB_t cb_func);
void        _433D_rx_cancel    (_433D_rx_t *self);
int         _433D_rx_ready     (_433D_rx_t *self);
uint64_t    _433D_rx_code      (_433D_rx_t *self);
void        _433D_rx_data      (_433D_rx_t *self, _433D_rx_data_t *data);
void        _433D_rx_set_bits  (_433D_rx_t *self, int min_bits, int max_bits);
void        _433D_rx_set_glitch(_433D_rx_t *self, int glitch);

/* TX

_433D_tx starts a transmitter on Pi pi with GPIO gpio.

_433D_tx_send tranmits a code.  By default the code is 24 bits long
and is sent 6 times.  The default intercode gap is 9000, short
pulse is 300, and long pulse is 900 microseconds,

_433D_tx_set_repeats sets the number of times a code should be sent.

_433D_tx_set_bits sets the transmitted code length in bits.

_433D_tx_set_timings sets the intercode gap, short pulse, and
long pulse length in microseconds.

At program end the tx transmitter should be cancelled using
_433D_tx_cancel.  This releases system resources.

*/

_433D_tx_t *_433D_tx            (int pi, int gpio);
void        _433D_tx_cancel     (_433D_tx_t *self);
void        _433D_tx_send       (_433D_tx_t *self, uint64_t code);
void        _433D_tx_set_repeats(_433D_tx_t *self, int repeats);
void        _433D_tx_set_bits   (_433D_tx_t *self, int bits);
void        _433D_tx_set_timings(_433D_tx_t *self, int gap, int t0, int t1);

#endif

