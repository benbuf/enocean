#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from enocean.consolelogger import init_logging
import enocean.utils
from enocean.communicators.serialcommunicator import SerialCommunicator
from enocean.protocol.packet import RadioPacket, ResponsePacket
from enocean.protocol.constants import PACKET, RORG
import sys
import traceback

import queue

def assemble_radio_packet(transmitter_id):
    return RadioPacket.create(rorg=RORG.BS4, rorg_func=0x20, rorg_type=0x01,
                              sender=transmitter_id,
                              CV=50,
                              TMP=21.5,
                              ES='true')

#init_logging()
communicator = SerialCommunicator("COM3")
communicator.start()
print('The Base ID of your module is %s.' % enocean.utils.to_hex_string(communicator.base_id))

setpoint = 21

#if communicator.base_id is not None:
#    print('Sending example package.')
#    communicator.send(assemble_radio_packet(communicator.base_id))

def testSAB05():

    toSAB = RadioPacket.create(rorg=RORG.BS4, rorg_func=0x20, rorg_type=0x01,
                                sender=communicator.base_id,
                                direction=2,
                                destination=[0x01, 0x85, 0x9F, 0xBA],
                                #learn=True, 
                                #["TMP", 10; "LRBN", 1])
                                TMP = 10, LRNB = 0)

    
    communicator.send(toSAB)

def lrn_SAB05(in_packet):
    """working LEARN Packet!"""

    packet = RadioPacket.create(RORG.BS4, rorg_func=0x20, rorg_type=0x01, direction=2,
                sender=communicator.base_id, destination=in_packet.sender, learn=in_packet.learn)

    # copy EEP and manufacturer ID
    packet.data[1:5] = in_packet.data[1:5]
    # update flags to acknowledge learn request
    packet.data[4] = 0xf0

    communicator.send(packet)

    for k in packet.parse_eep(0x20, 0x01, 2):
        print('%s: %s' % (k, packet.parsed[k]))            

def answer_SAB05(in_packet, new_setpoint):
    """ normale Antwort an SAB05"""

    # Extract Temperature from orig. package
    

    #temp = in_packet.parse_eep(0x20, 0x01, 1)
    #temp = in_packet.parsed(0x20, 0x01, 1)
    temp = in_packet.parse()
    tempSAB05_all = temp["TMP"]
    tempSAB = tempSAB05_all["value"]
    setp_all = temp["CV"]
    setp = setp_all["value"]

    #loop over packet? or build funktion to get packet in dict?
    print("Testausgabe:\n")
    
    print(tempSAB05_all)
    print(tempSAB)
    print(setp_all)
    print(setp)
    #Check if new_setpoint is int?

    out_packet = RadioPacket.create(RORG.BS4, rorg_func=0x20, rorg_type=0x01, direction=2,
                sender=communicator.base_id, destination=in_packet.sender, SPS=1, SP=new_setpoint, TMP=19, LFS=1, RIN=1, RCU=0, learn=False)


    print(out_packet.data)
    communicator.send(out_packet)

    # Debugging output
    print("Gesendete Antwort: \n ")
    for k in out_packet.parse_eep(0x20, 0x01, 2):
        print('%s: %s' % (k, out_packet.parsed[k]))            



# endless loop receiving radio packets
while communicator.is_alive():
    try:
        # Loop to empty the queue...
        packet = communicator.receive.get(block=True, timeout=1)

        if packet.packet_type == PACKET.RADIO and packet.rorg == RORG.BS4:
            # parse packet with given FUNC and TYPE
            print("\n \n Empfangenes Packet von SAB:\n")
            for k in packet.parse_eep(0x20, 0x01):
                print('%s: %s' % (k, packet.parsed[k]))            

            if packet.learn:
                lrn_SAB05(packet)
            else:
                answer_SAB05(packet, setpoint)



    except queue.Empty:
        continue
    except KeyboardInterrupt:
        break
    except Exception:
        traceback.print_exc(file=sys.stdout)
        break

if communicator.is_alive():
    communicator.stop()
