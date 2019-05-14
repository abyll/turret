/*
Remote control code mapper
*/

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <unistd.h>

#include <pigpiod_if2.h>

#include "_433D.h"

/*

REQUIRES

A 313 or 434 MHz radio receiver (to use the RX functions) and/or a radio
transmitter (to use the TX functions).

TO BUILD

gcc -Wall -pthread -o controller controller.c _433D.c -lpigpiod_if2

TO RUN

sudo pigpiod # If the daemon is not already running

then

./_433D -rRXGPIO

or

./_433D -tTXGPIO 12345 78901

*/

void fatal(char *fmt, ...)
{
    char buf[128];
    va_list ap;

    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    fprintf(stderr, "%s\n", buf);

    fflush(stderr);

    exit(EXIT_FAILURE);
}

void usage()
{
    fprintf(stderr, "\n" \
        "Usage: _433D [OPTION] ...\n" \
        "    -r value, rx gpio, 0-31,                        default None\n" \
        "    -t value, tx gpio, 0-31,                        default None\n" \
        "    -d value, monitoring duration in seconds, default 60\n" \
        "\n" \
        "    -b value, TX bits, 6-64,                        default 24\n" \
        "    -x value, TX repeats, 1-50,                    default 6\n" \
        "    -0 value, TX t0, 100-1000,                     default 300\n" \
        "    -1 value, TX t1, 300-3000,                     default 900\n" \
        "    -g value, TX gap, 5000-13000,                 default 9000\n" \
        "\n" \
        "    -l value, RX glitch, 0-500,                    default 150\n" \
        "    -m value, RX min bits, 6-64,                  default 8\n" \
        "    -n value, RX max bits, 6-64,                  default 32\n" \
        "    -f        , RX show full code details,        default off\n" \
        "\n" \
        "    -h string, host name,                            default NULL\n" \
        "    -p value, socket port, 1024-32000,          default 8888\n" \
        "EXAMPLE\n" \
        "_433D -r20\n" \
        "    Listen for received codes on GPIO 20.\n" \
        "\n" \
        "_433D -t21 2345 8789001\n" \
        "    Transmit codes 2345 and 8789001 on GPIO 21.\n" \
        "\n" \
        "_433D -r20 -t21 8675 878 9041\n" \
        "    Transmit codes 8675, 878, and 9041 on GPIO 21.\n" \
        "    Then listen for received codes on GPIO 20.\n" \
);
}

int optRx      = -1;
int optTx      = -1;

int optBits = 24;
int optRepeats = 6;
int opt0 = 300;
int opt1 = 900;
int optGap = 9000;

int optMinBits = 8;
int optMaxBits = 32;
int optGlitch = 150;
int optFull = 0;

char *optHost    = NULL;
char *optPort    = NULL;
float optDuration = 60;

const int ADDRESS = 0b101010101010;
const int MASK = 0b111111111111;
const double GAP_THRESHOLD = 0.080; // max seconds between codes sent before we assume we missed some and reset all buttons
const char CH_UP = 4;
const char CH_DOWN = 2;
const char CH_LEFT = 8;
const char CH_RIGHT = 0;
const char CH_FIRE = 6;

double last_time = 0;

/* Current button flags */
char up_state     = 0;
char down_state   = 0;
char left_state   = 0;
char right_state  = 0;
char fire_state   = 0;

static uint64_t getNum(char *str, int *err)
{
    uint64_t val;
    char *endptr;

    *err = 0;
    val = strtoll(str, &endptr, 0);
    if (*endptr) {*err = 1; val = -1;}
    return val;
}


static void initOpts(int argc, char *argv[])
{
    int opt, err, i;

    while ((opt = getopt(argc, argv, "r:t:d:b:x:0:1:g:l:m:n:fh:p:")) != -1)
    {
        switch (opt)
        {
            case 'r':
                i = getNum(optarg, &err);
                if ((i >= 0) && (i <= 31)) optRx = i;
                else fatal("invalid -r option (%s)", optarg);
                break;

            case 't':
                i = getNum(optarg, &err);
                if ((i >= 0) && (i <= 31)) optTx = i;
                else fatal("invalid -t option (%s)", optarg);
                break;

            case 'd':
                i = getNum(optarg, &err);
                if ((i>0) && (i<=86400) && (!err)) optDuration = i;
                else fatal("invalid -d option (%s)", optarg);
                break;

            case 'b':
                i = getNum(optarg, &err);
                if ((i>=6) && (i<=64) && (!err)) optBits = i;
                else fatal("invalid -b option (%s)", optarg);
                break;

            case 'x':
                i = getNum(optarg, &err);
                if ((i>0) && (i<=50) && (!err)) optRepeats = i;
                else fatal("invalid -x option (%s)", optarg);
                break;

            case '0':
                i = getNum(optarg, &err);
                if ((i >= 100) && (i <= 1000)) opt0 = i;
                else fatal("invalid -0 option (%s)", optarg);
                break;

            case '1':
                i = getNum(optarg, &err);
                if ((i >= 300) && (i <= 3000)) opt1 = i;
                else fatal("invalid -1 option (%s)", optarg);
                break;

            case 'g':
                i = getNum(optarg, &err);
                if ((i >= 5000) && (i <= 13000)) optGap = i;
                else fatal("invalid -g option (%s)", optarg);
                break;

            case 'l':
                i = getNum(optarg, &err);
                if ((i>=0) && (i<=500) && (!err)) optGlitch = i;
                else fatal("invalid -l option (%s)", optarg);
                break;

            case 'm':
                i = getNum(optarg, &err);
                if ((i>=6) && (i<=64) && (!err)) optMinBits = i;
                else fatal("invalid -m option (%s)", optarg);
                break;

            case 'n':
                i = getNum(optarg, &err);
                if ((i>=6) && (i<=64) && (!err)) optMaxBits = i;
                else fatal("invalid -n option (%s)", optarg);
                break;

            case 'f':
                optFull = 1;
                break;

            case 'h':
                optHost = malloc(sizeof(optarg)+1);
                if (optHost) strcpy(optHost, optarg);
                break;

            case 'p':
                optPort = malloc(sizeof(optarg)+1);
                if (optPort) strcpy(optPort, optarg);
                break;

          default: /* '?' */
              usage();
              exit(-1);
          }
     }
}



static inline void change_switch(char *new, char *cur, char *name) {
    if(*new && !*cur) {
        printf("%s\n", name);
        *cur = 1;
    }
    else if(!*new && *cur) {
        printf("!%s\n", name);
        *cur = 0;
    }
    *cur = *new;
}

void cbf(_433D_rx_data_t r)
{
    int address = r.code >> 11;
    if( r.bits == 24 && address == ADDRESS ) {
        int code = r.code & MASK;
        char up = (code & 1 << CH_UP) != 0;
        char down = (code & 1 << CH_DOWN) != 0;
        char left = (code & 1 << CH_LEFT) != 0;
        char right = (code & 1 << CH_RIGHT) != 0;
        char fire = (code & 1 << CH_FIRE) != 0;
        
        change_switch(&up, &up_state, "UP");
        change_switch(&down, &down_state, "DOWN");
        change_switch(&left, &left_state, "LEFT");
        change_switch(&right, &right_state, "RIGHT");
        change_switch(&fire, &fire_state, "FIRE");
        fflush(stdout);
        double current_time = time_time();
        //double time_elapsed = current_time - last_time;
        last_time = current_time;
    }
}

int main(int argc, char *argv[])
{
    int pi, arg;
    _433D_rx_t *rx=NULL;
    _433D_tx_t *tx=NULL;

    initOpts(argc, argv);

    pi = pigpio_start(optHost, optPort);

    if (pi >= 0)
    {
        if (optRx >= 0)
        {
            rx = _433D_rx(pi, optRx, cbf);
            _433D_rx_set_bits(rx, optMinBits, optMaxBits);
            _433D_rx_set_glitch(rx, optGlitch);
            printf("starting\n");
        }


        if (rx)
        {
            last_time = time_time();
            /* Give some time for some keyfob presses. */
            while(1) {
                time_sleep(GAP_THRESHOLD - 0.01);
                double current_time = time_time();
                if(current_time - last_time > GAP_THRESHOLD) {
                    char up = 0;
                    char down = 0;
                    char left = 0;
                    char right = 0;
                    char fire = 0;
                    change_switch(&up, &up_state, "UP");
                    change_switch(&down, &down_state, "DOWN");
                    change_switch(&left, &left_state, "LEFT");
                    change_switch(&right, &right_state, "RIGHT");
                    change_switch(&fire, &fire_state, "FIRE");
                    fflush(stdout);
                    last_time = time_time();
                }
            }
            _433D_rx_cancel(rx);
        }

        pigpio_stop(pi);
    }
    
    return 0;
}

