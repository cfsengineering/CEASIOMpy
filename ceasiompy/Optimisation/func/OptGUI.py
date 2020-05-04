#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 12:15:22 2020

@author: vivien
"""

from tkinter import *


def recupere():
    print("Get value : ", entree.get())
def clavier(event):
    touche = event.keysym
    print(touche)


# Create window
fenetre = Tk()
fenetre['bg']='white'

# Create frames
Frame1 = Frame(fenetre, borderwidth=2, relief=GROOVE)
Frame1.pack(side=LEFT, padx=10, pady=10)
Frame2 = Frame(Frame1, borderwidth=2, relief=GROOVE)
Frame2.pack(side=RIGHT, padx=5, pady=5)

# Get objective value
value = StringVar(Frame1)
value.set("Objective function")

l = LabelFrame(fenetre, text="Titre de la frame", padx=20, pady=20)
l.pack(fill="both", expand="yes")

entree = Entry(Frame1, textvariable=value, width=30)
entree.pack()
bouton = Button(Frame1, text="Valider", command=recupere)
bouton.pack()

# Choose driver
label = Label(Frame1, text="Driver :")
label.pack()
# bouton1 = Radiobutton(Frame2, text="COBYLA", variable=value, value=1)
# bouton2 = Radiobutton(Frame2, text="SLSQP", variable=value, value=2)
# bouton1.pack()
# bouton2.pack()
bouton1 = Radiobutton(Frame1, text="Uniform", variable=value, value=1)
bouton2 = Radiobutton(Frame1, text="FullFactorial", variable=value, value=2)
bouton1.pack()
bouton2.pack()

label = Label(Frame1, text="Level or nb of iterations")
label.pack()
s = Spinbox(Frame1, from_=0, to=10)
s.pack()




# canvas = Canvas(fenetre, width=500, height=500)
# canvas.focus_set()
# canvas.bind("<Key>", clavier)
# canvas.pack()


# liste = Listbox(fenetre)
# liste.insert(1, "COBYLA")
# liste.insert(2, "SLSQP")
# liste.insert(3, "shgo")

# liste.pack()


# value = DoubleVar()
# scale = Scale(fenetre, variable=value)
# scale.pack()




# l = LabelFrame(fenetre, text="Titre de la frame", padx=20, pady=20)
# l.pack(fill="both", expand="yes")

# Label(l, text="A l'intérieure de la frame").pack()







fenetre.mainloop()
