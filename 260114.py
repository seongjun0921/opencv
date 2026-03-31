import tkinter as tk

def but_clik(text):
    pass



window = tk.Tk()
window.title("계산기")

label=tk.Label(window)
entry = tk.Entry(window).grid(row=0, column=0, columnspan=4)


buttons = [('7', 1, 0), ('8', 1, 1), ('9', 1, 2),('+', 1, 3),
           ('4', 2, 0), ('5', 2, 1), ('6', 2, 2),('-', 2, 3),
           ('1', 3, 0), ('2', 3, 1), ('3', 3, 2),('*', 3, 3),
           ('0', 4, 0), ('.', 4, 1), ('/', 4, 2)]

for (t, r, c) in buttons:
        tk.Button(window, width = 5, height = 2, text = t, command = lambda t = text:entry.get(t)).grid(row=r, column=c)


window.mainloop()