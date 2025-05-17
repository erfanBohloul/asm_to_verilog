from processor import process_asm
from generator import generate_verilog
import sys

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python parser.py <filename>")
        sys.exit(1)
    
    print("Processing ASM file...")

    filename = sys.argv[1]
    processed_data = process_asm(filename)

    print("Processed Data:")
    print(processed_data)

    print("Generating Verilog code...")
    verilog = generate_verilog(processed_data)
    
# Improved file handling
output_file = "output.v"
try:
    with open(output_file, "w") as f:
        f.write("\n".join(verilog))
    print(f"Verilog code written to {output_file}")
except IOError as e:
    print(f"Error writing file: {e}")
    sys.exit(1)

    