def file_merger():
    try:
        with open("wordlist_a.txt", "r") as file_a:
            wordlist_a = {
                line.strip()
                for line in file_a
                if line.strip()
            }

        with open("wordlist_b.txt", "r") as file_b:
            wordlist_b = {
                line.strip()
                for line in file_b
                if line.strip()
            }

        combined_wordlist = wordlist_a | wordlist_b

        with open("merged_wordlist.txt", "w") as merged_file:
            for payload in combined_wordlist:
                merged_file.write(payload + "\n")

        total_a = len(wordlist_a)
        total_b = len(wordlist_b)
        total_combined = len(combined_wordlist)

        duplicates_removed = (total_a + total_b) - total_combined

        print(f"[+] Total unique entries : {total_combined}")
        print(f"[*] Duplicates removed   : {duplicates_removed}")

    except FileNotFoundError:
        print("[!] File not found")


file_merger()