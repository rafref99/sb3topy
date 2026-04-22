import cProfile
import pstats
import io
import sys
import os
import argparse
from sb3topy import main

def profile_conversion(project_path, output_path):
    """Profiles the conversion of a Scratch project."""
    print(f"Profiling conversion of {project_path}...")
    
    pr = cProfile.Profile()
    pr.enable()
    
    # Run the main conversion process
    # Mocking args for main.main
    sys.argv = ['sb3topy', project_path, output_path, '-r'] if '-r' in sys.argv else ['sb3topy', project_path, output_path]
    
    try:
        main.main()
    except SystemExit:
        pass
    
    pr.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(30)
    
    print(s.getvalue())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Profile sb3topy conversion")
    parser.add_argument("project", help="Path to the .sb3 file")
    parser.add_argument("--output", default="profile_output", help="Output directory")
    args = parser.parse_args()
    
    if not os.path.exists(args.project):
        print(f"Error: Project file {args.project} not found.")
        sys.exit(1)
        
    profile_conversion(args.project, args.output)
