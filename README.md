# SSL Hardware Challenge Tool

This tool will check if the robots/ball are correctly placed for the given
challenge.

It will wait untill all robots/ball are placed, wait 2 seconds and ask the user
to confirm the beggining of the challenge. After that, everything will happen
automatically.

## Dependencies

- Python 3.8.5
  - [WebSocket](https://pypi.org/project/websocket-client/)

PS: Only tested in Ubuntu 20.04.

To install the Python packages run

```shell
pip3 install websocket-client
```

The project already contains de compiled .proto files for Python, but, in case
you need to re-compile/update them you need to place the new .proto files in
the `proto` folder and then use the included script:

```shell
./update_protos.sh
```

## Usage

Open the GameController and run the `ChallengeManager.py` with:

```shell
python3 ChallengeManager.py -f <challenge_positions.json> -c <challenge_number>
```

- **challenge_positions.json**: is the .json file that contains the positions of
  the challenge.
- **challenge_number**: is the **id** of the challenge, must be between 1 and 4.

For more information about the input arguments use:

```shell
python3 ChallengeManager.py -h
```
