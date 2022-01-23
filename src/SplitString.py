from math import fabs
from turtle import pensize
import websockets
import asyncio
import base64
import json
import pyaudio
import json
import pyautogui
import pydirectinput
import PySimpleGUI as gui
from number_parser import parse_number

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
WIDTH, HEIGHT = pyautogui.size()
print(WIDTH)
print(HEIGHT)
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

c = open("assets/controls.json")
controls = json.load(c)
normal = [[], [], []]
variable = [[], [], [], []]


def getAudioList():
    global p
    names = []
    for i in range(0, p.get_host_api_info_by_index(0)["deviceCount"]):
        if p.get_device_info_by_host_api_device_index(0, i)["maxInputChannels"] > 0:
            names.append(p.get_device_info_by_host_api_device_index(0, i)["name"])
    return names


audioDevices = getAudioList()


def load_controls():
    f = open("controls.json", "r")
    controls = json.load(f)
    f.close()
    return controls


def load_controls_more(controls):
    controlNames = []
    controlKeys = []
    controlMovement = []
    for attr, value in controls.items():
        for val in value:
            controlNames.append(val["name"])
            controlKeys.append(val["keys"])
            controlMovement.append(val["movement"])
    return controlNames, controlKeys, controlMovement


controls = load_controls()

controlNames, controlKeys, controlMovement = load_controls_more(controls)

startstop = {"text": "Start", "colour": "green"}


def addToJson(name, keys, movement, group):
    controls = load_controls()
    controls[group].append({"name": name, "keys": keys, "movement": movement})
    f = open("controls.json", "w")
    json.dump(controls, f)
    f.close()


def removeFromJson(name, group):
    controls = load_controls()
    controlNames, controlKeys, controlMovement = load_controls_more(controls)
    for i, item in enumerate(controlNames):
        if item == name:
            controls[group].pop(i)
    f = open("controls.json", "w")
    json.dump(controls, f)
    f.close()


# Create custom theme and add to the list of themes
gui.theme_add_new(
    "CustomTheme",
    {
        "BACKGROUND": "#292929",
        "TEXT": "#fff4c9",
        "INPUT": "#c7e78b",
        "TEXT_INPUT": "#000000",
        "SCROLL": "#c7e78b",
        "BUTTON": ("white", "#709053"),
        "PROGRESS": ("#01826B", "#D0D0D0"),
        "BORDER": 1,
        "SLIDER_DEPTH": 0,
        "PROGRESS_DEPTH": 0,
    },
)

# Set options and theme
gui.set_options(font=("Uni Sans-Trial Book", 35))
gui.theme("CustomTheme")

# Table
top = ["Controls", "Key", "Movement"]

data_selected = [[]]


def open_window(oldWindow):
    layout = [
        [
            gui.Push(),
            gui.Text("Input Phrase", font=("Uni Sans-Trial Book", 20)),
            gui.Input(do_not_clear=False),
            gui.T(
                "Not Selected ", size=(32, 1), background_color="white", key="blank1"
            ),
            gui.Push(),
        ],
        [
            gui.Push(),
            gui.Text("Input Key", font=("Uni Sans-Trial Book", 20)),
            gui.Input(do_not_clear=False),
            gui.T(
                "Not Selected ", size=(32, 1), background_color="white", key="blank2"
            ),
            gui.Push(),
        ],
        [
            gui.Push(),
            gui.Text("Input Movement", font=("Uni Sans-Trial Book", 20)),
            gui.Input(do_not_clear=False),
            gui.T(
                "Not Selected ", size=(32, 1), background_color="white", key="blank3"
            ),
            gui.Push(),
        ],
        [
            gui.Button(
                "Enter",
                size=(10, 1),
                visible=True,
                font=("Uni Sans-Trial Book", 10),
                key="submit",
            )
        ],
    ]
    window = gui.Window("", layout, modal=True, size=(500, 300))
    choice = None
    while True:
        event, values = window.read()
        if event == gui.WIN_CLOSED:
            break
        if event in ("submit"):
            # TODO: Filter out wrong values
            addToJson(
                values[0].split(","),
                values[1].split(","),
                values[2].split(","),
                "normal",
            )
            data.append([values[0], values[1], values[2]])
            oldWindow.Element("table").Update(values=data[1:])
            break

    window.close()


def make_table(num_rows, num_cols):
    data = [[""] * num_cols for i in range(num_rows + 1)]
    for i, item in enumerate(controlNames):
        if controlMovement[i] == "":
            controlMovement[i] = "              "
        data[i + 1] = [item, controlKeys[i], controlMovement[i]]
    return data


# ------ Make the Table Data ------
data = make_table(len(controlNames), 3)
headings = [(top[x]) for x in range(len(top))]

# Layout
layout = [
    [
        gui.Push(),
        gui.Text(
            "Voice Craft", font=("Uni Sans-Trial Book", 80), justification="center"
        ),
        gui.Push(),
    ],
    [
        gui.Push(),
        gui.Table(
            values=data[1:],
            headings=headings,
            size=(150, 150),
            max_col_width=15,
            font=("Uni Sans-Trial Book", 20),
            justification="center",
            auto_size_columns=True,
            num_rows=5,
            alternating_row_color="#505050",
            key="table",
            enable_events=True,
            row_height=40,
        ),
        gui.Push(),
    ],
    [
        gui.Push(),
        gui.Button(
            "Add",
            size=(10, 1),
            visible=True,
            font=("Uni Sans-Trial Book", 15),
            key="adder",
        ),
        gui.Text("            "),
        gui.Button(
            "Delete",
            size=(10, 1),
            visible=True,
            font=("Uni Sans-Trial Book", 15),
            button_color="red",
            key="delete",
        ),
        gui.Push(),
    ],
    [
        gui.Push(),
        gui.Button(
            startstop["text"],
            size=(20, 2),
            visible=True,
            font=("Uni Sans-Trial Book", 20),
            button_color=startstop["colour"],
            key="startstop",
        ),
        gui.Push(),
        gui.Text("Choose Device", size=(12, 1), font=("Uni Sans-Trial Book", 25)),
        gui.Combo(
            audioDevices,
            key="dest",
            size=(30, 1),
            font=("Uni Sans-Trial Book", 20),
            enable_events=True,
        ),
        gui.Push(),
    ]
    # gui.Image(r'./assets/logo.png',size=(200,200)),gui.Frame(layout=col_layout, element_justification='left', title='')
]

window = gui.Window(
    "", layout, resizable=True, size=(700, 700), icon=r"./assets/logo.ico"
)


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
        elif movement == "coordinate":
            pyautogui.moveTo(values[0], values[1], 1)
        elif movement == "drag":
            pyautogui.moveTo(values[0], values[1], 1)
            pyautogui.dragTo(values[2], values[3], 1)
            pyautogui.click(button="left")
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
                            if word == "exit":
                                exit()
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


async def windowMaker():
    global window
    global controls
    global controlNames
    global controlKeys
    global controlMovement
    global startstop
    global audioDevices
    global top
    global data_selected
    global data
    global headings
    global layout
    global stream
    while True:
        event, values = window.read()
        if event == gui.WIN_CLOSED:
            break
        if event in ("startstop"):
            window.close()
        if event in ("dest"):
            combo = audioDevices.index(values["dest"])
            closeStream()
            openStream(combo)
        if event in "table":
            data_selected = [data[row + 1] for row in values[event]]
        if event in ("adder"):
            open_window(window)
        if event in ("delete"):
            removeFromJson(data_selected[0][0], "normal")
            print("Deleted", data_selected[0])
            data.remove(data_selected[0])
            window.Element("table").Update(values=data[1:])
            print("data:", data)
        if event in ("window"):
            window.Element("table").Update(values=data[1:])


async def wait_list():
    await asyncio.gather(send_receive(), windowMaker())


loop = asyncio.get_event_loop()
loop.run_until_complete(wait_list())
loop.close()
