#! /usr/bin/env python
if __name__ == "__main__":

    import sys
    import time
    import pigpio
    import _433

    RX=3
    TX=4

    # define optional callback for received codes.

    def rx_callback(code, bits, gap, t0, t1):
        output = "{0:b}".format(code)
        print("code={} bits={})".
            format(code, output))

    pi = pigpio.pi() # Connect to local Pi.

    rx=_433.rx(pi, gpio=RX, callback=rx_callback)
    try:
        args = len(sys.argv)

        if args > 1:

            # If the script has arguments they are assumed to codes
            # to be transmitted.

            tx=_433.tx(pi, gpio=TX)

            for i in range(args-1):
                print("sending {}".format(sys.argv[i+1]))
                tx.send(int(sys.argv[i+1]))
                time.sleep(1)

            tx.cancel() # Cancel the transmitter.

        time.sleep(60)
    finally:
        rx.cancel() # Cancel the receiver.

        pi.stop() # Disconnect from local Pi.
