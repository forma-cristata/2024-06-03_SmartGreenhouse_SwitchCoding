# Sunrise/Sunset Smart Light Controller

A Raspberry Pi-based project that automatically controls smart lights based on sunrise and sunset times of the local area. The system uses LED indicators and bar graphs to display various states and timing information.

## Features

- Automatic grow-light control based on daily sunrise/sunset times
    - Supports multiple smart switches
    - LED indicators for system status and DST
- Visual feedback through LED bar graphs
    - Shows rate of change of day length
    - Displays current relative daylight ratio

## Requirements

- Raspberry Pi
- GPIO LED components
- Custom Tasmota flashed smart switches
    - https://www.amazon.com/Sonoff-S31-SONOFF-Plug-White/dp/B08TNF4835?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&psc=1&smid=ATVPDKIKX0DER&gQT=1
    - https://tasmota.github.io/docs/devices/Sonoff-Basic/
    - https://www.youtube.com/watch?v=IvfiLcHMekQ
- Python 3.x

## Setup

Configure your smart switch IP addresses in the script and connect the LEDs to the specified GPIO pins. The system will automatically handle daylight savings time adjustments and daily timing calculations.

## Fun Extras

Includes some LED light show functions for testing and entertainment: Startup functions create different lighting patterns across the LED arrays.
