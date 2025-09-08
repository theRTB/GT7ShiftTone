# GT7ShiftTone

**Calibrated audio tone that indicates when to shift for optimal acceleration in Gran Turismo 7**

![example Toyota GR Supra Racing Concept '18 GUI](images/GUI-1.png)

# Optimal shift points
[Click here for optimal shift points with visualization of in-game UI on when to shift](/plots)

## Current release

GT7ShiftTone is being primarily developed for Group 1, 2, 3, 4 and B cars as they tend to run under BoP with fixed settings:
- This program should work out-of-the-box for supported cars
  -  The car data will only be loaded if activately racing, not in replays or menus or during race countdown
- Be aware that false positives exist: not every beep is an upshift.

### Launch with:
- GT7ShiftTone-beta2.exe: if you have downloaded the PyInstaller release
  - Windows Firewall will ask for confirmation for network access
- gtbeep.py: For Python users  

**Changes:**  
- Generated pyinstaller executable for Windows
- Added 300+ stock curves
- Added toggle in Settings to load stock curves for all cars: Disabled by default
  - Emphasis on car being stock, or else the beep is simply incorrect
- Added support for Linux through library simpleaudio (requires libasound2-dev)

# Information below this point is not required for using the shift tone

Sample power curve:  
![example Subaru WRX STI 2014 Power](images/Power.png)
## Implementation

The Tone Offset is dynamic. The program keeps track of the time between a shift tone and an initiated shift, and modifies the running Tone Offset if the tone is early or late.

There are three triggers for the shift tone:
- **Shift RPM**: The RPM value at which power in the current gear becomes lower than the power in the next gear: the ideal time to upshift. If the application predicts shift RPM is reached in the defined tone offset time, trigger a beep
- **Percentage of revlimit**: Uses the tone offset distance as predicted distance to current RPM hitting the listed percentage of rev limit
  - Example: A rev limit of 7500 and a value of 98.0% triggers a tone if it predicts 7350 RPM will be reached in 283 milliseconds
- **Time distance to revlimit**: uses the tone offset value plus the revlimit ms value as predicted distance to current RPM hitting the defined revlimit. Defaults to 100 milliseconds, which leads to a default prediction distance of 383ms

The delay between beep triggers is currently set to 0.5 seconds. This time-out is shared between the three triggers.  
If you choose to not shift and remain above the trigger RPM, the program will not beep again even if revlimit is hit.

### General display values:

- **Revlimit**: The limit on engine RPM by its own power.
- **Revbar**: The range in which the revbar lights up. It begins at 85% and starts blinking at 99% of a predetermined value
  - This is generally equal to the upshift line value in the Transmission tuning page, but there are exceptions.
- **Power**: At which RPM peak power is hit.
- **'vmax'**: The top speed of the car as provided by telemetry. This is in native units of the game (mph or kph) and does not include hybrid power or DRS.
- **Tach**: The current RPM value as reported by the telemetry. Updates 30 times per second
- **Car ID**: The internal ID of the car.

### Per gear:

- **Target**: The derived shift RPM value.  
- **Rel. Ratio**: The relative ratio of the gear ratios between two consecutive gears.
Say the next gear has a number of 1.35: It is 35% longer. Peak power is reached at a speed 35% higher, revlimit is reached at a speed 35% higher.
- **Ratio**: The gear ratio of the gear
  - Toggle between Ratio and Rel. Ratio by double clicking the "Ratio" or "Rel. Ratio" label text

### General configuration:

- **Tone offset**: Predicted distance between the beep trigger and the trigger RPM value.
  - This should not be taken as reaction time and minimized. It should be regarded as the time you consistently respond to the tone with the least amount of mental effort. Defaults to 283 ms.
- **Volume**: Adjusts the volume of the beep in four steps total. Each step is about half as loud as the previous, where the second loudest is the default. A value of 0 mutes only the shift beep.
- **Reset button**: If pressed, reset revlimit, power curve and all values for all gears. Configuration values are unchanged. If the UI is unresponsive, restart the application.
- **Start/Stop button**: Stops or starts the loop to collect packets. In short, if button says "Stop" it is running, if it says "Start" the program is not tracking the game's packets and will not beep.
- **Shift history**: Displays a table with the last 10 shifts including target RPM, actual shift RPM, gear and measured offset between beep and shift.
- **View Power Graph**: If enabled and pressed, displays a power graph in a separate window.

In **Settings**:  
- **Hysteresis**: Hysteresis may be set as another layer to smooth RPM. An intermediary RPM value is updated only if the change in RPM is larger than the hysteresis value, which is then used for the shift beep tests. Defaults to 0.5% of maximum engine RPM.
- **Revlimit %**: The respected rev limit in percentage of actual rev limit. This is to create a buffer for transients that could cause the engine to cut out due to hitting actual rev limit. Defaults to 98.0%.
- **Revlimit ms**: The minimum predicted distance to actual rev limit. This is to create a buffer for fast changes in RPM that would otherwise lead to hitting actual rev limit, such as in first gear. Defaults to 100ms.
- **Dynamic Tone Offset**: Enables or disables the dynamic updating of the tone offset.
- **Include replays**: Sets the program to function during replays: useful primarily to log shift points in a replay. Also allows loading of car data when in race menu.
- **Car is stock**: Defaults to off. Assumes the driven car is stock. Do not toggle this if the driven car is tuned.
- **Bluetooth keepalive**: Defaults to off. Bluetooth devices tend to go into power saving and not play the beep in time or at all. This attempts to force the connection to stay alive by playing silence in-between.

## Playstation IP-address

The program will attempt to find an active Playstation console with Gran Turismo 7 active. On Windows, it does this by assuming both the Playstation and the device the code runs on are on the same local network (the most common range of 192.168.x.y).  
If that fails, you will need to find and manually set your console IP address into the config file:

- Find the IP address by going to the PS Settings -> Network -> Connection Status -> View Connection Status -> IPv4 address
- Open _config.json_ in the installation folder and add the IP-adress within the quotation marks in the line with **"target_ip": "",**
  - For example: _"target_ip": "192.168.1.123",_
  - This file is generated after starting and exiting the program once

## Settings are saved to config.json

The settings are saved to _config.json_ on exit. This includes Tone offset, Hysteresis, Revlimit %, Revlimit ms, Volume, Dynamic Tone Offset, Window Location.
Remote telemetry sends data at 60 packets per second. The offset variables (Tone offset, revlimit ms) while defined in milliseconds currently use packet counts in the backend.  
There is one packet per 16.667 milliseconds, approximately.

## Notes and known issues
- Assumptions: Stock or BoP, full throttle, not grip limited, instantaneous shifts
- Program can beep on a downshift (fix work in progress)  
~~- The supplied gear ratios given by the game may not be correct (fix work in progress)~~
- Gear 9 and 10 are never filled in even if the car has them: Limitation of the telemetry and implementation
- The program assumes the car is driven with the stock Power curve, some upgrades will result in suboptimal shifts:
  - Power Restrictor for example affects the shape of the curve: adjustments will not match a saved curve
  - Turbos affect the shape considerably and increase the cost of shifting
  - Upgrades that affect the RPM range of the engine
  - Conversely, upgrades that maintain the same shape are fine: Such as ECU percentage adjustment
- The default values are arbitrarily chosen and may not suit individual cars or track surface
- (Script only) The socket is not always closed cleanly for no apparent reason: requiring a new console on most consecutive launches
- Application will on rare occasions just crash: related to the UI library and cannot be fixed
- Requires at minimum Python 3.10 (statistics linear regression)
- This program _'works for me'_. If you wish to run this script and there are issues, please report them.





