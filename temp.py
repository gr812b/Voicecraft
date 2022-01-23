import PySimpleGUI as sg
import random
import string

rows = [1,2,3,4,5,6,7,8,9,10]
cols = [1,2,3]
# ------ Some functions to help generate data for the table ------
def word():
    return 'Hello'
def number(max_val=1000):
    return 10
#def makes_table(num_rows,num_cols):
 #   for i in range(num_rows-1):
#
 #       for j in range(num_cols-1):
            

def make_table(num_rows, num_cols):
    data = [[j for j in range(num_cols)] for i in range(num_rows)]
    data[0] = [word() for __ in range(num_cols)]
    for i in range(1, num_rows):
        data[i] = [word(), *[number() for i in range(num_cols - 1)]]
    return data
    

# ------ Make the Table Data ------
data = make_table(105, 3)
headings = [str(data[0][x]) for x in range(len(data[0]))]

# ------ Window Layout ------
layout = [[sg.Text('wassup')],[sg.Table(values=data[1:], headings=headings, max_col_width=25,
                    auto_size_columns=True,
                    justification='center',
                    num_rows=5,
                    alternating_row_color='blue',
                    key='-TABLE-',
                    row_height=20)]]

# ------ Create Window ------
window = sg.Window('', layout)

# ------ Event Loop ------
while True:
    event, values = window.read()
    print(event, values)
    if event == sg.WIN_CLOSED:
        break
window.close()