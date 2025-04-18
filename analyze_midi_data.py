from collections import defaultdict
import argparse
import sys
import mido

def extract_note_events(midi_file):
    """
    Extract note events and PPQN from a MIDI file
    
    Args:
        midi_file (str): Path to MIDI file
        
    Returns:
        tuple: (note_events, ppqn)
    """
    try:
        midi = mido.MidiFile(midi_file)
        ppqn = midi.ticks_per_beat
        
        note_events = []
        
        # Process each track
        for track in midi.tracks:
            # Process messages in this track
            for msg in track:
                if msg.type in ('note_on', 'note_off'):
                    # Convert velocity=0 note_on messages to note_off
                    if msg.type == 'note_on' and msg.velocity == 0:
                        msg_type = 'note_off'
                    else:
                        msg_type = msg.type
                    
                    note_events.append({
                        'type': msg_type,
                        'note': msg.note,
                        'time': msg.time
                    })
        
        return note_events, ppqn
    
    except Exception as e:
        print(f"Error processing {midi_file}: {str(e)}")
        return None, None

def analyze_rhythm_pattern(note_events, ppqn):
    """
    Analyze both the rhythm and melodic patterns from the note events
    
    Args:
        note_events (list): List of note events
        ppqn (int): Pulses Per Quarter Note
        
    Returns:
        set: Set of unique rhythm patterns in the file (as frozensets)
    """
    if not note_events:
        print("No note events to analyze")
        return set()
    
    # Convert note timings to absolute positions
    absolute_times = []
    current_time = 0
    
    # Group notes by their absolute start times
    notes_by_time = defaultdict(list)
    
    # Track when notes start and end for visualization
    note_timeline = {}
    
    for event in note_events:
        current_time += event['time']
        
        if event['type'] == 'note_on':
            absolute_times.append(current_time)
            notes_by_time[current_time].append(event['note'])
            
            # Start tracking this note in the timeline
            if event['note'] not in note_timeline:
                note_timeline[event['note']] = []
            note_timeline[event['note']].append({'start': current_time, 'end': None})
        elif event['type'] == 'note_off':
            # Find the most recent note_on for this note and mark its end
            if event['note'] in note_timeline and note_timeline[event['note']]:
                # Find the most recent unended note
                for note_event in reversed(note_timeline[event['note']]):
                    if note_event['end'] is None:
                        note_event['end'] = current_time
                        break
    
    # Create a rhythm visualization
    print("\n--- RHYTHM PHRASAL STRUCTURE ANALYSIS ---")
    
    # Detect measure length (assuming 4/4 time signature)
    measure_length = 4 * ppqn  # 4 quarter notes per measure
    
    # Create a rhythm grid
    max_time = max(absolute_times) if absolute_times else 0
    measures = (max_time // measure_length) + 1
    
    print(f"Total measures: {int(measures)}")
    print(f"Total duration: {max_time} ticks ({max_time / ppqn:.2f} quarter notes)")
    
    # Collect all onset positions for each measure
    measure_onset_patterns = []
    for measure in range(int(measures)):
        measure_start = measure * measure_length
        measure_end = (measure + 1) * measure_length
        
        # Get all onset times in this measure, normalized to 16th notes (0-15)
        onsets = []
        for time in sorted(notes_by_time.keys()):
            if measure_start <= time < measure_end:
                # Convert to 16th-note position (0-15) within the measure
                pos_in_measure = (time - measure_start) // (ppqn // 4)
                onsets.append(int(pos_in_measure))
        
        measure_onset_patterns.append(sorted(onsets))
        
    # Identify identical measures rhythmically
    identical_measures = defaultdict(list)
    for i, pattern1 in enumerate(measure_onset_patterns):
        for j, pattern2 in enumerate(measure_onset_patterns):
            if i != j and pattern1 == pattern2:
                identical_measures[i].append(j)
    
    # Find measure groups
    measure_groups = []
    processed = set()
    
    for i in range(len(measure_onset_patterns)):
        if i in processed:
            continue
            
        group = [i]
        processed.add(i)
        
        for j in identical_measures.get(i, []):
            if j not in processed:
                group.append(j)
                processed.add(j)
        
        if group:
            measure_groups.append(sorted(group))
    
    
    # Analyze pattern sequence
    pattern_sequence = []
    pattern_map = {}
    
    for i in range(len(measure_groups)):
        pattern_map[i] = chr(65 + i)  # A, B, C, etc.
    
    for i in range(len(measure_onset_patterns)):
        for group_idx, group in enumerate(measure_groups):
            if i in group:
                pattern_sequence.append(pattern_map[group_idx])
                break
        
    # Find repeating patterns in the sequence
    if len(pattern_sequence) > 1:
        
        # Check for different repeating pattern lengths
        for pattern_length in range(1, len(pattern_sequence) // 2 + 1):
            for start in range(len(pattern_sequence) - pattern_length):
                subpattern = pattern_sequence[start:start+pattern_length]

    # Now analyze melodic patterns
    
    # Create a list of note sequences by measure, preserving onset order and notes
    measure_note_sequences = []
    
    for measure in range(int(measures)):
        measure_start = measure * measure_length
        measure_end = (measure + 1) * measure_length
        
        # Get all notes with their onset times in this measure
        measure_notes = []
        for time in sorted(notes_by_time.keys()):
            if measure_start <= time < measure_end:
                # Convert to relative position in the measure (16th notes)
                pos_in_measure = (time - measure_start) // (ppqn // 4)
                # Include both position and notes
                for note in sorted(notes_by_time[time]):
                    measure_notes.append((int(pos_in_measure), note))
        
        # Sort by onset time within measure
        measure_note_sequences.append(sorted(measure_notes))
    
    # Print note sequences for each measure
    for i, sequence in enumerate(measure_note_sequences):
        for pos, note in sequence:
            beat = (pos // 4) + 1  # Convert to 1-indexed beat number
            subdivision = pos % 4  # Subdivision within beat
            
            # Format subdivision as text
            if subdivision == 0:
                beat_pos = f"Beat {beat}"
            elif subdivision == 1:
                beat_pos = f"Beat {beat}+"
            elif subdivision == 2:
                beat_pos = f"Beat {beat}&"
            else:
                beat_pos = f"Beat {beat}a"
                
            note_name = get_note_name(note)
    
    # Compare melodic sequences between measures
    identical_melodic_measures = defaultdict(list)
    for i, seq1 in enumerate(measure_note_sequences):
        for j, seq2 in enumerate(measure_note_sequences):
            if i != j:
                # Compare full note sequences including both timing and pitch
                if seq1 == seq2:
                    identical_melodic_measures[i].append(j)
    
    # Find melodic measure groups
    melodic_measure_groups = []
    processed = set()
    
    for i in range(len(measure_note_sequences)):
        if i in processed:
            continue
            
        group = [i]
        processed.add(i)
        
        for j in identical_melodic_measures.get(i, []):
            if j not in processed:
                group.append(j)
                processed.add(j)
        
        if group:
            melodic_measure_groups.append(sorted(group))
    
    
    # Analyze melodic pattern sequence
    melodic_pattern_sequence = []
    melodic_pattern_map = {}
    
    for i in range(len(melodic_measure_groups)):
        melodic_pattern_map[i] = chr(65 + i)  # A, B, C, etc.
    
    for i in range(len(measure_note_sequences)):
        for group_idx, group in enumerate(melodic_measure_groups):
            if i in group:
                melodic_pattern_sequence.append(melodic_pattern_map[group_idx])
                break
        
    
    # Compare rhythmic and melodic patterns
    print("\n--- COMBINED RHYTHM AND MELODIC ANALYSIS ---")
    if pattern_sequence == melodic_pattern_sequence:
        print("The rhythmic and melodic patterns match exactly.")
    else:
        print("The rhythmic and melodic patterns differ:")
        print(f"  Rhythmic: {''.join(pattern_sequence)}")
        print(f"  Melodic:  {''.join(melodic_pattern_sequence)}")
    
    
    # Get all unique notes for range information
    all_notes = set()
    for events in notes_by_time.values():
        all_notes.update(events)
    
    note_range = (min(all_notes), max(all_notes))
    print(f"\nNote range: {get_note_name(note_range[0])} to {get_note_name(note_range[1])}")
    
    # Calculate the rhythmic density
    density = len(absolute_times) / int(measures)
    print(f"Rhythmic density: {density:.2f} onsets per measure")
    
    # Analyze unique 1-bar rhythm patterns
    unique_patterns = set()
    for pattern in measure_onset_patterns:
        unique_patterns.add(frozenset(pattern))
    
    print(f"\nNumber of unique 1-bar rhythm patterns: {len(unique_patterns)}")
    print("\nUnique 1-bar rhythm patterns:")
    print("-" * 40)
    
    # Convert frozensets to sorted lists for better display
    sorted_patterns = [sorted(list(pattern)) for pattern in unique_patterns]
    sorted_patterns.sort(key=lambda x: (len(x), x if x else [-1]))  # Sort by length, then by content
    
    for i, pattern in enumerate(sorted_patterns, 1):
        # Convert 16th note positions to more readable format
        readable_positions = []
        for pos in pattern:
            beat = (pos // 4) + 1
            subdivision = pos % 4
            
            if subdivision == 0:
                beat_pos = f"{beat}"
            elif subdivision == 1:
                beat_pos = f"{beat}.1"
            elif subdivision == 2:
                beat_pos = f"{beat}.2"
            else:
                beat_pos = f"{beat}.3"
                
            readable_positions.append(beat_pos)
        
        print(f"Pattern {i}: {' '.join(readable_positions)}")
    
    # Identify section boundaries based on melodic pattern changes
    if len(melodic_pattern_sequence) > 1:
        section_boundaries = [0]  # Start of the piece
        
        for i in range(1, len(melodic_pattern_sequence)):
            if melodic_pattern_sequence[i] != melodic_pattern_sequence[i-1]:
                section_boundaries.append(i)
        
        section_boundaries.append(len(melodic_pattern_sequence))  # End of the piece
        
        
        sections = []
        for i in range(len(section_boundaries) - 1):
            start = section_boundaries[i]
            end = section_boundaries[i+1] - 1
            pattern = melodic_pattern_sequence[start]
            length = end - start + 1
            
            sections.append({
                'pattern': pattern,
                'start': start + 1,  # 1-indexed for display
                'end': end + 1,      # 1-indexed for display
                'length': length
            })
        
        
        # Describe the overall form
        form = ''.join([section['pattern'] for section in sections])
        print(f"\nOverall melodic form: {form}")
        
    return unique_patterns

def get_note_name(midi_note):
    """Convert MIDI note number to note name"""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    note = notes[midi_note % 12]
    return f"{note}{octave}"

def main():
    parser = argparse.ArgumentParser(description='Analyze a MIDI file for rhythm patterns')
    parser.add_argument('midi_file', help='Path to the MIDI file to analyze')
    
    args = parser.parse_args()
    
    note_events, ppqn = extract_note_events(args.midi_file)
    
    if note_events and ppqn:
        analyze_rhythm_pattern(note_events, ppqn)
    else:
        print(f"Could not analyze {args.midi_file}")
        sys.exit(1)

if __name__ == '__main__':
    main() 