# pipewire-simple-audio-link
Create audio between applications and your microphones with ease!

# Requirements
- Pipewire
- git
- Python 3.11 (tested version)
- PyQt6 (python package)

# Installation
You can [download pre-compiled binary](https://github.com/lyuksovannyy/pipewire-simple-audio-link/releases) or use raw python file instead or build it your self.
Clone this repository and move to newly created directory

- `git clone https://github.com/lyuksovannyy/pipewire-simple-audio-link && cd pipewire-simple-audio-link`

Make sure you make bash scripts (`prepare_venv.sh`, `run.sh`) executabe
- `chmod +x prepare_venv.sh`
- `chmod +x run.sh`

Run `prepare_venv.sh` on first launch and then you need to use only `run.sh`
- `prepare_venv.sh`
- `run.sh`

Also if you're so lazy here is one-line command for you:
- `git clone https://github.com/lyuksovannyy/pipewire-simple-audio-link | cd && chmod +x prepare_venv.sh && chmod +x run.sh && prepare_venv.sh && run.sh`

Want to compile file yourself? Then make `build.sh` executable and run it!
- `chmod +x build.sh && build.sh`

After compilation process you'll find your compiled binary inside `dist/soundstreamer/`,
now you can use compiled binary with ease!
