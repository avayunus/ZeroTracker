# ZeroTracker

A lightweight Valorant tracker built on the LCU API. Zero bloat, zero overlays, 100% open source.

## Features

* **Lightweight:** Minimal resource usage compared to other trackers.
* **LCU API Integration:** Interacts directly with the local Valorant client API.
* **Zero Bloat:** No unnecessary overlays or ads.
* **Open Source:** Transparent code that you can inspect and modify.

## Prerequisites

* [Python 3.x](https://www.python.org/downloads/)
* Valorant must be running for the tracker to access the LCU API.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/avayunus/ZeroTracker.git](https://github.com/avayunus/ZeroTracker.git)
    cd ZeroTracker
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Running from Source
To run the tracker directly from the Python script:

1.  Open Valorant.
2.  Run the main script:
    ```bash
    python main.py
    ```

### Building the Executable
This project includes a `ZeroTracker.spec` file for use with PyInstaller. To build a standalone `.exe`:

1.  Install PyInstaller:
    ```bash
    pip install pyinstaller
    ```
2.  Run the build command:
    ```bash
    pyinstaller ZeroTracker.spec
    ```
3.  The executable will be located in the `dist/` folder.

## Legal & Disclaimer

ZeroTracker is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.

## License

[Insert License Name Here] - see the [LICENSE](LICENSE) file for details.
