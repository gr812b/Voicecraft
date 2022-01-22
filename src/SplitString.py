from math import fabs
import websockets
import asyncio
import base64
import json
import pyaudio
import string
<<<<<<< HEAD
from number_parser import parse_number
=======
import json
>>>>>>> 0f789e3e42d9a3e028d7539fe64200971529a2b8

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()


# the AssemblyAI endpoint we're going to hit
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

counter = 0
variable_search = False
variable_temp = ""
variable_value = 0

c = open('src\controls.json')
controls = json.load(c)
normal = [[],[],[]]
variable = [[],[],[]]

def reloadJson():
    global normal
    global variable
    for i in range(len(controls["normal"])):
        normal[0].append(controls["normal"][i]["name"])
        normal[1].append(controls["normal"][i]["keys"])
        normal[2].append(controls["normal"][i]["movement"])
    for i in range(len(controls["variable"])):
        variable[0].append(controls["variable"][i]["name"])
        variable[1].append(controls["variable"][i]["keys"])
        variable[2].append(controls["variable"][i]["movement"])



def openStream():
    global stream
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=FRAMES_PER_BUFFER,
    )


def openStream(index):
    global stream
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=FRAMES_PER_BUFFER,
        input_device_index=index,  # Index of input device based on Input select
    )


def closeStream():
    global stream
    stream.close()


def getAudioList():
    global p
    names = []
    for i in range(0, p.get_host_api_info_by_index(0)["deviceCount"]):
        if p.get_device_info_by_host_api_device_index(0, i)["maxInputChannels"] > 0:
            names.append(p.get_device_info_by_host_api_device_index(0, i)["name"])
    return names


openStream(0)


async def send_receive():
    print(f"Connecting websocket to url ${URL}")
    async with websockets.connect(
        URL,
        extra_headers=(("Authorization", "da3f18895a4b4c7f960502644138d6f8"),),
        ping_interval=5,
        ping_timeout=20,
    ) as _ws:
        await asyncio.sleep(0.1)
        print("Receiving SessionBegins ...")
        session_begins = await _ws.recv()
        print(session_begins)
        print("Sending messages ...")

        async def send():
            global tempCount
            while True:
                try:
                    data = stream.read(FRAMES_PER_BUFFER)
                    data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data": str(data)})
                    await _ws.send(json_data)
                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break
                except Exception as e:
                    if "Stream closed" in str(e):
                        print("Stream closed, trying to reconnect")
                    else:
                        assert False, "Not a websocket 4008 error"
                await asyncio.sleep(0.01)

            return True

        async def receive():
            global counter
            global variable_search
            global variable_temp
            global variable_value
            global normal
            global variable
            reloadJson()
            while True:
                try:
                    result_str = await _ws.recv()

                    sentance = json.loads(result_str)["text"]
                    subSentence = sentance[counter:].strip()
                    messageType = json.loads(result_str)["message_type"]
                    if messageType == "FinalTranscript":
                        counter = 0
                    else:
                        print(subSentence)
                        # Split subsentance into words
                        words = subSentence.split()
                        # for each word in subsentance
                        for word in words:
                        # if variable search
                            if variable_search:
                                parse_value = parse_number(variable_temp + word)
                                if parse_value:
                                    if parse_value >= 360:
                                        variable_value = 360
                                        variable_search = False
                                    else:
                                        variable_temp += word
                                else:
                                    variable_value = parse_number(variable_temp) if parse_number(variable_temp) else 0
                                    variable_search = False

                            # IF WORD IS COMMAND and variable is not true
                            else:
                                if variable_value != 0:
                                    print(variable_value)
                                    variable_value = 0
                                elif word in normal[0]:
                                    index = normal[0].index(word)
                                    print(normal[1][index])
                                elif word in variable[0]:
                                    index = variable[0].index(word)
                                    #print(variable[2][index])
                                    variable_search = True
                                #if variable_value != 0:
                                    #print(variable_value)

                                    #print(word)
                                #elif word in controls["variable"]["name"]:
                                    #print(word)
                                    #variable_search = True
                                    # CALL FUNCTION TO DO STUFF
                                
                                
                            # Else wait for next word until number
                        
                        # variable search = true
                        # CALL function with variabnle input
                        counter = len(sentance)

                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break
                except Exception as e:
                    print(e)
                    assert False, "Not a websocket 4008 error"

        send_result, receive_result = await asyncio.gather(send(), receive())


asyncio.run(send_receive())
