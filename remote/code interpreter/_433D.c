/*
_433D.c
2015-11-17
Public Domain
*/

#include <stdio.h>
#include <stdlib.h>

#include <pigpiod_if2.h>

#include "_433D.h"

/*

RX

Code to read the wireless codes transmitted by 433 MHz wireless fobs.

*/

struct _433D_rx_s
{
   int pi;
   int gpio;
   _433D_rx_CB_t cb;
   int min_bits;
   int max_bits;
   int glitch;

   int _cb_id;

   int _in_code;
   int _edge;
   int _bits;
   uint64_t _code;

   int _gap;
   int _t0, _t1;

   int _ready;
   _433D_rx_data_t _data;

   uint32_t _last_edge_tick;
   int _e0, _even_edge_len;
   int _min0, _max0, _min1, _max1;
};

static void _timings(_433D_rx_t *self, int e0, int e1)
{
   /*
   Accumulates the short and long pulse length so that an
   average short/long pulse length can be calculated. The
   figures may be used to tune the transimission settings.
   */
   int shorter, longer;

   if (e0 < e1)
   {
      shorter = e0;
      longer = e1;
   }
   else
   {
      shorter = e1;
      longer = e0;
   }

   if (self->_bits)
   {
      self->_t0 += shorter;
      self->_t1 += longer;
   }
   else
   {
      self->_t0 = shorter;
      self->_t1 = longer;
   }

   self->_bits += 1;
}

static void _calibrate(_433D_rx_t *self, int e0, int e1)
{
   /*
   The first pair of pulses is used as the template for
   subsequent pulses.  They should be one short, one long, not
   necessarily in that order.  The ratio between long and short
   should really be 2 or more.  If less than 1.5 the pulses are
   assumed to be noise.
   */
   float ratio;
   int slack0, slack1;

   self->_bits = 0;
   _timings(self, e0, e1);
   self->_bits = 0;

   ratio = (float)self->_t1 / (float)self->_t0;

   if (ratio < 1.5) self->_in_code = 0;

   slack0 = 0.5 * self->_t0;
   slack1 = 0.3 * self->_t1;

   self->_min0 = self->_t0 - slack0;
   self->_max0 = self->_t0 + slack0;
   self->_min1 = self->_t1 - slack1;
   self->_max1 = self->_t1 + slack1;
}

static int _test_bit(_433D_rx_t *self, int e0, int e1)
{
   /*
   Returns the bit value represented by the sequence of pulses.

   0: short long
   1: long short
   2: illegal sequence
   */
   _timings(self, e0, e1);

   if      ( (self->_min0 < e0) && (e0 < self->_max0) &&
             (self->_min1 < e1) && (e1 < self->_max1) )
      return 0;
   else if ( (self->_min0 < e1) && (e1 < self->_max0) &&
             (self->_min1 < e0) && (e0 < self->_max1) )
      return 1;
   else
      return 2;
}

static void _cb_RX(
   int pi, unsigned gpio, unsigned level, uint32_t tick, void *user)
{
   /*
   Accumulates the code from pairs of short/long pulses.
   The code end is assumed when an edge greater than 5 ms
   is detected.
   */

   _433D_rx_t *self=user;
   int edge_len, bit;

   // printf("pi=%d gpio=%d level=%d tick=%u\n", pi, gpio, level, tick);

   edge_len = tick - self->_last_edge_tick;
   self->_last_edge_tick = tick;

   if (edge_len > 5000) /* 5000 us, 5 ms. */
   {
      if (self->_in_code)
      {
         if ((self->min_bits <= self->_bits) &&
            (self->_bits <= self->max_bits))
         {
            self->_data.bits = self->_bits;
            self->_data.code = self->_code;
            self->_data.gap = self->_gap;
            self->_data.t0 = self->_t0 / self->_bits;
            self->_data.t1 = self->_t1 / self->_bits;
            self->_ready = 1;

            if (self->cb) self->cb(self->_data);
         }
      }

      self->_in_code = 1;
      self->_gap = edge_len;
      self->_edge = 0;
      self->_bits = 0;
      self->_code = 0;
   }

   else if (self->_in_code)
   {
      if (self->_edge == 0) self->_e0 = edge_len;
      else if (self->_edge == 1) _calibrate(self, self->_e0, edge_len);

      if (self->_edge % 2) /* Odd edge. */
      {
         bit = _test_bit(self, self->_even_edge_len, edge_len);
         self->_code = self->_code << 1;
         if (bit == 1) self->_code += 1;
         else if (bit != 0)
         {
            /* Uncomment the next block if you suspect timing problems. */
            /*
            if (self->_bits > 7)
            {
               printf("t=%d b=%d e0=%d e1=%d (b0=%d t0=%d b1=%d t1=%d) c=%u\n",
                  bit, self->_bits, self->_even_edge_len, edge_len,
                  self->_min0, self->_max0, self->_min1, self->_max1,
                  self->_code);
            }
            */
            self->_in_code = 0;
         }
      }
      else /* Even edge. */
      {
         self->_even_edge_len = edge_len;
      }

      self->_edge += 1;
   }
}

void _433D_rx_set_bits(_433D_rx_t *self, int min_bits, int max_bits)
{
   if (min_bits < 6) min_bits = 6;
   if (min_bits > 64) min_bits = 64;

   if (max_bits < 6) max_bits = 6;
   if (max_bits > 64) max_bits = 64;

   if (min_bits <= max_bits)
   {
      self->min_bits = min_bits;
      self->max_bits = max_bits;
   }
}

void _433D_rx_set_glitch(_433D_rx_t *self, int glitch)
{
   if (glitch < 0) glitch = 0;
   if (glitch > 500) glitch = 500;

   if (glitch != self->glitch)
   {
      set_glitch_filter(self->pi, self->gpio, glitch);
   }
   self->glitch = glitch;
}

int _433D_rx_ready(_433D_rx_t *self)
{
   /*
   Returns True if a new code is ready.
   */
   return self->_ready;
}

uint64_t _433D_rx_code(_433D_rx_t *self)
{
   /*
   Returns the last receieved code.
   */
   self->_ready = 0;
   return self->_data.code;
}

void _433D_rx_data(_433D_rx_t *self, _433D_rx_data_t *data)
{
  /*
   Returns reading of the last receieved code.  The reading
   consist of the code, the number of bits, the length (in us)
   of the gap, short pulse, and long pulse.
   */
   self->_ready = 0;
   *data = self->_data;
}

_433D_rx_t *_433D_rx(int pi, int gpio, _433D_rx_CB_t cb_func)
{
   _433D_rx_t *self;

   self = malloc(sizeof(_433D_rx_t));

   if (!self) return NULL;

   self->pi = pi;
   self->gpio = gpio;
   self->cb = cb_func;
   self->min_bits = 8;
   self->max_bits = 32;
   self->glitch = 150;

   self->_in_code = 0;
   self->_edge = 0;
   self->_code = 0;
   self->_gap = 0;

   self->_ready = 0;

   set_mode(pi, gpio, PI_INPUT);
   set_glitch_filter(pi, gpio, self->glitch);

   self->_last_edge_tick = get_current_tick(pi);

   self->_cb_id = callback_ex(pi, gpio, EITHER_EDGE, _cb_RX, self);

   return self;
}

void _433D_rx_cancel(_433D_rx_t *self)
{
   if (self)
   {
      if (self->_cb_id >= 0)
      {
         set_glitch_filter(self->pi, self->gpio, 0);
         callback_cancel(self->_cb_id);
         self->_cb_id = -1;
      }
      free(self);
   }
}

/*

TX

Code to transmit the wireless codes sent by 433 MHz wireless fobs.

*/

struct _433D_tx_s
{
   int pi;
   int gpio;
   int repeats;
   int bits;
   int gap, t0, t1;
   int _amble, _wid0, _wid1;
};

static void _make_waves(_433D_tx_t *self)
{
   /*
   Generates the basic waveforms needed to transmit codes.
   */
   wave_add_generic(self->pi, 2, (gpioPulse_t[])
      {{1<<self->gpio, 0, self->t0}, {0, 1<<self->gpio, self->gap}});

   self->_amble = wave_create(self->pi);

   wave_add_generic(self->pi, 2, (gpioPulse_t[])
      {{1<<self->gpio, 0, self->t0}, {0, 1<<self->gpio, self->t1}});

   self->_wid0 = wave_create(self->pi);

   wave_add_generic(self->pi, 2, (gpioPulse_t[])
      {{1<<self->gpio, 0, self->t1}, {0, 1<<self->gpio, self->t0}});

   self->_wid1 = wave_create(self->pi);
}

void _433D_tx_set_repeats(_433D_tx_t *self, int repeats)
{
   /*
   Set the number of code repeats.
   */
   if ((repeats >=1) && (repeats <= 50)) self->repeats = repeats;
}

void _433D_tx_set_bits(_433D_tx_t *self, int bits)
{
   /*
   Set the number of code bits.
   */
   if ((bits >= 6) && (bits <= 64)) self->bits = bits;
}

void _433D_tx_set_timings(_433D_tx_t *self, int gap, int t0, int t1)
{
   /*
   Sets the code gap, short pulse, and long pulse length in us.
   */
   self->gap = gap;
   self->t0 = t0;
   self->t1 = t1;

   wave_delete(self->pi, self->_amble);
   wave_delete(self->pi, self->_wid0);
   wave_delete(self->pi, self->_wid1);

   _make_waves(self);
}

void _433D_tx_send(_433D_tx_t *self, uint64_t code)
{
   /*
   Transmits the code (using the current settings of repeats,
   bits, gap, short, and long pulse length).
   */
   int i, p=0;
   uint64_t bit;
   char chain[256];

   chain[p++] = self->_amble;
   chain[p++] = 255;
   chain[p++] = 0;

   bit = ((uint64_t)1<<(self->bits-1));

   for (i=0; i<self->bits; i++)
   {
      if (code & bit) chain[p] = self->_wid1;
      else            chain[p]= self->_wid0;
      bit >>= 1;
      p++;
   }

   chain[p++] = self->_amble;
   chain[p++] = 255;
   chain[p++] = 1;
   chain[p++] = self->repeats;
   chain[p++] = 0;

   wave_chain(self->pi, chain, p);

   while (wave_tx_busy(self->pi)) time_sleep(0.1);
}

_433D_tx_t *_433D_tx(int pi, int gpio)
{
   /*
   Instantiate with the Pi and the GPIO connected to the wireless
   transmitter.

   The number of repeats (default 6) and bits (default 24) may
   be set with set_repeats and set_bits.

   The pre-/post-amble gap (default 9000 us), short pulse length
   (default 300 us), and long pulse length (default 900 us) may
   be set with set_timings.
   */
   _433D_tx_t *self;

   self = malloc(sizeof(_433D_tx_t));

   if (!self) return NULL;

   self->pi = pi;
   self->gpio = gpio;
   self->repeats = 6;
   self->bits = 24;
   self->gap = 9000;
   self->t0 = 300;
   self->t1 = 900;

   _make_waves(self);

   set_mode(pi, gpio, PI_OUTPUT);

   return self;
}

void _433D_tx_cancel(_433D_tx_t *self)
{
   /*
   Cancels the wireless code transmitter.
   */
   if (self)
   {
      wave_delete(self->pi, self->_amble);
      wave_delete(self->pi, self->_wid0);
      wave_delete(self->pi, self->_wid1);
      free(self);
   }
}

