# Fly-Brain Dino

**A CS student's curiosity project: can a simulated fruit fly brain learn to play Chrome Dino?**

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white) ![Pygame CE](https://img.shields.io/badge/Pygame%20CE-2.5%2B-00A86B) ![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-013243?logo=numpy&logoColor=white)

<p align="center">
  <img src="docs/brain-game-loop.gif" alt="Animated illustration of the game state moving through a simulated neural network to a jump or duck action" width="820">
</p>

## The idea

This project began with a simple question: **what happens if I connect a fruit fly inspired brain simulation to the Chrome dinosaur game?** As a computer science student, I wanted to explore how a neural network could respond to game inputs, and to understand what a small interactive model can and cannot tell us about a real brain.

The result is a desktop game and an educational neural simulation. A rule based coach demonstrates when to jump or duck. A simulated network processes game features, and a trainable readout learns to imitate the coach. You can also play yourself or let the readout control the dinosaur.

## What it does

- Runs a Chrome style dinosaur game with cacti, birds, scoring, and day and night scenes.
- Simulates leaky integrate and fire neural activity and displays it over a fruit fly brain image.
- Offers human, coach learning, and neural control modes.
- Saves and reloads the learned jump and duck readout weights.
- Lets an advanced user provide a prepared connectome graph in NPZ format.

The default network is configured for **166,700 simulated units**. Its default wiring is generated synthetically; this number describes the program setting, not a claim that the official MaleCNS connections are running.

## Technology

| Part | Technology |
|---|---|
| Language | Python |
| Game and interface | Pygame CE |
| Neural simulation and learning | NumPy |
| Image handling | Pillow |

## Run the game

Windows and Python 3.9 or newer are recommended. On the first run, `run.bat` installs the required Python packages.

1. Download or clone this repository.
2. Double click `run.bat`.
3. The game loads the bundled readout weights and starts in neural control mode. Press `2` to enter coach learning mode.

You can also start it from PowerShell:

```powershell
py -m pip install -r requirements.txt
py main.py
```

If the game starts without saved readout weights, it begins in coach learning mode. Press `S` to save the readout.

## Controls

| Key | Action |
|---|---|
| `1` | Human mode. `Space` or `Up` jumps; `Down` ducks. |
| `2` | Coach learning mode. |
| `3` | Neural control mode. |
| `P` | Toggle learning while in neural control mode. |
| `B` | Toggle birds. |
| `F` | Toggle four times speed. |
| `R` | Restart. |
| `S` | Save learned readout weights. |
| `Esc` | Quit and save. |

## How the simulation works

1. Game state is converted into features such as obstacle distance, height, speed, and dinosaur movement.
2. Population coded inputs stimulate sensory units in a leaky integrate and fire network.
3. A linear readout turns simulated activity into jump and duck values.
4. During coach learning, a hand written rule supplies target actions and the readout adjusts to imitate them.
5. In neural control mode, the readout chooses the game actions.

The coach provides the learning signal. The network does not discover the game or learn from a biological fly.

## What inspired it, and what is not included

The body model idea comes from [TuragaLab's FlyBody project](https://github.com/TuragaLab/flybody), developed with Google DeepMind and HHMI Janelia Research Campus. FlyBody uses [MuJoCo](https://github.com/google-deepmind/mujoco) for fruit fly body physics. **This game does not currently load FlyBody or run MuJoCo.** It uses a custom 2D Pygame game instead.

The brain idea is inspired by the [MaleCNS connectome project](https://male-cns.janelia.org/), which maps the central nervous system of an adult male *Drosophila melanogaster*. The project is a collaboration involving FlyEM at HHMI Janelia, the University of Cambridge, the MRC Laboratory of Molecular Biology, and Google Research.

**The official MaleCNS connection graph is not included or used by default.** The standard run creates synthetic wiring. The code has an optional loader for a separately prepared NPZ graph containing `pre`, `post`, and `weight` arrays, with an optional `sign` array. The bundled `brain_weights.npz` file stores learned action readout values; it is not a connectome.

The brain image is used as a visual background. Simulated neuron positions are sampled across the image for display and are not anatomical neuron coordinates.

## Limitations

This is a curiosity driven prototype, not a biological brain model. The network wiring is synthetic by default, the coach is hand written, and the game physics are simplified. The project has not been evaluated as a scientific model of fly behaviour. A compatible official connectome import, anatomical mapping, sensory model, motor model, and controlled behavioural evaluation would all be needed for stronger biological claims.

## Project documents

- [Project report](docs/PROJECT_REPORT.md)
- [Thesis style write up](docs/THESIS.md)

## Credits

- [TuragaLab/FlyBody](https://github.com/TuragaLab/flybody), a fruit fly body model for MuJoCo developed with Google DeepMind and HHMI Janelia.
- [Google DeepMind/MuJoCo](https://github.com/google-deepmind/mujoco), the open source physics engine used by FlyBody.
- [MaleCNS Connectome Project](https://male-cns.janelia.org/), including its [data and download documentation](https://male-cns.janelia.org/download/).
- Game and neural simulation code in this repository.
