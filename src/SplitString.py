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
var_search = False
var_temp = ""
var_count = 0
var_index = 0
var_values = []
currentKeys = []
currentMouse = []
sensivity = int((146 / 90))

c = open("src\controls.json")
controls = json.load(c)
normal = [[], [], []]
variable = [[], [], [], []]


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
        variable[3].append(controls["variable"][i]["count"])


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


def move(command, values=None, movement=None, keys=None):
    global currentKeys
    global currentMouse
    print(command + " command")
    print(str(keys) + " keys")
    if values:
        if movement == "right":
            print("MOVING MOUSE")
            pyautogui.move((sensivity * values[0]), 0, 0.15)
        elif movement == "left":
            pyautogui.move((sensivity * values[0]), 0, 0.15)
        elif movement == "up":
            pyautogui.move(0, (sensivity * values[0]), 0.15)
        elif movement == "down":
            pyautogui.move(0, (sensivity * values[0]), 0.15)
        elif movement == "coordiante":
            pyautogui.move(values[0], values[1], 0.15)
        elif movement == "drag":
            pyautogui.move(values[0], values[1], 0.15)
            pyautogui.drag(values[2], values[3], duration=0.15)
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
            global var_search
            global var_temp
            global var_values
            global var_index
            global normal
            global variable
            reloadJson()
            while True:
                try:
                    result_str = await _ws.recv()

                    sentence = json.loads(result_str)["text"]
                    subSentence = sentence[counter:].strip()
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
                            if var_search:
                                print("parsing :" + var_temp + " " + word)
                                parse_value = parse_number(var_temp + " " + word)
                                if parse_value:
                                    print("Adding " + word + " to " + var_temp)
                                    var_temp += " " + word
                                else:
                                    var_value = (
                                        parse_number(var_temp)
                                        if parse_number(var_temp)
                                        else -1
                                    )
                                    if var_value != -1:
                                        var_values.append(var_value)
                                    else:
                                        if word in normal[0]:
                                            index = normal[0].index(word)
                                            move(
                                                normal[0][index], keys=normal[1][index]
                                            )
                                            print(normal[1][index])
                                            var_search = False
                                            var_temp = ""
                                            var_values = []
                                            continue
                                        elif word in variable[0]:
                                            var_index = variable[0].index(word)
                                            var_count = variable[3][var_index]
                                            print(variable[2][var_index])
                                            var_temp = ""
                                            var_values = []
                                            continue
                                    print(
                                        "Search ended final value is " + str(var_value)
                                    )
                                    print(
                                        "Current variable values are " + str(var_values)
                                    )
                                    print(
                                        "Current number of variables: "
                                        + str(len(var_values))
                                        + "\nLooking for: "
                                        + str(var_count)
                                    )
                                    var_temp = ""
                                    if len(var_values) == var_count:
                                        move(
                                            command=variable[0][var_index],
                                            values=var_values,
                                            movement=variable[2][var_index],
                                        )

                                        var_values = []
                                        var_search = False

                            # IF WORD IS COMMAND and variable is not true
                            else:
                                if word in normal[0]:
                                    index = normal[0].index(word)
                                    move(normal[0][index], keys=normal[1][index])
                                    print(normal[1][index])
                                elif word in variable[0]:
                                    var_index = variable[0].index(word)
                                    var_count = variable[3][var_index]
                                    print(variable[2][var_index])
                                    var_search = True
                        counter = len(sentence)

                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break

        send_result, receive_result = await asyncio.gather(send(), receive())


asyncio.run(send_receive())
