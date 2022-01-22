import websockets
import asyncio
import base64
import json
import pyaudio
import string
import json

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()


# the AssemblyAI endpoint we're going to hit
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

counter = 0


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


openStream()


async def send_receive():
    global counter
    global tempCount
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
            while True:
                try:
                    result_str = await _ws.recv()

                    sentance = json.loads(result_str)["text"]
                    subSentance = sentance[counter:].strip()
                    messageType = json.loads(result_str)["message_type"]
                    if messageType == "FinalTranscript":
                        counter = 0
                    else:
                        print(subSentance)
                        # Split subsentance into words
                        # for each word in subsentance
                        # IF WORD IS COMMAND and variable is not true
                        # CALL FUNCTION TO DO STUFF
                        # Else wait for next word until number
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
