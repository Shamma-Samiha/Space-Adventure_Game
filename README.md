# Space Adventure (Pygame)
A children’s space game: arrow-key shuttle, parallax stars, coins, monsters that chase, 3 lives, reach the sun.

## Run (Windows)
1) Python 3.10+  
2) pip install pygame  
3) cd game && python space_adventure.py

## Build Windows EXE
From game/:  
pyinstaller --noconsole --onefile --name SpaceAdventure --add-data "assets;assets" space_adventure.py

The exe appears in dist/SpaceAdventure.exe.

## Publish
- Create a GitHub release and upload the exe.  
- Put web/ contents in the repo and enable GitHub Pages to serve from /web (or /docs).  
- Link the “Download for Windows” button to the Release URL.
