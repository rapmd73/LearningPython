#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Validate user input

# oldChar='lOSZ'
# newChar='1052'

def IsNumbersOnly(ustring):
    numbers='0123456789.'

    if ustring=='':
        return False

    for usChar in ustring:
        if usChar not in numbers:
            return False
    return True

# Ask for the closing price and give the stop loss and take profit prices.
# stop loss and take profit in the form reward/risk.
# R:R 2:1 means 2 times the reward for your risk

def GetUserNumber(question):
    done=False
    answer=''
    while not done:
        answer=input(question)
        if IsNumbersOnly(answer):
            done=True
        else:
            print("Enter a number.")

    return float(answer)

