from math import fabs
import websockets
import asyncio
import base64
import json
import pyaudio
import json
import pyautogui
import pydirectinput
from number_parser import parse_number

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
command_temp = ""
movement_temp = ""
currentKeys = []
currentMouse = []
sensivity = int((146 / 90))

c = open("src\controls.json")
controls = json.load(c)
normal = [[], [], []]
variable = [[], [], []]


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


def openStream(index=p.get_default_input_device_info()["index"]):
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


def stopMovement():
    global currentKeys
    for i in currentKeys:
        pydirectinput.keyUp(i)
    for i in currentMouse:
        pydirectinput.mouseUp(button=i)
    currentMouse.clear()
    currentKeys.clear()


def move(command, value=None, movement=None, keys=None):
    global currentKeys
    global currentMouse
    print(command + " command")
    print(str(keys) + " keys")
    if value or value == 0:
        if movement == "right":
            print("MOVING MOUSE")
            pyautogui.move((sensivity * value), 0, 0.15)
        elif movement == "left":
            pyautogui.move((sensivity * value), 0, 0.15)
        elif movement == "up":
            pyautogui.move(0, (sensivity * value), 0.15)
        elif movement == "down":
            pyautogui.move(0, (sensivity * value), 0, 0.15)
    elif command == "stop":
        stopMovement()
    else:
        for i in keys:
            if i == "left" or i == "right":
                pydirectinput.mouseDown(button=i)
                currentMouse.append(i)
            else:
                pydirectinput.keyDown(i)
                currentKeys.append(i)


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
            global command_temp
            global movement_temp
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
                                print("parsing :" + variable_temp + " " + word)
                                parse_value = parse_number(variable_temp + " " + word)
                                if parse_value:
                                    if parse_value >= 360:
                                        variable_value = 360
                                        variable_search = False
                                    else:
                                        print("Adding " + word + " to " + variable_temp)
                                        variable_temp += " " + word
                                else:
                                    variable_value = (
                                        parse_number(variable_temp)
                                        if parse_number(variable_temp)
                                        else 0
                                    )
                                    print(
                                        "Search ended final value is "
                                        + str(variable_value)
                                    )
                                    print(
                                        "Calling move("
                                        + command_temp
                                        + ","
                                        + str(variable_value)
                                        + ")"
                                    )
                                    move(
                                        command_temp,
                                        value=variable_value,
                                        movement=movement_temp,
                                    )
                                    variable_temp = ""
                                    command_temp = ""
                                    movement_temp = ""
                                    variable_search = False

                            # IF WORD IS COMMAND and variable is not true
                            else:
                                if word in normal[0]:
                                    index = normal[0].index(word)
                                    move(normal[0][index], keys=normal[1][index])
                                    # make function call saying move(normal[1][index])
                                    print(normal[1][index])
                                elif word in variable[0]:
                                    index = variable[0].index(word)
                                    print(variable[2][index])
                                    movement_temp = variable[2][index]
                                    variable_search = True
                                    command_temp = word
                        counter = len(sentance)

                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break

        send_result, receive_result = await asyncio.gather(send(), receive())


asyncio.run(send_receive())
