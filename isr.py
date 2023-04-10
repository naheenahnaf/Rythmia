# isr.py
# Authors: Ahnaf Naheen, Anhela Francees
# Date: April 5, 2023
# Version: 1.1

import micropython, time

left_flag = 0
left_debounce_time = 0
middle_flag = 0
middle_debounce_time = 0
right_flag = 0
right_debounce_time = 0

def L_handler(left_btn):
    micropython.alloc_emergency_exception_buf(100)
    global left_flag, left_debounce_time
    if (time.ticks_ms() - left_debounce_time) > 100:
        left_flag = 1
        left_debounce_time = time.ticks_ms()

def M_handler(middle_btn):
    micropython.alloc_emergency_exception_buf(100)
    global middle_flag, middle_debounce_time
    if (time.ticks_ms() - middle_debounce_time) > 100:
        middle_flag = 1
        middle_debounce_time = time.ticks_ms()

def R_handler(right_btn):
    micropython.alloc_emergency_exception_buf(100)
    global right_flag, right_debounce_time
    if (time.ticks_ms() - right_debounce_time) > 100:
        right_flag = 1
        right_debounce_time = time.ticks_ms()
