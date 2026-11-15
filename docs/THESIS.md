# Thesis Style Write Up

## Exploring a Simulated Fruit Fly Brain Through the Chrome Dinosaur Game

### A computer science student's curiosity project

| Detail | Description |
|---|---|
| Project | Fly-Brain Dino |
| Format | Prototype study and thesis style technical write up |
| Status | Preliminary implementation; no formal behavioural evaluation completed |

## Abstract

This project explores a simple question: can a simulated, fruit fly inspired neural network be connected to the Chrome dinosaur game, and what can such a prototype teach a computer science student about perception, learning, and action? Fly-Brain Dino combines a two dimensional Pygame game with a leaky integrate and fire network. A hand written coach supplies jump and duck labels, and a trainable linear readout learns to imitate those labels. The interface provides human play, coach learning, and neural control modes, alongside a visualization of activity over a fruit fly brain image.

The prototype uses synthetic network wiring by default. Although its design is inspired by TuragaLab's FlyBody project and the MaleCNS connectome research, it does not currently load FlyBody, run MuJoCo, or use the official MaleCNS connection graph in its standard configuration. The project is therefore best understood as an educational simulation, not a biologically faithful fly or a validated connectome model. A basic startup check confirmed that the saved readout weights load and the neural simulation advances; no controlled performance study has yet been conducted.

## 1. Introduction

A computer science project can begin with a small curiosity. In this case, the curiosity was whether a simulated fruit fly brain could play the familiar Chrome dinosaur game. The game provides a compact setting for experimentation: the program observes a changing scene and must produce a small number of actions.

The project takes inspiration from two research resources. TuragaLab's FlyBody provides an anatomically detailed fruit fly body model for MuJoCo physics and locomotion research. The MaleCNS project provides a reconstructed central nervous system connectome for an adult male *Drosophila melanogaster*. These resources motivate the project, but they are not automatically present in the implementation. The distinction between inspiration, data, and executable model is central to interpreting the prototype.

## 2. Project question and objectives

### 2.1 Project question

How can a simple spiking network be connected to a familiar game to help a student explore the relationship between game inputs, simulated neural activity, learned readout values, and actions?

### 2.2 Objectives

1. Build a small interactive dinosaur game with clear obstacles and actions.
2. Encode selected game features as inputs to a simulated neural network.
3. Train an output readout from action labels supplied by a coach.
4. Let the network readout control the game.
5. Make the process visible through an activity panel.
6. Document what is and is not represented biologically.

## 3. Background and source projects

### 3.1 FlyBody and MuJoCo

[FlyBody](https://github.com/TuragaLab/flybody) is a fruit fly body model for MuJoCo and locomotion tasks. Its repository describes development in collaboration between Google DeepMind and HHMI Janelia Research Campus. [MuJoCo](https://github.com/google-deepmind/mujoco) is the physics engine associated with that work.

Fly-Brain Dino currently has a separate Pygame implementation. The game does not load FlyBody's model files or use MuJoCo physics. FlyBody is credited as project inspiration, not as an integrated dependency.

### 3.2 MaleCNS connectome

The [MaleCNS Connectome Project](https://male-cns.janelia.org/) provides access to the reconstructed male fruit fly central nervous system data. The project credits a collaboration involving FlyEM at HHMI Janelia, the University of Cambridge, the MRC Laboratory of Molecular Biology, and Google Research.

Fly-Brain Dino's standard configuration does not use the official graph. Its default connections are generated synthetically. The code includes an optional loader for a prepared NPZ graph with `pre`, `post`, and `weight` arrays and an optional `sign` array. The repository does not include an official MaleCNS graph export or a conversion workflow for the source data.

## 4. System design

The program consists of four main parts:

| Component | Role |
|---|---|
| `dino_game.py` | 2D game state, obstacles, collisions, game features, and coach rules |
| `fly_brain.py` | Network wiring, sensory encoding, neural updates, readout, learning, and optional graph loading |
| `brain_view.py` | Visualization of simulated activity over a brain image |
| `main.py` | Window, keyboard input, mode changes, display loop, and saving weights |

The default network is configured for 166,700 simulated units and about 2.67 million synthetically generated connections. The number is an implementation setting. It does not establish that the corresponding MaleCNS neurons or synapses are being simulated.

## 5. Method

### 5.1 Game state encoding

The game supplies normalized features such as obstacle distance, obstacle height and width, speed, dinosaur position and velocity, ducking state, and whether a bird is present. Population coding maps feature values onto selected sensory units.

### 5.2 Neural update

Each simulation step updates leaky state variables, propagates activity through the configured sparse connections, adds noise, and records unit firing rates. Under the default configuration, the sparse connections are synthetic and generated from spatially local and long range rules.

### 5.3 Action readout and coach learning

The readout uses network activity to produce jump and duck values. A hand written coach inspects the game and produces target action labels. During learning, a normalized least mean squares style update adjusts readout weights toward the coach's decisions. In neural mode, the readout values determine game actions; plasticity can be toggled.

This method learns imitation of the coach. The coach is an engineered source of supervision, so the observed behavior cannot be interpreted as autonomous discovery or biological learning.

### 5.4 Visualization

Activity is drawn over a fruit fly brain image to make changes visible. Unit positions are sampled from the image mask for display. They are not mapped from MaleCNS anatomical coordinates, neuron IDs, or morphology. The visualization is explanatory rather than a spatial reconstruction.

## 6. Implementation and operation

The program is written in Python and uses Pygame CE for the desktop game and interface, NumPy for neural state and weight updates, and Pillow for image loading when available. A Windows launcher installs the dependencies and starts the game.

If saved readout weights are present and match the configured network size, the application loads them and starts in neural control mode. Otherwise it begins in coach learning mode. The user can press `1` for human play, `2` for learning, or `3` for neural control. `P` toggles plasticity, `S` saves, and `Esc` quits and saves.

## 7. Preliminary verification

A basic startup check was run in a Windows environment with Python 3.14.7, Pygame CE 2.5.8, NumPy 2.5.4, and Pillow 13.0.0. It initialized the game components, loaded `brain_weights.npz`, constructed the 166,700 unit synthetic network, and completed one neural update.

This check supports a limited conclusion: the application can initialize in that environment. It does not establish successful long duration play, robust decision quality, agreement with the coach over a full game, or biological accuracy. No numerical behavioural results are reported in this write up.

## 8. Limitations

1. **Synthetic connectivity:** the default network is not the MaleCNS connectome.
2. **Simplified biology:** the leaky integrate and fire units, weights, noise, and learning rule are simplified computational choices.
3. **Hand written supervision:** the coach defines target behavior, so training imitates a programmed rule.
4. **Simplified environment:** the game is 2D and uses custom collision and movement logic rather than MuJoCo physics.
5. **Non anatomical display:** neuron positions on the image are for visualization only.
6. **Unvalidated data import:** the optional graph loader has not been validated here against an official MaleCNS export.
7. **Limited evaluation:** the project has no controlled comparison, repeated trial statistics, or scientific validation.

## 9. Evaluation plan

A future evaluation should separate software performance from biological interpretation.

### 9.1 Software performance

Run multiple fixed seeds and record score, survival frames, collisions, action timing, coach agreement, and processing time. Compare human, coach, and neural modes. Report the number of trials, hardware, software versions, and whether the readout is trained or loaded.

### 9.2 Learning behavior

Track coach agreement and game survival over training time. Compare the learned readout with a fixed coach baseline and an untrained readout. Keep training and evaluation runs separate to reduce the risk of reporting only favorable examples.

### 9.3 Connectome integration

If an official graph is added, document the data release, neuron mapping, edge filtering, signs, and weight conversion. Validate that node and edge counts match the processed dataset. Compare the graph based network against the existing synthetic baseline under the same inputs and learning setup.

### 9.4 Embodied simulation

If FlyBody is integrated, document the mapping between the game or task state, neural outputs, and MuJoCo action controls. Evaluate this as a new system rather than implying that the current Pygame version already uses physical fly dynamics.

## 10. Discussion

The prototype is useful as a learning aid because the loop is small enough to inspect. It links an environment state to neural activity, then to a trainable readout and action. The game makes abstract pieces of a model visible and gives the student a concrete reason to investigate connectomes and body simulation.

The most important interpretive risk is overclaiming from surface similarities. A fly brain image, a fly sized network, and a connectome inspired description do not make the network a connectome simulation. Data provenance, structural correspondence, biologically grounded neural dynamics, and careful evaluation are needed before drawing claims about a real fly nervous system.

## 11. Conclusion

Fly-Brain Dino is a curiosity driven computer science prototype that connects a simplified spiking network to a familiar game. The coach guided readout demonstrates one way to map game features to actions and makes the process observable. Its current value is educational and exploratory. It does not yet demonstrate an official MaleCNS connectome controlling a FlyBody model, nor does it provide evidence about biological fly behavior.

The clearest next step is a repeatable evaluation of the existing controller. A separate, carefully documented effort would be required to import the official MaleCNS connectivity or integrate FlyBody with MuJoCo.

## References

1. TuragaLab. [FlyBody: fruit fly body model for MuJoCo physics](https://github.com/TuragaLab/flybody).
2. Google DeepMind. [MuJoCo physics engine](https://github.com/google-deepmind/mujoco).
3. FlyEM and collaborators. [MaleCNS Connectome Project](https://male-cns.janelia.org/).
4. MaleCNS Connectome Project. [Data and download documentation](https://male-cns.janelia.org/download/).
