# Project Report

## Fly Brain Dino

**A CS student's curiosity project about a simulated fruit fly brain playing Chrome Dino**

## Executive summary

Fly Brain Dino is a desktop project that combines a Chrome style dinosaur game with a simulated neural network. It began as a computer science student's curiosity about whether a fruit fly inspired brain simulation could react to a familiar game. A hand written coach demonstrates jump and duck actions. A trainable readout learns to imitate the coach and can then control the game.

The software is an educational prototype. Its default network wiring is synthetic, and its game is built with Pygame CE. It does not currently use the official MaleCNS connection graph, the FlyBody model, or MuJoCo physics.

## Motivation and objective

The goal was to make neural simulation concepts visible and interactive. Chrome Dino offers a simple environment with clear inputs and actions: obstacle distance, obstacle type, jump, and duck. This makes it possible to observe a basic loop from game state to simulated neural activity to an action.

The project asks:

> How can a simple spiking network be connected to a familiar game so a student can explore its inputs, outputs, and limitations?

## What the program does

1. Presents a 2D side scrolling dinosaur game with cacti and birds.
2. Encodes selected game features as inputs to a leaky integrate and fire network.
3. Calculates jump and duck outputs using a linear readout over network activity.
4. Trains that readout using action labels from a rule based coach.
5. Shows simulated activity over a fruit fly brain image.
6. Saves and loads readout weights in `brain_weights.npz`.

The code defaults to 166,700 simulated units and approximately 2.67 million synthetically generated connections. These are implementation settings, not a representation of the official MaleCNS wiring.

## Technologies

| Area | Technology |
|---|---|
| Programming language | Python |
| Game and window | Pygame CE |
| Neural state and learning | NumPy |
| Image handling | Pillow, with a Pygame fallback |
| Optional graph input | NumPy NPZ file |

## How it works

1. The game derives normalized features for the current situation.
2. Sensory populations respond to those values.
3. A leaky integrate and fire update advances the simulated network.
4. A linear readout maps activity to jump and duck values.
5. In learning mode, a rule based coach provides target actions and the readout weights update.
6. In neural control mode, the readout actions are sent back to the game.

This is supervised imitation of a hand written coach. The coach is an engineered source of supervision, so the observed behavior cannot be interpreted as autonomous discovery or biological learning.

## Upstream inspiration and scope

The project draws inspiration from [TuragaLab's FlyBody](https://github.com/TuragaLab/flybody), a fruit fly body model developed with Google DeepMind and HHMI Janelia Research Campus, and from the [MaleCNS connectome project](https://male-cns.janelia.org/), a collaboration involving FlyEM at HHMI Janelia, the University of Cambridge, the MRC Laboratory of Molecular Biology, and Google Research.

The current implementation is separate from those research projects. It uses Pygame's 2D game logic rather than FlyBody and MuJoCo. The default network uses synthetic connections rather than the official MaleCNS graph. A custom NPZ graph can be supplied through the optional loader, but the repository does not contain an official data export or a conversion pipeline. The displayed brain image is a background for visualization; the simulated units are not placed using anatomical coordinates.

## Current validation

A basic startup check was completed in a Windows development environment with Python 3.14.7, Pygame CE 2.5.8, NumPy 2.5.4, and Pillow 13.0.0. The game components initialized, the saved readout loaded, and one simulation step completed using the 166,700 unit configuration.

This check confirms basic initialization only. It does not measure how well the controller plays, establish long term training performance, or validate the biology of the simulation.

## Limitations

1. Default connections are synthetic rather than MaleCNS connectome edges.
2. The coach is hand written, so the readout learns to imitate programmed rules.
3. The game is a simplified 2D environment and does not use MuJoCo.
4. Neuron positions in the visualization are sampled over an image and are not anatomical coordinates.
5. The optional NPZ loader has not been validated against an official MaleCNS export.
6. No controlled performance or scientific validation study has been completed.

## Suggested next steps

1. Measure coach agreement, score, survival time, and action timing over repeated runs.
2. Add repeatable seeds and export run metrics for comparison.
3. Document and validate a converter from MaleCNS data into the optional graph format.
4. Compare synthetic wiring with a real graph under identical input and training conditions.
5. If a MuJoCo embodiment is added, define a documented interface between neural outputs and FlyBody actions.

## Conclusion

Fly Brain Dino turns a student's curiosity into a working interactive prototype. Its main value is educational: it makes a simple perception, neural activity, and action loop visible. It also demonstrates why using a connectome image or neuron count is not the same as running a connectome. Clear data integration and controlled evaluation are the next steps toward stronger claims.

## References

1. [TuragaLab/FlyBody repository](https://github.com/TuragaLab/flybody).
2. [Google DeepMind MuJoCo repository](https://github.com/google-deepmind/mujoco).
3. [MaleCNS Connectome Project](https://male-cns.janelia.org/).
4. [MaleCNS data and download documentation](https://male-cns.janelia.org/download/).
