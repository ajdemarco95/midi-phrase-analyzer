#!/usr/bin/env python3
import os
import argparse
import sys
import json
from analyze_midi_data import analyze_rhythm_pattern, extract_note_events
from collections import Counter, defaultdict

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

def extract_pattern_sequences(note_events, ppqn):
    """
    Extract both rhythmic and melodic pattern sequences from note events
    
    Args:
        note_events (list): List of note events
        ppqn (int): Pulses Per Quarter Note
        
    Returns:
        tuple: (rhythmic_pattern, melodic_pattern)
    """
    from collections import defaultdict
    
    if not note_events:
        return "", "", []
    
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
    
    # Detect measure length (assuming 4/4 time signature)
    measure_length = 4 * ppqn  # 4 quarter notes per measure
    
    # Create a rhythm grid
    max_time = max(absolute_times) if absolute_times else 0
    measures = (max_time // measure_length) + 1
    
    # -- RHYTHMIC ANALYSIS --
    
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
    identical_rhythm_measures = defaultdict(list)
    for i, pattern1 in enumerate(measure_onset_patterns):
        for j, pattern2 in enumerate(measure_onset_patterns):
            if i != j and pattern1 == pattern2:
                identical_rhythm_measures[i].append(j)
    
    # Find rhythm measure groups
    rhythm_measure_groups = []
    processed = set()
    
    for i in range(len(measure_onset_patterns)):
        if i in processed:
            continue
            
        group = [i]
        processed.add(i)
        
        for j in identical_rhythm_measures.get(i, []):
            if j not in processed:
                group.append(j)
                processed.add(j)
        
        if group:
            rhythm_measure_groups.append(sorted(group))
    
    # Analyze rhythmic pattern sequence
    rhythm_pattern_sequence = []
    rhythm_pattern_map = {}
    
    for i in range(len(rhythm_measure_groups)):
        rhythm_pattern_map[i] = chr(65 + i)  # A, B, C, etc.
    
    for i in range(len(measure_onset_patterns)):
        for group_idx, group in enumerate(rhythm_measure_groups):
            if i in group:
                rhythm_pattern_sequence.append(rhythm_pattern_map[group_idx])
                break
    
    # -- MELODIC ANALYSIS --
    
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
    
    return ''.join(rhythm_pattern_sequence), ''.join(melodic_pattern_sequence), measure_onset_patterns

def extract_unique_rhythm_patterns(measure_onset_patterns):
    """
    Extract unique 1-bar rhythm patterns from all measures
    
    Args:
        measure_onset_patterns (list): List of onset patterns for each measure
        
    Returns:
        set: Set of unique rhythm patterns (as frozen sets for hashability)
    """
    # Convert each pattern to a frozenset for hashability
    unique_patterns = set()
    
    for pattern in measure_onset_patterns:
        # Convert to frozenset for hashability
        unique_patterns.add(frozenset(pattern))
    
    return unique_patterns

def process_midi_file(midi_file, rhythm_counter, melodic_counter, unique_rhythms, rhythm_pattern_counter, files_with_pattern):
    """
    Process a single MIDI file and run the analysis
    
    Args:
        midi_file (str): Path to MIDI file
        rhythm_counter (Counter): Counter to collect rhythmic pattern data
        melodic_counter (Counter): Counter to collect melodic pattern data
        unique_rhythms (set): Set to collect unique rhythm patterns
        rhythm_pattern_counter (Counter): Counter to track frequency of each rhythm pattern
        files_with_pattern (dict): Dictionary tracking which files contain each pattern
    """
    print(f"\n\n{'=' * 80}")
    print(f"Processing: {midi_file}")
    print(f"{'=' * 80}")
    
    note_events, ppqn = extract_note_events(midi_file)
    
    if note_events and ppqn:
        # Run the full analysis with output
        analyze_rhythm_pattern(note_events, ppqn)
        
        # Extract just the patterns for our visualization
        rhythm_pattern, melodic_pattern, measure_onset_patterns = extract_pattern_sequences(note_events, ppqn)
        
        # Extract and store unique rhythm patterns
        file_unique_rhythms = extract_unique_rhythm_patterns(measure_onset_patterns)
        unique_rhythms.update(file_unique_rhythms)
        
        # Count the frequency of each rhythm pattern
        for pattern in measure_onset_patterns:
            rhythm_pattern_counter[frozenset(pattern)] += 1
        
        # Track which patterns appear in this file (only count each pattern once per file)
        file_patterns = set()
        for pattern in measure_onset_patterns:
            pattern_key = frozenset(pattern)
            file_patterns.add(pattern_key)
        
        # Update the files_with_pattern dictionary for each unique pattern in this file
        for pattern_key in file_patterns:
            if pattern_key not in files_with_pattern:
                files_with_pattern[pattern_key] = set()
            files_with_pattern[pattern_key].add(midi_file)
        
        if rhythm_pattern:
            rhythm_counter[rhythm_pattern] += 1
        
        if melodic_pattern:
            melodic_counter[melodic_pattern] += 1
            
        # Create and save JSON metadata file for this MIDI file
        create_metadata_file(midi_file, rhythm_pattern, melodic_pattern)
    else:
        print(f"Could not analyze {midi_file}")

def create_metadata_file(midi_file, rhythm_pattern, melodic_pattern):
    """
    Create and save a JSON metadata file for a MIDI file
    
    Args:
        midi_file (str): Path to MIDI file
        rhythm_pattern (str): Rhythmic pattern (e.g. 'AABA')
        melodic_pattern (str): Melodic pattern (e.g. 'ABAB')
    """
    # Create metadata structure
    metadata = {
        "phrasal": {
            "rhythmic": {
                "pattern": rhythm_pattern
            },
            "melodic": {
                "pattern": melodic_pattern
            }
        }
    }
    
    # Generate metadata filename by replacing the MIDI extension with .json
    metadata_file = os.path.splitext(midi_file)[0] + ".json"
    
    # Save the metadata as JSON
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=4)
    
    print(f"Created metadata file: {metadata_file}")

def create_pattern_chart(rhythm_counter, melodic_counter):
    """
    Create a bar chart showing the distribution of both rhythmic and melodic phrase patterns
    
    Args:
        rhythm_counter (Counter): Counter object with rhythmic pattern sequences and counts
        melodic_counter (Counter): Counter object with melodic pattern sequences and counts
    """
    if not rhythm_counter and not melodic_counter:
        print("No pattern data to visualize")
        return
    
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Create stats directory if it doesn't exist
        stats_dir = "stats"
        os.makedirs(stats_dir, exist_ok=True)
        
        # Combine counters to find most common patterns
        combined_counter = Counter()
        for pattern in rhythm_counter:
            combined_counter[pattern] += rhythm_counter[pattern]
        for pattern in melodic_counter:
            combined_counter[pattern] += melodic_counter[pattern]
        
        # Get the most common patterns (limit to top 15 if there are many)
        MAX_PATTERNS = 15
        if len(combined_counter) > MAX_PATTERNS:
            print(f"\nNote: Limiting chart to the top {MAX_PATTERNS} most common patterns from {len(combined_counter)} total patterns")
            most_common_patterns = [item[0] for item in combined_counter.most_common(MAX_PATTERNS)]
            sorted_patterns = most_common_patterns
        else:
            sorted_patterns = sorted(combined_counter.keys())
        
        # Prepare data for grouped bar chart
        rhythmic_counts = [rhythm_counter.get(pattern, 0) for pattern in sorted_patterns]
        melodic_counts = [melodic_counter.get(pattern, 0) for pattern in sorted_patterns]
        
        # Adjust figure size based on number of patterns
        fig_width = max(12, len(sorted_patterns) * 0.8)
        plt.figure(figsize=(fig_width, 8))
        
        # Set up bar positions
        x = np.arange(len(sorted_patterns))
        width = 0.35
        
        # Create bars
        plt.bar(x - width/2, rhythmic_counts, width, label='Rhythmic Patterns', color='royalblue')
        plt.bar(x + width/2, melodic_counts, width, label='Melodic Patterns', color='orange')
        
        # Add labels and title
        plt.xlabel('Pattern')
        plt.ylabel('Frequency')
        plt.title('Distribution of Phrase Patterns in MIDI Files')
        
        # Rotate labels for better readability if there are many patterns
        if len(sorted_patterns) > 5:
            plt.xticks(x, sorted_patterns, rotation=45, ha='right')
        else:
            plt.xticks(x, sorted_patterns)
            
        plt.legend()
        
        # Add gridlines for better readability
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add value labels on top of bars
        for i, count in enumerate(rhythmic_counts):
            if count > 0:
                plt.text(i - width/2, count + 0.1, str(count), ha='center')
                
        for i, count in enumerate(melodic_counts):
            if count > 0:
                plt.text(i + width/2, count + 0.1, str(count), ha='center')
        
        # Add information about total patterns analyzed
        if len(combined_counter) > MAX_PATTERNS:
            patterns_text = f"Showing top {len(sorted_patterns)} of {len(combined_counter)} total patterns"
            plt.figtext(0.5, 0.01, patterns_text, ha='center', fontsize=10, 
                      bbox={'facecolor': 'lightgray', 'alpha': 0.5, 'pad': 5})
        
        # Save the chart
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)  # Add space at bottom for rotated labels
        output_path = os.path.join(stats_dir, 'pattern_distribution.png')
        plt.savefig(output_path)
        print(f"\nChart saved as: {output_path}")
        
        # Show the chart
        plt.show()
        
        # Print full stats for all patterns if limited
        if len(combined_counter) > MAX_PATTERNS:
            print("\nComplete pattern statistics:")
            print(f"{'Pattern':<10} {'Rhythmic':<10} {'Melodic':<10} {'Total':<10}")
            print("-" * 40)
            for pattern, total in combined_counter.most_common():
                r_count = rhythm_counter.get(pattern, 0)
                m_count = melodic_counter.get(pattern, 0)
                print(f"{pattern:<10} {r_count:<10} {m_count:<10} {total:<10}")
        
    except ImportError:
        print("\nWarning: matplotlib is not installed. Cannot create visualization.")
        print("To install, run: pip install matplotlib")

def visualize_rhythm_patterns(unique_rhythms, rhythm_pattern_counter=None, files_with_pattern=None):
    """
    Create a visualization of the unique rhythm patterns
    
    Args:
        unique_rhythms (set): Set of unique rhythm patterns
        rhythm_pattern_counter (Counter, optional): Counter with frequency of each pattern
        files_with_pattern (dict, optional): Dictionary tracking which files contain each pattern
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        import numpy as np
        
        # Create stats directory if it doesn't exist
        stats_dir = "stats"
        os.makedirs(stats_dir, exist_ok=True)
        
        # Convert frozensets to sorted lists for better display
        sorted_patterns = [sorted(list(pattern)) for pattern in unique_rhythms]
        
        # If we have frequency data, sort by file frequency first, then by occurrence count
        if files_with_pattern and rhythm_pattern_counter:
            # Create a list of (pattern, num_files, total_occurrences)
            pattern_data = []
            for pattern in sorted_patterns:
                pattern_key = frozenset(pattern)
                num_files = len(files_with_pattern.get(pattern_key, set()))
                total_occurrences = rhythm_pattern_counter[pattern_key]
                pattern_data.append((pattern, num_files, total_occurrences))
            
            # Sort by number of files first, then by total occurrences
            pattern_data.sort(key=lambda x: (-x[1], -x[2], len(x[0]), x[0]))
            
            sorted_patterns = [p[0] for p in pattern_data]
            file_counts = [p[1] for p in pattern_data]
            occurrences = [p[2] for p in pattern_data]
        elif rhythm_pattern_counter:
            # Fall back to sorting by occurrence count if file data not available
            pattern_freq = [(pattern, rhythm_pattern_counter[frozenset(pattern)]) for pattern in sorted_patterns]
            pattern_freq.sort(key=lambda x: (-x[1], len(x[0]), x[0]))
            sorted_patterns = [p[0] for p in pattern_freq]
            occurrences = [p[1] for p in pattern_freq]
            file_counts = None
        else:
            # Default sort by length and content
            sorted_patterns.sort(key=lambda x: (len(x), x if x else [-1]))
            occurrences = None
            file_counts = None
        
        # Limit to top 30 patterns if there are many
        MAX_PATTERNS = 30
        if len(sorted_patterns) > MAX_PATTERNS:
            print(f"\nNote: Limiting visualization to {MAX_PATTERNS} patterns")
            sorted_patterns = sorted_patterns[:MAX_PATTERNS]
            if occurrences:
                occurrences = occurrences[:MAX_PATTERNS]
            if file_counts:
                file_counts = file_counts[:MAX_PATTERNS]
        
        # Create the figure
        num_patterns = len(sorted_patterns)
        
        # Calculate more appropriate figure size
        fig_height = max(6, num_patterns * 0.5)  # Increased height for better readability
        fig, ax = plt.subplots(figsize=(12, fig_height))
        
        # Set background color for better contrast
        ax.set_facecolor('#f8f8f8')
        
        # Draw the measures grid
        for i in range(num_patterns):
            y_pos = num_patterns - i - 1  # Reverse order for better visualization
            
            # Draw horizontal separator line
            ax.axhline(y=y_pos-0.5, color='gray', linestyle='-', alpha=0.3, linewidth=1)
        
        # Add a final horizontal line at the bottom
        ax.axhline(y=-0.5, color='gray', linestyle='-', alpha=0.3, linewidth=1)
        
        # Draw vertical lines for beats
        for beat in range(5):  # 0 to 4 (inclusive) to show measure boundaries
            x_pos = beat * 4
            ax.axvline(x=x_pos, color='gray', linestyle='-', alpha=0.5, linewidth=1)
            
        # For each pattern, draw the rhythm
        for i, pattern in enumerate(sorted_patterns):
            y_pos = num_patterns - i - 1  # Reverse order for better visualization
            
            # Draw note markers
            for pos in range(16):
                # Background shading for beats
                if pos % 4 == 0:
                    ax.add_patch(Rectangle((pos, y_pos-0.4), 1, 0.8, facecolor='#e8e8e8', alpha=0.5, edgecolor=None))
                    
                # Draw notes
                if pos in pattern:
                    ax.add_patch(Rectangle((pos-0.35, y_pos-0.35), 0.7, 0.7, facecolor='royalblue', edgecolor='black', linewidth=0.5))
            
            # Add pattern label with frequency if available
            if file_counts and occurrences:
                label = f"Pattern {i+1} (in {file_counts[i]} files, {occurrences[i]} times)"
            elif occurrences:
                label = f"Pattern {i+1} ({occurrences[i]} times)"
            else:
                label = f"Pattern {i+1}"
                
            ax.text(-1, y_pos, label, va='center', ha='right', fontsize=10)
            
            # Add a small descriptive text of the pattern
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
            
            pattern_text = ' '.join(readable_positions)
            if len(pattern_text) > 25:  # Truncate if too long
                pattern_text = pattern_text[:22] + '...'
                
            ax.text(17, y_pos, pattern_text, va='center', ha='left', fontsize=9, color='#444444')
        
        # Set the axis limits
        ax.set_xlim(-2, 20)  # Expanded to show pattern text
        ax.set_ylim(-0.5, num_patterns - 0.5)
        
        # Add labels and title
        ax.set_title(f'Unique 1-bar Rhythm Patterns ({len(unique_rhythms)} total)', fontsize=14, pad=10)
        ax.set_xlabel('16th Note Position in Measure', fontsize=12, labelpad=10)
        
        # Remove y-axis ticks
        ax.set_yticks([])
        
        # Add beat numbers
        for beat in range(4):
            ax.text(beat*4 + 2, -0.2, f'Beat {beat+1}', ha='center', va='top', fontsize=10, 
                   bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
        
        # Add a grid for sixteenth notes (faint vertical lines)
        for pos in range(16):
            if pos % 4 != 0:  # Only add lines that aren't on the beat
                ax.axvline(x=pos, color='gray', linestyle='-', alpha=0.15, linewidth=0.5)
        
        # Draw x-axis to indicate the measure boundary
        ax.axhline(y=-0.5, color='black', linestyle='-', alpha=0.5, linewidth=1.5)
        
        # Add a note about the visualization
        note_text = "Visualization shows each unique rhythm pattern with 16th note grid. Blue squares indicate note onsets."
        if len(unique_rhythms) > MAX_PATTERNS:
            note_text += f" Showing top {MAX_PATTERNS} of {len(unique_rhythms)} patterns by frequency."
            
        plt.figtext(0.5, 0.01, note_text, ha='center', fontsize=9, 
                   bbox=dict(facecolor='white', alpha=0.8, edgecolor='lightgray', boxstyle='round,pad=0.5'))
        
        # Adjust layout and save
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.06)  # Add space for note at bottom
        output_path = os.path.join(stats_dir, 'rhythm_patterns.png')
        plt.savefig(output_path, dpi=120)
        print(f"\nRhythm patterns visualization saved as: {output_path}")
        
        # Show the chart
        plt.show()
        
    except ImportError:
        print("\nWarning: matplotlib is not installed. Cannot create visualization.")
        print("To install, run: pip install matplotlib")

def create_rhythm_summary(unique_rhythms, rhythm_pattern_counter, files_with_pattern=None):
    """
    Create a summary visualization of the most common rhythm patterns
    
    Args:
        unique_rhythms (set): Set of unique rhythm patterns
        rhythm_pattern_counter (Counter): Counter with frequency of each pattern
        files_with_pattern (dict, optional): Dictionary tracking which files contain each pattern
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.patches import Rectangle
        
        # Create stats directory if it doesn't exist
        stats_dir = "stats"
        os.makedirs(stats_dir, exist_ok=True)
        
        # Only show the top patterns
        TOP_PATTERNS = 10
        
        # Convert frozensets to sorted lists for better display
        sorted_patterns = [sorted(list(pattern)) for pattern in unique_rhythms]
        
        # If we have file frequency data, sort by that first
        if files_with_pattern:
            # Create a list of (pattern, num_files, total_occurrences)
            pattern_data = []
            for pattern in sorted_patterns:
                pattern_key = frozenset(pattern)
                num_files = len(files_with_pattern.get(pattern_key, set()))
                total_occurrences = rhythm_pattern_counter[pattern_key]
                pattern_data.append((pattern, num_files, total_occurrences))
            
            # Sort by number of files first, then by total occurrences
            pattern_data.sort(key=lambda x: (-x[1], -x[2], len(x[0]), x[0]))
            
            # Take only the top patterns
            top_patterns_data = pattern_data[:TOP_PATTERNS]
            
            # Extract data for plotting
            patterns = [p[0] for p in top_patterns_data]
            file_counts = [p[1] for p in top_patterns_data]
            frequencies = [p[2] for p in top_patterns_data]
            
            # Value to show in the bar chart
            bar_values = file_counts
            bar_title = 'Number of Files'
            bar_xlabel = 'Files Containing Pattern'
        else:
            # Fall back to sorting by occurrence count if file data not available
            pattern_freq = [(pattern, rhythm_pattern_counter[frozenset(pattern)]) for pattern in sorted_patterns]
            pattern_freq.sort(key=lambda x: (-x[1], len(x[0]), x[0]))
            
            # Take only the top patterns
            top_patterns = pattern_freq[:TOP_PATTERNS]
            
            # Extract data for plotting
            patterns = [p[0] for p in top_patterns]
            frequencies = [p[1] for p in top_patterns]
            file_counts = None
            
            # Value to show in the bar chart
            bar_values = frequencies
            bar_title = 'Frequency'
            bar_xlabel = 'Number of Occurrences'
        
        # Create a figure with two subplots - rhythm grid and frequency bar chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8), gridspec_kw={'width_ratios': [3, 1]})
        
        # Set background color
        ax1.set_facecolor('#f8f8f8')
        ax2.set_facecolor('#f8f8f8')
        
        # Create grid in first subplot
        num_patterns = len(patterns)
        
        # Draw horizontal separator lines
        for i in range(num_patterns + 1):
            y_pos = i - 0.5
            ax1.axhline(y=y_pos, color='gray', linestyle='-', alpha=0.3, linewidth=1)
        
        # Draw vertical lines for beats
        for beat in range(5):  # 0 to 4 (inclusive) to show measure boundaries
            x_pos = beat * 4
            ax1.axvline(x=x_pos, color='gray', linestyle='-', alpha=0.5, linewidth=1)
            
        # For each pattern, draw the rhythm
        for i, pattern in enumerate(patterns):
            # Draw note markers
            for pos in range(16):
                # Background shading for beats
                if pos % 4 == 0:
                    ax1.add_patch(Rectangle((pos, i-0.4), 1, 0.8, facecolor='#e8e8e8', alpha=0.5, edgecolor=None))
                    
                # Draw notes
                if pos in pattern:
                    ax1.add_patch(Rectangle((pos-0.35, i-0.35), 0.7, 0.7, facecolor='royalblue', edgecolor='black', linewidth=0.5))
            
            # Add pattern label with frequency
            if file_counts:
                label = f"Pattern {i+1} (in {file_counts[i]} files, {frequencies[i]} times)"
            else:
                label = f"Pattern {i+1} ({frequencies[i]} times)"
                
            ax1.text(-1, i, label, va='center', ha='right', fontsize=10)
            
            # Add a small descriptive text of the pattern
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
            
            pattern_text = ' '.join(readable_positions)
            ax1.text(17, i, pattern_text, va='center', ha='left', fontsize=9, color='#444444')
        
        # Add a grid for sixteenth notes (faint vertical lines)
        for pos in range(16):
            if pos % 4 != 0:  # Only add lines that aren't on the beat
                ax1.axvline(x=pos, color='gray', linestyle='-', alpha=0.15, linewidth=0.5)
        
        # Set the axis limits for the grid
        ax1.set_xlim(-2, 20)
        ax1.set_ylim(-0.5, num_patterns - 0.5)
        
        # Labels and title for the grid
        ax1.set_title('Most Common Rhythm Patterns', fontsize=14, pad=10)
        ax1.set_xlabel('16th Note Position in Measure', fontsize=12, labelpad=10)
        
        # Remove y-axis ticks
        ax1.set_yticks([])
        
        # Add beat numbers
        for beat in range(4):
            ax1.text(beat*4 + 2, -0.2, f'Beat {beat+1}', ha='center', va='top', fontsize=10, 
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
        
        # Create frequency bar chart in second subplot
        y_pos = np.arange(num_patterns)
        ax2.barh(y_pos, bar_values, color='royalblue', edgecolor='black', alpha=0.7)
        
        # Add labels to bars
        for i, val in enumerate(bar_values):
            ax2.text(val + max(bar_values) * 0.02, i, str(val), va='center', fontsize=10)
        
        # Set the axis limits for the bar chart
        ax2.set_xlim(0, max(bar_values) * 1.15)
        ax2.set_ylim(-0.5, num_patterns - 0.5)
        
        # Labels and title for the bar chart
        ax2.set_title(bar_title, fontsize=14, pad=10)
        ax2.set_xlabel(bar_xlabel, fontsize=12, labelpad=10)
        
        # Remove y-axis ticks
        ax2.set_yticks([])
        
        # Add gridlines to bar chart
        ax2.grid(axis='x', linestyle='--', alpha=0.3)
        
        # Overall title
        if file_counts:
            plt.suptitle(f'Top {num_patterns} Rhythm Patterns by Number of Files (out of {len(unique_rhythms)} total patterns)', 
                        fontsize=16, y=0.98)
        else:
            plt.suptitle(f'Top {num_patterns} Most Common 1-bar Rhythm Patterns (out of {len(unique_rhythms)} total)', 
                        fontsize=16, y=0.98)
        
        # Adjust layout and save
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        output_path = os.path.join(stats_dir, 'rhythm_summary.png')
        plt.savefig(output_path, dpi=120)
        print(f"\nSummary chart saved as: {output_path}")
        
        # Show the chart
        plt.show()
        
    except ImportError:
        print("\nWarning: matplotlib is not installed. Cannot create visualization.")
        print("To install, run: pip install matplotlib")

def main():
    parser = argparse.ArgumentParser(description='Analyze MIDI files for rhythm patterns')
    parser.add_argument('directory', help='Directory to search for MIDI files')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        sys.exit(1)
    
    midi_files = find_midi_files(args.directory)
    
    if not midi_files:
        print(f"No MIDI files found in {args.directory}")
        sys.exit(0)
    
    print(f"Found {len(midi_files)} MIDI files")
    
    # Initialize counters for collecting pattern data
    rhythm_counter = Counter()
    melodic_counter = Counter()
    
    # Initialize set for unique rhythm patterns
    unique_rhythms = set()
    
    # Initialize counter for rhythm pattern frequency
    rhythm_pattern_counter = Counter()
    
    # Initialize dictionary to track which files contain each pattern
    files_with_pattern = {}
    
    # Process all files and collect pattern data
    for midi_file in midi_files:
        process_midi_file(midi_file, rhythm_counter, melodic_counter, unique_rhythms, rhythm_pattern_counter, files_with_pattern)
    
    # Print the number of unique 1-bar rhythm patterns found
    print("\n\n" + "=" * 80)
    print(f"Number of unique 1-bar rhythm patterns: {len(unique_rhythms)}")
    
    # After processing all files, create and display the chart
    print("\n\n" + "=" * 80)
    print("Generating pattern distribution visualization...")
    create_pattern_chart(rhythm_counter, melodic_counter)

    # Display detailed information about the unique rhythm patterns
    if unique_rhythms:
        print("\n\n" + "=" * 80)
        print("Unique 1-bar rhythm patterns (sorted by number of files containing them, then total occurrences):")
        print("-" * 40)
        
        # Convert frozensets to sorted lists for better display
        sorted_patterns = [sorted(list(pattern)) for pattern in unique_rhythms]
        
        # Sort by number of files first, then by occurrence count
        pattern_data = []
        for pattern in sorted_patterns:
            pattern_key = frozenset(pattern)
            num_files = len(files_with_pattern.get(pattern_key, set()))
            total_occurrences = rhythm_pattern_counter[pattern_key]
            pattern_data.append((pattern, num_files, total_occurrences))
        
        pattern_data.sort(key=lambda x: (-x[1], -x[2], len(x[0]), x[0]))
        
        for i, (pattern, num_files, freq) in enumerate(pattern_data, 1):
            # Convert 16th note positions to more readable format (1.1, 1.2, etc.)
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
            
            print(f"Pattern {i}: {' '.join(readable_positions)} (in {num_files} files, occurs {freq} times)")
        
        # Create visualization of the rhythm patterns with frequency information
        print("\n\n" + "=" * 80)
        print("Generating rhythm patterns visualization...")
        visualize_rhythm_patterns(unique_rhythms, rhythm_pattern_counter, files_with_pattern)
        
        # Create summary visualization of most common patterns if we have enough patterns
        if len(unique_rhythms) > 5:
            print("\n\n" + "=" * 80)
            print("Generating summary of most common rhythm patterns...")
            create_rhythm_summary(unique_rhythms, rhythm_pattern_counter, files_with_pattern)

if __name__ == '__main__':
    main() 