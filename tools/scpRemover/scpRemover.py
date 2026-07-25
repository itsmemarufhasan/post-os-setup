import argparse
import sys
import os

def remove_duplicates(file1, file2):
    try:
        if not os.path.isfile(file1):
            print(f"Error: {file1} does not exist.")
            sys.exit(1)
        
        if not os.path.isfile(file2):
            print(f"Error: {file2} does not exist.")
            sys.exit(1)

        print(f"Reading from {file1} and {file2}...")

        with open(file1, 'r') as f1, open(file2, 'r') as f2:
            file1_content = f1.readlines()
            file2_content = f2.readlines()

        print(f"Content of {file1}: {file1_content}")
        print(f"Content of {file2}: {file2_content}")

        updated_content = [line for line in file1_content if line.strip() not in (line.strip() for line in file2_content)]

        print(f"Updated content to be written in {file1}: {updated_content}")

        with open(file1, 'w') as f1:
            f1.writelines(updated_content)

        print(f"Successfully updated {file1} by removing lines found in {file2}.")
    
    except FileNotFoundError as e:
        print(f"File error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(description="Remove duplicate text from one file based on another.")
    parser.add_argument('-r', '--read', help="File to read and remove duplicates from", required=True)
    parser.add_argument('-d', '--delete', help="File containing the text to be removed", required=True)

    args = parser.parse_args()

    remove_duplicates(args.read, args.delete)

if __name__ == "__main__":
    main()
