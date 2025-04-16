#!/usr/bin/env python3
import os
import argparse
import sys
from analyze_midi_data import analyze_rhythm_pattern, extract_note_events

def find_midi_files(directory):
    """
    Recursively find all MIDI files (.mid, .midi) in the given directory
    
    Args:
        directory (str): Path to search
        
    Returns:
        list: List of paths to MIDI files
    """
    midi_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.mid', '.midi')):
                midi_files.append(os.path.join(root, file))
    
    return midi_files

def process_midi_file(midi_file):
    """
    Process a single MIDI file and run the analysis
    
    Args:
        midi_file (str): Path to MIDI file
    """
    print(f"\n\n{'=' * 80}")
    print(f"Processing: {midi_file}")
    print(f"{'=' * 80}")
    
    note_events, ppqn = extract_note_events(midi_file)
    
    if note_events and ppqn:
        analyze_rhythm_pattern(note_events, ppqn)
    else:
        print(f"Could not analyze {midi_file}")

def main():
    parser = argparse.ArgumentParser(description='Analyze MIDI files for rhythm patterns')
    parser.add_argument('directory', help='Directory to search for MIDI files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print verbose output')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        sys.exit(1)
    
    midi_files = find_midi_files(args.directory)
    
    if not midi_files:
        print(f"No MIDI files found in {args.directory}")
        sys.exit(0)
    
    if args.verbose:
        print(f"Found {len(midi_files)} MIDI files:")
        for file in midi_files:
            print(f"  - {file}")
    else:
        print(f"Found {len(midi_files)} MIDI files")
    
    for midi_file in midi_files:
        process_midi_file(midi_file)

if __name__ == '__main__':
    main() 