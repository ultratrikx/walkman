---
title: walkman
author: rohanth
description:
created-at: 2025-07-20
---

Total Hours: 5.5

20 July 2025: 2 Hours

-   started CAD. making a simple cad, something that fits the cassete tape + electronics for now. goal is find a real walkman and gut it out and embed electronics into that.
-   Did some research on parts and did a deep dive on walkmans. heres some cool videos about them lol
    -   [sony walkman commercial](https://youtu.be/7lipckhgG5g?si=Js0StyAzr2QiRBN8)
    -   [verge video](https://youtu.be/2DWtkSVNvTg?si=Ki9YeWAQCsqFfhlF)
    -   [Techmoan](https://youtu.be/8hMtcq_agWY?si=C_aE3jzZ9w3zR8_n)
-   Tried to find a place to thrift an old walkman from thrift store (unsuccessful)

25 July 2025: 1 hours

-   finished the cad
-   just made two simple parts, can be attached together by glue

![cad3](assets/cad3.png)

-   found models for each electronic component and added them into the cad
-   also planned out the wiring and did some research on esp boards that could run the OLED display. (some boards need like a voltage stepper and such which makes things annoying)
-   decided on raspi pico because i had familiarity working on it in the past and it should work for my needs. its also pretty cheap and small and can get the job done.

**wiring diagram**
![wiring diagram](assets/wiring.jpg)

29 July 2025: 1.5 hours

-   made the journal, BOM, repo
-   started the firmware part of the project
    -   first started with connecting nfc module wo the pi, simple io pins read/write for that.
    -   implemented logic so that based on a numerical value of an nfc tag, the song/playlist played is changed.
    -   then added logic for the oled display
    -   shows debugging messages and connection with wifi as well as the current song being played. future plan is to add a nice animation for an synth wave looking player while music is being played

29 July 2025: 1 hour

-   finished the firmware part, uploaded code to the repo.
-   for the firmware, added connection with homeassistant by using the api functionality
    -   plays a certain playlist on my room's speakers by calling that device in HA and giving it a playlist ID

11 Sep 2025: 4 hours

-   printed the parts and started soldering
-   had to redo the wiring and wired the display and nfc reader in serial to make it easier to control via firmware
-   switched firmware to circuitpy for simiplicity
-   struggled to get api calling code to work so left for tomorrow

![soldered](assets/soldered.jpeg)

12 Sep 2025: 3 hours

-   struggled with lots of firmware issues (see folder broken firmware attempts)
-   made code as simple as possible by removied HA setup and just linking to computer and creating an AHK command to launch
-   struggled with displaying text on oled so swapped to using bitmap lib, etc. this worked better lol
-   finally got a sorta working product

Next steps:

-   working on building proper integration with HA and getting it to work remotely without computer connection
-   improve case design, because it doesn't really fit the casettes i have, also make it more polished bc it lowk ugly rn

![polished](assets/polished.jpeg)

Demo Video:

[video](assets/video.mp4)
