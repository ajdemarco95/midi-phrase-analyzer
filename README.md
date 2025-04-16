# MIDI Phrase Analyzer

A Python tool for analyzing rhythmic and melodic patterns in MIDI files. This tool extracts and visualizes musical patterns, helping musicians, composers, and music theorists understand the structure of music pieces.

## Features

- **Rhythm Pattern Analysis**: Analyzes note onset patterns and identifies rhythmic structures
- **Melodic Pattern Analysis**: Examines note sequences and detects recurring melodic patterns
- **Section Identification**: Detects musical sections based on pattern changes 
- **Form Visualization**: Displays the overall musical form using letter notation (e.g., AABA)
- **Note Range Analysis**: Shows the range of notes used in the composition
- **Rhythmic Density Calculation**: Computes the average number of notes per measure

## Installation

1. Clone this repository:
```bash
git clone https://github.com/ajdemarco95/midi-phrase-analyzer.git
cd midi-rhythm-analyzer
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Analyzing a Single MIDI File

Use `analyze_midi_data.py` to analyze a single MIDI file:

```bash
python analyze_midi_data.py path/to/your/file.mid
```

### Analyzing Multiple MIDI Files

Use `process_midi_files.py` to recursively analyze all MIDI files in a directory:

```bash
python process_midi_files.py path/to/midi/directory
```

## Example Output

```
================================================================================
Processing: midi/melody.mid
================================================================================

--- RHYTHM PHRASAL STRUCTURE ANALYSIS ---
Total measures: 4
Total duration: 1984 ticks (15.50 quarter notes)

--- COMBINED RHYTHM AND MELODIC ANALYSIS ---
The rhythmic and melodic patterns differ:
  Rhythmic: AAAA
  Melodic:  ABAB

Note range: E3 to D4
Rhythmic density: 7.00 onsets per measure

Overall melodic form: ABAB
```

## How It Works

1. The tool parses MIDI files using the `mido` library to extract note events
2. It analyzes the timing of note onsets to identify rhythmic patterns
3. It examines the pitch sequence of notes to detect melodic patterns
4. It compares measures to identify repeated sections
5. It maps the patterns to letter notation (A, B, C, etc.) to visualize the musical form

## Requirements

- Python 3.6+
- mido 1.2.10+

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Thanks to the creators of the mido library for making MIDI file processing easier
- Inspired by music theory analysis techniques used by composers and theorists 