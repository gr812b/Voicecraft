import PySimpleGUI as gui 
import os

dir = os.getcwd()

#Create custom theme and add to the list of themes
gui.theme_add_new('CustomTheme', {'BACKGROUND': '#292929',
                'TEXT': '#fff4c9',
                'INPUT': '#c7e78b',
                'TEXT_INPUT': '#000000',
                'SCROLL': '#c7e78b',
                'BUTTON': ('white', '#709053'),
                'PROGRESS': ('#01826B', '#D0D0D0'),
                'BORDER': 1,
                'SLIDER_DEPTH': 0,
                'PROGRESS_DEPTH': 0})

#Set options and theme
gui.set_options(font=("Uni Sans-Trial Book", 35))
gui.theme('CustomTheme')

col_layout = [
    [gui.Button('Start', size=(20, 2), visible=True, font=('Uni Sans-Trial Book', 20))]
]

layout = [  [gui.Text('Voice Craft',font=('Uni Sans-Trial Book',80))],
            [gui.Column(col_layout, element_justification='left', expand_x=True)],
            [gui.Text('Choose Device',size=(12,1),font =('Uni Sans-Trial Book',25))],
            [gui.Image(r'' + dir + '\\assets\\logo.png')],
            [gui.Combo(['laptop mic','headset'],key='dest')] ]

window = gui.Window('',layout, resizable=True, size=(700, 700))

while True:
    event, values = window.read()
    if event == gui.WIN_CLOSED: 
        break

window.close()