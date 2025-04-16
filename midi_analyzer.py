#!/usr/bin/env python3
"""
MIDI Analyzer - Recursively loads MIDI files and prints note data and rhythmic analysis from track 0
"""

import os
import argparse
import mido
from collections import defaultdict

def find_midi_files(directory):
    """
    Recursively find all MIDI files in a directory
    
    Args:
        directory (str): Directory to search for MIDI files
        
    Returns:
        list: List of paths to MIDI files
    """
    midi_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.mid', '.midi')):
                midi_files.append(os.path.join(root, file))
                
    return midi_files

def extract_note_data(midi_file):
    """
    Extract note data from track 0 of a MIDI file
    
    Args:
        midi_file (str): Path to MIDI file
        
    Returns:
        tuple: (list of note events, PPQN value)
    """
    try:
        midi = mido.MidiFile(midi_file)
        note_events = []
        
        # Print PPQN (Pulses Per Quarter Note)
        ppqn = midi.ticks_per_beat
        print(f"PPQN (Pulses Per Quarter Note): {ppqn}")
        
        if len(midi.tracks) > 0:
            track = midi.tracks[0]
            print(f"Track name: {track.name}")
            
            for msg in track:
                if msg.type in ['note_on', 'note_off']:
                    note_events.append({
                        'type': msg.type,
                        'note': msg.note,
                        'time': msg.time,
                    })
            
            # Print note data
            print(f"Note events: {len(note_events)}")
            for note in note_events:
                print(f"  {note}")
        else:
            print("No tracks found in MIDI file")
                    
        return note_events, ppqn
    except Exception as e:
        print(f"Error processing {midi_file}: {e}")
        return [], 0

def analyze_rhythm_pattern(note_events, ppqn):
    """
    Analyze the rhythm pattern from the note events
    
    Args:
        note_events (list): List of note events
        ppqn (int): Pulses Per Quarter Note
    """
    if not note_events:
        print("No note events to analyze")
        return
    
    # Convert note timings to absolute positions
    absolute_times = []
    current_time = 0
    
    # Group notes by their absolute start times
    notes_by_time = defaultdict(list)
    
    for event in note_events:
        current_time += event['time']
        if event['type'] == 'note_on':
            absolute_times.append(current_time)
            notes_by_time[current_time].append(event['note'])
    
    # Create a rhythm visualization
    print("\nRhythm Analysis:")
    
    # Detect measure length (assuming 4/4 time signature)
    measure_length = 4 * ppqn  # 4 quarter notes per measure
    
    # Create a rhythm grid
    max_time = absolute_times[-1] if absolute_times else 0
    measures = (max_time // measure_length) + 1
    
    print(f"Estimated measures: {measures}")
    print(f"Quarter note = {ppqn} ticks")
    print(f"Eighth note = {ppqn/2} ticks")
    print(f"16th note = {ppqn/4} ticks")
    
    # Print rhythm grid - show which beats have notes
    print("\nRhythm grid (measures × beats):")
    for measure in range(int(measures)):
        measure_start = measure * measure_length
        beat_markers = []
        
        # Divide each measure into 16 parts (16th notes in 4/4)
        for i in range(16):
            beat_time = measure_start + (i * ppqn // 4)
            
            # Check if there's a note at or near this time
            has_note = False
            for abs_time in absolute_times:
                # Allow for small timing variations (1/32 note)
                if abs_time >= beat_time - (ppqn // 8) and abs_time < beat_time + (ppqn // 8):
                    has_note = True
                    break
            
            # Mark quarter notes with numbers, 8th notes with + and 16th with .
            if i % 4 == 0:  # Quarter notes
                marker = str(i // 4 + 1) if has_note else str(i // 4 + 1)
            elif i % 2 == 0:  # 8th notes
                marker = '+' if has_note else '+'
            else:  # 16th notes
                marker = '.' if has_note else '.'
            
            # Bold or highlight notes that are played
            if has_note:
                beat_markers.append(f"[{marker}]")
            else:
                beat_markers.append(f" {marker} ")
        
        print(f"Measure {measure+1}: {''.join(beat_markers)}")
    
    # Analyze note patterns
    if len(notes_by_time) > 0:
        print("\nNote pattern:")
        # Count occurrences of each note
        note_counts = defaultdict(int)
        for notes in notes_by_time.values():
            for note in notes:
                note_counts[note] += 1
        
        # Find most common notes (likely rhythm/percussion notes)
        common_notes = sorted(note_counts.items(), key=lambda x: x[1], reverse=True)
        print("Most frequent notes (MIDI number: count):")
        for note, count in common_notes[:5]:  # Top 5 most common notes
            note_name = get_note_name(note)
            print(f"  {note} ({note_name}): {count} times")

def get_note_name(midi_note):
    """Convert MIDI note number to note name"""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    note = notes[midi_note % 12]
    return f"{note}{octave}"

def analyze_midi_directory(directory):
    """
    Analyze all MIDI files in a directory
    
    Args:
        directory (str): Directory to search for MIDI files
    """
    midi_files = find_midi_files(directory)
    
    if not midi_files:
        print(f"No MIDI files found in {directory}")
        return
        
    print(f"Found {len(midi_files)} MIDI file(s)")
    
    for midi_file in midi_files:
        print(f"\nAnalyzing: {midi_file}")
        note_events, ppqn = extract_note_data(midi_file)
        analyze_rhythm_pattern(note_events, ppqn)

def main():
    parser = argparse.ArgumentParser(description='Analyze MIDI files in a directory')
    parser.add_argument('directory', help='Directory containing MIDI files')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        return
    
    analyze_midi_directory(args.directory)

if __name__ == '__main__':
    main() 